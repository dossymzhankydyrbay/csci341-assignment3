"""Part 3: FastAPI administrative CRUD for the conference review database.

Run: uvicorn assignment3.web:app --host 0.0.0.0 --port 8000
Interactive interface: /docs (FastAPI Swagger UI); no login required by assignment.
DB: PostgreSQL in production; SQLite exclusively for automated offline tests.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError

from .db import get_engine, reset_database, table_counts
from .validation import (
    BusinessRuleError, assign_paper_session, create_review, replace_paper_authors,
)
from .web_schemas import (
    AuthorProfile, PaperCreate, PaperPatch, PaperVersionCreate, PaperVersionPatch,
    ReviewCreate, ReviewPatch, ReviewerProfile, SessionCreate, SessionPatch,
    UserCreate, UserPatch,
)


# Identifiers below are from hardcoded allowlists. All user values are bound parameters.
def one(c: Connection, sql: str, **params) -> dict | None:
    row = c.execute(text(sql), params).mappings().first()
    return dict(row) if row is not None else None


def many(c: Connection, sql: str, **params) -> list[dict]:
    return [dict(row) for row in c.execute(text(sql), params).mappings().all()]


def required(row: dict | None, entity: str, identity: int) -> dict:
    if row is None:
        raise HTTPException(status_code=404, detail=f'{entity} {identity} not found')
    return row


def next_id(c: Connection, table: str, key: str) -> int:
    if (table, key) not in {('app_user','user_id'), ('paper','paper_id'),
                             ('review','review_id'), ('conference_session','session_id')}:
        raise RuntimeError('Invalid ID allocation')
    # Appendix A uses INTEGER PRIMARY KEY instead of IDENTITY. Advanced concurrency
    # handling is not required; production multi-writer installations should add sequences.
    return int(c.execute(text(f'SELECT COALESCE(MAX({key}), 0) + 1 FROM {table}')).scalar_one())


def update_fields(c: Connection, table: str, pk: str, pkval: int,
                  values: dict, allowed: frozenset[str]) -> None:
    changes = {k: v for k,v in values.items() if k in allowed}
    if not changes:
        return
    # Only trusted identifiers from a fixed allowlist are interpolated.
    statement = f'UPDATE {table} SET ' + ', '.join(f'{k}=:{k}' for k in changes) + f' WHERE {pk}=:__pk'
    c.execute(text(statement), {**changes, '__pk': pkval})


def clean_labels(labels: list[str], field: str) -> list[str]:
    out = [label.strip() for label in labels]
    if any(not label or len(label) > 150 for label in out):
        raise BusinessRuleError(f'{field} labels must contain 1–150 characters')
    if len(set(out)) != len(out):
        raise BusinessRuleError(f'Duplicate {field} label')
    return out


def write_author(c: Connection, user_id: int, profile: AuthorProfile | None) -> None:
    existing = one(c, 'SELECT author_id FROM author WHERE author_id=:uid', uid=user_id)
    if profile is None:
        if existing:
            c.execute(text('DELETE FROM author WHERE author_id=:uid'), {'uid':user_id})
        return
    areas = clean_labels(profile.research_areas, 'research area')
    if existing:
        c.execute(text('UPDATE author SET orcid=:orcid WHERE author_id=:uid'),
                  {'orcid':profile.orcid, 'uid':user_id})
    else:
        c.execute(text('INSERT INTO author(author_id,orcid) VALUES (:uid,:orcid)'),
                  {'uid':user_id,'orcid':profile.orcid})
    c.execute(text('DELETE FROM author_research_area WHERE author_id=:uid'), {'uid':user_id})
    for area in areas:
        c.execute(text('INSERT INTO author_research_area(author_id,area_label) VALUES (:uid,:label)'),
                  {'uid':user_id,'label':area})


def write_reviewer(c: Connection, user_id: int, profile: ReviewerProfile | None) -> None:
    existing = one(c,'SELECT reviewer_id FROM reviewer WHERE reviewer_id=:uid', uid=user_id)
    if profile is None:
        if existing:
            c.execute(text('DELETE FROM reviewer WHERE reviewer_id=:uid'), {'uid':user_id})
        return
    expertise = clean_labels(profile.expertise, 'expertise')
    if existing:
        c.execute(text('UPDATE reviewer SET years_experience=:yrs WHERE reviewer_id=:uid'),
                  {'yrs':profile.years_experience,'uid':user_id})
    else:
        c.execute(text('INSERT INTO reviewer(reviewer_id,years_experience) VALUES (:uid,:yrs)'),
                  {'uid':user_id,'yrs':profile.years_experience})
    c.execute(text('DELETE FROM reviewer_expertise WHERE reviewer_id=:uid'), {'uid':user_id})
    for area in expertise:
        c.execute(text('INSERT INTO reviewer_expertise(reviewer_id,area_label) VALUES (:uid,:label)'),
                  {'uid':user_id,'label':area})


def user_details(c: Connection, user_id: int) -> dict:
    user = required(one(c, 'SELECT * FROM app_user WHERE user_id=:uid', uid=user_id), 'User', user_id)
    author = one(c, 'SELECT orcid FROM author WHERE author_id=:uid', uid=user_id)
    if author is not None:
        author['research_areas'] = [r['area_label'] for r in many(c,
            'SELECT area_label FROM author_research_area WHERE author_id=:uid ORDER BY area_label', uid=user_id)]
    reviewer = one(c, 'SELECT years_experience FROM reviewer WHERE reviewer_id=:uid', uid=user_id)
    if reviewer is not None:
        reviewer['expertise'] = [r['area_label'] for r in many(c,
            'SELECT area_label FROM reviewer_expertise WHERE reviewer_id=:uid ORDER BY area_label', uid=user_id)]
    return {**user, 'author':author, 'reviewer':reviewer}


def track_conference(c: Connection, track_id: int) -> int:
    row = required(one(c, 'SELECT conference_id FROM track WHERE track_id=:id', id=track_id),
                   'Track', track_id)
    return row['conference_id']


def ensure_valid_assignment(c: Connection, track_id: int, paper_status: str,
                            session_id: int | None) -> int:
    conf = track_conference(c, track_id)
    if session_id is not None:
        session = required(one(c,
            'SELECT conference_id FROM conference_session WHERE session_id=:id', id=session_id),
            'Session', session_id)
        if paper_status != 'accepted':
            raise BusinessRuleError('Only accepted papers may be assigned to a session')
        if session['conference_id'] != conf:
            raise BusinessRuleError('Paper track and session must belong to the same conference')
    return conf


def ensure_reviewers_fit_track(c: Connection, paper_id: int, conference_id: int) -> None:
    bad = one(c, '''SELECT r.reviewer_id FROM review r
        WHERE r.paper_id=:pid AND NOT EXISTS (
        SELECT 1 FROM conference_reviewer cr
        WHERE cr.reviewer_id=r.reviewer_id AND cr.conference_id=:cid) LIMIT 1''',
        pid=paper_id, cid=conference_id)
    if bad:
        raise BusinessRuleError('Track change would move existing reviews outside the conference reviewer pool')


def write_keywords(c: Connection, paper_id: int, keywords: list[str]) -> None:
    labels = clean_labels(keywords, 'keyword')
    if not labels:
        raise BusinessRuleError('A paper must have at least one keyword')
    c.execute(text('DELETE FROM paper_keyword WHERE paper_id=:pid'), {'pid':paper_id})
    for keyword in labels:
        c.execute(text('INSERT INTO paper_keyword(paper_id,keyword) VALUES (:pid,:keyword)'),
                  {'pid':paper_id, 'keyword':keyword})


def author_tuples(authors):
    return [(x.author_id,x.author_position,x.is_corresponding) for x in authors]


def add_version(c: Connection, paper_id: int, version: PaperVersionCreate) -> None:
    c.execute(text('''INSERT INTO paper_version
       (paper_id,version_no,file_location,uploaded_at,change_note)
       VALUES (:pid,:ver,:loc,:uploaded,:note)'''),
       {'pid':paper_id,'ver':version.version_no,'loc':version.file_location,
        'uploaded':version.uploaded_at,'note':version.change_note})


def paper_details(c: Connection, paper_id: int) -> dict:
    paper = required(one(c, '''SELECT p.*, t.conference_id FROM paper p
        JOIN track t ON t.track_id=p.track_id WHERE p.paper_id=:pid''', pid=paper_id), 'Paper', paper_id)
    paper['authors'] = many(c, '''SELECT pa.author_id, pa.author_position, pa.is_corresponding,
        u.given_name, u.surname, u.email FROM paper_author pa
        JOIN app_user u ON u.user_id=pa.author_id WHERE pa.paper_id=:pid
        ORDER BY pa.author_position''', pid=paper_id)
    paper['keywords'] = [x['keyword'] for x in many(c,
        'SELECT keyword FROM paper_keyword WHERE paper_id=:pid ORDER BY keyword', pid=paper_id)]
    paper['versions'] = many(c, '''SELECT version_no,file_location,uploaded_at,change_note
        FROM paper_version WHERE paper_id=:pid ORDER BY version_no DESC''', pid=paper_id)
    paper['current_version_no'] = paper['versions'][0]['version_no'] if paper['versions'] else None
    return paper


def review_details(c: Connection, review_id: int) -> dict:
    return required(one(c, '''SELECT r.*,u.given_name AS reviewer_given_name,
        u.surname AS reviewer_surname, p.title AS paper_title
        FROM review r JOIN app_user u ON u.user_id=r.reviewer_id
        JOIN paper p ON p.paper_id=r.paper_id WHERE r.review_id=:id''', id=review_id),
        'Review', review_id)


def session_details(c: Connection, session_id: int) -> dict:
    session = required(one(c, 'SELECT * FROM conference_session WHERE session_id=:sid', sid=session_id),
                       'Session', session_id)
    session['assigned_papers'] = many(c, '''SELECT paper_id,title,status FROM paper
         WHERE session_id=:sid ORDER BY paper_id''', sid=session_id)
    return session


def ensure_chair_in_pool(c: Connection, conference_id: int, chair_id: int) -> None:
    required(one(c, 'SELECT conference_id FROM conference WHERE conference_id=:cid', cid=conference_id),
             'Conference', conference_id)
    if one(c, '''SELECT 1 FROM conference_reviewer
                 WHERE conference_id=:cid AND reviewer_id=:rid''', cid=conference_id, rid=chair_id) is None:
        raise BusinessRuleError('Session chair must belong to the selected conference reviewer pool')


def reject_none_fields(payload: dict, required_columns: set[str]) -> None:
    for key in required_columns.intersection(payload):
        if payload[key] is None:
            raise BusinessRuleError(f'{key} cannot be null')


def create_app(engine: Engine | None = None, auto_setup: bool | None = None) -> FastAPI:
    db_engine = engine

    def active_engine():
        nonlocal db_engine
        if db_engine is None:
            db_engine = get_engine()
        return db_engine
    auto_setup = (os.getenv('AUTO_SETUP', 'false').lower() in ('1','true','yes')) if auto_setup is None else auto_setup

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        # First-deploy-only initialization. Never drop data on a restart.
        if auto_setup and not inspect(active_engine()).has_table('app_user'):
            reset_database(active_engine(), include_view=True)
        yield

    app = FastAPI(
        title='CSCI 341 Conference & Paper Review Manager',
        description=('Administrative API and interactive forms for all Part 3 CRUD workflows. '
                     'Open /docs, expand an operation, click Try it out, and use the sample JSON. '
                     'No authentication or PDF uploads are required for this assignment.'),
        version='1.0.0', lifespan=lifespan,
        openapi_tags=[{'name':x,'description':f'Manage {x.lower()}'} for x in
                      ('Dashboard','Users','Papers','Versions','Reviews','Sessions','Reference Data')],
    )
    app.state.engine = db_engine

    def get_connection():
        with active_engine().connect() as c:
            yield c


    @app.exception_handler(BusinessRuleError)
    async def business_error(_, exc: BusinessRuleError):
        return JSONResponse(status_code=422, content={'detail':str(exc)})

    @app.exception_handler(IntegrityError)
    async def integrity_error(_, exc: IntegrityError):
        # Return useful feedback without exposing the server connection string.
        reason = str(exc.orig).split('\n')[0][:300]
        return JSONResponse(status_code=409, content={'detail':'Database constraint rejected the operation',
                                                      'database_reason':reason})

    @app.get('/', response_class=HTMLResponse, tags=['Dashboard'])
    def home():
        return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1"><title>CSCI 341 Manager</title>
        <style>body{font-family:system-ui,Arial;margin:0;background:#f6f7fb;color:#182130}
        main{max-width:850px;margin:60px auto;background:white;padding:40px;border-radius:12px;box-shadow:0 4px 24px #dde3ee}
        a{color:#0957a7}code{background:#eef1f6;padding:2px 6px;border-radius:4px}
        li{line-height:2}h1{margin-top:0}</style></head><body><main>
        <h1>Conference & Paper Review Management</h1>
        <p>CSCI 341 · Assignment 3 · Research conference administration</p>
        <p><strong>Working interface:</strong> <a href="/docs">Open interactive CRUD forms (Swagger UI)</a></p>
        <p>Use <em>Try it out</em> in /docs to create, view, update and delete records.</p>
        <ul><li>Users — author and reviewer roles / research and expertise labels</li>
        <li>Papers — authors, keywords, file-location versions, sessions</li>
        <li>Reviews — completed reviews with self-review prevention</li>
        <li>Sessions — validation of conference, chair and scheduled papers</li></ul>
        <p><a href="/redoc">API reference</a> · <a href="/catalog">Selection lists</a> ·
        <a href="/schedule">Accepted paper schedule</a> · <a href="/health">Health check</a></p>
        <p>Authentication and actual file uploads intentionally not included, as allowed by the assignment.</p>
        </main></body></html>'''

    @app.get('/health', tags=['Dashboard'])
    def health(c: Connection = Depends(get_connection)):
        c.execute(text('SELECT 1'))
        return {'status':'ok','database':'connected'}

    @app.get('/stats', tags=['Dashboard'])
    def stats(c: Connection = Depends(get_connection)):
        return {'tables':{x['table']:x['rows'] for x in table_counts(c)}}

    @app.get('/catalog', tags=['Reference Data'])
    def catalog(c: Connection = Depends(get_connection)):
        return {
            'conferences':many(c, '''SELECT * FROM conference ORDER BY conference_id'''),
            'tracks':many(c, '''SELECT track_id,conference_id,name,research_area,coordinator_id FROM track ORDER BY track_id'''),
            'reviewer_pools':many(c, '''SELECT cr.conference_id,cr.reviewer_id,u.given_name,u.surname
                FROM conference_reviewer cr JOIN app_user u ON u.user_id=cr.reviewer_id
                ORDER BY cr.conference_id,cr.reviewer_id'''),
            'hosts':many(c, 'SELECT * FROM conference_host ORDER BY conference_id,host_name'),
            'author_research_areas':many(c, '''SELECT * FROM author_research_area ORDER BY author_id,area_label'''),
            'reviewer_expertise':many(c, '''SELECT * FROM reviewer_expertise ORDER BY reviewer_id,area_label'''),
        }

    @app.get('/schedule', tags=['Reference Data'])
    def schedule(c: Connection = Depends(get_connection)):
        return many(c, '''SELECT * FROM accepted_paper_schedule
            ORDER BY conference_id,session_date,start_time,session_id,paper_id''')

    # User and role CRUD --------------------------------------------------
    @app.get('/users', tags=['Users'])
    def list_users(c: Connection = Depends(get_connection), limit: int = Query(100,ge=1,le=500), offset: int = Query(0,ge=0)):
        ids = [r['user_id'] for r in many(c, '''SELECT user_id FROM app_user
                 ORDER BY user_id LIMIT :lim OFFSET :off''', lim=limit,off=offset)]
        return [user_details(c, uid) for uid in ids]

    @app.get('/users/{user_id}', tags=['Users'])
    def get_user(user_id: int, c: Connection = Depends(get_connection)):
        return user_details(c,user_id)

    @app.post('/users', status_code=status.HTTP_201_CREATED, tags=['Users'])
    def add_user(body: UserCreate, c: Connection = Depends(get_connection)):
        with c.begin():
            uid = next_id(c,'app_user','user_id')
            data = body.model_dump(exclude={'author','reviewer'})
            c.execute(text('''INSERT INTO app_user(user_id,given_name,surname,email,affiliation,country,phone_number)
                VALUES (:uid,:given_name,:surname,:email,:affiliation,:country,:phone_number)'''),
                {'uid':uid,**data})
            if body.author is not None:
                write_author(c, uid, body.author)
            if body.reviewer is not None:
                write_reviewer(c, uid, body.reviewer)
            result = user_details(c, uid)
        return result

    @app.patch('/users/{user_id}', tags=['Users'])
    def edit_user(user_id: int, body: UserPatch, c: Connection = Depends(get_connection)):
        with c.begin():
            current = user_details(c,user_id)
            data = body.model_dump(exclude_unset=True)
            reject_none_fields(data,{'given_name','surname','email','affiliation','country'})
            eventual_author = data.get('author',current['author'])
            eventual_reviewer = data.get('reviewer',current['reviewer'])
            if eventual_author is None and eventual_reviewer is None:
                raise BusinessRuleError('Every user must have at least one author or reviewer role')
            # A role is replaced only when it occurs in the PATCH payload.
            update_fields(c,'app_user','user_id',user_id,data,
                frozenset({'given_name','surname','email','affiliation','country','phone_number'}))
            if 'author' in body.model_fields_set:
                write_author(c,user_id,body.author)
            if 'reviewer' in body.model_fields_set:
                write_reviewer(c,user_id,body.reviewer)
            result = user_details(c,user_id)
        return result

    @app.delete('/users/{user_id}', tags=['Users'])
    def remove_user(user_id: int, c: Connection = Depends(get_connection)):
        with c.begin():
            required(one(c,'SELECT user_id FROM app_user WHERE user_id=:uid',uid=user_id), 'User',user_id)
            # DB RESTRICT references refuse deletion of an active author/reviewer.
            c.execute(text('DELETE FROM app_user WHERE user_id=:uid'),{'uid':user_id})
        return {'deleted_user_id':user_id}

    # Paper CRUD, including authorships and keywords ---------------------
    @app.get('/papers', tags=['Papers'])
    def list_papers(c: Connection = Depends(get_connection), limit: int = Query(100,ge=1,le=500), offset: int = Query(0,ge=0)):
        ids = [r['paper_id'] for r in many(c,
            'SELECT paper_id FROM paper ORDER BY paper_id LIMIT :lim OFFSET :off', lim=limit,off=offset)]
        return [paper_details(c,pid) for pid in ids]

    @app.get('/papers/{paper_id}', tags=['Papers'])
    def get_paper(paper_id: int,c: Connection = Depends(get_connection)):
        return paper_details(c,paper_id)

    @app.post('/papers',status_code=status.HTTP_201_CREATED,tags=['Papers'])
    def add_paper(body: PaperCreate,c: Connection = Depends(get_connection)):
        with c.begin():
            ensure_valid_assignment(c,body.track_id,body.status,body.session_id)
            pid=next_id(c,'paper','paper_id')
            c.execute(text('''INSERT INTO paper
                (paper_id,track_id,title,abstract,submission_date,status,session_id)
                VALUES (:pid,:track,:title,:abstract,:date,:status,:sid)'''),
                {'pid':pid,'track':body.track_id,'title':body.title,'abstract':body.abstract,
                 'date':body.submission_date,'status':body.status,'sid':body.session_id})
            replace_paper_authors(c,pid,author_tuples(body.authors))
            write_keywords(c,pid,body.keywords)
            numbers=[x.version_no for x in body.versions]
            if len(numbers)!=len(set(numbers)):
                raise BusinessRuleError('A paper cannot have duplicate version numbers')
            for v in body.versions:
                add_version(c,pid,v)
            result=paper_details(c,pid)
        return result

    @app.patch('/papers/{paper_id}',tags=['Papers'])
    def edit_paper(paper_id: int,body: PaperPatch,c: Connection = Depends(get_connection)):
        with c.begin():
            current=paper_details(c,paper_id)
            data=body.model_dump(exclude_unset=True)
            reject_none_fields(data,{'track_id','title','abstract','submission_date','status','authors','keywords'})
            new_track=data.get('track_id',current['track_id'])
            new_status=data.get('status',current['status'])
            new_session=data.get('session_id',current['session_id'])
            new_conf=ensure_valid_assignment(c,new_track,new_status,new_session)
            if new_conf != current['conference_id']:
                ensure_reviewers_fit_track(c,paper_id,new_conf)
            # Apply the final state atomically (no invalid assignment is persisted).
            update_fields(c,'paper','paper_id',paper_id,data,
                 frozenset({'track_id','title','abstract','submission_date','status','session_id'}))
            if 'authors' in body.model_fields_set:
                replace_paper_authors(c,paper_id,author_tuples(body.authors))
            if 'keywords' in body.model_fields_set:
                write_keywords(c,paper_id,body.keywords)
            result=paper_details(c,paper_id)
        return result

    @app.delete('/papers/{paper_id}',tags=['Papers'])
    def remove_paper(paper_id: int,c: Connection = Depends(get_connection)):
        with c.begin():
            paper_details(c,paper_id)
            c.execute(text('DELETE FROM paper WHERE paper_id=:pid'),{'pid':paper_id})
        return {'deleted_paper_id':paper_id, 'dependent_records':'cascaded by foreign keys'}

    # Versions (paper workflow, file LOCATION only) ----------------------
    @app.get('/papers/{paper_id}/versions',tags=['Versions'])
    def list_versions(paper_id: int,c: Connection = Depends(get_connection)):
        return paper_details(c,paper_id)['versions']

    @app.post('/papers/{paper_id}/versions',status_code=status.HTTP_201_CREATED,tags=['Versions'])
    def create_version(paper_id: int,body: PaperVersionCreate,c: Connection = Depends(get_connection)):
        with c.begin():
            paper_details(c,paper_id)
            add_version(c,paper_id,body)
            result=paper_details(c,paper_id)
        return {'paper_id':paper_id,'current_version_no':result['current_version_no'],
                'versions':result['versions']}

    @app.patch('/papers/{paper_id}/versions/{version_no}',tags=['Versions'])
    def edit_version(paper_id: int,version_no: int,body: PaperVersionPatch,c: Connection = Depends(get_connection)):
        with c.begin():
            paper_details(c,paper_id)
            required(one(c,'''SELECT version_no FROM paper_version
                WHERE paper_id=:pid AND version_no=:ver''',pid=paper_id,ver=version_no),
                'Version',version_no)
            data=body.model_dump(exclude_unset=True)
            reject_none_fields(data,{'file_location','uploaded_at'})
            changes={k:v for k,v in data.items() if k in ('file_location','uploaded_at','change_note')}
            if changes:
                sql='UPDATE paper_version SET '+', '.join(f'{k}=:{k}' for k in changes)+\
                    ' WHERE paper_id=:__pid AND version_no=:__ver'
                c.execute(text(sql),{**changes,'__pid':paper_id,'__ver':version_no})
            result=required(one(c,'''SELECT * FROM paper_version
                 WHERE paper_id=:pid AND version_no=:ver''',pid=paper_id,ver=version_no),
                 'Version',version_no)
        return result

    @app.delete('/papers/{paper_id}/versions/{version_no}',tags=['Versions'])
    def remove_version(paper_id: int,version_no: int,c: Connection = Depends(get_connection)):
        with c.begin():
            versions=paper_details(c,paper_id)['versions']
            if not any(v['version_no']==version_no for v in versions):
                raise HTTPException(status_code=404,detail=f'Version {version_no} not found')
            if len(versions)<=1:
                raise BusinessRuleError('A paper must retain at least one version')
            c.execute(text('DELETE FROM paper_version WHERE paper_id=:pid AND version_no=:ver'),
                      {'pid':paper_id,'ver':version_no})
            current=one(c,'SELECT MAX(version_no) AS ver FROM paper_version WHERE paper_id=:pid',pid=paper_id)['ver']
        return {'deleted_version_no':version_no,'paper_id':paper_id,'current_version_no':current}

    # Completed reviews CRUD --------------------------------------------
    @app.get('/reviews',tags=['Reviews'])
    def list_reviews(c: Connection = Depends(get_connection),limit: int=Query(100,ge=1,le=500),offset: int=Query(0,ge=0)):
        ids=[r['review_id'] for r in many(c,
            'SELECT review_id FROM review ORDER BY review_id LIMIT :lim OFFSET :off',lim=limit,off=offset)]
        return [review_details(c,rid) for rid in ids]

    @app.get('/reviews/{review_id}',tags=['Reviews'])
    def get_review(review_id: int,c: Connection = Depends(get_connection)):
        return review_details(c,review_id)

    @app.post('/reviews',status_code=status.HTTP_201_CREATED,tags=['Reviews'])
    def add_review(body: ReviewCreate,c: Connection = Depends(get_connection)):
        with c.begin():
            rid=next_id(c,'review','review_id')
            create_review(c,review_id=rid,**body.model_dump())
            result=review_details(c,rid)
        return result

    @app.patch('/reviews/{review_id}',tags=['Reviews'])
    def edit_review(review_id: int,body: ReviewPatch,c: Connection = Depends(get_connection)):
        with c.begin():
            current=review_details(c,review_id)
            data=body.model_dump(exclude_unset=True)
            reject_none_fields(data,{'paper_id','reviewer_id','overall_score','recommendation',
                                     'comments_for_authors','review_submission_date'})
            old={k:current[k] for k in ('paper_id','reviewer_id','overall_score','recommendation',
                'comments_for_authors','confidential_comments','review_submission_date')}
            full={**old,**data}
            # Delete + re-insert within a single transaction guarantees that the SAME
            # self-review / pool checks are applied to modified paper/reviewer pairs.
            # Any failure rolls back both statements and restores the old review.
            c.execute(text('DELETE FROM review WHERE review_id=:rid'),{'rid':review_id})
            create_review(c,review_id=review_id,**full)
            result=review_details(c,review_id)
        return result

    @app.delete('/reviews/{review_id}',tags=['Reviews'])
    def remove_review(review_id: int,c: Connection = Depends(get_connection)):
        with c.begin():
            review_details(c,review_id)
            c.execute(text('DELETE FROM review WHERE review_id=:rid'),{'rid':review_id})
        return {'deleted_review_id':review_id}

    # Session CRUD --------------------------------------------------------
    @app.get('/sessions',tags=['Sessions'])
    def list_sessions(c: Connection = Depends(get_connection),limit: int=Query(100,ge=1,le=500),offset: int=Query(0,ge=0)):
        ids=[r['session_id'] for r in many(c,
            'SELECT session_id FROM conference_session ORDER BY session_id LIMIT :lim OFFSET :off',lim=limit,off=offset)]
        return [session_details(c,sid) for sid in ids]

    @app.get('/sessions/{session_id}',tags=['Sessions'])
    def get_session(session_id: int,c: Connection = Depends(get_connection)):
        return session_details(c,session_id)

    @app.post('/sessions',status_code=status.HTTP_201_CREATED,tags=['Sessions'])
    def add_session(body: SessionCreate,c: Connection = Depends(get_connection)):
        with c.begin():
            ensure_chair_in_pool(c,body.conference_id,body.chair_id)
            sid=next_id(c,'conference_session','session_id')
            values=body.model_dump()
            values['start_time']=body.start_time.isoformat()
            values['end_time']=body.end_time.isoformat()
            c.execute(text('''INSERT INTO conference_session(session_id,conference_id,title,
               session_date,start_time,end_time,room_label,chair_id)
               VALUES (:sid,:conference_id,:title,:session_date,:start_time,:end_time,:room_label,:chair_id)'''),
               {'sid':sid,**values})
            result=session_details(c,sid)
        return result

    @app.patch('/sessions/{session_id}',tags=['Sessions'])
    def edit_session(session_id: int,body: SessionPatch,c: Connection = Depends(get_connection)):
        with c.begin():
            current=session_details(c,session_id)
            data=body.model_dump(exclude_unset=True)
            for key in ('start_time','end_time'):
                if data.get(key) is not None:
                    data[key]=data[key].isoformat()
            reject_none_fields(data,{'conference_id','title','session_date','start_time','end_time',
                                     'room_label','chair_id'})
            final={**{k:current[k] for k in ('conference_id','title','session_date','start_time',
                'end_time','room_label','chair_id')},**data}
            # SQLite returns strings for time values in offline tests; SQL time types in PG.
            if str(final['end_time']) <= str(final['start_time']):
                raise BusinessRuleError('Session end time must be later than start time')
            ensure_chair_in_pool(c,final['conference_id'],final['chair_id'])
            mismatch=one(c,'''SELECT p.paper_id FROM paper p JOIN track t ON t.track_id=p.track_id
               WHERE p.session_id=:sid AND (p.status<>'accepted' OR t.conference_id<>:cid) LIMIT 1''',
               sid=session_id,cid=final['conference_id'])
            if mismatch:
                raise BusinessRuleError('Changing the session conference would invalidate assigned paper(s)')
            update_fields(c,'conference_session','session_id',session_id,data,
                frozenset({'conference_id','title','session_date','start_time','end_time','room_label','chair_id'}))
            result=session_details(c,session_id)
        return result

    @app.delete('/sessions/{session_id}',tags=['Sessions'])
    def remove_session(session_id: int,c: Connection = Depends(get_connection)):
        with c.begin():
            old=session_details(c,session_id)
            c.execute(text('DELETE FROM conference_session WHERE session_id=:sid'),{'sid':session_id})
        return {'deleted_session_id':session_id,
                'unassigned_paper_ids':[p['paper_id'] for p in old['assigned_papers']]}

    return app


app=create_app()
