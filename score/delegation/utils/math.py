EXA = 10 ** 18
halfEXA = EXA // 2
SECONDS_PER_YEAR = 31536000


def exaMul(a: int, b: int) -> int:
    return (halfEXA + (a * b)) // EXA


def exaDiv(a: int, b: int) -> int:
    half_b = b // 2
    return (half_b + (a * EXA)) // b


def exaPow(x: int, n: int) -> int:
    z = x if n % 2 != 0 else EXA

    n = n // 2
    while n != 0:
        x = exaMul(x, x)

        if n % 2 != 0:
            z = exaMul(z, x)

        n = n // 2

    return z


def calculateLinearInterest(_rate: int, _lastUpdateTimestamp: int) -> int:
    time_difference = _lastUpdateTimestamp // 10 ** 6
    time_delta = exaDiv(time_difference, SECONDS_PER_YEAR)
    return exaMul(_rate, time_delta) + EXA


def calculateCompoundedInterest(_rate: int, _lastUpdateTimestamp: int) -> int:
    time_difference = _lastUpdateTimestamp // 10 ** 6
    rate_per_second = _rate // SECONDS_PER_YEAR
    return exaPow((rate_per_second + EXA), time_difference)
