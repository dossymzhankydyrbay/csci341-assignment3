# CSCI 341 — Assignment 3 (Fall 2026): Parts 1, 2 and 3

**Research Conference and Paper Review Management System**

**Start here before final submission:** see [`FINAL_SUBMISSION_CHECKLIST.md`](FINAL_SUBMISSION_CHECKLIST.md) for the complete local PostgreSQL → SQL results → HTTP tests → public deployment → video → Moodle ZIP workflow. Run `python scripts/verify_submission.py` for a non-destructive audit of remaining work. This source bundle is **not** represented as a fully submitted, hosted application.

This package implements **Part 1 (PostgreSQL relational schema and seed), Part 2 (numbered SQL demonstrations through Python/SQLAlchemy), and Part 3 (FastAPI CRUD web application)**. It includes local Docker Compose configuration, a Render hosting Blueprint, HTTP demonstration scripts, tests, and submission-document templates. **It has not been deployed to an external host:** the live public URL, demonstration video, and actual team member details must be provided by the submitting team.

> **Important for evaluators:** Appendix A of the provided Assignment 3 PDF is the basis for the relational schema. The separate Assignment 1 design was not provided; document and reconcile any differences from your team's A1 design before final submission. Do not claim a public deployment until you have checked its live URL.

## Technology / environment

- Python 3.10 or newer (tested offline with Python 3.13)
- SQLAlchemy 2.x and bound parameters via `sqlalchemy.text()`
- **PostgreSQL 14+ is the target DBMS** (SQLite is used **only** by optional offline automated tests)
- PostgreSQL Python adapter: `psycopg2-binary` 2.9+
- FastAPI 0.110+, Pydantic 2.x, Uvicorn, httpx
- `pytest` 8+
- OS: Windows, Linux, or macOS with PostgreSQL and Python installed

## Quick start (PostgreSQL)

**1.** Create an EMPTY database in PostgreSQL. For example, using `psql`:

```bash
psql -U postgres -c 'CREATE DATABASE csci341_a3;'
```

**2.** Open a terminal in this project directory and install Python dependencies:

```bash
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**3.** Configure your local database connection. Replace `YOUR_PASSWORD` with a real password; this is NOT a provided login or password. Examples:

```bash
# macOS / Linux
export DATABASE_URL='postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/csci341_a3'

# Windows PowerShell
$env:DATABASE_URL='postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/csci341_a3'
```

If your PostgreSQL user is not `postgres`, substitute the actual user. Passwords with special URI characters must be percent-encoded. No real passwords should be committed to the ZIP or video.

**4.** For a **complete restoration** of all 15 tables, sample data, and the view:

```bash
python -m assignment3.setup
```

**5.** For **graded Part 2 evidence**, execute all required numbered operations, each against the original data. `--reset` recreates and populates the database at the start. This command also writes the full displayed SQL, bound parameter values, table counts, before/after mutation results, query results, and view results:

```bash
python -m assignment3.part2 --reset --output evidence/part2_results.txt
```

The first use of `--reset` **deletes existing project data** in these tables. Do not run against any production/shared database. The four mutation tasks run inside individual transactions which are always rolled back; Tasks 5–8 therefore use the original sample data.

**6.** Run optional automated tests:

```bash
python -m pytest -v tests/
```

These tests use in-memory SQLite to test DB constraints, application checks, expected row-level results, all 14 task operations, and rollback. They do **not** replace a PostgreSQL end-to-end grading run. Record the `part2_results.txt` produced against real PostgreSQL before submission.

## Part 3: FastAPI web app (40 points — implemented, public hosting pending)

**Fastest local start with persistent PostgreSQL:** From the project root, install Docker Desktop (or Docker Engine with Compose) and run:

```bash
docker compose up --build
```

Wait for the PostgreSQL health check and app startup. Visit **http://localhost:8000/docs** for the actual interactive CRUD interface ("Try it out" request forms) or **http://localhost:8000/** for the dashboard. The app seeds **only if `app_user` does not exist** (`AUTO_SETUP=true`); it never resets existing tables on a restart. The database lives in the named Docker volume `csci341_pgdata`. Do **not** use `docker compose down -v` unless you intentionally want to delete local database records. The Docker Compose password is an **example for local development only**, not production.

**Without Docker:** Use steps 1–4 above to install dependencies and create/seed PostgreSQL; then start:

```bash
python -m uvicorn assignment3.web:app --host 0.0.0.0 --port 8000
```

`DATABASE_URL` must be set first. `AUTO_SETUP` defaults to `false`, so the app assumes tables already exist; if setting `AUTO_SETUP=true`, it initializes a **missing** schema only, and leaves an existing one untouched. On Windows, use `scripts/run_app.ps1`; on macOS/Linux use `scripts/run_app.sh`.

### Supported web workflows

| Resource | Full CRUD | Required related features |
|---|---|---|
| `GET/POST/PATCH/DELETE /users` | Yes | Author and reviewer roles, ORCID, experience, research areas and expertise |
| `GET/POST/PATCH/DELETE /papers` | Yes | Track, status, scheduling, author positions + exactly one corresponding author, keyword replacement, initial paper versions |
| `GET/POST/PATCH/DELETE /papers/{paper_id}/versions` | Yes | File-location metadata only, positive version numbering, current highest version; actual file upload is not needed |
| `GET/POST/PATCH/DELETE /reviews` | Yes | Completed review data, bound fields, pool membership, no self-reviews, max one review/reviewer/paper |
| `GET/POST/PATCH/DELETE /sessions` | Yes | Chair in reviewer pool, time validation, no cross-conference scheduled papers, deletion unassigns papers |
| `GET /catalog`, `/schedule`, `/stats`, `/health` | Read-only | Seeded conferences/tracks/hosts/reviewer pools, real schedule view, table counts, DB health |

- The **two mandatory application checks** are executed before commits: a reviewer must not author the paper (including updates to paper authors), and a paper may be scheduled only if accepted and belonging to the same conference as the session. Relevant changes to paper status/track and session conference are checked. Invalid operations receive **422** responses and are rolled back.
- Database duplicate/FK/CHECK violations are rejected with **409** responses. All related writes are inside SQLAlchemy transactions. Missing records return **404**. Validation errors return **422**.
- The UI is **Swagger interactive API documentation** at `/docs`, which the assignment explicitly accepts as a suitable interface. There is no authentication and no PDF upload endpoint, both intentionally omitted under the assignment instructions.
- The schema uses integer keys specified by Appendix A; the API allocates new integers using `MAX(id)+1`, acceptable for the single-user assignment demo. It is not intended for concurrent multi-writer production use.
- Supporting conferences, tracks, reviewer pools, hosts and research/expertise lookup labels are seed-populated and **read only** as permitted. One-page HTML index is informational; CRUD is through `/docs`.

### Verify and demonstrate Part 3

```bash
python -m pytest -v tests/                        # 20 automated tests total
python scripts/demo_part3.py http://localhost:8000 # full live HTTP CRUD demo
```

The HTTP demo creates a temporary user (with both profiles), session, paper (with authors/keywords/versions), and review; demonstrates reading and updating each, checks invalid self-review and invalid scheduling responses, then deletes the temporary rows. It **does not reset** the seed. The script is documented in `docs/part3_walkthrough.md` and a local offline run is in `evidence/offline_part3_http_demo.txt`.

### Public deployment: Render example

1. Put **this project root** in a Git repository (e.g., GitHub); `render.yaml` must stay at repository root. Do not commit `.env`.
2. In the Render dashboard choose **New → Blueprint**, connect the repository, inspect the two resources (`csci341-conference-review-manager` web service and `csci341-conference-db` PostgreSQL database), then deploy.
3. The `render.yaml` config wires the Render PostgreSQL connection string to `DATABASE_URL`, sets `AUTO_SETUP=true`, runs FastAPI on `$PORT` and checks `/health`. After the first creation, new startup instances **do not reset data**.
4. Confirm the actual public address Render assigns you: `https://YOUR-SERVICE.onrender.com/docs` (replace the placeholder with the real address); test CRUD and run `python scripts/demo_part3.py https://YOUR-SERVICE.onrender.com`.
5. Put the real link in `links.txt`, then record an accessible Google Drive video and place that URL in `links.txt` too. Use `docs/part3_walkthrough.md` for the video sequence.

**Hosting note:** Render's free PostgreSQL database currently expires after **30 days**; create it near grading or choose an appropriately persistent provider/plan. Free web services may sleep when idle. Hosting requires your own Render/Git account; none has been used in this package. Always check availability during grading.

## Plain SQL database export (schema + seed data + view)

- **`sql/database_export.sql`**: complete reproducible plain PostgreSQL script (tables, keys, constraints, indexes, deterministic inserts and the database view). This is the equivalent SQL reconstruction export included with Parts 1–2.
- `sql/01_schema.sql`: all 15 table creation statements, foreign keys, CHECKs, unique constraints and relevant delete actions.
- `sql/02_seed.sql`: all fictional sample rows, deliberately chosen for the assignment queries.
- `sql/03_view.sql`: `accepted_paper_schedule` definition.

Restore directly using `psql` if preferred:

```bash
psql -U postgres -d csci341_a3 -v ON_ERROR_STOP=1 -f sql/database_export.sql
```

The file is built from the same three scripts executed by Python; it drops and recreates the **project's** tables, so use only on a designated assignment database. To generate an additional database-native pg_dump export **after** creating the database, run:

```bash
pg_dump -U postgres -d csci341_a3 --no-owner --no-privileges --inserts --clean --if-exists > sql/postgres_dump.sql
```

If instructors specifically require pg_dump format, include that newly generated file in your final ZIP. The provided portable recreation script is a plain SQL export equivalent for rebuilding the seeded schema.

## Part 1: relational design and constraints

The 15 base relations correspond to Appendix A. All multivalued fields are in junction/attribute relations rather than comma-separated lists. Primary and foreign keys and deletion policies are itemized in `docs/schema_and_rules.md`.

### Mandatory constraints implemented in the database

- Keys and references for users, authors, reviewers, conferences, hosts, pools, tracks, sessions, papers, paper authors, keywords, versions, and reviews.
- Non-null required fields, unique emails, unique author positions within a paper, and one completed review maximum per `(paper_id, reviewer_id)`.
- CHECK paper status (`submitted`, `under review`, `accepted`, `rejected`, `withdrawn`), score `1..5`, recommendation (`accept`, `reject`), positive author position and version, nonnegative reviewing experience, conference end >= start, session end > start.
- Versions have composite key `(paper_id, version_no)`: gaps are allowed; **MAX(version_no)** is the current version. All versions use file locations, **not** uploaded PDF data.
- `paper.session_id` is nullable and scalar: any paper is in **at most one session**.
- `ON DELETE CASCADE` from `paper` to `paper_version`, `paper_keyword`, `paper_author`, and `review` makes Task 4.1 a single transactional DELETE. Foreign key constraints are never disabled.
- A PostgreSQL partial unique index prevents **more than one** corresponding author per paper.

### Required application checks implemented

`assignment3/validation.py` contains callable, transactional write services:

- `create_review`: reject reviewers who authored the selected paper (and enforce reviewer role/pool membership).
- `replace_paper_authors`: reject author changes that would cause any existing review to become a self-review; maintain one corresponding author.
- `assign_paper_session`: accept scheduling only when the paper is accepted and its track conference matches the session conference.
- `change_paper_status`, `change_paper_track`, `change_session_conference`, `change_track_conference`: reject modifications that would invalidate an existing assignment. Part 3 calls these checks or equivalent checks inside transactional HTTP workflows. Direct raw SQL updates can bypass application checks, as permitted by the assignment.

The runner demonstrates that both required invalid-operation categories are rejected. `tests/test_assignment.py` tests additional invalid modifications. Call these functions in a single `with engine.begin() as connection:` block so exception handling rolls back every related change.

### Other Assignment 1 business rules

- **Verified in the seed:** every user has an author and/or reviewer role; every paper has authors, exactly one corresponding author, keywords and versions; every conference has a host; each coordinator/chair belongs to its own conference's reviewer pool; all reviewers who submit reviews belong to their conference's pool.
- **Enforced by the supplied application write services:** exactly one corresponding author when replacing authors, reviewer pool membership when creating a review, and pool membership when changing a track/session conference.
- **Not universally enforced by SQL triggers:** every newly inserted user having a role; every new paper having all its child records and exactly one corresponding author; every newly inserted conference having at least one host; coordinator/chair pool membership on arbitrary direct SQL inserts or other edits. These optional multirow business rules are enforced in the Part 3 user and paper creation/update workflows where applicable, but not through arbitrary direct SQL changes. **They also hold in the supplied seed.**

## Sample data / grading edge cases

| Requirement | Sample rows / records |
|---|---|
| >= 10 users / papers / versions / completed reviews | **15** users, **14** papers, **19** versions, **26** completed reviews |
| At least two conferences | **3**: 101 (Astana), 102 (Berlin), 103 (Astana with no papers) |
| Author-only, reviewer-only, dual-role users | Amina = author only; Arman = reviewer only; Timur = both |
| All five paper statuses | `paper.status` across the 14 paper records |
| Multiple authors and versions | Paper 1 has 2 authors and versions 1, 3, 5; paper 2 has 2 versions |
| Empty track / empty conference | Tracks 1003 and 3001; Conference 103 has no papers |
| Reviewer without reviews | Reviewer 13 (Asel Yermek) |
| Accepted with / without a session | Paper 1 is scheduled; paper 7 and paper 10 are unscheduled |
| Amina's withdrawn corresponding-author papers | Paper IDs **2 and 3** (review and author children are present and cascade on deletion) |
| Arman phone UPDATE | `arman.armanov@example.com`, original phone not equal to target |
| Empty Astana sessions | Session IDs **502, 503, 505**; nonempty Astana session 501 remains |
| Both UPDATE branches | Conference cities Astana and Berlin; all three deadline rows change |
| Case-insensitive machine learning abstract query | Papers **1 and 8** (different casing) |
| Conference 101 Databases reviewers with >= 3 years | Reviewer IDs **1, 4, 5, 9, 10** |
| Aggregates / NULL handling | Empty track, no-paper conference, no-review reviewer, varied review counts |

## Part 2 task-to-file map

| Task | Location / result |
|---|---|
| 1 – CREATE | `sql/01_schema.sql`; invoked by `assignment3.part2` |
| 2 – INSERT and row counts | `sql/02_seed.sql`; `assignment3.db.table_counts` |
| 3.1 / 3.2 – UPDATE | `assignment3/queries.py` (`OPERATIONS`), executed in `part2.py` with before/after + rollback |
| 4.1 / 4.2 – DELETE | Same; cascades / no-paper sessions shown with before/after + rollback |
| 5.1–5.4 – simple SELECT | `assignment3/queries.py` |
| 6.1–6.4 – aggregate / nested SELECT | `assignment3/queries.py`, database-side counting and averaging |
| 7 – derived acceptance rate | `assignment3/queries.py` |
| 8 – CREATE VIEW + ordered SELECT | `sql/03_view.sql` + `assignment3/queries.py` |

Queries use SQLAlchemy `text()` with bound values rather than concatenating inputs into SQL. All joins, case-insensitive filters, grouping, DISTINCT counts, and weighted averages execute **in the database**, not Python.

### Query parameter values

| Task | Input value(s) |
|---|---|
| 3.1 | `email='arman.armanov@example.com'`, `phone_number='+77773414141'` |
| 3.2 | `target_city='Astana'` |
| 4.1 | `status='withdrawn'`, `email='amina.aminova@example.com'` |
| 4.2 | `city='Astana'` |
| 5.1 | `status='accepted'` |
| 5.2 | `phrase='machine learning'` |
| 5.3 | `paper_id=1` (shows versions 5, 3, 1) |
| 5.4 | `conference_id=101`, `expertise='Databases'`, `min_years=3` |
| 6–8 | no user-supplied parameters |

## Project tree (selected files)

```text
assignment3/db.py, setup.py, queries.py, part2.py, validation.py
assignment3/web.py, web_schemas.py       FastAPI application and request models
sql/01_schema.sql, 02_seed.sql, 03_view.sql, database_export.sql
scripts/run_app.sh, run_app.ps1           Launch web app locally
scripts/demo_part3.py                    External HTTP CRUD verification/demo
scripts/run_part2.sh, run_part2.ps1      Part 2 query demonstration
Dockerfile, compose.yaml                 Containerized app + persistent local Postgres
render.yaml                              Public web + PostgreSQL Blueprint
tests/test_assignment.py, test_web.py    20 automated offline tests
evidence/offline_smoke_test.txt          Part 2 SQLite-only demonstration
evidence/offline_part3_http_demo.txt     Part 3 HTTP using local SQLite test database
docs/schema_and_rules.md, grading_crosswalk.md, part3_walkthrough.md
executive_summary_TEMPLATE.md, links.txt  Must be personalized/finalized
```

## Required submission actions and verification boundary

1. The code for Parts 1, 2 and 3 is included, but **no public app deployment, public URL or accessible recording has been performed**. The user must deploy on a hosting account and record a demonstration video (ideally at most ten minutes). Fill in `links.txt` with actual working URLs and any credentials if you add them.
2. The **full 20-test suite passed** in the development environment using SQLite as an offline test engine. A local HTTP server also ran the Part 3 demo script successfully. PostgreSQL server, Docker build and external hosting runs were **not available for verification** here; run the provided PostgreSQL setup, query script and HTTP demo on the target service before claiming end-to-end PostgreSQL correctness.
3. The team's Assignment 1 EER/UML was not supplied, so the relational design follows Assignment 3 Appendix A and may need to be reconciled with original Assignment 1 design assumptions.
4. Complete `executive_summary_TEMPLATE.md` with actual team members, IDs and contributions, add the real video and app URLs to `links.txt`, ensure the team was registered, and rename the ZIP according to the assignment's `Assignment-3_Lastname1_Lastname2_Lastname3.zip` format before submitting to Moodle. **Do not submit placeholder links or the video file itself.**
5. `AUTO_SETUP=true` is for initializing a **missing** schema. Manual `python -m assignment3.setup` and Part 2's `--reset` mode deliberately wipe project tables: never use these against an active deployed DB that should preserve user changes.
