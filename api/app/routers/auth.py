"""FastAPI Route for GET current account details"""

from fastapi import APIRouter, Request, Response, status
from sqlalchemy import select

from app.db import SessionDep
from app.learner import LEARNER_COOKIE_NAME, LEARNER_TOKEN_PATTERN, issue_learner_identity
from app.models import Account, Learner, OAuthIdentity
from app.schemas import AccountMeGetResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=AccountMeGetResponse | None)
def get_me(request: Request, session: SessionDep) -> AccountMeGetResponse | None:
    token = request.cookies.get(LEARNER_COOKIE_NAME)
    if not token or not LEARNER_TOKEN_PATTERN.fullmatch(token):
        return None

    account = session.scalar(
        select(Account)
        .join(Learner, Learner.account_id == Account.id)
        .where(Learner.token == token)
    )

    if account is None:
        return None

    providers = session.scalars(
        select(OAuthIdentity.provider).where(OAuthIdentity.account_id == account.id).distinct()
    ).all()

    return AccountMeGetResponse(
        display_name=account.display_name,
        avatar_url=account.avatar_url,
        email=account.email,
        providers=sorted(set(providers)),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def logout(request: Request, response: Response, session: SessionDep) -> None:
    token = request.cookies.get(LEARNER_COOKIE_NAME)

    if token and LEARNER_TOKEN_PATTERN.fullmatch(token):
        learner = session.scalar(select(Learner).where(Learner.token == token))
        if learner:
            session.delete(learner)

    issue_learner_identity(session, response)
