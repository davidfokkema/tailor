"""Compare various comparison methods for NumPy arrays.

So... in Tailor, when you change data the plots are updated automatically. But that means that old model fits should be invalidated. So how to figure out if data really changed? Keep copies of the data like in 'old' Tailor? I don't like that. Only keep a checksum? Better, but may be slow. Let's check!
"""

import hashlib
import timeit

import numpy as np
import xxhash

N = 10000

a = np.random.random(size=[5000, 10])
b = a.copy()
c = a.copy()
c[-1][3] = 1.0

assert (a == b).all() == True
assert (a == c).all() == False
t = timeit.timeit(lambda: (a == b).all(), number=N) / N
print(f"Comparing arrays: {t * 1e6:.1f} μs")

## WARNING: hash() is non-deterministic and changes between python runs
# assert hash(a.tobytes()) == hash(b.tobytes())
# assert hash(a.tobytes()) != hash(c.tobytes())
# t = timeit.timeit(lambda: hash(a.tobytes()) == hash(b.tobytes()), number=N) / N
# print(f"Comparing arrays using hash(): {t * 1e6:.1f} μs")
# print(f"{hash(a.tobytes())=}")
# print(f"{hash(b.tobytes())=}")
# print(f"{hash(c.tobytes())=}")


def compare_with_hash(hash):
    a = np.random.random(size=[5000, 10])
    b = a.copy()
    c = a.copy()
    c[4][3] = 1.0

    def f(a, b):
        return hash(a).hexdigest() == hash(b).hexdigest()
        # return a.tobytes() == b.tobytes()

    assert f(a, b) is True
    assert f(a, c) is False
    t = timeit.timeit(lambda: f(a, b), number=N) / N
    print(f"Comparing arrays using {hash().name} hashes: {t * 1e6:.1f} μs")


compare_with_hash(hashlib.sha1)
compare_with_hash(hashlib.sha256)
compare_with_hash(hashlib.md5)
compare_with_hash(hashlib.blake2b)
compare_with_hash(hashlib.blake2s)

compare_with_hash(xxhash.xxh3_64)
print(f"{xxhash.xxh3_64(a).hexdigest()=}")
