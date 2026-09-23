with ranked as (
    select *, row_number() over (partition by guid order by _fetched_at desc) as rn
    from {{ source('raw', 'himalayas') }}
)

select
    'himalayas'                                                   as source,
    'hm:' || guid                                                 as job_id,
    trim(title)                                                   as title,
    trim(companyName)                                             as company,
    coalesce(nullif(array_to_string(locationRestrictions, ', '), ''), 'Worldwide') as location,
    lower(coalesce(array_to_string(seniority, ','), ''))          as seniority_hint,
    minSalary::double                                             as salary_min,
    maxSalary::double                                             as salary_max,
    upper(coalesce(currency, 'USD'))                              as currency,
    lower(coalesce(salaryPeriod, 'annual'))                       as salary_period,
    array_to_string(categories, ', ')                             as tags,
    {{ strip_html('description') }}                               as description,
    to_timestamp(pubDate)::date                                   as published_on,
    coalesce(applicationLink, guid)                               as url,
    _fetched_at                                                   as fetched_at
from ranked
where rn = 1
