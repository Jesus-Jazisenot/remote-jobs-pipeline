with jobs as (select * from {{ ref('fct_tech_jobs') }}),
total as (select count(*) as n from jobs)

select
    s.skill,
    s.category,
    count(*)                                                        as n_jobs,
    round(count(*) / any_value(total.n), 4)                         as share_of_jobs,
    count(j.salary_mid_usd)                                         as n_with_salary,
    round(median(j.salary_mid_usd))                                 as median_salary_usd,
    count(*) filter (where j.open_to_mexico)                        as n_open_to_mexico,
    round(median(j.salary_mid_usd) filter (where j.open_to_mexico)) as median_salary_open_to_mexico_usd
from {{ ref('int_job_skills') }} s
join jobs j using (job_id)
cross join total
group by s.skill, s.category
order by n_jobs desc
