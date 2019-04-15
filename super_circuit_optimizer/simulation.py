""" Module that contains interface code with JoSIM """

from typing import List, Optional
from numpy import interp

from pyjosim.input import CliOptions, Input, AnalysisType, InputType
from pyjosim.matrix import Matrix
from pyjosim.output import Output, Trace
from pyjosim.simulation import Simulation


class CircuitSimulatorOuput:
    """ Property class for output of Simulation objects """
    traces_: List[Trace]

    def __init__(self, time_steps, traces):
        self.time_steps_ = time_steps
        self.traces_ = traces

    @property
    def time_steps(self):
        """ Get the time step array """
        return self.time_steps_

    @property
    def traces(self):
        """ Get the list of traces """
        return self.traces_

    def sample(self, time: float):
        """ Sample the output """
        samples: List[float] = []

        for trace in self.traces:
            sample = interp(time, self.time_steps, trace.get_data())
            samples.append(sample)

        return samples


class CircuitSimulator:
    """ Class that handles circuit simulation """

    def __init__(
        self,
        circuit_path: str,
        parameter_names: List[str],
        trace_names: Optional[List[str]] = None,
        phase_mode: bool = False
    ):
        self.circuit_path_ = circuit_path
        self.parameter_names_ = parameter_names
        self.trace_names_ = trace_names
        self.phase_mode_ = phase_mode

        self.input_ = self._load_input()

    def _load_input(self) -> Input:
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

        # TODO ensure that parameters exists

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

        if self.trace_names_ is None:
            for trace in traces:
                output_traces.append(trace)
            return CircuitSimulatorOuput(time_steps, output_traces)

        for trace_name in self.trace_names_:
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
                "{} not in {}".format(
                    trace_name, [trace.name for trace in traces]
                )
            )

        return CircuitSimulatorOuput(time_steps, output_traces)

    def change_traces(self, trace_names: List[str]) -> None:
        """ Modify the traces that are output by simulate """
        self.trace_names_ = trace_names

    def change_parameters(self, parameter_names: List[str]) -> None:
        """ Modify the parameters that are modified """
        self.parameter_names_ = parameter_names

    def all_parameters(self) -> List[str]:
        raise NotImplementedError("CircuitSimulator::all_parameters")
