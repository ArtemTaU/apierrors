"""Unit tests for HttpErrorEnvelope dataclass (transport-agnostic envelope)."""

from dataclasses import is_dataclass

import pytest

from apierrors.errors_models.base import Error
from apierrors.errors_models import HttpErrorEnvelope


@pytest.fixture
def sample_error() -> Error:
    """Provide a minimal valid Error instance."""
    return Error(code="BAD_REQUEST", error_type="bad_request", message="oops")


def test_constructor_is_keyword_only(sample_error: Error):
    """All fields are keyword-only due to @dataclass(kw_only=True)."""
    with pytest.raises(TypeError):
        HttpErrorEnvelope(400)


def test_field_types(sample_error: Error):
    """Runtime typing: status_code=int, detail=list[Error], headers=dict[str,str]|None."""
    env = HttpErrorEnvelope(
        status_code=400,
        detail=[sample_error],
        headers={"X-Trace": "t-1"},
    )
    assert is_dataclass(env)
    assert isinstance(env.status_code, int)
    assert isinstance(env.detail, list)
    assert all(isinstance(e, Error) for e in env.detail)
    assert isinstance(env.headers, dict)
    assert all(
        isinstance(k, str) and isinstance(v, str) for k, v in env.headers.items()
    )


def test_required_params(sample_error: Error):
    """Only status_code is required; omitting it must raise TypeError."""
    with pytest.raises(TypeError):
        HttpErrorEnvelope()

    env = HttpErrorEnvelope(status_code=400)
    assert env.status_code == 400


def test_defaults_values_are_applied():
    """detail defaults to a new empty list; headers defaults to None."""
    env = HttpErrorEnvelope(status_code=400)
    assert env.detail == []
    assert env.headers is None

    other = HttpErrorEnvelope(status_code=400)
    env.detail.append(Error(code="C", error_type="t", message="m"))
    assert other.detail == []


def test_detail_smoke_list_of_errors(sample_error: Error):
    """Smoke: envelope accepts list of Error instances and preserves order."""
    e2 = Error(code="BAD_REQUEST", error_type="bad_request", message="second")
    env = HttpErrorEnvelope(status_code=400, detail=[sample_error, e2])

    assert len(env.detail) == 2
    assert env.detail[0].message == "oops"
    assert env.detail[1].message == "second"
