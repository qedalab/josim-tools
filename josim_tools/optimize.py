""" Optimization routines and containers """

from typing import List, Optional, Tuple, Dict
from multiprocessing import cpu_count

import numpy as np
from scipy.optimize import differential_evolution, OptimizeResult
from scipy.spatial.distance import cdist as scipy_cdist

from .configuration import (
    VerifyConfiguration,
    MarginAnalysisConfiguration,
    OptimizeConfiguration,
    OptimizerParameterConfiguration,
)
from .analysis import MarginAnalysis, print_margin_analysis_result


class NumpyVectorArray:
    """ Dynamic array of numpy arrays """

    # data.shape == (num_arrays_in_vector, array_size)
    data_: np.ndarray

    size_: int

    def __init__(self, array_size: int, default_allocation: int = 4):
        assert default_allocation >= 0
        self.size_ = 0
        self.data_ = np.empty((default_allocation, array_size))

    def append(self, array: np.ndarray) -> None:
        """ Append the array to the vector """

        size = self.size()
        capacity = self.capacity()

        new_size = size + 1

        if new_size > capacity:
            if capacity == 0:
                new_capacity = 1
            else:
                new_capacity = capacity * 2

            new_data = np.empty((new_capacity, self.array_size()))
            new_data[:size] = self.view()
            self.data_ = new_data

        self.data_[size] = array
        self.size_ += 1

    def append_list(self, list_of_arrays: List[np.ndarray]) -> None:
        """ Append all items in array to the vector """
        for array in list_of_arrays:
            self.append(array)

    def size(self) -> int:
        """ Returns the number of arrays in the vector """
        out = self.size_
        assert out >= 0
        return out

    def capacity(self) -> int:
        """ Returns the capacity of vector """
        return self.data_.shape[0]

    def array_size(self) -> int:
        """ Returns the array size of the vector """
        return self.data_.shape[1]

    def view(self) -> np.ndarray:
        """ Returns a view of the data """
        out = self.data_[: self.size(), :]
        out.flags.writeable = False
        return out


class OptimizeState:
    """ State required during optimization """

    guessed_points_: NumpyVectorArray
    points_of_failure_: NumpyVectorArray

    def __init__(self, num_parameters: int):
        self.guessed_points_ = NumpyVectorArray(num_parameters)
        self.points_of_failure_ = NumpyVectorArray(num_parameters)

    def add_guess(self, guessed_point: np.ndarray) -> None:
        """ Add a guess """
        self.guessed_points_.append(guessed_point)

    def add_point_of_failure(self, point_of_failure: np.ndarray) -> None:
        """ Add a point of failure """
        self.points_of_failure_.append(point_of_failure)

    def add_points_of_failure(self, points_of_failure: List[np.ndarray]) -> None:
        """ Add multiple points of failure """
        self.points_of_failure_.append_list(points_of_failure)

    def guessed_points(self) -> np.ndarray:
        """ Returns a view to the guessed points """
        return self.guessed_points_.view()

    def points_of_failure(self) -> np.ndarray:
        """ Returns a view to the points of failure """
        return self.points_of_failure_.view()


class OptimizerParameter:
    """ Optimizer parameter """

    minimum_: Optional[float]
    maximum_: Optional[float]

    adjustable_: bool
    testable_: bool

    def __init__(
        self,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        adjustable: bool = True,
        testable: bool = True,
    ):

        assert adjustable or testable

        if minimum is not None:
            assert minimum >= 0

        self.minimum_ = minimum
        self.maximum_ = maximum
        self.adjustable_ = adjustable
        self.testable_ = testable

    @property
    def minimum(self) -> float:
        """ Returns the parameter minimum """
        if self.minimum_ is None:
            return 0

        return self.minimum_

    @property
    def maximum(self) -> float:
        """ Returns the parameter maximum """
        if self.maximum_ is None:
            return float("inf")

        return self.maximum_

    @property
    def adjustable(self) -> bool:
        """ Returns wether the parameter is adjustable """
        return self.adjustable_

    @property
    def testable(self) -> bool:
        """ Returns wether the parameter is testable """
        return self.testable_

    def adjust_boundaries(self, boundaries: Tuple[float, float]) -> Tuple[float, float]:
        """ Adjusts the boundaries to account for min and max """
        assert self.adjustable_
        assert boundaries[0] < boundaries[1]
        assert boundaries[0] < self.maximum
        assert boundaries[1] > self.minimum

        lower = max(boundaries[0], self.minimum)
        upper = min(boundaries[1], self.maximum)

        return (lower, upper)


class Optimizer:
    """ Class that handles the optimization """

    parameters_: Dict[str, OptimizerParameter]

    state_: OptimizeState

    converge_: float
    search_radius_: float
    max_iterations_: int

    margin_analysis_: MarginAnalysis
    num_parameters_: int
    num_margin_threads_: int

    verbose_ = True
    debug_ = True

    keys_: List[str]
    ones_: np.ndarray

    def __init__(
        self,
        verify_config: VerifyConfiguration,
        margin_config: MarginAnalysisConfiguration,
        optimize_config: OptimizeConfiguration,
        optimize_parameters: Dict[str, OptimizerParameterConfiguration],
    ):
        self.margin_analysis_ = MarginAnalysis(verify_config, margin_config)

        self.converge_ = optimize_config.converge
        self.search_radius_ = optimize_config.search_radius
        self.max_iterations_ = optimize_config.max_iterations

        self.parameters_ = {}
        for key, item in optimize_parameters.items():
            self.parameters_[key] = OptimizerParameter(item.min, item.max)

        self.keys_ = list(optimize_parameters.keys())

        self.num_margin_threads_ = min(2 * self.num_parameters(), cpu_count())

        self.state_ = OptimizeState(self.num_parameters())
        self.ones_ = np.ones((1, self.num_parameters()))

    def num_parameters(self) -> int:
        """ Returns the number of parameters """
        return len(self.parameters_)

    def _analyze_point(self, point: Dict[str, float]) -> None:
        """ Analyze the point and update state """

        print("Analyzing point")

        keys = self.keys_
        data = np.empty((self.num_parameters()), float)

        for index, key in enumerate(keys):
            data[index] = point[key]

        print("  Adding point to list of guesses")
        self.state_.add_guess(data)

        print("  Doing margin analysis of point:")
        print()

        margin_output = self.margin_analysis_.analyse(point, self.num_margin_threads_)
        print_margin_analysis_result(margin_output)

        max_search = self.margin_analysis_.max_search
        min_search = self.margin_analysis_.min_search

        print()
        print("  Adding all margin boundaries to points of failure")
        for index, key in enumerate(keys):
            initial = data[index]

            min_margin, max_margin = margin_output[key]

            if not np.isclose(min_margin, min_search):
                data[index] = initial * min_margin
                self.state_.add_point_of_failure(data)

            if not np.isclose(max_margin, max_search):
                data[index] = initial * max_margin
                self.state_.add_point_of_failure(data)

            data[index] = initial

        print("  Finished analyzing point")

    def _get_guess_boundaries(
        self, current_best_point: np.ndarray
    ) -> List[Tuple[float, float]]:

        boundaries: List[Tuple[float, float]] = []

        for index, key in enumerate(self.keys_):
            xi = float(current_best_point[index])
            min_boundary = (1 - self.search_radius_) * xi
            max_boundary = (1 + self.search_radius_) * xi

            boundary = (min_boundary, max_boundary)

            boundary = self.parameters_[key].adjust_boundaries(boundary)

            boundaries.append(boundary)

        if self.debug_:
            print("  Debug: Boundaries:")
            for index, key in enumerate(self.keys_):
                print("    {}: {}".format(key, boundaries[index]))

        return boundaries

    def _score(self, x_array: np.ndarray) -> np.ndarray:
        if len(x_array.shape) == 1:
            x_array = x_array.reshape((1, -1))

        num = x_array.shape[0]
        out = np.empty((num), dtype=float)

        for i in range(num):
            x = x_array[i]
            assert x.shape == (self.num_parameters(),)

            samples = self.state_.points_of_failure() / x[np.newaxis, :]
            distances = scipy_cdist(self.ones_, samples)
            out[i] = float(np.min(distances))

        return out * 100

    def _cost(self, x_array: np.ndarray) -> np.ndarray:
        return -self._score(x_array)

    def _best_point(self) -> np.ndarray:
        guessed_points = self.state_.guessed_points()
        scores = self._score(guessed_points)
        max_index = np.argmax(scores)
        best_point = guessed_points[max_index]
        return best_point

    def _next_guess(self, current_best_point: np.ndarray) -> np.ndarray:
        print("Determining next guess")

        print("  Computing guess boundaries")
        guess_boundaries = self._get_guess_boundaries(current_best_point)

        print("  Starting differential evolution routine", flush=True)
        # result: OptimizeResult = differential_evolution(
        #     self._score, guess_boundaries, workers=-1
        # )
        result: OptimizeResult = differential_evolution(
            self._cost, guess_boundaries, workers=1, popsize=25, maxiter=10000
        )

        if self.verbose_:
            print("  Verbose: Differential evolution completed")
            print("    number of function evaluations: {}".format(result.nfev))
            print("    number of iterations: {}".format(result.nit))

        if not result.success:
            print()
            print("ERROR: unable to determine next guess with differential evolution")
            print("  message: {}".format(result.message))
            exit(-1)

        next_guess = result.x

        print("  Next guess found")
        print("    value = {}".format(next_guess))
        print("    estimated score = {}".format(float(self._score(next_guess))))
        print(flush=True)

        return next_guess

    def _array_to_dict(self, array: np.ndarray) -> Dict[str, float]:
        out: Dict[str, float] = {}

        for index, key in enumerate(self.keys_):
            out[key] = array[index]

        return out

    def _dict_to_array(self, parameters: Dict[str, float]) -> np.ndarray:
        out: List[float] = []

        for key in self.keys_:
            out.append(parameters[key])

        return np.array(out)

    def optimize(self, x0: Dict[str, float]) -> None:

        print("Starting value optimization")
        self._analyze_point(x0)
        best_point = self._dict_to_array(x0)
        iteration = 1

        # Iterate
        while iteration < self.max_iterations_:
            print("Starting iteration {}".format(iteration), flush=True)
            iteration += 1

            best_point = self._best_point()
            best_score = float(self._score(best_point))

            print("Current best:")
            print("  point: {}".format(best_point))
            print("  score: {}".format(best_score), flush=True)

            next_guess = self._next_guess(best_point)
            estimated_score = float(self._score(next_guess))

            print("Verifying next guess", flush=True)
            next_guess_dict = self._array_to_dict(next_guess)
            valid: bool = self.margin_analysis_.verifier_.verify(next_guess_dict)

            if not valid:
                print("Adding invalid guess to known points of failure")
                self.state_.add_point_of_failure(next_guess)
                print("Skipping analysis of invalid point")
                continue

            self._analyze_point(next_guess_dict)

            actual_score = float(self._score(next_guess))
            estimation_error = estimated_score - actual_score

            print("Guess score estimation error: {}".format(estimation_error))

            if estimation_error < self.converge_:
                print("Convergence reached")
                break

        if iteration >= self.max_iterations_:
            print("Reached maximum number of iterations")

        optimized_point = self._best_point()
        optimized_score = float(self._score(optimized_point))

        print("Optimized:")
        print("  point: {}".format(optimized_point))
        print("  score: {}".format(optimized_score))
