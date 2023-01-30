from lmfit import models


def test_min_max():
    model = models.Model(lambda x, a: a * x)
    params = model.make_params()
    params["a"].min = 1e-23
    params["a"].max = 1.1e-23
    model.fit([1, 2, 3], x=[1, 2, 3], params=params)


if __name__ == "__main__":
    test_min_max()
