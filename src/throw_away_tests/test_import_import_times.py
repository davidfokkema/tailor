import time

t1 = time.monotonic()

import numpy

t2 = time.monotonic()


def main():
    print(f"Second import of NumPy took {1000 * (t2 - t1):.1f} ms")


if __name__ == "__main__":
    main()
