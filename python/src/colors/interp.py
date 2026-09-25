"""
Small numeric helpers that stand in for the handful of numpy functions this package needs.
Pure functions only -- this module has no dependencies outside the standard library.
"""


def linspace(start: float, stop: float, num: int) -> list[float]:
    """
    Create evenly spaced values over interval.
    :return: List of evenly spaced float values from start to stop
    """
    if num == 1:
        return [stop]
    return [start + (stop - start) * i / (num - 1) for i in range(num)]


def interp(x: list[float], xp: list[float], fp: list[float]) -> list[float]:
    """
    Perform 1D linear interpolation.
    :return: Interpolated values at points x
    """
    result = []
    for xi in x:
        if xi <= xp[0]:
            result.append(fp[0])
            continue
        if xi >= xp[-1]:
            result.append(fp[-1])
            continue
        for j in range(len(xp) - 1):
            if xp[j] <= xi <= xp[j + 1]:
                x0, x1 = xp[j], xp[j + 1]
                y0, y1 = fp[j], fp[j + 1]
                yi = y0 + (xi - x0) * (y1 - y0) / (x1 - x0)
                result.append(yi)
                break
    return result


def stack(arrays: list[list[float]], axis: int = 1) -> list[list[int]]:
    """
    Stack arrays along axis, with uint8 clamping.
    :return: 2D list with values clamped to 0-255 range and converted to int
    """
    if axis != 1:
        raise ValueError("Only axis=1 is supported")
    n_rows = len(arrays[0])
    return [[int(round(max(0, min(255, arrays[i][j])))) for i in range(len(arrays))] for j in range(n_rows)]
