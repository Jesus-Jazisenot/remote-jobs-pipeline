-- Remotive publishes salary as free text: "$90k - $105k", "50-70 USD/hour", "€60,000".
with ranked as (
    select *, row_number() over (partition by id order by _fetched_at desc) as rn
    from {{ source('raw', 'remotive') }}
),

parsed as (
    select
        *,
        lower(replace(coalesce(salary, ''), ',', '')) as salary_txt,
        list_filter(
            list_transform(
                regexp_extract_all(lower(replace(coalesce(salary, ''), ',', '')), '\d+(?:\.\d+)?\s*k?'),
                x -> case when x like '%k' then trim(replace(x, 'k', ''))::double * 1000
                          else trim(x)::double end
            ),
            n -> n >= 10
        ) as salary_numbers
    from ranked
    where rn = 1
)

select
    'remotive'                                                    as source,
    'rv:' || id                                                   as job_id,
    trim(title)                                                   as title,
    trim(company_name)                                            as company,
    coalesce(nullif(candidate_required_location, ''), 'Worldwide') as location,
    ''                                                            as seniority_hint,
    list_min(salary_numbers)                                      as salary_min,
    list_max(salary_numbers)                                      as salary_max,
    case when salary_txt like '%€%' or salary_txt like '%eur%' then 'EUR'
         when salary_txt like '%£%' or salary_txt like '%gbp%' then 'GBP'
         else 'USD' end                                           as currency,
    case when regexp_matches(salary_txt, 'hour|/h\b|\bhr') then 'hourly'
         when salary_txt like '%month%' then 'monthly'
         else 'annual' end                                        as salary_period,
    array_to_string(tags, ', ')                                   as tags,
    {{ strip_html('description') }}                               as description,
    publication_date::date                                        as published_on,
    url,
    _fetched_at                                                   as fetched_at
from parsed
