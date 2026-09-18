import secrets
from typing import Annotated

from fastapi import Depends, Request, Response, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.db import SessionDep
from app.models import Learner

LEARNER_COOKIE_NAME = "learner_token"
LEARNER_TOKEN_BYTES = 32


def get_current_learner(request: Request, response: Response, session: SessionDep) -> Learner:
    token = request.cookies.get(LEARNER_COOKIE_NAME)

    try:
        if token:
            learner = session.scalar(select(Learner).where(Learner.token == token))
            if learner is not None:
                return learner

        # If a learner could not be found, add learner with new token to learners table
        learner = Learner(token=secrets.token_urlsafe(LEARNER_TOKEN_BYTES))
        session.add(learner)
        session.commit()
        session.refresh(learner)

        response.set_cookie(
            key=LEARNER_COOKIE_NAME, value=learner.token, httponly=True, samesite="lax", path="/"
        )

        return learner

    except OperationalError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database Unavailable",
        ) from exc


LearnerDep = Annotated[Learner, Depends(get_current_learner)]
