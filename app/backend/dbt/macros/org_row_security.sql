{#
    Row-level security for analytics tables that have bge_id and sub_bge_id.
    Use as a post-hook: dbt recreates the table on every run, which drops its
    grants and policies, so they are added again after each build.

    - TO roles see every row.
    - Org roles see rows for their assigned BGEs, and for their assigned
      sub-BGEs / service designees and everything under them
      (functions in alembic 015_org_scope_functions).

    dbt runs as the table owner, which RLS doesn't apply to, so builds and
    tests still see all rows.
#}
{% macro org_row_security() %}
    grant select on {{ this }} to tap_org_admin, tap_org_user;

    alter table {{ this }} enable row level security;

    create policy to_all on {{ this }}
        for select
        to tap_to_admin, tap_to_viewer
        using (true);

    create policy org_scope on {{ this }}
        for select
        to tap_org_admin, tap_org_user
        using (
            -- (select ...) runs the function once per query, not per row. The
            -- ::integer[] cast makes ANY compare against the array's items
            -- rather than treat the select as a subquery of arrays.
            bge_id = any ((select tap_private.allowed_bge_ids())::integer[])
            or sub_bge_id = any ((select tap_private.allowed_sub_bge_ids())::integer[])
        );
{% endmacro %}
