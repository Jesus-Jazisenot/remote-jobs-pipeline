-- Which skills are asked for together (e.g. "Python + AWS"): tells you what to learn as a bundle.
select
    a.skill as skill_a,
    b.skill as skill_b,
    count(*) as n_jobs
from {{ ref('int_job_skills') }} a
join {{ ref('int_job_skills') }} b on a.job_id = b.job_id and a.skill < b.skill
where a.job_id in (select job_id from {{ ref('fct_tech_jobs') }})
group by 1, 2
having count(*) >= 5
order by n_jobs desc
limit 50
