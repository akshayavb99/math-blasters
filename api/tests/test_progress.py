from app.models import Account, Completion, Learner
from tests.helpers import attach_signed_in_account, row_count


def test_signed_out_progress_is_empty_and_does_not_create_learner(client, session):
    response = client.get("/api/progress")

    assert response.status_code == 200
    assert response.json() == []
    assert row_count(session, Learner) == 0


def test_signed_in_account_without_completions_gets_empty_list(client, session):
    attach_signed_in_account(client, session, email="first@example.com", token="a" * 43)

    response = client.get("/api/progress")

    assert response.status_code == 200
    assert response.json() == []


def test_progress_returns_only_signed_in_accounts_lesson_slugs(client, session):
    account = attach_signed_in_account(client, session, email="first@example.com", token="a" * 43)
    other_account = Account(email="second@example.com")
    session.add(other_account)
    session.flush()

    session.add_all(
        [
            Completion(account_id=account.id, lesson_slug="making-ten"),
            Completion(account_id=account.id, lesson_slug="adding-two-numbers"),
            Completion(account_id=other_account.id, lesson_slug="counting-on"),
        ]
    )
    session.flush()

    response = client.get("/api/progress")

    assert response.status_code == 200
    assert response.json() == ["adding-two-numbers", "making-ten"]
