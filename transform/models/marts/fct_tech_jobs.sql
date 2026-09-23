-- Tech postings that name at least two known skills: the population every mart analyzes.
with skill_counts as (
    select job_id, count(*) as n_skills, list(skill order by skill) as skills
    from {{ ref('int_job_skills') }}
    group by job_id
)

select
    j.job_id, j.source, j.title, j.company, j.level, j.location, j.open_to_mexico,
    j.salary_min_usd, j.salary_max_usd,
    (j.salary_min_usd + j.salary_max_usd) / 2 as salary_mid_usd,
    s.n_skills, s.skills, j.published_on, j.url
from {{ ref('int_jobs') }} j
join skill_counts s using (job_id)
where j.is_tech_title and s.n_skills >= 2
