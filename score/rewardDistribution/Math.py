
EXA = 10 ** 18
halfEXA = EXA // 2
SECONDS_PER_YEAR = 31536000
# 365 days = (365 days) × (24 hours/day) × (3600 seconds/hour) = 31536000 seconds


def exaMul(a: int, b: int) -> int:
    return (halfEXA + (a*b)) // EXA


def exaDiv(a: int, b: int) -> int:
    halfB = b // 2
    return (halfB + (a * EXA)) // b