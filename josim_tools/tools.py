""" JoSIM Tools CLI interface """

from typing import Any, Tuple, Dict
from multiprocessing import cpu_count

from argparse import ArgumentParser
from toml import load as toml_load
from jsonschema import (
    validate as schema_validate,
    ValidationError as SchemaValidationError,
)

from . import __version__
from .verify import Verifier
from .analysis import MarginAnalysis, print_margin_analysis_result, YieldAnalysis
from .optimize import Optimizer
from .schema import CONFIG as SCHEMA_CONFIG
from .configuration import (
    VerifyConfiguration,
    MarginAnalysisConfiguration,
    YieldAnalysisConfiguration,
    OptimizeConfiguration,
    MarginParameterConfiguration,
    OptimizerParameterConfiguration,
    YieldParameterConfiguration,
)


def run() -> None:
    """ Run the tool parsing the commandline arguments """
    print(f"JoSIM Tools {__version__}")

    parser = ArgumentParser(description="Circuit tools built on JoSIM")

    parser.add_argument("configuration", type=str)

    parser.add_help = True
    parser.allow_abbrev = True

    args = parser.parse_args()

    configuration = toml_load(args.configuration)

    try:
        schema_validate(instance=configuration, schema=SCHEMA_CONFIG)
    except SchemaValidationError as error:
        print("ERROR: configuration file validation failed")
        print("       reason: {}".format(error.message))
        exit(-1)

    mode = configuration["mode"]

    if mode == "verify":
        verify_configuration = VerifyConfiguration.from_dict(configuration["verify"])

        verifier = Verifier(verify_configuration)
        if verifier.verify():
            print("SUCCESS")
        else:
            print("FAILURE")

    elif mode == "margin":
        verify_configuration = VerifyConfiguration.from_dict(configuration["verify"])
        margin_configuration = MarginAnalysisConfiguration.from_dict(
            configuration.get("margin", {})
        )

        margin_parameters: Dict[str, MarginParameterConfiguration] = {}

        for key, item in configuration["parameters"].items():
            margin_parameters[key] = MarginParameterConfiguration.from_dict(item)

        margin_analysis = MarginAnalysis(verify_configuration, margin_configuration)

        num_threads = min(2 * len(margin_parameters), cpu_count())

        margin_analysis_parameters: Dict[str, float] = {}

        for key, item in margin_parameters.items():
            margin_analysis_parameters[key] = item.nominal

        result = margin_analysis.analyse(margin_analysis_parameters, num_threads)

        print_margin_analysis_result(
            result,
            left_size=margin_configuration.min_search,
            right_size=margin_configuration.max_search,
        )

    elif mode == "yield":
        verify_configuration = VerifyConfiguration.from_dict(configuration["verify"])
        yield_configuration = YieldAnalysisConfiguration.from_dict(
            configuration["yield"]
        )

        yield_parameters: Dict[str, YieldParameterConfiguration] = {}

        for key, item in configuration["parameters"].items():
            yield_parameters[key] = YieldParameterConfiguration.from_dict(item)

        num_samples = yield_configuration.num_samples
        num_threads = min(num_samples, cpu_count())

        yield_analysis = YieldAnalysis(verify_configuration, yield_parameters)
        yield_analysis.sample(num_samples, num_threads)

        print(
            "Yield: {} / {} = {:.1f} %".format(
                yield_analysis.num_success(),
                yield_analysis.num_total(),
                yield_analysis.percentage() * 100,
            )
        )
    elif mode == "optimize":
        verify_configuration = VerifyConfiguration.from_dict(configuration["verify"])

        margin_configuration = MarginAnalysisConfiguration.from_dict(
            configuration.get("margin", {})
        )

        optimize_configuration = OptimizeConfiguration.from_dict(
            configuration["optimize"]
        )

        optimize_parameters: Dict[str, OptimizerParameterConfiguration] = {}

        for key, item in configuration["parameters"].items():
            optimize_parameters[key] = OptimizerParameterConfiguration.from_dict(item)

        optimizer = Optimizer(
            verify_configuration,
            margin_configuration,
            optimize_configuration,
            optimize_parameters,
        )

        optimization_parameters: Dict[str, float] = {}

        for key, item in optimize_parameters.items():
            optimization_parameters[key] = item.nominal

        optimizer.optimize(optimization_parameters)

        # TODO do more with the output
    else:
        assert False, "INTERNAL ERROR: UNREACHABLE CODE"


if __name__ == "__main__":
    run()
