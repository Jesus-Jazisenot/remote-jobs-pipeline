-- Fails the run if a whole source silently returned nothing (API change, block, outage).
with expected as (select unnest(['himalayas', 'remotive', 'remoteok']) as source)
select e.source
from expected e
left join (select distinct source from {{ ref('int_jobs') }}) j using (source)
where j.source is null
