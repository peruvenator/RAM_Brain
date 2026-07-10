# Adding URLs to Blogs

## Goal

Populate the **Main URL** property in the **Publications List [M&S]** Notion database for entries that are missing it. Focus on blog posts and other published content where a public URL exists but was never recorded in the database.

## Target Database

| Item | Value |
|---|---|
| Database | Publications List [M&S] |
| Database ID | `60b55bf9-54ce-476c-a050-167034bd1346` |
| Data source | `collection://e8717675-3685-4d87-b1f8-f5317da846c1` |
| Target property | `Main URL` (type: url) |

## Approach

1. **Discovery** -- Query the Publications database for entries where `Main URL` is empty, filtered to content types that should have a URL (blog posts, articles, etc.)
2. **URL sourcing** -- Determine the correct URL for each entry (from known site domains, HubSpot, or manual lookup)
3. **Population** -- Update each page's `Main URL` property via the Notion API
4. **Validation** -- Verify URLs resolve correctly before writing

## Key Configuration

- **API key**: `NOTION_API_KEY` from `RAM_Brain/.env`
- **Notion MCP**: Can also query/update via the connected Notion MCP server for interactive work

## Notes for Future Sessions

- The `Main URL` property is a native Notion `url` type field -- updates are straightforward via the API
- The database has 1000+ entries; always filter and batch to avoid rate limits
- Some content types (internal memos, templates) intentionally have no URL -- skip those
- Check `Status` and `Content Type` properties to identify which entries should have URLs
