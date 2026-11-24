"""Offline HTTP integration tests of Part 3, using SQLite only as test transport.
Production SQL target remains PostgreSQL. These tests exercise actual FastAPI routes.
"""
from __future__ import annotations
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import StaticPool
from assignment3.db import reset_database
from assignment3.web import create_app


@pytest.fixture
def client():
    engine = create_engine('sqlite://',future=True,
        connect_args={'check_same_thread':False},poolclass=StaticPool)
    @event.listens_for(engine, 'connect')
    def enable_foreign_keys(dbapi_conn,_):
        dbapi_conn.execute('PRAGMA foreign_keys=ON')
    reset_database(engine,include_view=False)
    with engine.begin() as c:
        c.exec_driver_sql(
            __import__('assignment3.db',fromlist=['bundled_statements'])
                .bundled_statements('03_view.sql')[0].replace('CREATE OR REPLACE VIEW', 'CREATE VIEW', 1))
    with TestClient(create_app(engine=engine,auto_setup=False)) as test_client:
        yield test_client
    engine.dispose()


def valid_user():
    return {'given_name':'Test','surname':'Researcher','email':'test-researcher@example.com',
      'affiliation':'Research Lab','country':'Kazakhstan','phone_number':None,
      'author':{'orcid':None,'research_areas':['Databases','Machine Learning']},
      'reviewer':{'years_experience':2,'expertise':['Databases']}}


def valid_paper():
    return {'track_id':1002,'title':'New Conference Paper','abstract':'A test paper',
      'submission_date':'2027-01-09','status':'accepted','session_id':503,
      'authors':[{'author_id':2,'author_position':1,'is_corresponding':True},
                 {'author_id':3,'author_position':2,'is_corresponding':False}],
      'keywords':['Databases','Demonstration'],
      'versions':[{'version_no':1,'file_location':'papers/test/v1.pdf',
                   'uploaded_at':'2027-01-09T10:00:00Z','change_note':None}]}


def valid_review():
    return {'paper_id':7,'reviewer_id':4,'overall_score':4,'recommendation':'accept',
      'comments_for_authors':'Promising work','confidential_comments':None,
      'review_submission_date':'2027-02-25'}


def valid_session():
    return {'conference_id':101,'title':'New session','session_date':'2027-04-11',
      'start_time':'15:00:00','end_time':'16:00:00','room_label':'A500','chair_id':4}


def assert_no_seed_violation(client):
    from assignment3.validation import seed_invariant_violations
    with client.app.state.engine.connect() as c:
        assert seed_invariant_violations(c)==[]


def test_dashboard_and_read_routes(client):
    assert client.get('/').status_code==200
    assert client.get('/docs').status_code==200
    assert client.get('/openapi.json').status_code==200
    assert client.get('/health').json()['status']=='ok'
    assert client.get('/stats').json()['tables']['review']==26
    assert len(client.get('/catalog').json()['conferences'])==3
    assert len(client.get('/schedule').json())==3
    assert len(client.get('/users').json())==15
    assert len(client.get('/papers').json())==14
    assert len(client.get('/reviews').json())==26
    assert len(client.get('/sessions').json())==6
    assert client.get('/users/1').json()['reviewer']['years_experience']==7
    assert client.get('/papers/1').json()['current_version_no']==5
    assert [x['version_no'] for x in client.get('/papers/1/versions').json()]==[5,3,1]
    assert client.get('/reviews/1').json()['paper_id']==1
    assert len(client.get('/sessions/501').json()['assigned_papers'])==1
    for endpoint in ('/users/9999','/papers/9999','/reviews/9999',
                     '/sessions/9999','/papers/9999/versions'):
        assert client.get(endpoint).status_code==404


def test_user_create_update_role_persistence_delete(client):
    bad=valid_user()
    bad['author']=None;bad['reviewer']=None
    assert client.post('/users',json=bad).status_code==422
    new=client.post('/users',json=valid_user())
    assert new.status_code==201,new.text
    uid=new.json()['user_id']
    assert new.json()['author']['research_areas']==['Databases','Machine Learning']
    assert new.json()['reviewer']['expertise']==['Databases']
    patch=client.patch(f'/users/{uid}',json={'phone_number':'+77777777777',
                       'reviewer':{'years_experience':4,'expertise':['Data Mining']}})
    assert patch.status_code==200,patch.text
    assert patch.json()['reviewer']['years_experience']==4
    assert patch.json()['phone_number']=='+77777777777'
    assert client.patch(f'/users/{uid}',json={'author':None,'reviewer':None}).status_code==422
    assert client.get(f'/users/{uid}').json()['author'] is not None
    assert client.patch(f'/users/{uid}',json={'reviewer':None}).status_code==200
    assert client.get(f'/users/{uid}').json()['reviewer'] is None
    assert client.delete(f'/users/{uid}').status_code==200
    assert client.get(f'/users/{uid}').status_code==404
    assert client.delete('/users/2').status_code==409 # active author
    assert client.patch('/users/1',json={'given_name':None}).status_code==422
    assert_no_seed_violation(client)


def test_user_email_and_role_references(client):
    duplicate=valid_user(); duplicate['email']='arman.armanov@example.com'
    assert client.post('/users',json=duplicate).status_code==409
    assert client.patch('/users/2',json={'author':None}).status_code==422
    assert client.patch('/users/4',json={'author':None}).status_code==409
    assert client.get('/users/2').json()['author'] is not None
    assert client.patch('/users/1',json={'reviewer':None}).status_code==422
    assert client.patch('/users/4',json={'reviewer':None}).status_code==409
    assert_no_seed_violation(client)


def test_paper_create_update_children_and_delete_cascades(client):
    created=client.post('/papers',json=valid_paper())
    assert created.status_code==201,created.text
    pid=created.json()['paper_id']
    assert created.json()['current_version_no']==1
    assert len(created.json()['authors'])==2
    patch=client.patch(f'/papers/{pid}',json={'title':'Updated Title',
         'keywords':['Relational Databases'],
         'authors':[{'author_id':2,'author_position':1,'is_corresponding':True}]})
    assert patch.status_code==200,patch.text
    assert patch.json()['title']=='Updated Title'
    assert len(patch.json()['authors'])==1
    assert patch.json()['keywords']==['Relational Databases']
    assert client.patch(f'/papers/{pid}',json={'status':'rejected'}).status_code==422
    assert client.get(f'/papers/{pid}').json()['status']=='accepted'
    assert client.patch(f'/papers/{pid}',json={'status':'rejected','session_id':None}).status_code==200
    assert client.get(f'/papers/{pid}').json()['session_id'] is None
    assert client.delete(f'/papers/{pid}').status_code==200
    assert client.get(f'/papers/{pid}').status_code==404
    with client.app.state.engine.connect() as c:
        for table in ('paper_author','paper_keyword','paper_version','review'):
            assert c.execute(text(f'SELECT COUNT(*) FROM {table} WHERE paper_id=:pid'),{'pid':pid}).scalar_one()==0
    assert_no_seed_violation(client)


def test_version_full_crud_and_current_max(client):
    v={'version_no':8,'file_location':'papers/1/v8.pdf',
       'uploaded_at':'2027-01-08T00:00:00Z','change_note':'New revision'}
    create=client.post('/papers/1/versions',json=v)
    assert create.status_code==201,create.text
    assert create.json()['current_version_no']==8
    assert client.post('/papers/1/versions',json=v).status_code==409
    edited=client.patch('/papers/1/versions/8',json={'file_location':'papers/1/v8-revised.pdf'})
    assert edited.status_code==200,edited.text
    assert edited.json()['file_location'].endswith('v8-revised.pdf')
    assert client.delete('/papers/1/versions/8').status_code==200
    assert client.get('/papers/1').json()['current_version_no']==5
    assert client.delete('/papers/6/versions/1').status_code==422
    assert client.get('/papers/6').json()['current_version_no']==1
    assert_no_seed_violation(client)


def test_paper_invalid_session_self_review_and_reassign(client):
    assert client.patch('/papers/5',json={'session_id':501}).status_code==422 # not accepted
    assert client.patch('/papers/7',json={'session_id':504}).status_code==422 # other conference
    assert client.patch('/papers/1',json={'status':'rejected'}).status_code==422
    assert client.patch('/papers/1',json={'track_id':2001}).status_code==422
    assert client.patch('/papers/1',json={'authors':[
        {'author_id':2,'author_position':1,'is_corresponding':True},
        {'author_id':4,'author_position':2,'is_corresponding':False}]}).status_code==422
    assert [a['author_id'] for a in client.get('/papers/1').json()['authors']]==[2,3]
    assert client.patch('/papers/7',json={'session_id':503}).status_code==200
    assert client.patch('/papers/7',json={'track_id':1002}).status_code==200
    assert_no_seed_violation(client)


def test_review_create_update_delete_and_self_review(client):
    invalid=valid_review();invalid['reviewer_id']=7
    assert client.post('/reviews',json=invalid).status_code==422
    duplicate=valid_review(); duplicate['reviewer_id']=1
    assert client.post('/reviews',json=duplicate).status_code==409
    good=client.post('/reviews',json=valid_review())
    assert good.status_code==201,good.text
    rid=good.json()['review_id']
    assert client.patch(f'/reviews/{rid}',json={'reviewer_id':7}).status_code==422
    assert client.get(f'/reviews/{rid}').json()['reviewer_id']==4
    edited=client.patch(f'/reviews/{rid}',json={'reviewer_id':10,'overall_score':5,
                                               'confidential_comments':'Internal memo'})
    assert edited.status_code==200,edited.text
    assert edited.json()['reviewer_id']==10
    assert edited.json()['overall_score']==5
    assert client.delete(f'/reviews/{rid}').status_code==200
    assert client.get(f'/reviews/{rid}').status_code==404
    assert_no_seed_violation(client)


def test_session_create_update_delete_and_schedule_validations(client):
    bad=valid_session();bad['chair_id']=2 # author-only, not in pool
    assert client.post('/sessions',json=bad).status_code==422
    bad=valid_session();bad['end_time']='14:00:00'
    assert client.post('/sessions',json=bad).status_code==422
    good=client.post('/sessions',json=valid_session())
    assert good.status_code==201,good.text
    sid=good.json()['session_id']
    edited=client.patch(f'/sessions/{sid}',json={'title':'International New Session',
                'conference_id':102,'chair_id':7})
    assert edited.status_code==200,edited.text
    assert edited.json()['conference_id']==102
    assert client.patch('/sessions/501',json={'conference_id':102,'chair_id':7}).status_code==422
    assert client.get('/sessions/501').json()['conference_id']==101
    assert client.delete(f'/sessions/{sid}').status_code==200
    assert client.get(f'/sessions/{sid}').status_code==404
    assert_no_seed_violation(client)


def test_deleting_nonempty_session_unassigns_papers(client):
    old=client.get('/sessions/501').json()
    assert [p['paper_id'] for p in old['assigned_papers']]==[1]
    deleted=client.delete('/sessions/501')
    assert deleted.status_code==200
    assert deleted.json()['unassigned_paper_ids']==[1]
    assert client.get('/papers/1').json()['status']=='accepted'
    assert client.get('/papers/1').json()['session_id'] is None
    assert all(row['paper_id']!=1 for row in client.get('/schedule').json())
    assert_no_seed_violation(client)


def test_invalid_user_body_and_null_rejection(client):
    assert client.post('/users',json={**valid_user(),'email':''}).status_code==422
    assert client.post('/reviews',json={**valid_review(),'overall_score':6}).status_code==422
    assert client.post('/papers',json={**valid_paper(),'status':'fake'}).status_code==422
    assert client.patch('/papers/1',json={'title':None}).status_code==422
    assert client.patch('/sessions/501',json={'start_time':None}).status_code==422
    assert client.patch('/reviews/1',json={'overall_score':None}).status_code==422
    assert_no_seed_violation(client)
