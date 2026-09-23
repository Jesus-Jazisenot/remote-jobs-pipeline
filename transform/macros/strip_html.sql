{% macro strip_html(col) -%}
    trim(regexp_replace(
        regexp_replace(regexp_replace({{ col }}, '<[^>]+>', ' ', 'g'),
                       '&(nbsp|amp|lt|gt|quot|#\d+|[a-z]+);', ' ', 'g'),
        '\s+', ' ', 'g'))
{%- endmacro %}
