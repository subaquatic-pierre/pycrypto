from __future__ import annotations
from typing import Self
from unittest import TestCase

from ecc.const import P


class FieldElement:
    def __init__(self, num: int, prime: int) -> None:
        if num >= prime or num < 0:
            err = f"Num {num} is not in field range 0 to {prime - 1}"
            raise ValueError(err)

        self.num = num
        self.prime = prime

    def __repr__(self) -> str:
        return f"FieldElement_{self.prime}({self.num})"

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False

        return self.num == other.num and self.prime == other.prime

    def __ne__(self, other: object) -> bool:
        if self == other:
            return False

        return True

    def __add__(self, other: Self) -> Self:
        if self.prime != other.prime:
            raise TypeError(
                f"Addition of field elements can only be done with the same prime order FieldElements"
            )
        num = (self.num + other.num) % self.prime

        return self.__class__(num, self.prime)

    def __sub__(self, other: Self) -> Self:
        if self.prime != other.prime:
            raise TypeError(
                f"Subtraction of field elements can only be done with the same prime order FieldElements"
            )
        num = (self.num - other.num) % self.prime

        return self.__class__(num, self.prime)

    def __mul__(self, other: Self) -> Self:
        if self.prime != other.prime:
            raise TypeError("Cannot multiply two numbers in different Fields")
        # self.num and other.num are the actual values
        # self.prime is what we need to mod against
        num = (self.num * other.num) % self.prime
        # We return an element of the same class
        return self.__class__(num, self.prime)

    def __pow__(self, exp: int) -> Self:
        n = exp % (self.prime - 1)
        num = pow(self.num, n, self.prime)

        return self.__class__(num, self.prime)

    def __truediv__(self, other: Self) -> Self:
        if self.prime != other.prime:
            raise TypeError("Cannot divide two numbers in different Fields")
        # use Fermat's little theorem:
        # self.num**(p-1) % p == 1
        # this means:
        # 1/n == pow(n, p-2, p)
        # we return an element of the same class
        num = self.num * pow(other.num, self.prime - 2, self.prime) % self.prime
        return self.__class__(num, self.prime)

    def __rmul__(self, coefficient):
        num = (self.num * coefficient) % self.prime
        return self.__class__(num=num, prime=self.prime)


class S256FieldElement(FieldElement):
    def __init__(self, num: int, prime: int = None) -> None:
        super().__init__(num, prime=P)

    def sqrt(self) -> Self:
        return self ** ((P + 1) // 4)


# BTC generator point
Gx = S256FieldElement(
    0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
)
Gy = S256FieldElement(
    0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
)
