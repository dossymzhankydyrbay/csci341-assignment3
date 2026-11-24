# CSCI 341 — Assignment 3: Executive Summary

**Team members:** [Member 1 full name — student ID], [Member 2 full name — student ID], [Member 3 full name — student ID] (list only actual members)

**Project:** Research Conference and Paper Review Management System (Fall 2026)

**Contribution breakdown:** [Member 1: ...] · [Member 2: ...] · [Member 3: ...]. Each student should be able to explain the entire implementation.

**Part 1 — Database (20 marks):** Designed 15 normalized relational tables for PostgreSQL, with explicit keys, foreign keys, uniqueness, CHECK constraints, deletion actions and sample data. The sample includes 15 users, 14 papers, 19 versions, 26 completed reviews and three conferences with the required edge cases.

**Part 2 — SQL operations (40 marks):** Implemented all eight numbered task categories using Python, SQLAlchemy and database-side SQL, including conditional updates, cascading deletions, simple and aggregate queries, acceptance rates and the `accepted_paper_schedule` view. Mutation demonstrations display before/after data and are rolled back to the seed.

**Part 3 — Web application (40 marks):** Implemented a FastAPI web application with an interactive Swagger admin interface, full CRUD for users, papers, reviews and sessions, including user roles/profiles and paper authorship/keywords/versions. Transactions and required rule checks reject self-reviews and invalid session assignments. Provides Docker Compose, Render deployment configuration and an HTTP demonstration script.

**Testing:** Twenty local automated tests and an additional local HTTP demo succeeded using a SQLite test environment. [Add actual PostgreSQL and deployed-service test results after executing them.]

**Deployed application:** [INSERT ACTUAL PUBLIC URL]  
**Video demonstration:** [INSERT ACCESSIBLE GOOGLE DRIVE LINK]

**Incomplete/nonworking requirements:** [After final verification, state truthfully which requirements, if any, remain incomplete. Remove this instruction before submitting. As supplied, live public deployment and video recording are NOT complete.]

<!-- Keep the final executive summary to at most one printed page. -->
