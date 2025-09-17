import os
import json
from typing import Optional, Literal, Dict, Any

import httpx
from fastapi import FastAPI
from fastmcp import FastMCP

# === Config ===
UITDB_BASE = "https://search.uitdatabank.be"  # basis voor Search API (events/places/organizers)

# Pak secrets uit omgeving
UITDB_API_KEY = os.getenv("UITDB_API_KEY")
UITDB_CLIENT_ID = os.getenv("UITDB_CLIENT_ID")

# === MCP server ===
mcp = FastMCP("uitdb", stateless_http=True)

def _auth_params_and_headers() -> tuple[Dict[str, Any], Dict[str, str]]:
    """
    Bepaal auth via API key of client id.
    - Als API key aanwezig: stuur als X-Api-Key header én als apiKey queryparam (ruimdenkend voor varianten).
    - Als client id aanwezig: stuur als x-client-id header én als clientId queryparam.
    """
    params: Dict[str, Any] = {}
    headers: Dict[str, str] = {"Accept": "application/json"}

    if UITDB_API_KEY:
        headers["X-Api-Key"] = UITDB_API_KEY
        params["apiKey"] = UITDB_API_KEY
    if UITDB_CLIENT_ID:
        headers["x-client-id"] = UITDB_CLIENT_ID
        params["clientId"] = UITDB_CLIENT_ID

    return params, headers

async def _uitdb_search(
    endpoint: Literal["events", "places", "organizers"],
    q: Optional[str] = None,
    limit: int = 10,
    start: Optional[str] = None,
    end: Optional[str] = None,
    city: Optional[str] = None,
    page: int = 1,
) -> Dict[str, Any]:
    """
    Minimalistische wrapper rond UiTdatabank Search API.
    NB: Pas filters aan je noden aan; UiTdatabank ondersteunt veel meer parameters.
    """
    params, headers = _auth_params_and_headers()
    # Basisfilters
    if q:
        params["q"] = q
    params["size"] = limit
    params["page"] = page

    # Voorbeeld van extra filters (optioneel, afhankelijk van SAPI capabilities)
    if start:
        params["dateFrom"] = start  # ISO-8601 (bv. 2025-09-01)
    if end:
        params["dateTo"] = end
    if city:
        params["addressLocality"] = city

    url = f"{UITDB_BASE}/{endpoint}"
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json()

def _compact_event(e: Dict[str, Any]) -> Dict[str, Any]:
    """
    Maak resultaten compacter/leesbaar voor in Claude.
    Let op: veldnamen kunnen per versie verschillen; dit is een veilige, defensieve extractie.
    """
    def g(obj, *path, default=None):
        cur = obj
        for p in path:
            if isinstance(cur, dict) and p in cur:
                cur = cur[p]
            else:
                return default
        return cur

    return {
        "id": e.get("id"),
        "name": g(e, "name", "nl", default=g(e, "name", "en", default=e.get("name"))),
        "startDate": g(e, "calendar", "startDate"),
        "endDate": g(e, "calendar", "endDate"),
        "status": g(e, "status", "type"),
        "url": g(e, "url"),
        "location": g(e, "location", "address", "addressLocality"),
        "organizer": g(e, "organizer", "name"),
    }

@mcp.tool
async def search_uit(
    endpoint: Literal["events", "places", "organizers"],
    q: Optional[str] = None,
    limit: int = 10,
    page: int = 1,
    start: Optional[str] = None,
    end: Optional[str] = None,
    city: Optional[str] = None,
) -> dict:
    """
    Doorzoek de UiTdatabank Search API.

    Args:
      endpoint: 'events' | 'places' | 'organizers'
      q: vrije zoekterm
      limit: aantal items per pagina (default 10)
      page: paginanummer (default 1)
      start: ISO startdatum (bv '2025-09-01')
      end: ISO einddatum
      city: filter op stad (indien ondersteund)

    Returns:
      Compacte JSON met de belangrijkste velden.
    """
    raw = await _uitdb_search(endpoint, q=q, limit=limit, page=page, start=start, end=end, city=city)
    # Probeer generiek 'items' / 'member' / 'results' op te vangen
    items = raw.get("items") or raw.get("member") or raw.get("results") or []
    # Compacteer events alleen voor 'events'; voor andere endpoints returnen we raw items
    if endpoint == "events":
        compact = [_compact_event(e) for e in items]
    else:
        compact = items
    return {
        "endpoint": endpoint,
        "count": len(compact),
        "page": page,
        "data": compact,
        "raw_meta": {k: v for k, v in raw.items() if k not in ("items", "member", "results")},
    }

# === FastAPI app + MCP over HTTP/SSE ===
app = FastAPI()

# Mount FastMCP op /mcp (SSE/HTTP transport)
app.mount("/mcp", mcp.fastapi_app)

@app.get("/")
def health():
    return {"ok": True, "service": "uitdb-mcp", "mcp_endpoint": "/mcp"}
