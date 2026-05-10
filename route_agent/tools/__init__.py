"""Extensible tool modules for RouteAgent.

This directory contains standalone tool implementations that can be added
incrementally as you follow tutorials or extend the agent.

## How to add a new tool

1. Create a new file in this directory, e.g., `web_search.py`
2. Implement your tool function:

   ```python
   def web_search(query: str, max_results: int = 5) -> str:
       \"\"\"Search the web and return results.\"\"\"
       # Your implementation here
       return "search results..."
   ```

3. Register the tool in `route_agent/core/tools.py`:
   - Add your handler method to `ToolRegistry`
   - Add the function schema to `get_tools_schema()`
   - Or use the dynamic registration pattern:

   ```python
   from route_agent.tools.web_search import web_search
   registry.handlers["web_search"] = web_search
   ```

That's it — no other files need to change.
"""
