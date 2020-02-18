""" Contains schems for the input files """

# TODO
#   Validate file paths
#   Validate parameter names

VERIFY = {
    "type": "object",
    "properties": {"method": {"type": "string", "enum": ["spec_file"]}},
    "allOf": [
        {
            # Spec file
            "if": {"properties": {"method": {"const": "spec_file"}}},
            "then": {
                "properties": {
                    "method": {},
                    "file": {"type": "string"},
                    "threshold": {"type": "number"},
                    "circuit": {"type": "string"},
                    "wrspice_compatibility": {"type": "boolean"},
                },
                "additionalProperties": False,
                "required": ["file", "circuit"],
            },
        }
    ],
    "required": ["method"],
}

MARGIN_PARAMETER = {
    "type": "object",
    "properties": {"nominal": {"type": "number"}},
    "required": ["nominal"],
    "additionalProperties": False,
}

YIELD_PARAMETER = {
    "type": "object",
    "properties": {"nominal": {"type": "number"}, "variance": {"type": "number"}},
    "required": ["nominal", "variance"],
    "additionalProperties": False,
}

MARGIN = {
    "type": "object",
    "properties": {
        "max_search": {"type": "number", "default": 1.9},
        "min_search": {"type": "number", "default": 0.1},
        "scan_steps": {"type": "integer", "default": 4},
        "binary_search_steps": {"type": "integer", "default": 3},
    },
    "additionalProperties": False,
}

OPTIMIZE_PARAMETER = {
    "type": "object",
    "properties": {
        "nominal": {"type": "number"},
        "min": {"type": "number"},
        "max": {"type": "number"},
    },
    "required": ["nominal"],
    "additionalProperties": False,
}

OPTIMIZE = {
    "type": "object",
    "properties": {"method": {"type": "string", "enum": ["hybrid"]}},
    "allOf": [
        {
            # Spec file
            "if": {"properties": {"method": {"const": "hybdrid"}}},
            "then": {
                "properties": {
                    "method": {},
                    "search_radius": {"type": "number", "default": 0.05},
                    "converge": {"type": "number", "default": 0.01},
                    "max_iterations": {"type": "integer", "default": 500},
                    "output": {"type": "string"}
                },
                "additionalProperties": False,
            },
        }
    ],
    "required": ["method"],
}

YIELD = {
    "type": "object",
    "properties": {"num_samples": {"type": "integer"}},
    "required": ["num_samples"],
    "additionalProperties": False,
}

CONFIG = {
    "type": "object",
    "properties": {
        "mode": {"type": "string", "enum": ["verify", "margin", "yield", "optimize"]}
    },
    "allOf": [
        {
            # Verify
            "if": {"properties": {"mode": {"const": "verify"}}},
            "then": {
                "properties": {"mode": {}, "verify": VERIFY},
                "required": ["verify"],
                "additionalProperties": False,
            },
        },
        {
            # Margin
            "if": {"properties": {"mode": {"const": "margin"}}},
            "then": {
                "properties": {
                    "mode": {},
                    "verify": VERIFY,
                    "margin": MARGIN,
                    "parameters": {
                        "type": "object",
                        "additionalProperties": MARGIN_PARAMETER,
                    },
                },
                "required": ["verify", "parameters"],
                "additionalProperties": False,
            },
        },
        {
            # Yield
            "if": {"properties": {"mode": {"const": "yield"}}},
            "then": {
                "properties": {
                    "mode": {},
                    "verify": VERIFY,
                    "yield": YIELD,
                    "parameters": {
                        "type": "object",
                        "additionalProperties": YIELD_PARAMETER,
                    },
                },
                "required": ["verify", "yield", "parameters"],
                "additionalProperties": False,
            },
        },
        {
            # Optimize
            "if": {"properties": {"mode": {"const": "optimize"}}},
            "then": {
                "properties": {
                    "mode": {},
                    "verify": VERIFY,
                    "margin": MARGIN,
                    "optimize": OPTIMIZE,
                    "parameters": {
                        "type": "object",
                        "additionalProperties": OPTIMIZE_PARAMETER,
                    },
                },
                "required": ["verify", "optimize", "parameters"],
                "additionalProperties": False,
            },
        },
    ],
    "required": ["mode"],
}
