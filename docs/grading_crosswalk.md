# Parts 1, 2 and 3 — grading checklist / evidence map

**Source:** CSCI 341 Assignment 3, Fall 2026 (provided six-page specification). All three parts are implemented in source code (Parts 1 + 2: 60 marks; Part 3: 40 marks); deployment remains the user-controlled last step.

| Requirement | Where implemented | How to verify |
|---|---|---|
| PostgreSQL relations matching Appendix A | `sql/01_schema.sql` | Run `python -m assignment3.setup`, inspect 15 tables |
| Keys, references, NULL/unique/CHECK/positive/date/time constraints | `sql/01_schema.sql` | `test_database_enforces_core_constraints` |
| Normalize authors, keywords, expertise, research areas, hosts | Junction tables in `01_schema.sql` | `docs/schema_and_rules.md` |
| Enforce one completed review per reviewer/paper, paper-version key and cascading delete | `01_schema.sql` | `test_database_enforces_core_constraints`, `test_delete_4_1_cascades_every_dependent_type` |
| Prevent self-review on review insert AND changing authors | `assignment3/validation.py` | `test_application_checks_reject_each_invalid_change` |
| Session scheduling: accepted and same conference; relevant changes checked | `assignment3/validation.py` | `test_application_checks_reject_each_invalid_change` |
| Other Assignment 1 business rules hold in seed; enforcement extent stated | `02_seed.sql`, `validation.seed_invariant_violations`, README | `test_seed_and_all_required_edge_cases` |
| Minimum counts and unusual sample records including Amina/Arman | `sql/02_seed.sql` | `test_seed_and_all_required_edge_cases` |
| 1 – CREATE through Python | `assignment3/part2.py`, `db.py` | Full log, `TASK 1` |
| 2 – INSERT, row counts, reproducible reset | `assignment3/part2.py`, `db.py`, `setup.py` | Full log, `TASK 2` |
| 3.1 – Arman phone update by email | `queries.OPERATIONS['3.1']` | Before/after log, `test_update_3_1_by_email_and_3_2_both_branches` |
| 3.2 – ONE conditional UPDATE with +7/+3 days | `queries.OPERATIONS['3.2']` | Before/after log and both-city test |
| 4.1 – Delete Amina's withdrawn papers and their children | `queries.OPERATIONS['4.1']` | Before/after logs, cascade test (2 papers and 2 review children) |
| 4.2 – Delete all empty Astana sessions | `queries.OPERATIONS['4.2']` | Before/after logs, empty-session deletion test |
| 5.1 – Accepted papers with author, track, conference | `queries.OPERATIONS['5.1']` | `test_all_selects_and_aggregations` |
| 5.2 – Case-insensitive abstract phrase | `queries.OPERATIONS['5.2']` | `test_all_selects_and_aggregations` |
| 5.3 – Versions descending | `queries.OPERATIONS['5.3']` | `test_all_selects_and_aggregations` |
| 5.4 – Expert reviewer pool / experience / DISTINCT | `queries.OPERATIONS['5.4']` | `test_all_selects_and_aggregations` |
| 6.1 – Zero-paper tracks and distinct author counts | `queries.OPERATIONS['6.1']` | `test_all_selects_and_aggregations` |
| 6.2 – Zero-review reviewers and NULL average | `queries.OPERATIONS['6.2']` | `test_all_selects_and_aggregations` |
| 6.3 – Conference totals, accepted count, review-level averages, zero-paper case | `queries.OPERATIONS['6.3']` | `test_all_selects_and_aggregations` |
| 6.4 – Above-average reviewer counts incl. zero reviewers in population | `queries.OPERATIONS['6.4']` | `test_all_selects_and_aggregations` |
| 7 – Acceptance rate: accepted/(accepted+rejected) or NULL | `queries.OPERATIONS['7']` | `test_all_selects_and_aggregations` |
| 8 – Non-materialized `accepted_paper_schedule`, ordered output | `sql/03_view.sql`, `queries.OPERATIONS['8']` | `test_view_correct_order_and_exclusions` |
| SQL + result display and parameter logging | `assignment3/part2.py` | Full numbered output file |
| Independent mutation/retrieval/view baseline | `assignment3/part2.py` transactional rollback | Baseline row counts repeated at end |
| SQL reconstructable export incl. view | `sql/database_export.sql` | Restore via `psql -v ON_ERROR_STOP=1 -f ...` |

**Verification boundary:** The distributed evidence is an in-memory SQLite smoke-test transcript. A real PostgreSQL installation is required to generate production-grading results, not available in the file-creation environment. Run the README commands before claiming PostgreSQL execution. The separate Assignment 1 file also was not supplied.

## Part 3 — Web application requirements (40 marks)

| Requirement | Implementation / evidence |
|---|---|
| Framework and interactive admin UI | FastAPI `assignment3/web.py`; interactive Swagger `/docs` and HTML home `/` |
| Full users CRUD | `/users` POST/GET/PATCH/DELETE + tests in `tests/test_web.py` |
| Author/reviewer profiles via user workflow | Nested `author`/`reviewer`, ORCID, research areas, years of experience, expertise |
| Full papers CRUD | `/papers` POST/GET/PATCH/DELETE + linked authors/keywords + initial versions |
| Paper versions via paper workflow | `/papers/{paper_id}/versions` GET/POST/PATCH/DELETE; stores file locations only |
| Full reviews CRUD | `/reviews` POST/GET/PATCH/DELETE; calls `create_review` validations on create and update |
| Full sessions CRUD | `/sessions` POST/GET/PATCH/DELETE; chair membership and conference consistency |
| Self-review prevention + author-change guard | `create_review`, `replace_paper_authors`; invalid POST/PATCH returns 422; HTTP tests + live demo |
| Accepted/same-conference session assignment | `ensure_valid_assignment` and existing helper; status, track and session conference changes guard; invalid PATCH 422 |
| DB constraints and rollback | PostgreSQL `sql/01_schema.sql` plus `with c.begin()` per mutation; IntegrityError 409, failed requests roll back |
| Read-only supporting data | `/catalog` (conferences, tracks, hosts, reviewer pools and labels), `/schedule` real view |
| Persistent PostgreSQL | `compose.yaml` named Docker volume; Render database referenced by `render.yaml` |
| Externally accessible deployed URL | **Not yet fulfilled**: requires user's hosting account and live deployment; update `links.txt` |
| Demo recording and links | `scripts/demo_part3.py`, `docs/part3_walkthrough.md`; team must record/upload video and fill links |

**Part 3 test boundary:** Ten FastAPI HTTP tests pass using a SQLite test-only database, and a separate localhost HTTP demonstration completes with successful CRUD and expected 422 rejections. PostgreSQL deployment and public URL have not been verified. No marks are guaranteed.
