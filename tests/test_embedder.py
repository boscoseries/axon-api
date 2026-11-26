import math

import pytest

from services.embedder import _mean_pool, _normalize


def test_mean_pool_single_token_returns_that_token():
    assert _mean_pool([[1.0, 2.0, 3.0]]) == [1.0, 2.0, 3.0]


def test_mean_pool_averages_tokens():
    assert _mean_pool([[1.0, 3.0], [3.0, 5.0]]) == [2.0, 4.0]


def test_normalize_gives_unit_length():
    v = _normalize([3.0, 4.0])
    assert math.isclose(math.sqrt(sum(x * x for x in v)), 1.0)
