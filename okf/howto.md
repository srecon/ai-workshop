## How to run the OKF converter and indexer pipeline

You have to need two directories:
- raw_docs: Original docs, remains unchanged
- knowledge: knowledge graph in OKF format v2

```python
pip install "markitdown[all]" pyyaml

python3 okf_pipeline.py
```
## MCP server to expose the knowledge

```
"chirag127-okf-knowledge-mcp": {
  "command": "npx",
  "args": [
    "-y",
    "@chirag127/okf-knowledge-mcp"
  ],
  "env": {
    "KNOWLEDGE_ROOT": "/PATH_TO_Knowledge/knowledge"
  }
}
```

Prompts examples:
- List all concepts in the knowledge base.
- Search the knowledge base for anything related writing styles
- Read the concept file at Writing_styles/File_name

### How to Trigger Each Tool

1. search_knowledge — Use this when you want to find concepts by keyword.

```
"Search the knowledge base for anything related to billing."

"Look up our architectural decisions about authentication in the OKF knowledge base."

"Find all concepts tagged with 'security'."
``` 

2. read_concept — Use this when you know the relative path of a concept file and want its full content.

```
"Read the concept file at services/billing-service.md."

"Show me the contents of rules/agent/afk-vs-hitl-tasks.md."

"What does the OKF concept at decisions/use-postgres.md say?"
```

3. list_concepts — Use this to browse what's available in the knowledge base.

```
"List all concepts in the knowledge base."

"Show me every service concept in the OKF bundle."

"List all concepts of type decision or rule."
```

4. write_concept — Use this to create or update a concept file (requires Git sync if configured).

```
"Create a new OKF concept for a service called payment-gateway with the description 'Handles payment processing and webhooks' and tags payments, api."

"Update the concept at services/billing-service.md to add a new dependency on notification-service."

"Add a new rule concept titled 'No direct database access from frontend' with the body 'All database access must go through the API layer'."
```    