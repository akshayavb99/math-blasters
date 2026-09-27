"""Tests for OAuth account resolution and sign-in identity behavior."""

import secrets

import pytest
from sqlalchemy import func, select

from app.accounts import resolve_account
from app.models import Account, Learner, OAuthIdentity


def row_count(session, model):
    return session.scalar(select(func.count()).select_from(model))


@pytest.fixture
def signed_out_learner(session):
    """Create a learner whose token represents a signed-out identity cookie."""

    def create_learner():
        learner = Learner(token=secrets.token_urlsafe(32))
        session.add(learner)
        session.flush()
        return learner

    return create_learner


@pytest.fixture
def sign_in(session):
    """Simulate provider sign-in while exercising the production account resolver."""

    def sign_in_learner(
        learner: Learner,
        *,
        provider: str,
        provider_account_id: str,
        email: str,
        email_verified: bool,
    ) -> tuple[Account, str, str]:
        previous_token = learner.token
        account = resolve_account(
            session=session,
            provider=provider,
            provider_account_id=provider_account_id,
            email=email,
            email_verified=email_verified,
        )

        learner.account_id = account.id
        learner.token = secrets.token_urlsafe(32)
        session.flush()

        return account, previous_token, learner.token

    return sign_in_learner


def test_first_sign_in_creates_exactly_one_account_and_identity(
    session, signed_out_learner, sign_in
):
    learner = signed_out_learner()

    sign_in(
        learner,
        provider="github",
        provider_account_id="github-user-1",
        email="ada@example.com",
        email_verified=True,
    )

    assert row_count(session, Account) == 1
    assert row_count(session, OAuthIdentity) == 1


def test_same_provider_id_returns_the_same_account(session):
    first_account = resolve_account(
        session,
        provider="github",
        provider_account_id="github-user-1",
        email="ada@example.com",
        email_verified=True,
    )
    second_account = resolve_account(
        session,
        provider="github",
        provider_account_id="github-user-1",
        email="ada-renamed@example.com",
        email_verified=True,
    )

    assert second_account.id == first_account.id
    assert row_count(session, Account) == 1
    assert row_count(session, OAuthIdentity) == 1


def test_second_provider_with_same_verified_email_attaches_to_account(session):
    first_account = resolve_account(
        session,
        provider="github",
        provider_account_id="github-user-1",
        email="ada@example.com",
        email_verified=True,
    )
    second_account = resolve_account(
        session,
        provider="google",
        provider_account_id="google-user-2",
        email="ada@example.com",
        email_verified=True,
    )

    assert second_account.id == first_account.id
    assert row_count(session, Account) == 1
    assert row_count(session, OAuthIdentity) == 2


def test_same_email_unverified_creates_a_separate_account(session):
    verified_account = resolve_account(
        session,
        provider="github",
        provider_account_id="github-user-1",
        email="ada@example.com",
        email_verified=True,
    )
    unverified_account = resolve_account(
        session,
        provider="google",
        provider_account_id="google-user-2",
        email="ada@example.com",
        email_verified=False,
    )

    assert unverified_account.id != verified_account.id
    assert row_count(session, Account) == 2
    assert row_count(session, OAuthIdentity) == 2


def test_two_signed_out_cookies_for_same_provider_identity_do_not_duplicate_account(
    session, signed_out_learner, sign_in
):
    first_learner = signed_out_learner()
    second_learner = signed_out_learner()
    assert first_learner.token != second_learner.token

    first_account, first_old_token, first_new_token = sign_in(
        first_learner,
        provider="github",
        provider_account_id="github-user-1",
        email="ada@example.com",
        email_verified=True,
    )
    second_account, second_old_token, second_new_token = sign_in(
        second_learner,
        provider="github",
        provider_account_id="github-user-1",
        email="ada@example.com",
        email_verified=True,
    )

    assert first_account.id == second_account.id
    assert first_new_token != first_old_token
    assert second_new_token != second_old_token
    assert row_count(session, Account) == 1
    assert row_count(session, OAuthIdentity) == 1


def test_sign_in_rotates_token_and_old_token_no_longer_resolves(
    session, signed_out_learner, sign_in
):
    learner = signed_out_learner()
    old_token = learner.token

    account, previous_token, new_token = sign_in(
        learner,
        provider="github",
        provider_account_id="github-user-1",
        email="ada@example.com",
        email_verified=True,
    )

    assert previous_token == old_token
    assert new_token != old_token
    assert session.scalar(select(Learner).where(Learner.token == old_token)) is None

    signed_in_learner = session.scalar(select(Learner).where(Learner.token == new_token))
    assert signed_in_learner is not None
    assert signed_in_learner.account_id == account.id
