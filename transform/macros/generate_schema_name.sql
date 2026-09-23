{# Use the layer name as the schema (staging, marts…) instead of dbt's default "<target>_<layer>". #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name if custom_schema_name else target.schema }}
{%- endmacro %}
