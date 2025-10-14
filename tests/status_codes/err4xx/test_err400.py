from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from ....apierrors import Err400, HttpErr400BadRequest


# --------------------
# Tests for Err400
# --------------------


@pytest.fixture
def err() -> Err400:
    """Fresh instance per test."""
    return Err400(message="bad")


def test_cannot_override_init_false_fields():
    """Fields with init=False (status, code) must not be set via ctor."""
    with pytest.raises(TypeError):
        Err400(message="bad", code=499)
    with pytest.raises(TypeError):
        Err400(message="bad", code="OVERRIDE")


def test_constructor_is_keyword_only():
    """Constructor should not accept positional args for base fields."""
    with pytest.raises(TypeError):
        Err400("bad")


def test_defaults_of_own_fields(err: Err400):
    """Status/code are fixed by subclass defaults."""
    assert err.code == "BAD_REQUEST"
    assert err.error_type == "bad_request"


def test_inherited_fields_presence_and_defaults(err: Err400):
    """
    Verify fields coming from the base class:
      - error_type (default expected as per base/class config)
      - message (what we passed)
      - detail/request_id/path/method/traceback (None)
      - timestamp (ISO-8601, parsable by datetime.fromisoformat)
    """
    assert err.message == "bad"
    assert err.request_id is None
    assert err.path is None
    assert err.method is None
    assert err.traceback is None

    assert isinstance(err.timestamp, str)
    datetime.fromisoformat(err.timestamp)


def test_to_dict_filters_nones_and_merges_extra(err: Err400):
    """
    to_dict:
      - includes base fields
      - removes top-level None values
      - merges add_extra()
    """
    payload = err.to_dict()

    assert payload["code"] == "BAD_REQUEST"
    assert payload["error_type"] == "bad_request"
    assert payload["message"] == "bad"
    assert "timestamp" in payload

    for k in ("detail", "request_id", "path", "method", "traceback"):
        assert k not in payload


def test_optional_fields_show_up_in_payload_when_set():
    """Optional fields provided in actor must appear in the serialized payload."""
    err = Err400(
        message="bad",
        request_id="rid-1",
        path="/api/v1/x",
        method="GET",
    )
    payload = err.to_dict()
    assert payload["request_id"] == "rid-1"
    assert payload["path"] == "/api/v1/x"
    assert payload["method"] == "GET"


def test_parent_contract_types_exist(err: Err400):
    """
    Smoke test: ensure all expected attributes from the contract are present.
    """
    for attr in (
        "code",
        "error_type",
        "message",
        "request_id",
        "timestamp",
        "path",
        "method",
        "traceback",
    ):
        assert hasattr(err, attr)


def test_to_dict_include_nones_when_flag_false(err: Err400):
    """exclude_none=False keeps None-valued fields in the payload."""
    payload = err.to_dict(exclude_none=False)
    for k in ("request_id", "path", "method", "traceback"):
        assert k in payload and payload[k] is None


def test_timestamp_can_be_overridden():
    """Explicit timestamp passed to ctor is respected."""
    ts = "2025-10-09T12:34:56.789012+00:00"
    err = Err400(message="bad", timestamp=ts)
    assert err.timestamp == ts


def test_error_type_can_be_overridden_if_needed():
    """If allowed by model, error_type can be overridden via ctor and reflected in payload."""
    err = Err400(message="bad", error_type="custom_type")
    assert err.error_type == "custom_type"
    assert err.to_dict()["error_type"] == "custom_type"


# --------------------
# Tests for HttpErr400BadRequest
# --------------------


def test_400_single_error_with_headers(err: Err400):
    env = HttpErr400BadRequest(
        detail=(err,),
        headers={"X-Error": "validation"},
    )
    assert env.status_code == 400
    assert isinstance(env.detail, tuple)
    assert len(env.detail) == 1 and isinstance(env.detail[0], Err400)
    assert env.headers == {"X-Error": "validation"}


def test_400_multiple_errors(err: Err400):
    e1, e2 = err, err
    env = HttpErr400BadRequest(detail=(e1, e2))
    assert env.status_code == 400
    assert env.detail == (e1, e2)


def test_400_defaults_empty_detail_and_none_headers():
    env = HttpErr400BadRequest()
    assert env.status_code == 400
    assert env.detail == []
    assert env.headers is None


def test_400_is_frozen_and_detail_is_immutable(err: Err400):
    env = HttpErr400BadRequest(detail=(err,))
    with pytest.raises(FrozenInstanceError):
        env.status_code = 499
    with pytest.raises(FrozenInstanceError):
        env.detail = ()
    with pytest.raises(AttributeError):
        env.detail.append(Err400())


def test_400_cannot_pass_status_code_in_init():
    with pytest.raises(TypeError):
        HttpErr400BadRequest(status_code=418)
