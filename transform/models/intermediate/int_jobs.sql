-- One row per distinct posting across sources, with salary normalized to annual USD.
with unioned as (
    select * from {{ ref('stg_himalayas') }}
    union all by name
    select * from {{ ref('stg_remotive') }}
    union all by name
    select * from {{ ref('stg_remoteok') }}
),

-- The same posting often appears on several boards: keep one, preferring one with salary.
deduped as (
    select *,
        row_number() over (
            partition by lower(title), lower(company)
            order by (salary_min is not null) desc, fetched_at desc, source
        ) as rn
    from unioned
),

annualized as (
    select
        d.*,
        case d.salary_period
            when 'hourly' then 2080 when 'hour' then 2080
            when 'monthly' then 12 when 'month' then 12
            when 'weekly' then 52 when 'week' then 52
            else 1
        end * r.usd_rate as to_annual_usd
    from deduped d
    left join {{ ref('currency_rates') }} r on r.currency = d.currency
    where d.rn = 1
)

select
    job_id,
    source,
    title,
    company,
    location,
    published_on,
    url,
    tags,
    description,
    -- Discard obvious garbage ("1", monthly typed as annual, ranges wider than 4x).
    case when salary_valid then round(coalesce(salary_min, salary_max) * to_annual_usd) end as salary_min_usd,
    case when salary_valid then round(coalesce(salary_max, salary_min) * to_annual_usd) end as salary_max_usd,
    case
        when seniority_hint similar to '.*(senior|lead|manager|executive).*' then 'senior'
        when seniority_hint similar to '.*(entry|junior).*' then 'junior'
        when seniority_hint like '%mid%' then 'mid'
        when regexp_matches(title, '(?i)\b(senior|sr\.?|lead|principal|staff|head|director|architect)\b') then 'senior'
        when regexp_matches(title, '(?i)\b(junior|jr\.?|intern|internship|entry|trainee|graduate)\b') then 'junior'
        else 'mid'
    end as level,
    regexp_matches(location,
        '(?i)worldwide|anywhere|global|mexico|méxico|latam|latin america|americas|north america'
    ) as open_to_mexico,
    regexp_matches(title,
        '(?i)develop|engineer|programm|software|full.?stack|back.?end|front.?end|devops|\bdata\b|'
        '\bai\b|\bml\b|machine learning|automation|scrap|integrat|python|\bweb\b|cloud|platform|'
        '\bsre\b|\bqa\b|\btest|analyst|architect|technical|\bit\b|network|security|\bbot'
    ) as is_tech_title
from (
    select *,
        to_annual_usd is not null
        and coalesce(salary_min, salary_max) is not null
        and coalesce(salary_max, salary_min) * to_annual_usd >= 5000
        and coalesce(salary_min, salary_max) * to_annual_usd <= 1000000
        and coalesce(salary_max, salary_min) <= 4 * coalesce(salary_min, salary_max)
        as salary_valid
    from annualized
)
