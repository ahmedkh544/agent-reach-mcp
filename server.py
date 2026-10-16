
import os
import httpx

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings


mcp = FastMCP("agent-reach-mcp")


@mcp.tool()
async def search_github_repositories(
    query: str,
    limit: int = 5,
) -> dict:
    """Search public GitHub repositories by keywords."""
    query = query.strip()
    if not query:
        return {
            "error": "Search query cannot be empty.",
            "repositories": [],
        }

    limit = max(1, min(limit, 10))

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            "https://api.github.com/search/repositories",
            params={
                "q": query,
                "per_page": limit,
                "sort": "stars",
            },
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "agent-reach-mcp",
            },
        )
        response.raise_for_status()
        data = response.json()

    return {
        "total_count": data.get("total_count", 0),
        "repositories": [
            {
                "name": item["full_name"],
                "description": item.get("description"),
                "url": item["html_url"],
                "stars": item["stargazers_count"],
                "language": item.get("language"),
            }
            for item in data.get("items", [])
        ],
    }


@mcp.tool()
async def read_public_github_file(
    owner: str,
    repo: str,
    path: str,
    ref: str = "HEAD",
) -> dict:
    """Read a text file from a public GitHub repository."""

    owner = owner.strip()
    repo = repo.strip()
    path = path.strip()
    ref = ref.strip()

    if not owner or not repo or not path or not ref:
        return {
            "error": "Owner, repository, path, and ref are required."
        }

    url = (
        "https://raw.githubusercontent.com/"
        f"{owner}/{repo}/{ref}/{path}"
    )

    async with httpx.AsyncClient(
        timeout=20,
        follow_redirects=True,
    ) as client:
        response = await client.get(
            url,
            headers={"User-Agent": "agent-reach-mcp"},
        )
        response.raise_for_status()

    content = response.text

    return {
        "path": path,
        "ref": ref,
        "content": content[:30000],
        "truncated": len(content) > 30000,
    }


@mcp.tool()
def agent_reach_setup_status() -> dict:
    """Report the capabilities currently implemented by this server."""
    return {
        "status": "starter",
        "available": [
            "GitHub public repository search",
            "Public GitHub text-file reading",
            "Capability status report",
        ],
        "not_integrated": [
            "Reddit",
            "YouTube",
            "X",
            "Bilibili",
        ],
        "transport": "Streamable HTTP",
        "note": (
            "This server is a starter implementation, "
            "not the complete Agent-Reach integration."
        ),
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))

    security = TransportSecuritySettings(
        allowed_hosts=[
            "agent-reach-mcp-m7je.onrender.com",
            "agent-reach-mcp-m7je.onrender.com:*",
        ]
    )

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port,
        transport_security=security,
    )
