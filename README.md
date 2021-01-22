# Documentation

JoSIM Tools is a set of tools that does analysis on Superconducting Single Flux Quantum Circuits. JoSIM Tools is built on [JoSIM] and leverages [pyjosim]. The tools currently include verification, margin analysis, yield analysis, and optimization routines.

The full documentation can be found on the [JoSIM Tools Github Pages](https://qedalab.github.io/josim-tools/)

## Motivation

Existing tools require specialized format, are difficult to use, are not configurable, are slow, or have shortcoming in the method used.

## Goal

A tool which does analysis and optimization of SFQ circuits while being:

* Reasonably effecient
* Configurable
* Programmatically extendable

## Usage Example

JoSIM tools takes a single configuration file as input which describes the analysis

```toml
mode = "margin"

[parameters]
Btotal = {"nominal" = 1}
Ltotal = {"nominal" = 1}
Itotal = {"nominal" = 1}

[verify]
method = "spec_file"
circuit = "data/test_splitt_changed_sym.js"
file = "data/test_splitt_changed_sym.sp"
```

The configuration file description is described in the [Configuration File Section](configuration_file.md)

```console
$ josim-tools margin/simple_margin_analysis.toml
Btotal: 18.3 [                       #####|#                           ]  7.0
Ltotal: 29.5 [                    ########|######                      ] 23.9
Itotal:  7.0 [                           #|#####                       ] 21.1
Critical margin:  7.0 % ['Btotal+', 'Itotal-']
```

#### Alternatives

* [PSCAN2/COWBoy](alternatives.md#pscan2cowboy)
* [MALT](alternatives.md#malt)
* [xopt](alternatives.md#xopt)
* [Cadance AAO](alternatives.md#cadence-aao)

## Installation

Install [pyjosim]

Then install [poetry]

```console
$ pip install poetry
```

Then simply clone, build and install josim-tools
```console
$ git clone https://github.com/pleroux0/josim-tools
$ cd josim-tools
$ poetry build --format=wheel
$ pip install dist/josim_tools-0.1.0-py3-none-any.whl
```

## License

This software is licensed under the BSD-2-Clause license. See [LICENSE.md](https://github.com/pleroux0/josim-tools/LICENSE.md) for more details.

[JoSIM]: https://github.com/JoeyDelp/JoSIM
[pyjosim]: https://github.com/pleroux0/pyjosim
[poetry]: https://github.com/sdispater/poetry
