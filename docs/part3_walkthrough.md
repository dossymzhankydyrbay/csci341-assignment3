# Part 3: Run, demonstrate and deploy the web application

## 1. Start and open the actual interface

**Option A — easiest, real PostgreSQL:** From the directory containing `compose.yaml`:

```bash
docker compose up --build
```

- Wait until the web service prints that it is running and `postgres` is healthy.
- Open `http://localhost:8000/docs`. This **interactive API documentation** is the application's administrative interface and is expressly accepted in Part 3.
- Click an endpoint → **Try it out** → enter fields / JSON → **Execute**.
- The root dashboard is `http://localhost:8000/`; `/catalog` displays selection IDs, and `/schedule` displays the real schedule view.
- On first startup, the app creates the 15 PostgreSQL tables, seeds their records and creates the schedule view. Later restarts preserve data in the named PostgreSQL Docker volume.

**Option B — existing PostgreSQL installation:** Run `python -m assignment3.setup` **once** to restore the original sample data (destructive). Set `DATABASE_URL` using the README example, then:

```bash
python -m uvicorn assignment3.web:app --host 0.0.0.0 --port 8000
```

## 2. Quick live demonstration (automatically exercises real HTTP endpoints)

From a second terminal in the project root with the same Python dependencies installed:

```bash
python scripts/demo_part3.py http://localhost:8000
```

The script verifies all four CRUD categories, creates/updates/deletes nested paper versions, reads the schedule, and demonstrates the two mandatory invalid-operation checks. It creates a unique temporary user and leaves the original seed unchanged after cleanup. The expected invalid operations return HTTP 422; PostgreSQL integrity constraints return 409. A locally tested offline HTTP transcript is in `evidence/offline_part3_http_demo.txt` (not a PostgreSQL deployment transcript).

## 3. Suggested under-10-minute video plan

| Time | What to show on screen | Requirement addressed |
|---|---|---|
| 0:00–1:00 | `python -m assignment3.setup` with table counts, show PostgreSQL schema/seed and keys | Part 1, creation/seed |
| 1:00–4:30 | `python -m assignment3.part2 --output evidence/part2_results.txt`, show TASK 3.1–8 numbered SQL and key result tables, including rollbacks | Part 2 all queries |
| 4:30–5:00 | Public URL `/health`, `/stats`, `/docs`, `/catalog` | Deployed application with persistent PostgreSQL |
| 5:00–6:00 | `/users` CREATE, GET, PATCH, DELETE (dual role profiles) | User/profile CRUD |
| 6:00–7:00 | `/papers` CREATE, GET, PATCH, DELETE, including authors, keywords and `/versions` | Paper and children CRUD |
| 7:00–8:00 | `/reviews` CRUD and POST self-review with 422; PATCH paper authors to include existing reviewer → 422 | Review CRUD and self-review checks |
| 8:00–9:00 | `/sessions` CRUD, invalid scheduling POST/PATCH → 422, status or cross-conference assignment rejected | Sessions and assignment checks |
| 9:00–9:45 | Show `/schedule` view, persistent data after app restart, links in `links.txt` | View / persistence / access |

You can narrate the actions and show `scripts/demo_part3.py` instead of manually issuing every request. But show actual deployed website pages and the rejection payloads. Make it clear that the API is the administrative interface: appearance is not graded and Swagger is allowed.

## 4. Example manual requests in Swagger

User creation — POST `/users`:

```json
{
  "given_name": "Demo", "surname": "Participant", "email": "demo-unique@example.com",
  "affiliation": "Nazarbayev University", "country": "Kazakhstan",
  "author": {"orcid": null, "research_areas": ["Databases"]},
  "reviewer": {"years_experience": 5, "expertise": ["Databases"]}
}
```

Paper creation — POST `/papers` (use already-seeded authors 2 and 3):

```json
{
  "track_id": 1002, "title": "Example Research Paper", "abstract": "A sample study",
  "submission_date": "2027-01-10", "status": "accepted", "session_id": 503,
  "authors": [
    {"author_id": 2, "author_position": 1, "is_corresponding": true},
    {"author_id": 3, "author_position": 2, "is_corresponding": false}
  ],
  "keywords": ["Databases", "SQL"],
  "versions": [
    {"version_no": 1, "file_location": "papers/example/v1.pdf",
     "uploaded_at": "2027-01-10T10:00:00Z", "change_note": "First draft"}
  ]
}
```

Valid review — POST `/reviews` (use a paper/reviewer combination that has not yet been reviewed; the seed includes reviewers who have reviewed many existing papers):

```json
{
  "paper_id": 7, "reviewer_id": 4, "overall_score": 4,
  "recommendation": "accept", "comments_for_authors": "Clear contribution",
  "review_submission_date": "2027-02-25"
}
```

Rejected self-review — POST `/reviews` with `paper_id: 7, reviewer_id: 7` (reviewer 7 is an author of paper 7). Expect HTTP **422** with an explanatory error. For invalid scheduling, PATCH `/papers/7` with `{"session_id":504}` (paper is from conference 101, session 504 belongs to 102). Expect **422**. For invalid status of a scheduled paper, PATCH `/papers/1` with `{"status":"rejected"}` without clearing its session first. Expect **422**. All rejected requests leave the old data intact.

Other quick manual CRUD: session POST uses `{ "conference_id":101,"title":"New Session","session_date":"2027-04-11","start_time":"15:00:00","end_time":"16:00:00","room_label":"A500","chair_id":4 }`. Session PATCH can change title/room; review PATCH can change score/comments or review assignment; user PATCH can update profile fields; paper PATCH can replace authors and keywords. DELETE each created record after demonstration to restore the seed.

## 5. External deployment and final submission

- Use the included `render.yaml` as a one-click-ish Blueprint (requires your Git repository and Render account). It creates a public Python web service and a PostgreSQL service; the database URL is wired with a Render environment reference, not a literal password.
- Verify that `/docs`, `/health`, `/stats`, and all CRUD routes work at the **real public URL**. Run the demo script against that live URL. It must remain accessible during grading.
- Copy the actual app and Google Drive video links to `links.txt`. Set sharing so instructors/TAs can access them.
- Fill out the one-page `executive_summary_TEMPLATE.md`, rename for submission, and package the archive as `Assignment-3_Lastname1_Lastname2_Lastname3.zip` with only actual group members in its name.
- **Do not** include the video itself inside the ZIP and **do not** leave placeholder URLs in your submission.
- Render free PostgreSQL expires after 30 days (according to Render's current documentation), so ensure persistence through grading; do not use ephemeral SQLite or an unpersisted file-based database in production.
