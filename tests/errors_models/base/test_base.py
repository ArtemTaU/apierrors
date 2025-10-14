from dataclasses import is_dataclass
from time import sleep

import pytest
from datetime import datetime, timezone

from ....apierrors.errors_models.base.base import ErrorFields, Error


@pytest.fixture
def minimal_kwargs():
    """Provide minimal required kwargs for HttpErrorFields."""
    return dict(
        code="bad_request",
        error_type="BadRequest",
        message="Something went wrong",
    )


# --------------------
# Tests for ErrorFields
# --------------------


def test_is_dataclass(minimal_kwargs):
    """HttpErrorFields must be a dataclass."""
    assert is_dataclass(ErrorFields)
    obj = ErrorFields(**minimal_kwargs)
    assert is_dataclass(obj)


def test_required_fields_enforced(minimal_kwargs):
    """Missing any required field should raise TypeError (dataclass ctor)."""
    kw = minimal_kwargs.copy()
    kw.pop("code")
    with pytest.raises(TypeError):
        ErrorFields(**kw)


def test_defaults_are_none(minimal_kwargs):
    """Optional fields default to None."""
    obj = ErrorFields(**minimal_kwargs)
    assert obj.request_id is None
    assert obj.path is None
    assert obj.method is None
    assert obj.traceback is None


def test_timestamp_autofill_iso_utc(minimal_kwargs):
    """
    timestamp is autofill, valid ISO-8601, and in UTC.
    """
    obj = ErrorFields(**minimal_kwargs)
    assert isinstance(obj.timestamp, str)
    dt = datetime.fromisoformat(obj.timestamp)
    assert isinstance(dt, datetime)
    assert dt.tzinfo is not None
    assert dt.tzinfo.utcoffset(dt) == timezone.utc.utcoffset(dt)


def test_timestamp_differs_between_instances(minimal_kwargs):
    """Auto-generated timestamps should differ for separate instances (very likely)."""
    obj1 = ErrorFields(**minimal_kwargs)
    sleep(0.01)
    obj2 = ErrorFields(**minimal_kwargs)
    assert obj1.timestamp != obj2.timestamp


def test_timestamp_can_be_overridden(minimal_kwargs):
    """Explicit timestamp in ctor is respected."""
    ts = "2025-10-09T12:34:56.789012+00:00"
    obj = ErrorFields(**minimal_kwargs, timestamp=ts)
    assert obj.timestamp == ts
    dt = datetime.fromisoformat(obj.timestamp)
    assert dt.tzinfo is not None
    assert dt.tzinfo.utcoffset(dt) == timezone.utc.utcoffset(dt)


def test_constructor_is_keyword_only(minimal_kwargs):
    with pytest.raises(TypeError):
        ErrorFields(
            "not_named",
            code="unnamed",
            error_type="unnamed",
            message="some message",
        )


# --------------------
# Tests for Error
# --------------------
def test_error_is_dataclass_and_subclass(minimal_kwargs):
    """`Error` must be a dataclass and subclass of `ErrorFields`."""
    assert is_dataclass(Error)
    obj = Error(**minimal_kwargs)
    assert isinstance(obj, ErrorFields)
    assert is_dataclass(obj)


def test_error_inherits_fields_without_modification(minimal_kwargs):
    """
    `Error` must expose all fields from `ErrorFields` and keep their values/defaults.
    (We don't re-test ToDictMixin behavior here.)
    """
    obj = Error(**minimal_kwargs)
    assert obj.code == "bad_request"
    assert obj.error_type == "BadRequest"
    assert obj.message == "Something went wrong"

    assert hasattr(obj, "request_id")
    assert hasattr(obj, "timestamp")
    assert hasattr(obj, "path")
    assert hasattr(obj, "method")
    assert hasattr(obj, "traceback")


def test_error_has_to_dict_method(minimal_kwargs):
    """Smoke: `Error` provides a `to_dict` method via the mixin."""
    obj = Error(**minimal_kwargs)
    assert hasattr(obj, "to_dict")
    assert callable(obj.to_dict)


def test_error_to_dict_returns_mapping_smoke(minimal_kwargs):
    """
    Light integration smoke: calling `to_dict()` returns a dict.
    (The details of serialization are covered by ToDictMixin tests.)
    """
    obj = Error(**minimal_kwargs)
    d = obj.to_dict()
    assert isinstance(d, dict)