-- A posting's minimum salary can never exceed its maximum.
select job_id, salary_min_usd, salary_max_usd
from {{ ref('int_jobs') }}
where salary_min_usd > salary_max_usd
