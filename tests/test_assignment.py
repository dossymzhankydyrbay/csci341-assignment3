"""Offline full-stack database tests (SQLite emulates syntax; PostgreSQL is target).

For final PostgreSQL verification, set DATABASE_URL to a PostgreSQL DB and run:
    python -m assignment3.part2 --reset
These tests intentionally use no PostgreSQL-specific installation/network connection.
"""
from __future__ import annotations
from datetime import date
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from assignment3.db import reset_database,table_counts
from assignment3.part2 import Reporter,run,fetch
from assignment3.queries import OPERATIONS, PARAMETERS, MUTATION_PREVIEWS, SQLITE_DEADLINE_UPDATE
from assignment3.validation import (
  BusinessRuleError, seed_invariant_violations, create_review, replace_paper_authors,
  assign_paper_session,change_paper_status,change_paper_track,
  change_session_conference,change_track_conference,
)

@pytest.fixture
def engine():
    engine = create_engine('sqlite+pysqlite:///:memory:', future=True)
    with engine.connect() as conn:
        conn.exec_driver_sql('PRAGMA foreign_keys=ON')
        conn.commit()
    reset_database(engine, include_view=False)
    yield engine
    engine.dispose()


def test_seed_and_all_required_edge_cases(engine):
    with engine.connect() as c:
        counts = {x['table']:x['rows'] for x in table_counts(c)}
        assert counts['app_user']==15 and counts['paper']==14
        assert counts['paper_version']==19 and counts['review']==26
        assert counts['conference']==3
        assert seed_invariant_violations(c)==[]
        assert c.execute(text('SELECT COUNT(DISTINCT status) FROM paper')).scalar_one() == 5
        assert c.execute(text('''SELECT COUNT(*) FROM paper p WHERE p.status='accepted'
            AND p.session_id IS NULL''')).scalar_one() >= 1
        assert c.execute(text('''SELECT COUNT(*) FROM paper p WHERE p.status='accepted'
            AND p.session_id IS NOT NULL''')).scalar_one() >= 1
        assert c.execute(text('''SELECT COUNT(*) FROM reviewer r WHERE NOT EXISTS
            (SELECT 1 FROM review v WHERE v.reviewer_id=r.reviewer_id)''')).scalar_one() >= 1
        assert c.execute(text('''SELECT COUNT(*) FROM track t WHERE NOT EXISTS
            (SELECT 1 FROM paper p WHERE p.track_id=t.track_id)''')).scalar_one() >= 1
        assert c.execute(text('''SELECT COUNT(*) FROM conference c WHERE NOT EXISTS
            (SELECT 1 FROM track t JOIN paper p ON p.track_id=t.track_id
              WHERE t.conference_id=c.conference_id)''')).scalar_one() >= 1
        assert c.execute(text('''SELECT COUNT(*) FROM conference_session s
             JOIN conference c ON c.conference_id=s.conference_id
             WHERE c.city='Astana' AND NOT EXISTS
             (SELECT 1 FROM paper p WHERE p.session_id=s.session_id)''')).scalar_one() >= 1
        assert c.execute(text('''SELECT COUNT(*) FROM paper p
             JOIN paper_author pa ON pa.paper_id=p.paper_id AND pa.is_corresponding=TRUE
             JOIN app_user u ON u.user_id=pa.author_id
             WHERE status='withdrawn' AND u.email='amina.aminova@example.com' ''')).scalar_one() == 2


def test_update_3_1_by_email_and_3_2_both_branches(engine):
    with engine.connect() as c:
        tx = c.begin()
        assert c.execute(text(OPERATIONS['3.1']),PARAMETERS['3.1']).rowcount==1
        assert c.execute(text("SELECT phone_number FROM app_user WHERE email='arman.armanov@example.com'")).scalar_one()=='+77773414141'
        assert c.execute(text(SQLITE_DEADLINE_UPDATE),PARAMETERS['3.2']).rowcount==3
        dates=dict(c.execute(text('SELECT conference_id, review_deadline FROM conference')).all())
        assert dates=={101:'2027-03-10',102:'2027-05-04',103:'2027-07-12'}
        tx.rollback()
        assert c.execute(text("SELECT phone_number FROM app_user WHERE user_id=1")).scalar_one()!='+77773414141'


def test_delete_4_1_cascades_every_dependent_type(engine):
    with engine.connect() as c:
        tx=c.begin()
        assert c.execute(text(OPERATIONS['4.1']),PARAMETERS['4.1']).rowcount==2
        for tbl in ('paper','paper_author','paper_keyword','paper_version','review'):
            assert c.execute(text(f'SELECT COUNT(*) FROM {tbl} WHERE paper_id IN (2,3)')).scalar_one()==0
        assert c.execute(text('SELECT COUNT(*) FROM app_user')).scalar_one()==15
        assert c.execute(text('SELECT COUNT(*) FROM conference')).scalar_one()==3
        assert c.execute(text('SELECT COUNT(*) FROM paper')).scalar_one()==12
        tx.rollback()
        assert c.execute(text('SELECT COUNT(*) FROM paper')).scalar_one()==14


def test_delete_4_2_only_empty_astana_sessions(engine):
    with engine.connect() as c:
        tx=c.begin()
        assert c.execute(text(OPERATIONS['4.2']),PARAMETERS['4.2']).rowcount==3
        ids={r[0] for r in c.execute(text('SELECT session_id FROM conference_session'))}
        assert ids=={501,504,506}
        assert c.execute(text('SELECT COUNT(*) FROM conference')).scalar_one()==3
        tx.rollback()


def test_all_selects_and_aggregations(engine):
    with engine.connect() as c:
        for k in ('5.1','5.2','5.3','5.4','6.1','6.2','6.3','6.4','7'):
            assert fetch(c, OPERATIONS[k], PARAMETERS.get(k, {})),k
        papers=fetch(c,OPERATIONS['5.1'],PARAMETERS['5.1'])
        assert {x['paper_id'] for x in papers}=={1,7,8,10,12}
        assert len(papers)==5
        assert [x['paper_id'] for x in fetch(c,OPERATIONS['5.2'],PARAMETERS['5.2'])]==[1,8]
        assert [x['version_no'] for x in fetch(c,OPERATIONS['5.3'],PARAMETERS['5.3'])]==[5,3,1]
        assert {x['reviewer_id'] for x in fetch(c,OPERATIONS['5.4'],PARAMETERS['5.4'])}=={1,4,5,9,10}
        track={x['track_id']:x for x in fetch(c,OPERATIONS['6.1'])}
        assert len(track)==6 and track[1003]['paper_count']==0 and track[1003]['distinct_author_count']==0
        assert track[3001]['paper_count']==0
        assert track[1001]['paper_count']==5
        rev={x['reviewer_id']:x for x in fetch(c,OPERATIONS['6.2'])}
        assert len(rev)==9 and rev[13]['review_count']==0 and rev[13]['avg_overall_score'] is None
        assert sum(x['review_count'] for x in rev.values())==26
        conferences={x['conference_id']:x for x in fetch(c,OPERATIONS['6.3'])}
        assert len(conferences)==3
        assert conferences[101]['paper_count']==8 and conferences[102]['paper_count']==6
        assert conferences[103]['paper_count']==0 and conferences[103]['accepted_paper_count']==0
        assert conferences[103]['avg_overall_review_score'] is None
        high=fetch(c,OPERATIONS['6.4'])
        average=26/9
        assert all(row['review_count']>average for row in high)
        rates={x['conference_id']:x for x in fetch(c,OPERATIONS['7'])}
        assert rates[101]['accepted_count']==2 and rates[101]['rejected_count']==1
        assert rates[103]['acceptance_rate_percent'] is None
        assert abs(float(rates[101]['acceptance_rate_percent'])-66.67)<0.01


def test_view_correct_order_and_exclusions(engine):
    with engine.begin() as c:
        c.exec_driver_sql(__import__('assignment3.db',fromlist=['bundled_statements']).bundled_statements('03_view.sql')[0].replace('CREATE OR REPLACE VIEW','CREATE VIEW'))
    with engine.connect() as c:
        rows=fetch(c,OPERATIONS['8'])
        assert [x['paper_id'] for x in rows]==[1,8,12]
        assert all(x['corresponding_author_email'] for x in rows)


def test_database_enforces_core_constraints(engine):
    invalid = [
      "INSERT INTO app_user(user_id,given_name,surname,email,affiliation,country) VALUES(99,'N','N','arman.armanov@example.com','X','X')",
      "UPDATE reviewer SET years_experience=-1 WHERE reviewer_id=1",
      "UPDATE paper SET status='pending' WHERE paper_id=1",
      "UPDATE review SET overall_score=6 WHERE review_id=1",
      "UPDATE review SET recommendation='maybe' WHERE review_id=1",
      "UPDATE paper_author SET author_position=0 WHERE paper_id=1 AND author_id=2",
      "UPDATE paper_author SET author_position=1 WHERE paper_id=1 AND author_id=3",
      "UPDATE paper_author SET is_corresponding=TRUE WHERE paper_id=1 AND author_id=3",
      "INSERT INTO paper_version (paper_id,version_no,file_location,uploaded_at) VALUES(1,0,'x','2027-01-01')",
      "UPDATE conference SET end_date='2020-01-01' WHERE conference_id=101",
      "UPDATE conference_session SET end_time='08:00:00' WHERE session_id=501",
      "INSERT INTO review (review_id,paper_id,reviewer_id,overall_score,recommendation,comments_for_authors,review_submission_date) VALUES(999,1,1,4,'accept','x','2027-02-10')",
    ]
    for sql in invalid:
        with engine.connect() as c:
            tx=c.begin()
            try:
                with pytest.raises(IntegrityError):
                    c.exec_driver_sql(sql)
            finally:
                tx.rollback()


def test_application_checks_reject_each_invalid_change(engine):
    cases = [
      lambda c: create_review(c, review_id=200,paper_id=7,reviewer_id=7,
           overall_score=3,recommendation='accept',comments_for_authors='no',
           review_submission_date=date(2027,2,1)),
      lambda c: replace_paper_authors(c,1,[(4,1,True),(3,2,False)]),
      lambda c: assign_paper_session(c,5,501),
      lambda c: assign_paper_session(c,7,504),
      lambda c: change_paper_status(c,1,'withdrawn'),
      lambda c: change_paper_track(c,1,2001),
      lambda c: change_session_conference(c,501,102),
      lambda c: change_track_conference(c,1001,102),
    ]
    for fn in cases:
        with engine.connect() as c:
            tx=c.begin()
            try:
                with pytest.raises(BusinessRuleError):
                    fn(c)
            finally:
                tx.rollback()
    with engine.connect() as c:
        assert seed_invariant_violations(c)==[]


def test_valid_transactional_changes(engine):
    with engine.begin() as c:
        assign_paper_session(c,7,503)  # accepted, same conference
        change_paper_track(c,7,1002)  # different track, same conference
        replace_paper_authors(c,7,[(7,1,True),(2,2,False)])
        create_review(c,review_id=200,paper_id=7,reviewer_id=4,
                      overall_score=4,recommendation='accept',comments_for_authors='Nice',
                      review_submission_date=date(2027,2,25))
    with engine.connect() as c:
        assert seed_invariant_violations(c)==[]
        assert c.execute(text('SELECT session_id FROM paper WHERE paper_id=7')).scalar_one()==503
        assert c.execute(text('SELECT COUNT(*) FROM review WHERE review_id=200')).scalar_one()==1


def test_full_part2_numbered_execution_offline(engine):
    # Execute complete script, including reset and creation of actual query view.
    reporter=Reporter()
    run(engine,True,reporter)
    joined='\n'.join(reporter.lines)
    for task in ('1','2','3.1','3.2','4.1','4.2','5.1','5.2','5.3','5.4',
                 '6.1','6.2','6.3','6.4','7','8'):
        assert f'TASK {task} ' in joined
    assert 'ALL PART 1-2 DEMONSTRATIONS FINISHED' in joined
