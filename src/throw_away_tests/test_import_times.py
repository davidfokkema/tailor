import threading
import time

t0 = time.monotonic()


def import_numpy():
    import numpy


t = threading.Thread(target=import_numpy)
t.start()
t.join()
t1 = time.monotonic()

print(f"NumPy took {1000 * (t1 - t0):.1f} ms")

from test_import_import_times import main

main()
