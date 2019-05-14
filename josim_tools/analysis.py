""" Module that contains the yield information """
from typing import Dict, Tuple, Optional, List
from copy import deepcopy
from math import floor, isclose
from shutil import get_terminal_size
from multiprocessing.pool import Pool
from multiprocessing import current_process
from time import time

from numpy.random import normal, seed
from numpy import isclose

from .verify import Verifier
from .configuration import (
    VerifyConfiguration,
    MarginAnalysisConfiguration,
    MarginParameterConfiguration,
    YieldParameterConfiguration,
)


class Yield:
    """ Class that keep track of yield """

    num_success_: int = 0
    num_failure_: int = 0

    def add_success(self) -> None:
        """ Add an success event """
        self.num_success_ += 1

    def add_failure(self) -> None:
        """ Add an failure event """
        self.num_failure_ += 1

    def add_event(self, did_succeed: bool) -> None:
        """ Add an event """
        if did_succeed:
            self.add_success()
        else:
            self.add_failure()

    def num_success(self) -> int:
        """ Number of success events registered """
        return self.num_success_

    def num_failure(self) -> int:
        """ Number of failure events registered """
        return self.num_failure_

    def num_total(self) -> int:
        """ Total number of events registered """
        return self.num_failure() + self.num_success()

    def percentage(self) -> float:
        """ Percentage success of events registered """
        if self.num_total() == 0:
            raise RuntimeError(
                "Yield::percentage is undefined when Yield::num_total() == 0"
            )

        return float(self.num_success_) / float(self.num_total())


class NormalDistribution:
    """ Normal distribution """

    mean_: float
    variance_: float

    def __init__(self, mean: float, variance: float):
        self.mean_ = mean
        self.variance_ = variance

    @property
    def mean(self) -> float:
        """ The mean of the distribution """
        return self.mean_

    @property
    def variance(self) -> float:
        """ The variance of the distribution """
        return self.variance_

    def sample(self) -> float:
        """ Return a sample from the distribution """
        return float(normal(self.mean_, self.variance_, 1))


class YieldAnalysis(Yield):
    """ Class that does yield analysis """

    distributions_: Dict[str, NormalDistribution]
    verifier_: Optional[Verifier] = None

    verify_configuration_: VerifyConfiguration

    seed_: int

    def __init__(
        self,
        verify_config: VerifyConfiguration,
        parameters: Dict[str, YieldParameterConfiguration],
    ):
        distributions = {}

        for key, value in parameters.items():
            distributions[key] = NormalDistribution(value.nominal, value.variance)

        self.distributions_ = distributions
        self.verify_configuration_ = verify_config

        self.seed_ = int(time())

    def _work(self, num_samples: int) -> Tuple[int, int]:
        """ Do a number of samples returning number of success and failures """

        # Random seed
        pid = current_process().pid
        seed(self.seed_ + pid)

        # Lazily create verifier
        if self.verifier_ is None:
            self.verifier_ = Verifier(self.verify_configuration_)

        success = 0
        failure = 0

        for _ in range(num_samples):
            parameters: Dict[str, float] = {}

            for key, value in self.distributions_.items():
                parameters[key] = value.sample()

            if self.verifier_.verify(parameters):
                success += 1
            else:
                failure += 1

        return success, failure

    def sample(self, total_num_samples: int, num_threads: int = 1) -> None:
        """ Do samples for yield analysis """

        assert num_threads >= 1

        if num_threads == 1:
            success, failure = self._work(total_num_samples)
            self.num_success_ += success
            self.num_failure_ += failure
        else:
            # Division of work
            per_thread = int(floor(total_num_samples / num_threads))
            remainder = total_num_samples - per_thread * num_threads
            num_samples = [per_thread for _ in range(num_threads)]

            for index in range(remainder):
                num_samples[index] += 1

            # Cache verifier before forking
            verifier = self.verifier_
            self.verifier_ = None

            # Do work
            with Pool(num_threads) as pool:
                results = pool.map(self._work, num_samples)
                for success, failure in results:
                    self.num_success_ += success
                    self.num_failure_ += failure

            self.verifier_ = verifier


class MarginAnalysis:
    """ Class that handles margin analysis """

    circuit_path_: str
    nominal_: Dict[str, float]
    verifier_: Optional[Verifier] = None

    # Configuration
    max_search = 1.9
    min_search = 0.1
    scan_steps = 4
    binary_search_steps = 3

    verify_configuration_: VerifyConfiguration

    def _margin_line(
        self, packed: Tuple[str, Dict[str, float], bool]
    ) -> Tuple[str, bool, float]:
        # Unpack
        variable: str = packed[0]
        all_params: Dict[str, float] = packed[1]
        positive: bool = packed[2]

        # Lazily create verifier
        if self.verifier_ is None:
            self.verifier_ = Verifier(self.verify_configuration_)

        value = all_params[variable]
        all_params = deepcopy(all_params)

        search_from = 1.0

        if positive:
            search_to = self.max_search
        else:
            search_to = self.min_search

        # Do steps (Assume center point is already valid)
        scan_step_size: float = (search_to - search_from) / self.scan_steps
        scan_stop = False

        for i in range(1, self.scan_steps + 1):
            current: float = 1 + i * scan_step_size
            all_params[variable] = value * current

            valid = self.verifier_.verify(all_params)

            if not valid:
                scan_stop = True
                search_to = current
                break

            search_from = current

        if not scan_stop:
            # Valid for entire range
            return variable, positive, search_to

        # Do binary search between search_from and search_to
        for _ in range(self.binary_search_steps):
            sample = (search_from + search_to) / 2
            all_params[variable] = value * sample

            valid = self.verifier_.verify(all_params)

            if valid:
                search_from = sample
            else:
                search_to = sample

        return variable, positive, (search_from + search_to) / 2

    def __init__(
        self,
        verify_configuration: VerifyConfiguration,
        margin_analysis_configuration: MarginAnalysisConfiguration,
    ):
        self.max_search = margin_analysis_configuration.max_search
        self.min_search = margin_analysis_configuration.min_search
        self.scan_steps = margin_analysis_configuration.scan_steps
        self.binary_search_steps = margin_analysis_configuration.binary_search_steps

        self.verify_configuration_ = verify_configuration

    def analyse(
        self, nominal: Dict[str, float], num_threads: int = 1
    ) -> Dict[str, Tuple[float, float]]:
        """ Do a margin analysis with the following points """

        # Lazily create verifier
        if self.verifier_ is None:
            self.verifier_ = Verifier(self.verify_configuration_)

        if not self.verifier_.verify(nominal):
            raise RuntimeError(
                "MarginAnalysis::analysis must have a valid starting" "position"
            )

        work_items: List[Tuple[str, Dict[str, float], bool]] = []

        for key, _ in nominal.items():
            work_items.append((key, nominal, True))
            work_items.append((key, nominal, False))

        assert num_threads >= 1

        completed = None

        if num_threads == 1:
            completed = [self._margin_line(packed) for packed in work_items]
        else:
            # Cache verifier
            verifier = self.verifier_
            self.verifier_ = None

            with Pool(num_threads) as pool:
                completed = pool.map(self._margin_line, work_items)

            self.verifier_ = verifier

        positive_out: Dict[str, float] = {}
        negative_out: Dict[str, float] = {}

        assert completed is not None

        for variable, positive, value in completed:
            if positive:
                positive_out[variable] = value
            else:
                negative_out[variable] = value

        assert len(positive_out.keys()) == len(negative_out.keys())

        out: Dict[str, Tuple[float, float]] = {}

        for variable, positive_value in positive_out.items():
            negative_value = negative_out[variable]
            out[variable] = (negative_value, positive_value)

        return out


def print_margin_analysis_result(
    result: Dict[str, Tuple[float, float]],
    screen_col: Optional[int] = None,
    left_size: float = 0.1,
    right_size: float = 1.9,
) -> None:
    result = deepcopy(result)

    if screen_col is None:
        screen_col = get_terminal_size((80, 1)).columns

    max_key_size = max([len(i) for i in result.keys()])
    unusabled_chars = 15 + max_key_size

    usable_chars = screen_col - unusabled_chars

    # TODO figure out how to handle to small screen space
    assert usable_chars > 2

    critical_margin_value: float = float("inf")
    critical_margin_parameters: List[str] = []

    def update_critical_margin(value: float, parameter: str) -> None:
        nonlocal critical_margin_parameters
        nonlocal critical_margin_value

        if isclose(critical_margin_value, value):
            critical_margin_parameters.append(parameter)
        elif critical_margin_value > value:
            critical_margin_value = value
            critical_margin_parameters = [parameter]

    # Adjust results to be within plotting range and determine critical margin
    for key, item in result.items():
        tmp = result[key]

        update_critical_margin(abs(1 - tmp[0]), key + "-")
        update_critical_margin(abs(1 - tmp[1]), key + "+")

        result[key] = (
            100 - max(left_size, tmp[0]) * 100,
            min(right_size, tmp[1]) * 100 - 100,
        )

    assert len(critical_margin_parameters) > 0

    # TODO adjust to be symmetric
    adjust = ""
    if isclose(1 - left_size, right_size - 1):
        if usable_chars % 2 == 1:
            adjust = " "
            usable_chars -= 1

    def bar(percentage: float, bar_size: int, left: bool) -> str:
        filled_num: int = int(percentage / 100 * bar_size)
        filled: str = filled_num * "#"
        not_filled: str = (bar_size - filled_num) * " "

        if left:
            out = not_filled + filled
        else:
            out = filled + not_filled

        return out

    bar_left: int = int(usable_chars / 2)
    bar_right: int = int(usable_chars / 2)

    for key, item in result.items():
        print(
            "{key}: {adjust}{left:>4.1f} [{bar_left}|{bar_right}] {right:>4.1f}".format(
                key=key.ljust(max_key_size),
                adjust=adjust,
                left=item[0],
                bar_left=bar(item[0], bar_left, True),
                bar_right=bar(item[1], bar_right, False),
                right=item[1],
            )
        )

    print(
        "Critical margin: {1:>4.1f} % {0}".format(
            critical_margin_parameters, critical_margin_value * 100
        )
    )
