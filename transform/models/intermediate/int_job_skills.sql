-- Bridge table: which skills each posting asks for (regex dictionary in seeds/skills.csv).
-- Case-insensitive unless the seed says otherwise ("Go" the language vs. "go" the verb).
select
    j.job_id,
    s.skill,
    s.category
from {{ ref('int_jobs') }} j
join {{ ref('skills') }} s
    on regexp_matches(
        j.title || ' ' || coalesce(j.tags, '') || ' ' || coalesce(j.description, ''),
        case when s.case_sensitive then s.pattern else '(?i)' || s.pattern end
    )
