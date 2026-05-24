alter table ai.cycle_community_summary
    drop constraint if exists cycle_community_summary_summary_type_check;

alter table ai.cycle_community_summary
    add constraint cycle_community_summary_summary_type_check
    check (summary_type in ('cycle_graph_context_v1', 'cycle_community_ai_v2'));

create index if not exists idx_cycle_community_summary_type_node_date
    on ai.cycle_community_summary (summary_type, node_id, as_of_date desc);
