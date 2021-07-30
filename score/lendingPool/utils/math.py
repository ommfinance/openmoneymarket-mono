
EXA = 10**18
halfEXA = EXA // 2


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
