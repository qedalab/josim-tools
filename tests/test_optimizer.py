""" Test the optimizer classes """

import pytest
import numpy as np

from josim_tools.optimize import NumpyVectorArray


def test_numpy_vector_array():
    """ Test NumpyVectorArray class """
    array_a = np.array([1, 2, 3, 4])
    array_b = np.array([5, 6, 7, 8])
    array_c = np.array([9, 10, 11, 12])
    array_d = np.array([13, 14, 15, 16])

    vector_a = np.array([array_a])
    vector_b = np.array([array_a, array_b])
    vector_c = np.array([array_a, array_b, array_c])
    vector_d = np.array([array_a, array_b, array_c, array_d])

    array_size = 4

    numpy_vector_array = NumpyVectorArray(array_size, default_allocation=0)

    assert numpy_vector_array.capacity() == 0
    assert numpy_vector_array.size() == 0
    assert numpy_vector_array.array_size() == 4

    numpy_vector_array.append_list([array_a])

    assert numpy_vector_array.capacity() == 1
    assert numpy_vector_array.size() == 1
    assert numpy_vector_array.array_size() == 4
    assert np.all(vector_a == numpy_vector_array.view())

    numpy_vector_array.append_list([array_b])

    assert numpy_vector_array.capacity() == 2
    assert numpy_vector_array.size() == 2
    assert numpy_vector_array.array_size() == 4
    assert np.all(vector_b == numpy_vector_array.view())

    numpy_vector_array.append(array_c)

    assert numpy_vector_array.capacity() == 4
    assert numpy_vector_array.size() == 3
    assert numpy_vector_array.array_size() == 4
    assert np.all(vector_c == numpy_vector_array.view())

    numpy_vector_array.append(array_d)

    assert numpy_vector_array.capacity() == 4
    assert numpy_vector_array.size() == 4
    assert numpy_vector_array.array_size() == 4
    assert np.all(vector_d == numpy_vector_array.view())
