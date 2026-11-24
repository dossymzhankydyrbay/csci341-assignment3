# FINAL SUBMISSION CHECKLIST — CSCI 341 Assignment 3 (Fall 2026)

**Deadline: Friday, November 27, 2026.** Assignment total: 100 marks (Part 1: 20; Part 2: 40; Part 3: 40).

**Current state:** Part 1–3 source code is present and **20/20 offline tests pass**. Live PostgreSQL demonstration, external deployment, Google Drive video, and actual team details were **not** performed or supplied when this ZIP was produced. This ZIP is a consolidated **working package**, not yet a confirmed final Moodle submission.

> Work inside the folder containing `compose.yaml`, `README.md` and `requirements.txt`. **Do not run `--reset` after entering data you want to keep.** It drops and recreates the project's tables.

## 1. Run the bundled project locally with actual PostgreSQL

### macOS (Docker Desktop)

```bash
open -a Docker
# Wait until Docker Desktop is ready. Verify the SERVER section is available:
docker info
docker compose up --build -d --wait
docker compose ps
curl -f http://localhost:8000/health
curl -f http://localhost:8000/stats
```

Open `http://localhost:8000/docs` and try a few endpoints manually. If `docker info` shows a Docker daemon socket error, Docker Desktop is not running yet. If port 8000 is occupied, release that port or change the host port mapping in `compose.yaml`.

**Windows/Linux:** start Docker Desktop or Docker Engine normally, then run the same `docker compose` commands (omit `open -a Docker`).

**Critical:** `docker compose down` stops containers while preserving the named PostgreSQL data volume; **`docker compose down -v` deletes the persistent database volume**.

## 2. Produce REAL PostgreSQL Part 2 results (not just the existing SQLite evidence)

Run this **before** making manual app edits. It resets the demo database and produces task-by-task SQL, bound parameters, result sets, and before/after updates/deletes. The changes are rolled back between independent tasks.

```bash
docker compose exec -T web python -m assignment3.part2 \
  --reset --output /tmp/part2_results_postgresql.txt
docker compose cp web:/tmp/part2_results_postgresql.txt \
  evidence/part2_results_postgresql.txt
```

Check the file contains `TASK 1`, `TASK 2`, `TASK 3.1`–`8`, before/after results, and the final `ALL PART 1-2 DEMONSTRATIONS FINISHED WITHOUT ASSERTION ERRORS.` message.

Generate a native PostgreSQL dump **after** the reset, from the seeded database:

```bash
docker compose exec -T postgres pg_dump -U csci341 -d csci341_a3 \
  --no-owner --no-privileges --inserts --clean --if-exists \
  > sql/postgres_dump.sql
```

The existing `sql/database_export.sql` already reconstructs the PostgreSQL tables, seed and view. The native `pg_dump` is additional evidence and is recommended. If your computer does not support these Docker commands, use the non-Docker PostgreSQL instructions in `README.md` and run `python -m assignment3.part2 --reset --output evidence/part2_results_postgresql.txt` directly.

## 3. Test the live local application with full CRUD and both required rejections

If dependencies are not already installed in your host's Python environment:

```bash
python -m pip install -r requirements.txt
```

Now run:

```bash
python -m pytest -v tests/
python scripts/demo_part3.py http://localhost:8000
```

The demo script creates, reads, updates, and deletes user/profile, paper/author/keyword/version, review and session records, and expects **HTTP 422** for a self-review and an invalid session assignment. Open `/docs`, `/catalog`, `/schedule` to inspect actual responses.

**Persistence test:** manually create a temporary user with `POST /users` in Swagger, note the returned ID, run `docker compose restart web`, then retrieve that ID with `GET /users/{id}`. It should still exist. Delete the test user afterwards.

## 4. Deploy publicly using the provided Render blueprint

1. Push the **contents of this project folder** to a GitHub repository, with `render.yaml` at repository root. Do not push `.env`, passwords or local test data.
2. In [Render Dashboard](https://dashboard.render.com/), choose **New > Blueprint**, connect the repository, and deploy the web service and PostgreSQL database specified in `render.yaml`.
3. Get the **real** web-service URL that Render assigns. Visit `https://YOUR-REAL-HOST/docs`, `/health`, `/schedule`, and `/stats` in a normal browser and in a private/incognito window.
4. Run `python scripts/demo_part3.py https://YOUR-REAL-HOST` from your laptop. Check that HTTP CRUD succeeds and both invalid actions return 422. Demonstrate persistence by making a temporary change, restarting/redeploying the web service and confirming the change is still present.
5. Fill `links.txt` with that actual HTTPS URL. Keep the database and web service operational through grading. As of November 2026, Render documents that its **free PostgreSQL databases expire 30 days after creation**. Free web services may also spin down after inactivity.

**Never** use `http://localhost:8000` as the submission application link. The instructor must reach the deployed app from a different computer.

## 5. Final documents and demonstration video

- [ ] Fill `executive_summary_TEMPLATE.md`, save as **`executive_summary.md`**. Include **only actual members**, student IDs, contribution breakdown, completed work and any known incomplete requirements. Confirm it prints on **one page**.
- [ ] Reconcile the relational schema with **your own Assignment 1 model**; document any material changes in `README.md` or `docs/schema_and_rules.md`.
- [ ] Record a short presentation, ideally **10 minutes or less**, in this order: (1) PostgreSQL creation/seed, (2) numbered SQL queries and results, (3) live deployed app and CRUD + both rejection examples. See `docs/part3_walkthrough.md` for a timed outline.
- [ ] Upload the video to **Google Drive** and use a link that the instructor and TAs can open without requesting access. **Do not put the video itself in Moodle or the ZIP.**
- [ ] Replace **both URL placeholders** in `links.txt`, leave the truthful line that no demo credentials are needed if no authentication is used.
- [ ] Confirm team registration was submitted by the November 15 deadline (if not, contact the instructor promptly).

## 6. Run the built-in preflight checker

```bash
python scripts/verify_submission.py
```

It checks all required project files, ZIP export sections, local tests, placeholders, summary and evidence. To additionally connect to PostgreSQL, set the relevant `DATABASE_URL` (see `README.md`) and run:

```bash
python scripts/verify_submission.py --database \
  --url https://YOUR-REAL-HOST
```

You can use `--database` with an actual reachable PostgreSQL server, not SQLite. **Neither this checker nor the 20 offline tests guarantees a grade**. The video permission, one-page summary, Grade/Moodle links and grading-time uptime all need manual checks.

## 7. Make ONE Moodle ZIP and test it

After replacing the placeholder files and adding your PostgreSQL evidence, make a **new** ZIP containing the project files. Name it exactly as the assignment requests: `Assignment-3_Lastname1_Lastname2_Lastname3.zip` using only actual group members (for a solo submission use your own surname).

### macOS / Linux (run from the project root)

```bash
zip -r ../Assignment-3_Lastname1_Lastname2_Lastname3.zip \
  . -x '*.DS_Store' '*/__pycache__/*' '*.pyc' '.venv/*' '.git/*' '.env'
unzip -t ../Assignment-3_Lastname1_Lastname2_Lastname3.zip
```

**Inspect the archive contents** and make sure it includes `sql/database_export.sql` (and preferably `sql/postgres_dump.sql`), all Python/app code, `requirements.txt`, `README.md`, `executive_summary.md`, `links.txt`, `render.yaml`, and the PostgreSQL Part 2 results file. It should **not** include `.venv`, secret `.env`, or video files.

**Final acceptance check:** extract that *final submission ZIP* into a fresh directory and reproduce the setup or at least the 20 tests from the extracted copy; open the application/video links in incognito; then upload **one ZIP per group** to Moodle.

## Required grading coverage to demonstrate

| Part | Demonstration | Points |
|---|---|---:|
| 1 | 15 relations, constraints, sample data and both app checks | 20 |
| 2 | CREATE + INSERT, 2 UPDATE, 2 DELETE, 4 simple SELECT, 4 aggregate SELECT, acceptance rate, schedule view, numbered SQL and results; reset/rollback | 40 |
| 3 | Full users/papers/reviews/sessions CRUD including child records, valid/invalid actions, persistent PostgreSQL, externally accessible deployed URL | 40 |

**Source of truth:** the six-page instructor assignment PDF and this project's `README.md` / `docs/grading_crosswalk.md`.

**Docker network note:** The supplied Compose setup does not publish PostgreSQL port 5432 to your laptop. Therefore, `python scripts/verify_submission.py --database` on the host will only work with a *different externally reachable PostgreSQL connection*, or if you intentionally configure a host-accessible port. The recommended `docker compose exec -T web python -m assignment3.part2 --reset ...` command already tests real PostgreSQL **inside** Docker. When its successful results are copied to `evidence/part2_results_postgresql.txt`, the basic preflight checker recognizes that evidence file; it does not independently certify its provenance.
