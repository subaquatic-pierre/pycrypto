from random import randint

from ecc.element import FieldElement
from ecc.point import Point, N, G, S256Point
from ecc.key import PrivateKey


def main():
    print("--- FIELD ELEMENT ---")
    # a = FieldElement(3, 13)
    # b = FieldElement(1, 13)

    # print(f"a ** 3 == b:", a**3 == b)

    print("\n --- POINTS ---")

    # p1 = Point(-1, 1, 5, 7)
    # p2 = Point(-1, -2, 5, 7)

    # print(p1)

    # print(f"P1 + P1 = {p1 + p1}")

    private_key = PrivateKey(randint(0, N))

    x, y = (
        0x5CBDF0646E5DB4EAA398F365F2EA7A0E3D419B7E0330E39CE92BDDEDCAC4F9BC,
        0x6AEBCA40BA255960A3178D6D861A54DBA813D0B813FDE7B5A5082628087264DA,
    )

    secret = 9000
    point = S256Point(x, y)

    check = secret * G
    print(f"{private_key}")
    print(f"{point}")
    print(f"{check}")


if __name__ == "__main__":
    main()
