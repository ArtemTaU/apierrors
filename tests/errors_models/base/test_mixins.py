from dataclasses import dataclass

import pytest

from apierrors.errors_models.base.mixins import _compact_dict, ToDictMixin


# --------------------
# Tests for _compact_dict
# --------------------


@pytest.mark.parametrize(
    "input_dict, expected",
    [
        pytest.param({}, {}),
        pytest.param({"a": 1, "b": 2}, {"a": 1, "b": 2}),
        pytest.param({"a": None, "b": 2}, {"b": 2}),
        pytest.param({"a": 0, "b": False, "c": ""}, {"a": 0, "b": False, "c": ""}),
        pytest.param({"a": None, "b": {"k": None}}, {"b": {"k": None}}),
        pytest.param({"a": None, "b": [None, 1]}, {"b": [None, 1]}),
    ],
)
def test_compact_dict_top_level_only(input_dict, expected):
    """Only drop top-level None values; keep falsy values and nested Nones."""
    assert _compact_dict(input_dict) == expected


@pytest.fixture
def nested_payload():
    """Provide a nested mapping with top-level and nested None values."""
    return {
        "a": 1,
        "b": None,
        "c": {"k1": None, "k2": 2},
        "d": [None, 1, 2],
    }


def test_compact_dict_input_output_types(nested_payload):
    """Accept dict and return dict; do not mutate input."""
    with pytest.raises(TypeError):
        _compact_dict([])

    result = _compact_dict(nested_payload)
    assert isinstance(result, dict)


# --------------------
# Tests for ToDictMixin.to_dict
# --------------------
@dataclass
class SimpleDC(ToDictMixin):
    a: int
    b: str
    c: None | int = None


def test_to_dict_works_with_dataclass():
    """Serialize dataclass fields and drop None by default."""
    obj = SimpleDC(a=1, b="x", c=None)
    assert obj.to_dict() == {"a": 1, "b": "x"}


@pytest.mark.parametrize(
    "exclude_none, expected_keys",
    [
        (True, {"a", "b"}),
        (False, {"a", "b", "c"}),
    ],
)
def test_exclude_none_flag_behavior(exclude_none, expected_keys):
    """Respect exclude_none flag: drop/keep None-valued fields accordingly."""
    obj = SimpleDC(a=5, b="ok", c=None)
    d = obj.to_dict(exclude_none=exclude_none)
    assert set(d.keys()) == expected_keys


def test_to_dict_raises_on_non_dataclass_instance():
    """Raise TypeError when called on a non-dataclass instance."""
    with pytest.raises(TypeError):
        ToDictMixin().to_dict()


@dataclass
class NestedInner:
    x: int | None
    y: dict


@dataclass
class WithNested(ToDictMixin):
    inner: NestedInner
    note: str | None = None


def test_nested_objects_are_not_deeply_compacted():
    """Ensure serialization is shallow: nested objects are returned as-is."""
    inner = NestedInner(x=None, y={"k1": None, "k2": 3})
    obj = WithNested(inner=inner, note=None)
    d = obj.to_dict()
    assert "note" not in d
    assert "inner" in d
    assert isinstance(d["inner"], NestedInner)


def test_stability_does_not_mutate_instance():
    """Calling to_dict() must not mutate the dataclass instance state."""
    obj = SimpleDC(a=1, b="x", c=None)
    before = (obj.a, obj.b, obj.c)
    _ = obj.to_dict()
    after = (obj.a, obj.b, obj.c)
    assert before == after
