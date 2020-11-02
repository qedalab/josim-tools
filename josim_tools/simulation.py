""" Module that contains interface code with JoSIM """

from typing import List, Optional
from numpy import interp
from sys import exit
import re

import attr

from pyjosim import Input, AnalysisType, InputType, Matrix, Output, Simulation, ParameterName, Trace, Parameter


class CircuitSimulatorOuput:
    """ Property class for output of Simulation objects """

    traces_: List[Trace]
    time_steps_: List[float]

    def __init__(self, time_steps: List[float], traces: List[Trace]):
        self.time_steps_ = time_steps
        self.traces_ = traces

    @property
    def time_steps(self) -> List[float]:
        """ Get the time step array """
        return self.time_steps_

    @property
    def traces(self) -> List[Trace]:
        """ Get the list of traces """
        return self.traces_

    def sample(self, time: float):
        """ Sample the output """
        samples: List[float] = []

        for trace in self.traces:
            sample = interp(time, self.time_steps, trace.data)
            samples.append(sample)

        return samples


@attr.s(auto_attribs=True, frozen=True, slots=True)
class PlotParameter:
    """ Plot parameter """

    parameter: str
    plot_type: str = "PHASE"

    def to_plot_string(self) -> str:
        """ Convert the plot parameter to a string """
        return "{} {}".format(self.plot_type.upper(), self.parameter.upper())

    def to_trace_name(self) -> str:
        """ Convert plot parameter to trace name """

        if self.plot_type == "PHASE":
            return f"P({self.parameter.upper()})"
        elif self.plot_type == "DEVI":
            return f"I({self.parameter.upper()})"
        elif self.plot_type == "DEVV":
            return f"V({self.parameter.upper()})"
        elif self.plot_type == "DEVP":
            return f"P({self.parameter.upper()})"
        elif self.plot_type == "NODEV":
            return "NV_{}".format(self.parameter.upper())

        assert False
        raise RuntimeError("Assert: Unreachable code")


class CircuitSimulator:
    """ Class that handles circuit simulation """

    def __init__(
        self,
        circuit_path: str,
        parameter_names: List[str],
        plot_parameters: Optional[List[PlotParameter]] = None,
        phase_mode: bool = False,
        wrspice_compatibility: bool = False
    ):
        self.circuit_path_ = circuit_path
        self.phase_mode_ = phase_mode
        self.wrspice_compatibility_ = wrspice_compatibility

        self.input_ = self._load_input()

        self.parameter_names_ = parameter_names

        self.plot_parameters_: List[PlotParameter] = []
        if plot_parameters is not None:
            self.change_traces(plot_parameters)

    def _load_input(self) -> Input:
        if self.wrspice_compatibility_:
            input_type = InputType.WrSpice
        else:
            input_type = InputType.Jsim

        if self.phase_mode_:
            analysis_type = AnalysisType.Phase
        else:
            analysis_type = AnalysisType.Voltage

        input_object = Input(analysis_type, input_type, False)
        input_object.parse_file(self.circuit_path_)

        return input_object

    def _raw_simulate(self, parameter_values: List[float]) -> Output:
        assert len(parameter_values) == len(self.parameter_names_)

        # Don't harm our input object
        tmp_input = self.input_.clone()

        # Replace parameter
        parameters = tmp_input.parameters

        for name, value in list(zip(self.parameter_names_, parameter_values)):
            parameter_split = name.upper().split(".", 1)
            if len(parameter_split) > 1:
                assert len(parameter_split) == 2
                parameter_name = ParameterName(parameter_split[0], parameter_split[1])
            else:
                assert len(parameter_split) == 1
                parameter_name = ParameterName(parameter_split[0], "")
            parameter = Parameter()
            parameter.set_expression(str(value).upper())
            if parameter_name in parameters:
                current_expression = parameters[parameter_name].get_expression()
                parameters[parameter_name] = parameter
            else:
                print(f"ERROR: Failed replacing \"{parameter_name}\" with \"{value}\"")
                exit(-1)

        parameters = tmp_input.parameters

        if len(parameters) > 0:
            parameters.parse()

        tmp_input.parse_models()

        netlist = tmp_input.netlist
        netlist.expand_subcircuits()
        netlist.expand_maindesign()

        tmp_input.identify_simulation()

        matrix = Matrix(tmp_input)
        simulation = Simulation(tmp_input, matrix)
        output = Output(tmp_input, matrix, simulation)

        # Return output
        return output

    def simulate(self, parameter_values: List[float]) -> CircuitSimulatorOuput:
        """ Simulate and return list of traces """

        output = self._raw_simulate(parameter_values)
        traces = output.traces
        time_steps = traces[0].data
        traces = traces[1:]

        output_traces = []

        if self.parameter_names_ is None:
            for trace in traces:
                output_traces.append(trace)
            return CircuitSimulatorOuput(time_steps, output_traces)

        for plot_parameter in self.plot_parameters_:
            trace_name = plot_parameter.to_trace_name()

            found: bool = False
            for trace in traces:
                if trace.name == trace_name:
                    found = True
                    output_traces.append(trace)
                    break

            if found:
                continue

            raise RuntimeError(
                "Trace name not found in simulation output\n"
                "{} not in {}".format(trace_name, [trace.name for trace in traces])
            )

        for trace, parameter in zip(output_traces, self.plot_parameters_):
            assert trace.name == parameter.to_trace_name()

        return CircuitSimulatorOuput(time_steps, output_traces)

    def change_traces(self, plot_parameters: List[PlotParameter]) -> None:
        """ Modify the traces that are output by simulate """
        if self.plot_parameters_ == plot_parameters:
            return

        self.plot_parameters_ = plot_parameters

        self.input_.clear_all_plots()

        for plot_parameter in self.plot_parameters_:
            self.input_.add_plot(plot_parameter.to_plot_string())

    def write_file_with_updated_parameters(self, output_file: str, values: List[float]):
        match_name_regex = re.compile(r"(\s*\.PARAM\s*([^=\s]*)\s*=\s*).*\s*", re.IGNORECASE)

        upper_case_parameters = [param.upper() for param in self.parameter_names_]

        with open(output_file, "w") as output:
            for line in open(self.circuit_path_).readlines():
                if line.upper().startswith(".PARAM"):
                    result = match_name_regex.match(line)
                    if not result:
                        print(f"ERROR: Failed parsing parameter string: {line.strip()}")
                        exit(-1)
                    name = result.group(2)
                    name_uppercase = name.upper()
                    if name_uppercase in upper_case_parameters:
                        index = upper_case_parameters.index(name_uppercase)
                        value = values[index]
                        line = result.group(1) + str(value) + "\n"


                output.write(line)

    def change_parameters(self, parameter_names: List[str]) -> None:
        """ Modify the parameters that are modified """
        self.parameter_names_ = parameter_names
