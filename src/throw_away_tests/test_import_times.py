import threading
import time

t0 = time.monotonic()


def import_numpy():
    import numpy


t = threading.Thread(target=import_numpy)
t.start()
t.join()
t1 = time.monotonic()


import numpy

t2 = time.monotonic()


print(f"NumPy took {1000 * (t1 - t0):.1f} ms")
print(f"Second import of NumPy took {1000 * (t2 - t1):.1f} ms")
