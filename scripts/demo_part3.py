"""Part 3 automated external HTTP demonstration.

Runs every CRUD category + both required failed validations, then cleans up its rows.
Usage:
    python scripts/demo_part3.py http://127.0.0.1:8000
    python scripts/demo_part3.py https://YOUR-APP.onrender.com
Requires app running with original seed. No DB resets are performed.
"""
from __future__ import annotations
import sys
import time
import uuid
import httpx

BASE=sys.argv[1].rstrip('/') if len(sys.argv)>1 else 'http://127.0.0.1:8000'
client=httpx.Client(base_url=BASE,timeout=30,follow_redirects=True)


def request(method,path,expected,**kwargs):
    response=client.request(method,path,**kwargs)
    print(f'[{method:6}] {path:<40} status={response.status_code}')
    if response.status_code not in ({expected} if isinstance(expected,int) else set(expected)):
        raise AssertionError(f'Unexpected status {response.status_code}: {response.text[:1000]}')
    return response.json()


def main():
    user_id=paper_id=review_id=session_id=None
    print('CSCI 341 - Part 3 live HTTP CRUD demonstration')
    print('Server:',BASE,'\n')
    request('GET','/health',200)
    request('GET','/stats',200)
    request('GET','/catalog',200)
    request('GET','/schedule',200)
    try:
        print('\n[Users CRUD + author/reviewer profiles]')
        email=f'part3-demo-{uuid.uuid4().hex[:12]}@example.com'
        u=request('POST','/users',201,json={
            'given_name':'Demo','surname':'Tester','email':email,'affiliation':'Demo University',
            'country':'Kazakhstan','author':{'orcid':None,'research_areas':['Databases']},
            'reviewer':{'years_experience':4,'expertise':['Databases']}})
        user_id=u['user_id']
        request('GET',f'/users/{user_id}',200)
        request('PATCH',f'/users/{user_id}',200,json={'phone_number':'+77770000000'})

        print('\n[Session CRUD]')
        s=request('POST','/sessions',201,json={'conference_id':101,'title':'Part 3 Demonstration Session',
             'session_date':'2027-04-11','start_time':'15:00:00','end_time':'16:00:00',
             'room_label':'D-100','chair_id':4})
        session_id=s['session_id']
        request('GET',f'/sessions/{session_id}',200)
        request('PATCH',f'/sessions/{session_id}',200,json={'room_label':'D-200'})

        print('\n[Paper CRUD, author/keyword workflows, nested version CRUD]')
        p=request('POST','/papers',201,json={
             'track_id':1002,'title':'Part 3 Demonstration Paper',
             'abstract':'An example database paper created through FastAPI.',
             'submission_date':'2027-01-15','status':'accepted','session_id':session_id,
             'authors':[{'author_id':user_id,'author_position':1,'is_corresponding':True},
                        {'author_id':2,'author_position':2,'is_corresponding':False}],
             'keywords':['Databases','API'],
             'versions':[{'version_no':1,'file_location':'papers/demo/v1.pdf',
                         'uploaded_at':'2027-01-15T11:00:00+00:00','change_note':'Initial'}]})
        paper_id=p['paper_id']
        request('GET',f'/papers/{paper_id}',200)
        request('PATCH',f'/papers/{paper_id}',200,json={'title':'Revised Demonstration Paper',
               'keywords':['Databases','Transactions']})
        request('POST',f'/papers/{paper_id}/versions',201,json={'version_no':3,
                'file_location':'papers/demo/v3.pdf',
                'uploaded_at':'2027-01-17T11:00:00+00:00','change_note':'Improved paper'})
        request('PATCH',f'/papers/{paper_id}/versions/3',200,json={'change_note':'Final revision'})
        request('GET',f'/papers/{paper_id}/versions',200)
        request('DELETE',f'/papers/{paper_id}/versions/1',200)

        print('\n[Required invalid session assignment rejection]')
        request('PATCH',f'/papers/{paper_id}',422,json={'session_id':504})
        request('PATCH',f'/papers/{paper_id}',422,json={'status':'rejected'})
        request('PATCH',f'/sessions/{session_id}',422,json={'conference_id':102,'chair_id':7})

        print('\n[Reviews CRUD, self-review rejection, author-change rejection]')
        request('POST','/reviews',422,json={
            'paper_id':paper_id,'reviewer_id':user_id,'overall_score':5,
            'recommendation':'accept','comments_for_authors':'Illegal self review',
            'review_submission_date':'2027-02-18'})
        r=request('POST','/reviews',201,json={
            'paper_id':paper_id,'reviewer_id':4,'overall_score':4,
            'recommendation':'accept','comments_for_authors':'Good example',
            'review_submission_date':'2027-02-18'})
        review_id=r['review_id']
        request('GET',f'/reviews/{review_id}',200)
        request('PATCH',f'/reviews/{review_id}',200,json={'overall_score':5})
        request('PATCH',f'/papers/{paper_id}',422,json={'authors':[
           {'author_id':user_id,'author_position':1,'is_corresponding':True},
           {'author_id':4,'author_position':2,'is_corresponding':False}]})
        print('\nALL PART 3 HTTP DEMONSTRATIONS PASSED')
    finally:
        print('\n[Cleanup: delete created review, paper, session, user]')
        # Each deletion is independent; deleting the paper cascades its children.
        for endpoint,identifier in (('/reviews',review_id),('/papers',paper_id),
                                    ('/sessions',session_id),('/users',user_id)):
            if identifier is not None:
                resp=client.delete(f'{endpoint}/{identifier}')
                print(' DELETE',f'{endpoint}/{identifier}',resp.status_code)
                if resp.status_code not in (200,404):
                    print('Cleanup warning:',resp.text[:300])


if __name__=='__main__':
    try:
        main()
    finally:
        client.close()
