"""Part 1 required application checks and safe transactional write functions.

All functions receive a SQLAlchemy Connection and must be called within engine.begin().
Raise BusinessRuleError before writing inconsistent related rows; the caller transaction
must be rolled back on any error. Future Part 3 routes should use these same functions.
"""
from __future__ import annotations
from collections.abc import Sequence
from datetime import date
from sqlalchemy import text
from sqlalchemy.engine import Connection


class BusinessRuleError(ValueError):
    """A requested mutation violates an assignment business rule."""


def _one(conn: Connection, sql: str, **params):
    return conn.execute(text(sql), params).mappings().first()


def _exists(conn: Connection, sql: str, **params) -> bool:
    return _one(conn, sql, **params) is not None


def _paper(conn: Connection, paper_id: int):
    p = _one(conn, '''SELECT p.paper_id,p.status,p.session_id,t.conference_id
                       FROM paper p JOIN track t ON t.track_id=p.track_id
                       WHERE p.paper_id=:pid''', pid=paper_id)
    if not p:
        raise BusinessRuleError(f'Unknown paper {paper_id}')
    return p


def create_review(conn: Connection, *, review_id: int, paper_id: int, reviewer_id: int,
                  overall_score: int, recommendation: str, comments_for_authors: str,
                  review_submission_date: date, confidential_comments: str | None = None):
    """Check membership and avoid self-review BEFORE inserting a completed review."""
    p = _paper(conn, paper_id)
    if not _exists(conn,'SELECT 1 FROM reviewer WHERE reviewer_id=:rid',rid=reviewer_id):
        raise BusinessRuleError('User has no reviewer role')
    if _exists(conn, '''SELECT 1 FROM paper_author WHERE paper_id=:pid AND author_id=:rid''',
               pid=paper_id,rid=reviewer_id):
        raise BusinessRuleError('Self-review forbidden: reviewer is an author of this paper')
    if not _exists(conn, '''SELECT 1 FROM conference_reviewer
                       WHERE conference_id=:cid AND reviewer_id=:rid''',
                   cid=p['conference_id'],rid=reviewer_id):
        raise BusinessRuleError('Reviewer must belong to the conference reviewer pool')
    conn.execute(text('''INSERT INTO review
        (review_id,paper_id,reviewer_id,overall_score,recommendation,comments_for_authors,
         confidential_comments,review_submission_date)
        VALUES (:review_id,:paper_id,:reviewer_id,:overall_score,:recommendation,
                :comments_for_authors,:confidential_comments,:review_submission_date)'''),
        dict(review_id=review_id,paper_id=paper_id,reviewer_id=reviewer_id,
             overall_score=overall_score,recommendation=recommendation,
             comments_for_authors=comments_for_authors,
             confidential_comments=confidential_comments,
             review_submission_date=review_submission_date))


def replace_paper_authors(conn: Connection, paper_id: int, authors: Sequence[tuple[int,int,bool]]):
    """Replace all authors atomically; tuples = (author_id, position, corresponding)."""
    _paper(conn, paper_id)
    if not authors or sum(bool(a[2]) for a in authors) != 1:
        raise BusinessRuleError('Every paper must have exactly one corresponding author')
    if len(set(a[0] for a in authors)) != len(authors):
        raise BusinessRuleError('Duplicate author')
    if any(type(a[1]) is not int or a[1] < 1 for a in authors) or len(set(a[1] for a in authors)) != len(authors):
        raise BusinessRuleError('Author positions must be distinct positive integers')
    # Validate all records first; no partial replacement if business checks fail.
    for author_id, _, _ in authors:
        if not _exists(conn,'SELECT 1 FROM author WHERE author_id=:aid',aid=author_id):
            raise BusinessRuleError(f'Unknown author {author_id}')
        if _exists(conn,'''SELECT 1 FROM review WHERE paper_id=:pid AND reviewer_id=:aid''',
                   pid=paper_id,aid=author_id):
            raise BusinessRuleError('Author change forbidden: existing self-review would result')
    conn.execute(text('DELETE FROM paper_author WHERE paper_id=:pid'),dict(pid=paper_id))
    for author_id, position, corresponding in authors:
        conn.execute(text('''INSERT INTO paper_author
             (paper_id,author_id,author_position,is_corresponding)
             VALUES (:pid,:aid,:pos,:corr)'''),
             dict(pid=paper_id,aid=author_id,pos=position,corr=corresponding))


def assign_paper_session(conn: Connection, paper_id: int, session_id: int | None):
    p = _paper(conn,paper_id)
    if session_id is not None:
        s = _one(conn,'SELECT conference_id FROM conference_session WHERE session_id=:sid',sid=session_id)
        if not s:
            raise BusinessRuleError(f'Unknown session {session_id}')
        if p['status'] != 'accepted':
            raise BusinessRuleError('Only accepted papers may be scheduled')
        if p['conference_id'] != s['conference_id']:
            raise BusinessRuleError('Paper track and session must belong to the same conference')
    conn.execute(text('UPDATE paper SET session_id=:sid WHERE paper_id=:pid'),dict(sid=session_id,pid=paper_id))


def change_paper_status(conn: Connection, paper_id: int, new_status: str):
    p = _paper(conn,paper_id)
    if p['session_id'] is not None and new_status != 'accepted':
        raise BusinessRuleError('Unassign the session before moving a scheduled paper away from accepted')
    conn.execute(text('UPDATE paper SET status=:status WHERE paper_id=:pid'),
                 dict(status=new_status,pid=paper_id))


def change_paper_track(conn: Connection, paper_id: int, new_track_id: int):
    p = _paper(conn,paper_id)
    t = _one(conn,'SELECT conference_id FROM track WHERE track_id=:tid',tid=new_track_id)
    if not t:
        raise BusinessRuleError(f'Unknown track {new_track_id}')
    if p['session_id'] is not None:
        s = _one(conn,'SELECT conference_id FROM conference_session WHERE session_id=:sid',sid=p['session_id'])
        if s['conference_id'] != t['conference_id']:
            raise BusinessRuleError('Track change would invalidate scheduled session')
    conn.execute(text('UPDATE paper SET track_id=:tid WHERE paper_id=:pid'),
                 dict(tid=new_track_id,pid=paper_id))


def change_session_conference(conn: Connection, session_id: int, new_conference_id: int):
    if not _exists(conn, 'SELECT 1 FROM conference_session WHERE session_id=:sid',sid=session_id):
        raise BusinessRuleError(f'Unknown session {session_id}')
    if not _exists(conn, 'SELECT 1 FROM conference WHERE conference_id=:cid',cid=new_conference_id):
        raise BusinessRuleError('Unknown conference')
    mismatch = _exists(conn, '''SELECT 1 FROM paper p JOIN track t ON p.track_id=t.track_id
                               WHERE p.session_id=:sid AND t.conference_id<>:cid''',
                       sid=session_id,cid=new_conference_id)
    if mismatch:
        raise BusinessRuleError('Session conference change would invalidate a scheduled paper')
    # Chairs should be chosen from conference pool (optional Assignment 1 rule, enforced here).
    chair = _one(conn,'SELECT chair_id FROM conference_session WHERE session_id=:sid',sid=session_id)
    if not _exists(conn,'''SELECT 1 FROM conference_reviewer
            WHERE conference_id=:cid AND reviewer_id=:rid''',cid=new_conference_id,rid=chair['chair_id']):
        raise BusinessRuleError('Session chair is not in the destination conference reviewer pool')
    conn.execute(text('UPDATE conference_session SET conference_id=:cid WHERE session_id=:sid'),
                 dict(cid=new_conference_id,sid=session_id))


def change_track_conference(conn: Connection, track_id: int, new_conference_id: int):
    """An additional guard for the corresponding parent record mutation."""
    tr = _one(conn,'SELECT coordinator_id FROM track WHERE track_id=:tid',tid=track_id)
    if not tr:
        raise BusinessRuleError(f'Unknown track {track_id}')
    if not _exists(conn,'SELECT 1 FROM conference WHERE conference_id=:cid',cid=new_conference_id):
        raise BusinessRuleError('Unknown conference')
    if _exists(conn, '''SELECT 1 FROM paper p JOIN conference_session s
                    ON s.session_id=p.session_id WHERE p.track_id=:tid
                    AND s.conference_id<>:cid''',tid=track_id,cid=new_conference_id):
        raise BusinessRuleError('Track conference change would invalidate a scheduled paper')
    if not _exists(conn, '''SELECT 1 FROM conference_reviewer
                  WHERE conference_id=:cid AND reviewer_id=:rid''',cid=new_conference_id,rid=tr['coordinator_id']):
        raise BusinessRuleError('Track coordinator is not in the destination conference reviewer pool')
    conn.execute(text('UPDATE track SET conference_id=:cid WHERE track_id=:tid'),
                 dict(cid=new_conference_id,tid=track_id))


def seed_invariant_violations(conn: Connection) -> list[str]:
    """Check optional Assignment 1 rules and the two required checks in the seed."""
    checks = {
      'user_without_role': '''SELECT COUNT(*) FROM app_user u WHERE NOT EXISTS
          (SELECT 1 FROM author a WHERE a.author_id=u.user_id)
          AND NOT EXISTS (SELECT 1 FROM reviewer r WHERE r.reviewer_id=u.user_id)''',
      'paper_without_exactly_one_corresponding': '''SELECT COUNT(*) FROM paper p WHERE
          (SELECT COUNT(*) FROM paper_author pa WHERE pa.paper_id=p.paper_id AND pa.is_corresponding=TRUE)<>1''',
      'paper_without_author': '''SELECT COUNT(*) FROM paper p WHERE NOT EXISTS
          (SELECT 1 FROM paper_author pa WHERE pa.paper_id=p.paper_id)''',
      'paper_without_version': '''SELECT COUNT(*) FROM paper p WHERE NOT EXISTS
          (SELECT 1 FROM paper_version pv WHERE pv.paper_id=p.paper_id)''',
      'paper_without_keyword': '''SELECT COUNT(*) FROM paper p WHERE NOT EXISTS
          (SELECT 1 FROM paper_keyword pk WHERE pk.paper_id=p.paper_id)''',
      'conference_without_host': '''SELECT COUNT(*) FROM conference c WHERE NOT EXISTS
          (SELECT 1 FROM conference_host h WHERE h.conference_id=c.conference_id)''',
      'self_review': '''SELECT COUNT(*) FROM review r JOIN paper_author pa
          ON pa.paper_id=r.paper_id AND pa.author_id=r.reviewer_id''',
      'invalid_session_assignment': '''SELECT COUNT(*) FROM paper p
          JOIN track t ON p.track_id=t.track_id
          JOIN conference_session s ON p.session_id=s.session_id
          WHERE p.status<>'accepted' OR t.conference_id<>s.conference_id''',
      'coordinator_not_in_pool': '''SELECT COUNT(*) FROM track t WHERE NOT EXISTS
          (SELECT 1 FROM conference_reviewer cr WHERE cr.conference_id=t.conference_id
          AND cr.reviewer_id=t.coordinator_id)''',
      'chair_not_in_pool': '''SELECT COUNT(*) FROM conference_session s WHERE NOT EXISTS
          (SELECT 1 FROM conference_reviewer cr WHERE cr.conference_id=s.conference_id
          AND cr.reviewer_id=s.chair_id)''',
      'reviewer_not_in_pool': '''SELECT COUNT(*) FROM review r JOIN paper p ON r.paper_id=p.paper_id
          JOIN track t ON t.track_id=p.track_id WHERE NOT EXISTS
          (SELECT 1 FROM conference_reviewer cr WHERE cr.conference_id=t.conference_id
          AND cr.reviewer_id=r.reviewer_id)''',
    }
    return [f'{name}: {conn.execute(text(query)).scalar_one()} invalid rows'
            for name,query in checks.items() if conn.execute(text(query)).scalar_one() > 0]
