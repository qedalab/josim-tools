""" Test the configuration schemas """

import pytest

from jsonschema.validators import (
    validator_for as schema_validator_for,
    validate as schema_validate,
)

from josim_tools.schema import (
    VERIFY,
    MARGIN,
    MARGIN_PARAMETER,
    YIELD,
    YIELD_PARAMETER,
    CONFIG,
    OPTIMIZE,
    OPTIMIZE_HYBRID,
    OPTIMIZE_PARAMETER,
)

SIMPLE_VERIFY_EXAMPLE = {
    "mode": "verify",
    "circuit": "test_splitt_changed_sym.js",
    "verify": {"method": "spec_file", "file": "test_splitt_changed_sym.sp"},
}


ADVANCED_VERIFY_EXAMPLE = {
    "mode": "verify",
    "circuit": "data/test_splitt_changed_sym.js",
    "verify": {
        "method": "spec_file",
        "file": "data/test_splitt_changed_sym.sp",
        "threshold": 0.03,
    },
}


SIMPLE_MARGIN_ANALYSIS = {
    "mode": "margin",
    "circuit": "data/test_splitt_changed_sym.js",
    "margin": {
        "parameters": {
            "Btotal": {"nominal": 1},
            "Ltotal": {"nominal": 1},
            "Itotal": {"nominal": 1},
        }
    },
    "verify": {"method": "spec_file", "file": "data/test_splitt_changed_sym.sp"},
}


ADVANCED_MARGIN_ANALYSIS = {
    "mode": "margin",
    "circuit": "data/test_splitt_changed_sym.js",
    "margin": {
        "max_search": 1.9,
        "min_search": 0.1,
        "scan_steps": 4,
        "binary_search_steps": 3,
        "parameters": {
            "Btotal": {"nominal": 1},
            "Ltotal": {"nominal": 1},
            "Itotal": {"nominal": 1},
        },
    },
    "verify": {"method": "spec_file", "file": "data/test_splitt_changed_sym.sp"},
}


SIMPLE_YIELD_ANALYSIS = {
    "mode": "yield",
    "circuit": "data/test_splitt_changed_sym.js",
    "yield": {
        "num_samples": 500,
        "parameters": {
            "Btotal": {"nominal": 1, "variance": 0.1},
            "Ltotal": {"nominal": 1, "variance": 0.1},
            "Itotal": {"nominal": 1, "variance": 0.1},
        },
    },
    "verify": {"method": "spec_file", "file": "data/test_splitt_changed_sym.sp"},
}


SIMPLE_HYBDRID_OPTIMIZE = {
    "mode": "optimize",
    "circuit": "data/test_splitt_changed_sym.js",
    "optimize": {
        "method": "hybrid",
        "parameters": {
            "Btotal": {"nominal": 1, "min": 0.5, "max": 1.5},
            "Ltotal": {"nominal": 1, "min": 0.5, "max": 1.5},
            "Itotal": {"nominal": 1, "min": 0.5, "max": 1.5},
        },
        "hybrid": {"search_radius": 0.05, "converge": 0.01, "max_iterations": 500},
    },
    "margin": {
        "parameters": {
            "Btotal": {"nominal": 1},
            "Ltotal": {"nominal": 1},
            "Itotal": {"nominal": 1},
        }
    },
    "verify": {"method": "spec_file", "file": "data/test_splitt_changed_sym.sp"},
}


@pytest.mark.parametrize(
    "schema",
    [
        VERIFY,
        MARGIN,
        MARGIN_PARAMETER,
        YIELD,
        YIELD_PARAMETER,
        CONFIG,
        OPTIMIZE_PARAMETER,
        OPTIMIZE_HYBRID,
        OPTIMIZE,
    ],
)
def test_verify_schema(schema):
    """ Test if the schema files are valid schema files """
    schema_validator = schema_validator_for(True)
    schema_validator.check_schema(schema)


@pytest.mark.parametrize(
    "example",
    [
        SIMPLE_VERIFY_EXAMPLE,
        ADVANCED_VERIFY_EXAMPLE,
        SIMPLE_MARGIN_ANALYSIS,
        ADVANCED_MARGIN_ANALYSIS,
        SIMPLE_YIELD_ANALYSIS,
        SIMPLE_HYBDRID_OPTIMIZE,
    ],
)
def test_example(example):
    """ Test examples """
    schema_validate(example, CONFIG)
