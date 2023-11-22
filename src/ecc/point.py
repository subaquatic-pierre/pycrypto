from typing import Self

from ecc.element import FieldElement, S256FieldElement, Gx, Gy
from ecc.sign import Signature
from ecc.utils import encode_base58_checksum, hash160
from ecc.const import P, B, N, A


class Point:
    def __init__(
        self,
        x: FieldElement | None,
        y: FieldElement | None,
        a: FieldElement,
        b: FieldElement,
    ) -> None:
        self.a = a
        self.b = b
        self.x = x
        self.y = y

        # used for infinity point
        if x == None and y == None:
            return

        if self.y**2 != self.x**3 + self.a * self.x + self.b:
            raise ValueError(f"({x}, {y}) is not on the curve")

    def __add__(self, other: Self) -> Self:
        # used to create new FieldElement with prime order

        if self.a != other.a or self.b != other.b:
            raise TypeError(f"Points {self}, {other} are not on the same curve")

        # addition with identity returns self or other
        if self.x is None:
            return self.__class__(other.x, other.y, other.a, other.b)

        if other.x is None:
            return self.__class__(self.x, self.y, self.a, self.b)

        # point addition when x1 == x2. ie. Additive inverse is infinity
        if self.x == other.x and self.y != other.y:
            return self.__class__(None, None, self.a, self.b)

        # Point addition when x1 != x2
        if self.x != other.x:
            # calculate slope
            s = self.get_slope(self, other)

            # calculate x3
            x3 = s**2 - self.x - other.x

            # calculate y3
            y3 = s * (self.x - x3) - self.y

            return self.__class__(x3, y3, self.a, self.b)

        # Point addition when P1 == P2
        if self == other:
            s = (3 * (self.x**2) + self.a) / (2 * self.y)
            x3 = s**2 - 2 * self.x
            y3 = s * (self.x - x3) - self.y

            return self.__class__(x3, y3, self.a, self.b)

        if self == other and self.y == 0 * self.x:
            return self.__class__(None, None, self.a, self.b)

    def __repr__(self) -> str:
        return f"Point({self.x},{self.y}) -> y^2 = x^3 + {self.a}x + {self.b}"

    def __eq__(self, other: Self) -> bool:
        return (
            self.x == other.x
            and self.y == other.y
            and self.a == other.a
            and self.b == other.b
        )

    def __ne__(self, other: Self) -> bool:
        if self == other:
            return False

        return True

    def __rmul__(self, coefficient: int) -> Self:
        coef = coefficient
        current = self
        result = self.__class__(None, None, self.a, self.b)

        while coef:
            if coef & 1:
                result += current

            current += current
            coef >>= 1

        return result

    def get_slope(self, p1: Self, p2: Self):
        return (p2.y - p1.y) / (p2.x - p1.x)


class S256Point(Point):
    def __init__(
        self,
        x: int | None,
        y: int | None,
        a: int = None,
        b: int = None,
    ) -> None:
        a, b = S256FieldElement(A), S256FieldElement(B)
        if type(x) == int:
            super().__init__(x=S256FieldElement(x), y=S256FieldElement(y), a=a, b=b)
        else:
            super().__init__(x=x, y=y, a=a, b=b)

    def __rmul__(self, coefficient: int) -> Self:
        coef = coefficient % N
        return super().__rmul__(coef)

    def __repr__(self):
        if self.x is None:
            return "S256Point(infinity)"
        else:
            return "S256Point({}, {})".format(self.x, self.y)

    def verify(self, z, sig: Signature) -> bool:
        s_inv = pow(sig.s, N - 2, N)
        u = z * s_inv % N
        v = sig.r * s_inv % N
        total: Self = u * G + v * self
        return total.x.num == sig.r

    def sec(self, compressed: bool = True) -> bytes:
        """returns the binary version of the SEC, Standard For Efficient Cryptography format"""

        # return compressed key
        if compressed:
            prefix = b"\x02"
            # check if odd number, change prefix
            if self.y.num % 2 != 0:
                prefix = b"\x03"

            return prefix + self.x.num.to_bytes(32)

        # otherwise return uncompressed key
        return b"\x04" + self.x.num.to_bytes(32, "big") + self.y.num.to_bytes(32, "big")

    @classmethod
    def parse(self, sec_bin) -> Self:
        """returns a S256Point object from a SEC(Standard Effecient Cryptography) binary (not hex)"""

        # uncompressed format
        if sec_bin[0] == 4:
            x = S256FieldElement(int.from_bytes(sec_bin[1:33], "big"), P)
            y = S256FieldElement(int.from_bytes(sec_bin[33:65], "big"), P)

            return S256Point(x=x, y=y)

        is_even = sec_bin[0] == 2
        x = S256FieldElement(int.from_bytes(sec_bin[1:], "big"))

        # right side of the equation y^2 = x^3 + 7
        alpha: S256FieldElement = x**3 + S256FieldElement(B)

        # solve for left side
        beta = alpha.sqrt()

        if beta.num % 2 == 0:
            even_beta = beta
            odd_beta = S256FieldElement(P - beta.num)
        else:
            even_beta = S256FieldElement(P - beta.num)
            odd_beta = beta

        if is_even:
            return S256Point(x, even_beta)
        else:
            return S256Point(x, odd_beta)

    def hash160(self, compressed=True):
        return hash160(self.sec(compressed))

    def address(self, compressed=True, testnet=False):
        """Returns the address string"""
        h160 = self.hash160(compressed)
        if testnet:
            prefix = b"\x6f"
        else:
            prefix = b"\x00"
        return encode_base58_checksum(prefix + h160)


G = S256Point(Gx, Gy)
