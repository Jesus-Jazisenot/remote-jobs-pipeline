select skill, share_of_jobs
from {{ ref('mart_skill_demand') }}
where share_of_jobs <= 0 or share_of_jobs > 1
