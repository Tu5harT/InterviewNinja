---
trigger: always_on
---

# Code Review Graph Navigation Rules

When you need to understand the codebase, dependencies, or impact of changes:

1. **ALWAYS query the code-review-graph first** before reading raw files:
   - Use `/graph query "your question"` or call MCP tools directly
   - Prefer `get_review_context_tool` for token-efficient code reviews
   - Use `get_impact_radius_tool` to find affected files before making changes

2. **ONLY read raw files if**:
   - I explicitly say "read the file" or "show me the raw code"
   - The graph returns no results for a specific query
   - You need to inspect implementation details after graph navigation

3. **Use these graph tools for navigation**:
   - `query_graph_tool` → Find callers/callees/imports for any function or class
   - `semantic_search_nodes_tool` → Search by name or meaning across the codebase
   - `get_impact_radius_tool` → Before editing, check what will be affected
   - `get_review_context_tool` → Get minimal, structured context for reviews (saves ~8x tokens) [[README]]

4. **Token-saving workflow**:


5. **For code reviews**:
- Always start with `detect_changes_tool` or `get_impact_radius_tool`
- Never send entire files to the LLM — use `get_review_context_tool` which compresses structural info
- Benchmark: 8.2x average token reduction vs naive file reading [[README]]

6. **Wiki navigation** (if generated):
- Use `graphify-out/wiki/index.md` as entrypoint for architecture browsing
- Use `get_wiki_page_tool` to retrieve specific sections