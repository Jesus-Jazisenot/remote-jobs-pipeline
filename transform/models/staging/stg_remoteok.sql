with ranked as (
    select *, row_number() over (partition by id order by _fetched_at desc) as rn
    from {{ source('raw', 'remoteok') }}
)

select
    'remoteok'                                                    as source,
    'ro:' || id                                                   as job_id,
    trim(position)                                                as title,
    trim(company)                                                 as company,
    coalesce(nullif(location, ''), 'Worldwide')                   as location,
    ''                                                            as seniority_hint,
    nullif(salary_min, 0)::double                                 as salary_min,
    nullif(salary_max, 0)::double                                 as salary_max,
    'USD'                                                         as currency,
    'annual'                                                      as salary_period,
    array_to_string(tags, ', ')                                   as tags,
    {{ strip_html('description') }}                               as description,
    "date"::date                                                  as published_on,
    coalesce(url, apply_url)                                      as url,
    _fetched_at                                                   as fetched_at
from ranked
where rn = 1
