alter table ingest.source_document
    add column if not exists korean_title text,
    add column if not exists korean_summary text,
    add column if not exists translation_confidence numeric(5,4),
    add column if not exists translation_provider text,
    add column if not exists translation_model_name text,
    add column if not exists translation_invocation_id bigint references ai.model_invocation (invocation_id) on delete set null,
    add column if not exists translated_at timestamptz;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'source_document_translation_confidence_check'
    ) then
        alter table ingest.source_document
            add constraint source_document_translation_confidence_check
            check (
                translation_confidence is null
                or (translation_confidence >= 0 and translation_confidence <= 1)
            );
    end if;
end $$;

create index if not exists source_document_news_translation_pending_idx
    on ingest.source_document (published_at desc, document_id desc)
    where document_type = 'news_rss_item'
      and title is not null
      and korean_title is null;

create index if not exists source_document_translation_invocation_id_idx
    on ingest.source_document (translation_invocation_id)
    where translation_invocation_id is not null;
