import asyncio
import httpx
import pytest

from app.services.flagsmith_client import FlagsmithApiError, FlagsmithClient


def test_management_api_uses_official_cloud_host_and_auth_scheme(monkeypatch):
    requests = []
    real_async_client = httpx.AsyncClient

    async def handler(request):
        requests.append(request)
        return httpx.Response(200, json=[])

    def client_factory(*, timeout, follow_redirects):
        return real_async_client(
            timeout=timeout,
            follow_redirects=follow_redirects,
            transport=httpx.MockTransport(handler),
        )

    monkeypatch.setattr("app.services.flagsmith_client.httpx.AsyncClient", client_factory)

    async def run_test():
        client = FlagsmithClient("https://api.flagsmith.com/api/v1", "test-management-key")
        return client, await client.test_connection()

    client, result = asyncio.run(run_test())

    assert client.base_url == "https://api.flagsmith.com/api/v1"
    assert result["ok"] is True
    assert requests[0].url == "https://api.flagsmith.com/api/v1/projects/"
    assert requests[0].headers["Authorization"] == "Api-Key test-management-key"
    assert requests[0].extensions["timeout"]["connect"] > 0


def test_paginated_feature_discovery_reads_all_pages(monkeypatch):
    requests = []
    real_async_client = httpx.AsyncClient

    async def handler(request):
        requests.append(request)
        if request.url.params.get("page") == "2":
            return httpx.Response(
                200,
                json={"count": 2, "next": None, "results": [{"id": 2, "name": "second"}]},
            )
        return httpx.Response(
            200,
            json={
                "count": 2,
                "next": "https://api.flagsmith.com/api/v1/projects/8/features/?page=2",
                "results": [{"id": 1, "name": "first"}],
            },
        )

    def client_factory(*, timeout, follow_redirects):
        return real_async_client(
            timeout=timeout,
            follow_redirects=follow_redirects,
            transport=httpx.MockTransport(handler),
        )

    monkeypatch.setattr("app.services.flagsmith_client.httpx.AsyncClient", client_factory)

    async def run_test():
        client = FlagsmithClient("https://api.flagsmith.com/api/v1", "test-management-key")
        return await client.get_project_features(8)

    features = asyncio.run(run_test())

    assert [feature["id"] for feature in features] == [1, 2]
    assert [request.url.params.get("page") for request in requests] == [None, "2"]
    assert all(request.headers["Authorization"] == "Api-Key test-management-key" for request in requests)


def test_paginated_discovery_rejects_cross_origin_next_url(monkeypatch):
    real_async_client = httpx.AsyncClient

    async def handler(_request):
        return httpx.Response(
            200,
            json={
                "count": 1,
                "next": "http://127.0.0.1:8000/steal-token",
                "results": [{"id": 1, "name": "first"}],
            },
        )

    def client_factory(*, timeout, follow_redirects):
        return real_async_client(
            timeout=timeout,
            follow_redirects=follow_redirects,
            transport=httpx.MockTransport(handler),
        )

    monkeypatch.setattr("app.services.flagsmith_client.httpx.AsyncClient", client_factory)

    async def run_test():
        client = FlagsmithClient("https://api.flagsmith.com/api/v1", "test-management-key")
        await client.get_project_features(8)

    with pytest.raises(FlagsmithApiError, match="outside the configured API origin"):
        asyncio.run(run_test())
