#!/bin/sh

josim-tools yield_starting_values.toml 2>&1 | tee yield_starting_values.log
josim-tools yield_cadence_optimized.toml 2>&1 | tee yield_cadence_optimized.log
josim-tools yield_josim_tools_optimized.toml 2>&1 | tee yield_josim_tools_optimized.log
