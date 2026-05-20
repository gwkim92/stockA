# Free News RSS Config Runner Plan

## Summary

- Keep all real RSS publisher URLs outside git.
- Add a backend operations runner that reads a repo-outside JSON config and calls the existing `news-rss-upsert` boundary for each enabled feed.
- Keep output sanitized: expose feed names, enabled state, host, item limits, and status, not full URLs.

## Config Shape

```json
{
  "version": "news-rss-feed-config-v1",
  "feeds": [
    {
      "feed_name": "operator-owned-name",
      "feed_url": "https://publisher.example/rss",
      "enabled": true,
      "limit": 25,
      "default_language": "en"
    }
  ]
}
```

## Guardrails

- No paid provider.
- No API key.
- No committed publisher URLs.
- No scoring or broker mutation.
