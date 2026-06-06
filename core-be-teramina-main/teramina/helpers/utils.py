from itertools import combinations
import numpy as np
import pandas as pd


def heaviside_step(x):
    """heaviside function"""
    return np.heaviside([x], 1)[0]


def normal_trapezoidal(m, suitable_min, suitable_max, optimal_min, optimal_max):
    """normal trapezoid normalization
    m: value in t
    """
    if pd.isnull(m):
        ret = 0.25
    elif (m < suitable_min) or (m > suitable_max):
        ret = 0
    else:
        lower_score = (
            1
            if optimal_min == suitable_min
            else (m - suitable_min) / (optimal_min - suitable_min)
        )
        upper_score = (
            1
            if suitable_max == optimal_max
            else (suitable_max - m) / (suitable_max - optimal_max)
        )
        ret = min(
            (
                lower_score,
                1,
                upper_score,
            )
        )

    return ret


def left_trapezoidal(m, suitable_min, suitable_max, optimal_max):
    """left trapezoid normalization
    m: value in t
    """
    if pd.isnull(m):
        ret = 0.25
    elif (m < suitable_min) or (m > suitable_max):
        ret = 0
    else:
        ret = min((1, (suitable_max - m) / (suitable_max - optimal_max)))

    return ret


def right_trapezoidal(m, suitable_min, optimal_min):
    """right trapezoid normalization
    m: value in t
    """
    if pd.isnull(m):
        ret = 0.25
    elif m < suitable_min:
        ret = 0
    elif m >= optimal_min:
        ret = 1
    else:
        ret = (m - suitable_min) / (optimal_min - suitable_min)

    return ret


def combinate(n, x):
    """generate combination array

    Args:
        n (int): range of combination that we expected
        x (int): length of data that we expected

    Returns:
        np.ndarray: combination array
    """
    if n < x:
        raise IndexError("n should be higher than x")

    if n < 7:
        combined_data = np.array(list(combinations(range(n), x)))
    else:
        combined_data = np.array(list(combinations(range(n), x)))
        index = np.where(np.any(np.diff(combined_data) == 1, axis=1))[0]
        combined_data = combined_data[~np.isin(np.arange(len(combined_data)), index)]

    m = len(combined_data)
    out = np.zeros((m, n), dtype=int)
    out[np.arange(m)[:, None], combined_data] = 1
    return out
