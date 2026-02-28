from unittest.mock import AsyncMock, patch

import pytest

from web_mcp.search.provider_registry import close_search_provider, get_search_provider


class TestProviderRegistry:
    @pytest.mark.asyncio
    async def test_get_search_provider_returns_singleton(self):
        await close_search_provider()

        provider_one = get_search_provider()
        provider_two = get_search_provider()

        assert provider_one is provider_two
        await close_search_provider()

    @pytest.mark.asyncio
    async def test_close_search_provider_closes_existing_provider(self):
        await close_search_provider()
        provider = get_search_provider()

        with patch.object(provider, "close", AsyncMock()) as close_mock:
            await close_search_provider()
            close_mock.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_search_provider_is_noop_when_not_initialized(self):
        await close_search_provider()
        await close_search_provider()
