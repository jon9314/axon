# MCP Environment Setup

Axon bundles a set of helper servers that speak the Model Context Protocol (MCP). They provide basic filesystem, time and calculator operations and a markdown note store.

When using Docker these servers are started automatically alongside the backend. For local development you can run them with Python:

```bash
python -m mcp_servers
```

This launches the following services on localhost:

- **Filesystem** – `http://localhost:9001`
- **Time** – `http://localhost:9002`
- **Calculator** – `http://localhost:9003`
- **Markdown Backup** – `http://localhost:9004`
- **GitHub** – `http://localhost:9005` (basic repo access)
- **Docs** – `http://localhost:9006` (Python documentation)

The backend expects these URLs via environment variables when running in containers. They can be customised in `docker-compose.yml` or your shell environment.

