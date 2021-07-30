EXA = 10**18
halfEXA = EXA // 2
SECONDS_PER_YEAR = 31536000


def exaMul(a: int, b: int) -> int:
    return (halfEXA + (a*b)) // EXA

def exaDiv(a: int, b: int) -> int:
    halfB = b // 2
    return (halfB + (a * EXA)) // b

def convertToExa(_amount:int,_decimals:int)-> int:
    if _decimals >= 0:
        return _amount * EXA // (10 ** _decimals)

def convertExaToOther(_amount:int,_decimals:int)->int:
    if _decimals >= 0:
        return _amount * (10 ** _decimals) // EXA
