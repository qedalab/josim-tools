""" Configuration options """

from typing import Optional, Dict
from copy import deepcopy

import attr
from jsonschema import validate as schema_validate

from .schema import (
    VERIFY as SCHEMA_VERIFY,
    MARGIN as SCHEMA_MARGIN,
    MARGIN_PARAMETER as SCHEMA_MARGIN_PARAMETER,
    YIELD as SCHEMA_YIELD,
    YIELD_PARAMETER as SCHEMA_YIELD_PARAMETER,
    OPTIMIZE_PARAMETER as SCHEMA_OPTIMIZE_PARAMETER,
    OPTIMIZE as SCHEMA_OPTIMIZE,
)


class OptimizerParameterConfiguration:
    """ Configuration for OptimizerParameter """

    min_: Optional[float]
    max_: Optional[float]
    nominal_: float

    def __init__(self, nominal: float, min_: Optional[float], max_: Optional[float]):
        self.min_ = min_
        self.max_ = max_
        self.nominal_ = nominal

    @property
    def min(self) -> Optional[float]:
        """ Returns the parameter minimum """
        return self.min_

    @property
    def max(self) -> Optional[float]:
        """ Returns the paramter maximum """
        return self.max_

    @property
    def nominal(self) -> float:
        """ Returns the parameter maximum """
        return self.nominal_

    @staticmethod
    def from_dict(value: Dict) -> "OptimizerParameterConfiguration":
        """ Create a optimize parameter configuration from a dict """

        schema_validate(instance=value, schema=SCHEMA_OPTIMIZE_PARAMETER)

        nominal = value["nominal"]
        min_ = value.get("min")
        max_ = value.get("max")

        return OptimizerParameterConfiguration(nominal, min_, max_)


@attr.s(auto_attribs=True, frozen=True, slots=True)
class OptimizeConfiguration:
    """ Configuration for optimize """

    method: str

    search_radius: float = 0.05
    converge: float = 0.01
    max_iterations: float = 1000

    @classmethod
    def from_dict(cls, value: Dict) -> "OptimizeConfiguration":
        """ Create a optimize configuration """

        schema_validate(value, SCHEMA_OPTIMIZE)

        method: str = value["method"]

        search_radius: float = value.get("search_radius", 0.05)
        converge: float = value.get("converge", 0.01)
        max_iterations: float = value.get("max_iterations", 1000)

        return cls(method, search_radius, converge, max_iterations)


@attr.s(auto_attribs=True, frozen=True, slots=True)
class VerifyConfiguration:
    """ Configuration for Verify """

    method: str
    file_path: str
    circuit_path: str
    threshold: float = 0.05

    @staticmethod
    def from_dict(value: Dict) -> "VerifyConfiguration":
        """ Create a verify configuration from a dict """

        schema_validate(instance=value, schema=SCHEMA_VERIFY)

        method = value["method"]
        file_path = value["file"]
        circuit_path = value["circuit"]
        threshold = value.get("threshold", 0.05)

        return VerifyConfiguration(method, file_path, circuit_path, threshold)


@attr.s(auto_attribs=True, frozen=True, slots=True)
class MarginParameterConfiguration:
    """ Configuration for MarginParameter """

    nominal: Optional[float]

    @staticmethod
    def from_dict(value: Dict) -> "MarginParameterConfiguration":
        """ Create a verify configuration from a dict """

        schema_validate(instance=value, schema=SCHEMA_MARGIN_PARAMETER)

        nominal = value.get("nominal")

        return MarginParameterConfiguration(nominal)


@attr.s(auto_attribs=True, frozen=True, slots=True)
class YieldParameterConfiguration:
    """ Configuration for YieldParameter """

    variance: float
    nominal: Optional[float] = None

    @staticmethod
    def from_dict(value: Dict) -> "YieldParameterConfiguration":
        """ Create a yield parameter configuration from a dict """

        schema_validate(instance=value, schema=SCHEMA_YIELD_PARAMETER)

        nominal = value.get("nominal")
        variance = value["variance"]

        return YieldParameterConfiguration(variance, nominal)


@attr.s(auto_attribs=True, frozen=True, slots=True)
class YieldAnalysisConfiguration:
    """ Configuration for YieldAnalysis """

    num_samples: int

    @staticmethod
    def from_dict(value: Dict) -> "YieldAnalysisConfiguration":
        """ Create a yield analysis configuration from a dict """

        schema_validate(instance=value, schema=SCHEMA_YIELD)

        num_samples = value["num_samples"]

        return YieldAnalysisConfiguration(num_samples)


@attr.s(auto_attribs=True, frozen=True, slots=True)
class MarginAnalysisConfiguration:
    """ Configuration for MarginAnalysis """

    max_search: float = 1.9
    min_search: float = 0.1
    scan_steps: int = 4
    binary_search_steps: int = 3

    @staticmethod
    def from_dict(value: Dict) -> "MarginAnalysisConfiguration":
        """ Create a marginal analysis configuration from a dict """

        schema_validate(instance=value, schema=SCHEMA_MARGIN)

        max_search = value.get("max_search", 1.9)
        min_search = value.get("min_search", 0.1)
        scan_steps = value.get("scan_steps", 4)
        binary_search_steps = value.get("binary_search_steps", 3)

        return MarginAnalysisConfiguration(
            max_search, min_search, scan_steps, binary_search_steps
        )
