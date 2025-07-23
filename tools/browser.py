from __future__ import annotations

from logging_config import logger
from bs4 import BeautifulSoup
from server.cache import redis_cache
from .base import Tool

try:
    from browser_use.browser import BrowserSession
except Exception:  # pragma: no cover - optional dep
    BrowserSession = None

__all__ = ["browse_url", "BrowserTool"]


@redis_cache(ttl=600)
async def browse_url(url: str) -> str:
    """Return plain text from ``url`` using browser-use."""
    if BrowserSession is None:
        return "Browser integration is unavailable."
    session = BrowserSession()
    try:
        await session.navigate(url)
        html = await session.get_page_html()
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        return text[:1000]
    except Exception as exc:  # noqa: BLE001
        logger.bind(url=url, error=str(exc)).error("browser_use_failed")
        return "Sorry, I'm unable to access that page right now."
    finally:
        await session.close()


class BrowserTool(Tool):
    """Tool to fetch web page content via browser-use."""

    name = "browse_url"
    description = "Fetch the main text content of a web page."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Page URL"},
        },
        "required": ["url"],
    }

    async def run(self, url: str) -> str:  # type: ignore[override]
        return await browse_url(url)
