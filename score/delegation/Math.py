EXA = 10 ** 18
halfEXA = EXA // 2
SECONDS_PER_YEAR = 31536000


def exaMul(a: int, b: int) -> int:
    return (halfEXA + (a * b)) // EXA


def exaDiv(a: int, b: int) -> int:
    half_b = b // 2
    return (half_b + (a * EXA)) // b
