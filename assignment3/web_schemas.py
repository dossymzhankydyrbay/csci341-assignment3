"""Validated request bodies for Part 3's interactive FastAPI administration API."""
from __future__ import annotations
from datetime import date, datetime, time
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

PaperStatus = Literal['submitted', 'under review', 'accepted', 'rejected', 'withdrawn']
Recommendation = Literal['accept', 'reject']

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class AuthorProfile(StrictModel):
    orcid: str | None = Field(default=None, max_length=32)
    research_areas: list[str] = Field(default_factory=list)

class ReviewerProfile(StrictModel):
    years_experience: int = Field(ge=0)
    expertise: list[str] = Field(default_factory=list)

class UserCreate(StrictModel):
    given_name: str = Field(min_length=1, max_length=100)
    surname: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    affiliation: str = Field(min_length=1, max_length=200)
    country: str = Field(min_length=1, max_length=100)
    phone_number: str | None = Field(default=None, max_length=32)
    author: AuthorProfile | None = None
    reviewer: ReviewerProfile | None = None

    @model_validator(mode='after')
    def has_role(self):
        if self.author is None and self.reviewer is None:
            raise ValueError('At least one of author or reviewer must be provided')
        return self

class UserPatch(StrictModel):
    given_name: str | None = Field(default=None, min_length=1, max_length=100)
    surname: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    affiliation: str | None = Field(default=None, min_length=1, max_length=200)
    country: str | None = Field(default=None, min_length=1, max_length=100)
    phone_number: str | None = Field(default=None, max_length=32)
    author: AuthorProfile | None = None
    reviewer: ReviewerProfile | None = None

class AuthorAssignment(StrictModel):
    author_id: int = Field(gt=0)
    author_position: int = Field(gt=0)
    is_corresponding: bool = False

class PaperVersionCreate(StrictModel):
    version_no: int = Field(gt=0)
    file_location: str = Field(min_length=1)
    uploaded_at: datetime
    change_note: str | None = None

class PaperVersionPatch(StrictModel):
    file_location: str | None = Field(default=None, min_length=1)
    uploaded_at: datetime | None = None
    change_note: str | None = None

class PaperCreate(StrictModel):
    track_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=300)
    abstract: str = Field(min_length=1)
    submission_date: date
    status: PaperStatus
    session_id: int | None = None
    authors: list[AuthorAssignment] = Field(min_length=1)
    keywords: list[str] = Field(min_length=1)
    versions: list[PaperVersionCreate] = Field(min_length=1)

class PaperPatch(StrictModel):
    track_id: int | None = Field(default=None, gt=0)
    title: str | None = Field(default=None, min_length=1, max_length=300)
    abstract: str | None = Field(default=None, min_length=1)
    submission_date: date | None = None
    status: PaperStatus | None = None
    session_id: int | None = None
    authors: list[AuthorAssignment] | None = Field(default=None, min_length=1)
    keywords: list[str] | None = Field(default=None, min_length=1)

class ReviewCreate(StrictModel):
    paper_id: int = Field(gt=0)
    reviewer_id: int = Field(gt=0)
    overall_score: int = Field(ge=1, le=5)
    recommendation: Recommendation
    comments_for_authors: str = Field(min_length=1)
    confidential_comments: str | None = None
    review_submission_date: date

class ReviewPatch(StrictModel):
    paper_id: int | None = Field(default=None, gt=0)
    reviewer_id: int | None = Field(default=None, gt=0)
    overall_score: int | None = Field(default=None, ge=1, le=5)
    recommendation: Recommendation | None = None
    comments_for_authors: str | None = Field(default=None, min_length=1)
    confidential_comments: str | None = None
    review_submission_date: date | None = None

class SessionCreate(StrictModel):
    conference_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=200)
    session_date: date
    start_time: time
    end_time: time
    room_label: str = Field(min_length=1, max_length=100)
    chair_id: int = Field(gt=0)

    @model_validator(mode='after')
    def valid_time(self):
        if self.start_time >= self.end_time:
            raise ValueError('Session end time must be later than start time')
        return self

class SessionPatch(StrictModel):
    conference_id: int | None = Field(default=None, gt=0)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    session_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    room_label: str | None = Field(default=None, min_length=1, max_length=100)
    chair_id: int | None = Field(default=None, gt=0)

