""" Module that contains interface code with JoSIM """

from typing import List, Optional
from numpy import interp

import attr

from pyjosim.input import Input, AnalysisType, InputType
from pyjosim.matrix import Matrix
from pyjosim.output import Output, Trace
from pyjosim.simulation import Simulation


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
            sample = interp(time, self.time_steps, trace.get_data())
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

        if (
            self.plot_type == "PHASE"
            or self.plot_type == "DEVI"
            or self.plot_type == "DEVV"
            or self.plot_type == "DEVP"
        ):
            return self.parameter.upper()

        if self.plot_type == "NODEV":
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

        input_object.read_input_file(self.circuit_path_)
        input_object.split_netlist()

        input_object.expand_subcircuits()
        input_object.expand_maindesign()

        return input_object

    def _raw_simulate(self, parameter_values: List[float]) -> Output:
        assert len(parameter_values) == len(self.parameter_names_)

        # Don't harm our input object
        tmp_input = self.input_.clone()

        # Create objects
        matrix = Matrix()
        output = Output()
        simulation = Simulation()

        # Replace parameter
        parameters = tmp_input.parameters
        for name, value in zip(self.parameter_names_, parameter_values):
            parameters.replace_unparsed_param(name, value)

        # Setup simulation
        tmp_input.parse_parameters()
        simulation.identify_simulation(tmp_input)
        matrix.create_matrix(tmp_input)

        matrix.find_relevant_x(tmp_input)

        # Run simulation
        if self.phase_mode_:
            simulation.transient_phase_simulation(tmp_input, matrix)
        else:
            simulation.transient_voltage_simulation(tmp_input, matrix)

        # Gather output
        output.relevant_traces(tmp_input, matrix, simulation)

        # Return output
        return output

    def simulate(self, parameter_values: List[float]) -> CircuitSimulatorOuput:
        """ Simulate and return list of traces """

        output = self._raw_simulate(parameter_values)
        time_steps = output.get_timesteps()
        traces = output.get_traces()

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

        return CircuitSimulatorOuput(time_steps, output_traces)

    def change_traces(self, plot_parameters: List[PlotParameter]) -> None:
        """ Modify the traces that are output by simulate """
        if self.plot_parameters_ == plot_parameters:
            return

        self.plot_parameters_ = plot_parameters

        self.input_.clear_plots()

        for plot_parameter in self.plot_parameters_:
            self.input_.add_plot(plot_parameter.to_plot_string())

    def change_parameters(self, parameter_names: List[str]) -> None:
        """ Modify the parameters that are modified """
        self.parameter_names_ = parameter_names
