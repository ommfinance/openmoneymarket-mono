EXA = 10**18
halfEXA = EXA // 2
SECONDS_PER_YEAR = 31536000


def exaMul(a: int, b: int) -> int:
    return (halfEXA + (a*b)) // EXA

def exaDiv(a: int, b: int) -> int:
    halfB = b // 2
    return (halfB + (a * EXA)) // b

def exaPow(x: int, n: int) -> int:
    if n % 2 != 0:
        z = x
    else:
        z = EXA

    n = n // 2
    while n != 0:
        x = exaMul(x, x)

        if (n % 2 != 0):
            z = exaMul(z, x)

        n = n // 2
        
    return z

def calculateLinearInterest( _rate: int, _lastUpdateTimestamp: int) ->int:
    timeDifference = (_lastUpdateTimestamp) // 10**6
    timeDelta =  exaDiv(timeDifference, SECONDS_PER_YEAR)
    return exaMul(_rate, timeDelta) + EXA

def calculateCompoundedInterest( _rate: int, _lastUpdateTimestamp: int) ->int:
    timeDifference = (_lastUpdateTimestamp) // 10**6
    ratePerSecond =  _rate // SECONDS_PER_YEAR
    return exaPow((ratePerSecond + EXA), timeDifference)

def convertToExa(_amount:int,_decimals:int)-> int:
    if _decimals >= 0:
        return _balance * EXA // (10 ** _decimals)

def convertExaToOther(_amount:int,_decimals:int)->int:
    if _decimals >= 0:
        return _balance * (10 ** _decimals) // EXA