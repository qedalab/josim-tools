#!/bin/env python

import numpy as np

starting_values = np.array([
    5.136e-12,
    3.945e-12,
    4.34e-12,
    3.82e-12,
    2.575,
    2.45,
    2.4375,
    2.625,
    150e-6,
])

margins = np.array([
    0.44350714,
    1.56640472,
    0.89742061,
    0.55096671,
    1.01042576,
    0.91381355,
    0.93499926,
    0.91727843,
    1.21811015,
])

names = [
    "LD_unscaled",
    "LQ_unscaled",
    "LO_unscaled",
    "LREL_unscaled",
    "J1_unscaled",
    "J2_unscaled",
    "J3_unscaled",
    "J4_unscaled",
    "I1_unscaled",
]

values = starting_values * margins

for name, value in zip(names, values):
    print(f".param {name}={value}")
