-- Part 2, Task 8. A real query view (not a materialized table).
CREATE OR REPLACE VIEW accepted_paper_schedule AS
SELECT p.paper_id,
       p.title AS paper_title,
       c.conference_id,
       c.acronym AS conference_acronym,
       t.name AS track_name,
       s.session_id,
       s.title AS session_title,
       s.session_date,
       s.start_time,
       s.end_time,
       s.room_label,
       chair.given_name || ' ' || chair.surname AS chair_full_name,
       corresponding_user.given_name || ' ' || corresponding_user.surname AS corresponding_author_full_name,
       corresponding_user.email AS corresponding_author_email
FROM paper AS p
JOIN track AS t ON t.track_id = p.track_id
JOIN conference AS c ON c.conference_id = t.conference_id
JOIN conference_session AS s ON s.session_id = p.session_id
    AND s.conference_id = c.conference_id
JOIN app_user AS chair ON chair.user_id = s.chair_id
JOIN paper_author AS pa ON pa.paper_id = p.paper_id AND pa.is_corresponding = TRUE
JOIN app_user AS corresponding_user ON corresponding_user.user_id = pa.author_id
WHERE p.status = 'accepted' AND p.session_id IS NOT NULL;
