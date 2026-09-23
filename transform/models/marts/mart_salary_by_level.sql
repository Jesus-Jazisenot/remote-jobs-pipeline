select
    level,
    count(*)                                                        as n_jobs,
    count(salary_mid_usd)                                           as n_with_salary,
    round(quantile_cont(salary_mid_usd, 0.25))                      as p25_salary_usd,
    round(median(salary_mid_usd))                                   as median_salary_usd,
    round(quantile_cont(salary_mid_usd, 0.75))                      as p75_salary_usd,
    round(median(salary_mid_usd) filter (where open_to_mexico))     as median_open_to_mexico_usd
from {{ ref('fct_tech_jobs') }}
group by level
order by case level when 'junior' then 1 when 'mid' then 2 else 3 end
