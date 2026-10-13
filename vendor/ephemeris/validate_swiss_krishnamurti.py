#!/usr/bin/env python3
"""Validate the browser's compact Swiss-KP reference fit against pyswisseph."""
from __future__ import annotations

import math
import random

import swisseph as swe

START_JD = 2415020.5
END_JD = 2488434.5
COEFFICIENTS = (23.767374768561112, 1.4038517009258205, 0.00015506283475881375, 7.300019807173769e-10, 2.0332944117239102e-10)


def browser_fit(jd: float) -> float:
    x = (2 * jd - START_JD - END_JD) / (END_JD - START_JD)
    b1 = b2 = 0.0
    for coefficient in reversed(COEFFICIENTS[1:]):
        b0 = 2 * x * b1 - b2 + coefficient
        b2, b1 = b1, b0
    return x * b1 - b2 + COEFFICIENTS[0]


def main() -> None:
    swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
    samples = [START_JD, END_JD - 1e-7]
    samples.extend(START_JD + index * 31.0 + 0.617 for index in range(math.ceil((END_JD - START_JD) / 31)))
    rng = random.Random(20261012)
    samples.extend(rng.uniform(START_JD, END_JD) for _ in range(5000))
    errors = [abs(browser_fit(jd) - swe.get_ayanamsa_ut(jd)) * 3600 for jd in samples]
    maximum = max(errors)
    assert maximum < 0.00002, maximum
    print(f"Swiss Krishnamurti fit: {len(errors)} samples, maximum error {maximum:.9f} arcsecond")


if __name__ == "__main__":
    main()
