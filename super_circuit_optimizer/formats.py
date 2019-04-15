from typing import List, TextIO


class SpecFile:
    """ Spec file class """

    _path: str
    _names: List[str]
    _time: List[float]
    _data: List[List[int]]

    def _read_from_file(self, text_file: TextIO) -> None:
        lines = [line for line in text_file.readlines() if not line.isspace()]
        tokens = [[token for token in line.split() if token] for line in lines]

        if len(tokens) <= 2:
            raise RuntimeError("Spec file doesn't have enough lines")

        name_line = tokens[0]
        data_lines = tokens[1:]

        if name_line[0] != "time":
            raise RuntimeError("Spec file should start with: 'time' names...")

        if len(name_line) < 2:
            raise RuntimeError("Spec file must specify at least one variable")

        expected_line_length = len(name_line)

        # Save names
        self._names = name_line[1:]

        # Process data lines
        self._time = []
        self._data = []

        for line in data_lines:
            if len(line) != expected_line_length:
                raise RuntimeError("Unexpected number of tokens in data line")

            try:
                self._time.append(float(line[0]))
            except ValueError:
                raise RuntimeError(
                    "Expected a real number specifying time at start of data line"
                )

            try:
                self._data.append([int(token) for token in line[1:]])
            except ValueError:
                raise RuntimeError(
                    "Number of pi phase jumps should be an integer number"
                )

    def __init__(self, path: str):
        self._path = path

        with open(self._path, "rt") as text_file:
            self._read_from_file(text_file)

    def time(self) -> List[float]:
        """ Get the time sequence """
        return self._time

    def data(self) -> List[List[int]]:
        """ Get the data """
        return self._data

    def names(self) -> List[str]:
        """ Get the names """
        return self._names

    def time_value(self, index: int) -> float:
        """ Get a specific time value  """
        return self._time[index]

    def data_line(self, index: int) -> List[int]:
        """ Get a specific data line """
        return self._data[index]

    def data_value(self, line_index: int, index: int):
        """ Get a specific data value """
        return self._data[line_index][index]

    def name(self, index: int) -> str:
        """ Get a specific name """
        return self._names[index]
