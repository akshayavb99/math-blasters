from sqlalchemy import func, select

from app.learner import LEARNER_COOKIE_NAME
from app.models import Account, Learner


def row_count(session, model):
    return session.scalar(select(func.count()).select_from(model))


def attach_signed_in_account(client, session, *, email: str, token: str) -> Account:
    account = Account(email=email)
    learner = Learner(token=token, account=account)
    session.add_all([account, learner])
    session.flush()
    client.cookies.set(LEARNER_COOKIE_NAME, token)
    return account
