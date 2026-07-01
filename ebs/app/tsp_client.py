import httpx


class TspClient:
    """Thin async wrapper over tsp-core-service's REST API (see documentation.txt)."""

    def __init__(self, base_url: str, timeout_s: float):
        self._base_url = base_url.rstrip("/")
        self._timeout_s = timeout_s

    async def _get(self, path: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout_s) as client:
            resp = await client.get(path, params=params)
            resp.raise_for_status()
            return resp.json()

    async def _post(self, path: str, json: dict | None = None) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout_s) as client:
            resp = await client.post(path, json=json or {})
            resp.raise_for_status()
            return resp.json()

    async def controller_state(self) -> dict:
        return await self._get("/controller/state")

    async def health(self) -> dict:
        return await self._get("/status/health")

    async def start_mission(self, mission_id: str, params: dict | None = None) -> dict:
        return await self._post("/ag_manager/mission/start", {"mission_id": mission_id, "params": params or {}})

    async def abort_mission(self) -> dict:
        return await self._post("/ag_manager/mission/abort")
