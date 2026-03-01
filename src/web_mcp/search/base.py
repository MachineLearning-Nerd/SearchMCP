from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchResult:
    title: str
    url: str
    description: str = ""
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "source": self.source,
        }


@dataclass
class SearchResponse:
    results: list[SearchResult]
    suggestions: list[str] = field(default_factory=list)
    provider: str = ""
    query: str = ""

    @property
    def total(self) -> int:
        return len(self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self.results],
            "suggestions": self.suggestions,
            "provider": self.provider,
            "query": self.query,
            "total": self.total,
        }


# Search categories supported by SearxNG. Used for input validation in both
# the web_search tool and the SearxNG provider.
VALID_CATEGORIES: set[str] = {"general", "images", "videos", "news", "science", "files"}


class SearchProvider(ABC):
    """Base class that all search providers must implement.

    Concrete implementations: SearxNGProvider, GoogleProvider, FallbackSearchProvider.
    Each provider must define how to search and how to get suggestions.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    async def search(self, query: str, category: str = "general", limit: int = 5) -> SearchResponse:
        pass

    @abstractmethod
    async def get_suggestions(self, query: str) -> list[str]:
        pass
