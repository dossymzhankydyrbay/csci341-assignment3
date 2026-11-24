# Schema dictionary, foreign keys, delete actions, and decisions

Source: Assignment 3, Appendix A. Table / column identifiers are lowercase snake_case equivalents of the appendix. Every non-optional foreign key is `NOT NULL`.

| Relation | Primary key | Foreign keys / delete actions | Unique or checks of note |
|---|---|---|---|
| `app_user` | `user_id` | – | `email UNIQUE NOT NULL`; nonblank names |
| `author` | `author_id` | `author_id -> app_user.user_id` CASCADE | `orcid` unique optional |
| `author_research_area` | `(author_id,area_label)` | `author_id -> author.author_id` CASCADE | nonblank label |
| `reviewer` | `reviewer_id` | `reviewer_id -> app_user.user_id` CASCADE | `years_experience >= 0` |
| `reviewer_expertise` | `(reviewer_id,area_label)` | `reviewer_id -> reviewer.reviewer_id` CASCADE | nonblank label |
| `conference` | `conference_id` | – | `end_date >= start_date`; all required attributes NOT NULL |
| `conference_host` | `(conference_id,host_name)` | `conference_id -> conference.conference_id` CASCADE | nonblank host name |
| `conference_reviewer` | `(conference_id,reviewer_id)` | conference CASCADE; reviewer RESTRICT | one reviewer per conference-pool pair |
| `track` | `track_id` | `conference_id -> conference.conference_id` RESTRICT; `coordinator_id -> reviewer.reviewer_id` RESTRICT | `(conference_id,name)` unique |
| `conference_session` | `session_id` | conference RESTRICT; `chair_id -> reviewer.reviewer_id` RESTRICT | `end_time > start_time` |
| `paper` | `paper_id` | `track_id -> track.track_id` RESTRICT; `session_id -> conference_session.session_id` SET NULL | status constrained to specified 5 values |
| `paper_keyword` | `(paper_id,keyword)` | `paper_id -> paper.paper_id` CASCADE | nonblank keyword |
| `paper_author` | `(paper_id,author_id)` | paper CASCADE, author RESTRICT | `(paper_id,author_position)` unique; position positive; unique partial index for corresponding |
| `paper_version` | `(paper_id,version_no)` | paper CASCADE | version positive; optional change_note; version number need not be contiguous |
| `review` | `review_id` | paper CASCADE, reviewer RESTRICT | `(paper_id,reviewer_id)` unique; score 1–5; recommendation accept/reject; all completed fields required |

## Assumptions / design interpretation

1. **Author and reviewer are roles of APP_USER**, not separate people; author/reviewer IDs are identical to the matching user IDs (one-to-one subtype relations).
2. **No draft/incomplete review row**: every review requires non-NULL score, recommendation, comment for authors, submission date, and valid reviewer and paper references. `confidential_comments` is optional.
3. **At most one session per paper**, not one paper per session: the nullable session foreign key lives on `paper`. Several accepted papers can appear in one session (see paper 8 and 12).
4. **Accepted required for scheduling**: handled in application write services, alongside conference consistency; changing status, track, track conference or session conference is checked. Services reject invalid changes instead of auto-unassigning.
5. **Every paper exactly one corresponding author**: sample data fulfills this and the `replace_paper_authors` function enforces it. A partial unique index in PostgreSQL guarantees *at most one*; direct raw SQL creating a paper with zero authors is not prevented by triggers (not required by the assignment).
6. **Current version** is the row with highest `version_no` for a paper. Numbers may be skipped intentionally.
7. **Conference pool**: a reviewer's membership in the conference's reviewer pool is checked on review creation. Coordinator/chair membership in that conference pool is satisfied in seed and checked when changing the track/session conference through supplied service functions. Direct writes are not all guarded because these remaining rules are optional to enforce automatically.
8. **Delete actions**: paper children (authorship, keywords, versions, reviews) CASCADE; deleting a referenced author/reviewer is RESTRICT; deleting an assigned session sets paper session_id to NULL; deleting a conference cascades host/pool rows but is RESTRICTed by its tracks/sessions. Deleting a conference cannot indirectly delete independent user/reviewer records.
9. **Research areas, expertise, host institutions and keywords** are multivalued *attributes*, not additional independent domain entities. Their value columns and compound primary keys mirror the reference schema.
10. **Fictional conferences in 2027** make all session dates fall within conference dates; any city outside Astana takes the `+3 day` deadline branch. No actual paper files are uploaded, only paths are stored.
11. **No user authentication, deployed web frontend, or real file upload** is required for Parts 1–2; none is claimed to be implemented here.

## Data-dependent assertions exercised

The Python checker `seed_invariant_violations` verifies: user with no role, missing corresponding author, missing authors, missing version, missing keyword, hostless conference, self-review, invalid accepted/same-conference session, coordinator not in pool, chair not in pool, reviewer not in pool. Tests additionally force DB `UNIQUE`, `CHECK`, and foreign-key dependent deletes to fail or succeed in the expected way.

## Design differences from Assignment 1

The actual team's Assignment 1 conceptual model was not supplied. The implementation uses the professor's Appendix A reference model without changing its fifteen named relations; added indexes and an optional ORCID uniqueness constraint are ordinary implementation choices. If the prior A1 design differs materially, the group must document those changes here after comparing the two submissions.
