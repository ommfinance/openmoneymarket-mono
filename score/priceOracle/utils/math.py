EXA = 10 ** 18
halfEXA = EXA // 2


def convertToExa(_amount: int, _decimals: int) -> int:
    if _decimals == 18:
        return _amount;
    if _decimals >= 0:
        return _amount * EXA // (10 ** _decimals)


def exaDiv(a: int, b: int) -> int:
    halfB = b // 2
    return (halfB + (a * EXA)) // b


def exaMul(a: int, b: int) -> int:
    return (halfEXA + (a * b)) // EXA
