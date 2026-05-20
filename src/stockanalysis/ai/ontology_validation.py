from __future__ import annotations

from datetime import date

from stockanalysis.ingest.macro.sql import sql_date, sql_literal


DEFAULT_ALLOWED_RELATION_TYPES = (
    "parent_child",
    "contains",
    "belongs_to",
    "same_theme",
    "theme_contains_sector",
    "sector_contains_industry",
)


def render_ontology_lite_validation_sql(
    *,
    as_of_date: date,
    allowed_relation_types: tuple[str, ...] = DEFAULT_ALLOWED_RELATION_TYPES,
) -> str:
    if not allowed_relation_types:
        raise ValueError("allowed_relation_types must not be empty.")
    relation_literals = ", ".join(sql_literal(value) for value in allowed_relation_types)
    target_date_sql = sql_date(as_of_date)

    return f"""-- ai ontology-lite validation lookup
with orphan_classification_edges as (
    select
        'orphan_classification_edge' as check_name,
        edge.edge_id::text as object_id,
        json_build_object(
            'parent_node_id', edge.parent_node_id,
            'child_node_id', edge.child_node_id,
            'relation_type', edge.relation_type
        ) as details
    from ref.classification_edge edge
    left join ref.classification_node parent_node
      on parent_node.node_id = edge.parent_node_id
    left join ref.classification_node child_node
      on child_node.node_id = edge.child_node_id
    where parent_node.node_id is null
       or child_node.node_id is null
),
invalid_relation_types as (
    select
        'invalid_relation_type' as check_name,
        edge.edge_id::text as object_id,
        json_build_object(
            'relation_type', edge.relation_type,
            'allowed_relation_types', array[{relation_literals}]
        ) as details
    from ref.classification_edge edge
    where edge.relation_type not in ({relation_literals})
),
overlapping_classification_edge_windows as (
    select
        'overlapping_classification_edge_window' as check_name,
        left_edge.edge_id::text || ':' || right_edge.edge_id::text as object_id,
        json_build_object(
            'parent_node_id', left_edge.parent_node_id,
            'child_node_id', left_edge.child_node_id,
            'relation_type', left_edge.relation_type,
            'left_valid_from', left_edge.valid_from,
            'left_valid_to', left_edge.valid_to,
            'right_valid_from', right_edge.valid_from,
            'right_valid_to', right_edge.valid_to
        ) as details
    from ref.classification_edge left_edge
    join ref.classification_edge right_edge
      on right_edge.edge_id > left_edge.edge_id
     and right_edge.parent_node_id = left_edge.parent_node_id
     and right_edge.child_node_id = left_edge.child_node_id
     and right_edge.relation_type = left_edge.relation_type
     and daterange(left_edge.valid_from, coalesce(left_edge.valid_to, 'infinity'::date), '[]')
       && daterange(right_edge.valid_from, coalesce(right_edge.valid_to, 'infinity'::date), '[]')
),
overlapping_membership_windows as (
    select
        'overlapping_membership_window' as check_name,
        left_membership.membership_id::text || ':' || right_membership.membership_id::text as object_id,
        json_build_object(
            'instrument_id', left_membership.instrument_id,
            'node_id', left_membership.node_id,
            'membership_type', left_membership.membership_type,
            'left_valid_from', left_membership.valid_from,
            'left_valid_to', left_membership.valid_to,
            'right_valid_from', right_membership.valid_from,
            'right_valid_to', right_membership.valid_to
        ) as details
    from ref.instrument_classification_membership left_membership
    join ref.instrument_classification_membership right_membership
      on right_membership.membership_id > left_membership.membership_id
     and right_membership.instrument_id = left_membership.instrument_id
     and right_membership.node_id = left_membership.node_id
     and right_membership.membership_type = left_membership.membership_type
     and daterange(left_membership.valid_from, coalesce(left_membership.valid_to, 'infinity'::date), '[]')
       && daterange(right_membership.valid_from, coalesce(right_membership.valid_to, 'infinity'::date), '[]')
),
inferred_memberships_without_evidence as (
    select
        'inferred_membership_without_evidence' as check_name,
        membership.membership_id::text as object_id,
        json_build_object(
            'instrument_id', membership.instrument_id,
            'node_id', membership.node_id,
            'membership_type', membership.membership_type,
            'confidence', membership.confidence,
            'valid_from', membership.valid_from,
            'valid_to', membership.valid_to
        ) as details
    from ref.instrument_classification_membership membership
    where membership.membership_type in ('inferred', 'ai_inferred', 'news_inferred')
      and membership.valid_from <= {target_date_sql}
      and (membership.valid_to is null or membership.valid_to >= {target_date_sql})
      and (
          membership.source_document_id is null
          or membership.confidence is null
          or membership.confidence <= 0
      )
),
validation_rows as (
    select * from orphan_classification_edges
    union all
    select * from invalid_relation_types
    union all
    select * from overlapping_classification_edge_windows
    union all
    select * from overlapping_membership_windows
    union all
    select * from inferred_memberships_without_evidence
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'allowed_relation_types', array[{relation_literals}],
    'issue_count', (select count(*)::int from validation_rows),
    'issues',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'check_name', check_name,
                    'object_id', object_id,
                    'details', details
                )
                order by check_name, object_id
            )
            from validation_rows
        ),
        '[]'::json
    )
)::text;"""
