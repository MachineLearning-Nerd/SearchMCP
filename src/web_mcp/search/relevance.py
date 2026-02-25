from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from web_mcp.search.base import SearchResult

QUERY_INTENT_SECURITY = "security"
QUERY_INTENT_GENERAL = "general"

_CVE_PATTERN = re.compile(r"\bCVE-\d{4}-\d{4,}\b", flags=re.IGNORECASE)
_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")
_SECURITY_KEYWORDS = {
    "cve",
    "vulnerability",
    "vulnerabilities",
    "security",
    "exploit",
    "cvss",
    "advisory",
    "waiver",
    "patch",
    "mitigation",
}

_LOW_SIGNAL_SUFFIXES = (
    ".txt",
    ".csv",
    ".tsv",
    ".counts",
    ".vocab",
    ".xlsx",
    ".xls",
)
_LOW_SIGNAL_TOKENS = {
    "dictionary",
    "vocab",
    "wordlist",
    "words",
    "counts",
    "tokenizer",
}

_SECURITY_DOMAIN_BOOSTS: dict[str, float] = {
    "nvd.nist.gov": 8.0,
    "www.cve.org": 7.0,
    "cve.org": 7.0,
    "access.redhat.com": 5.0,
    "ubuntu.com": 5.0,
    "security.snyk.io": 4.0,
    "www.cvedetails.com": 3.0,
    "cvedetails.com": 3.0,
}

_GENERAL_DOMAIN_BOOSTS: dict[str, float] = {
    "docs.python.org": 4.0,
    "stackoverflow.com": 3.5,
    "realpython.com": 3.0,
    "developer.mozilla.org": 3.0,
    "github.com": 2.5,
    "en.wikipedia.org": 2.0,
}


@dataclass(frozen=True)
class ScoredSearchResult:
    result: SearchResult
    score: float


@dataclass(frozen=True)
class RankingOutcome:
    results: list[SearchResult]
    scored_results: list[ScoredSearchResult]
    quality_score: float


def detect_query_intent(query: str) -> str:
    if _CVE_PATTERN.search(query):
        return QUERY_INTENT_SECURITY

    lowered = query.lower()
    if any(keyword in lowered for keyword in _SECURITY_KEYWORDS):
        return QUERY_INTENT_SECURITY

    return QUERY_INTENT_GENERAL


def extract_cve_ids(query: str) -> set[str]:
    return {match.group(0).upper() for match in _CVE_PATTERN.finditer(query)}


def parse_engine_list(raw_value: str) -> list[str]:
    engines = [part.strip() for part in raw_value.split(",")]
    return [engine for engine in engines if engine]


def select_engines_for_query(
    query: str,
    mode: str,
    security_engines_raw: str,
    general_engines_raw: str,
) -> list[str] | None:
    normalized_mode = mode.strip().lower()
    if normalized_mode == "off":
        return None

    if normalized_mode != "auto":
        return None

    intent = detect_query_intent(query)
    if intent == QUERY_INTENT_SECURITY:
        engines = parse_engine_list(security_engines_raw)
        return engines or None

    engines = parse_engine_list(general_engines_raw)
    return engines or None


def rank_search_results(query: str, results: list[SearchResult], limit: int) -> RankingOutcome:
    if not results:
        return RankingOutcome(results=[], scored_results=[], quality_score=0.0)

    query_tokens = _tokenize(query)
    cve_ids = extract_cve_ids(query)
    intent = detect_query_intent(query)

    deduped: dict[str, ScoredSearchResult] = {}
    for result in results:
        score = _score_result(result, query_tokens, cve_ids, intent)
        scored_result = ScoredSearchResult(result=result, score=score)

        dedupe_key = _dedupe_key(result.url)
        existing = deduped.get(dedupe_key)
        if existing is None or scored_result.score > existing.score:
            deduped[dedupe_key] = scored_result

    ranked = sorted(
        deduped.values(),
        key=lambda item: (
            item.score,
            item.result.title.lower(),
            item.result.url.lower(),
        ),
        reverse=True,
    )

    capped_scored = ranked[:limit] if limit > 0 else ranked
    quality_score = _quality_from_scores([item.score for item in capped_scored])

    return RankingOutcome(
        results=[item.result for item in capped_scored],
        scored_results=capped_scored,
        quality_score=quality_score,
    )


def merge_ranked_results(
    query: str,
    primary_results: list[SearchResult],
    secondary_results: list[SearchResult],
    limit: int,
) -> RankingOutcome:
    return rank_search_results(
        query=query, results=[*primary_results, *secondary_results], limit=limit
    )


def is_low_quality(outcome: RankingOutcome, min_quality_score: float) -> bool:
    if not outcome.results:
        return True
    return outcome.quality_score < min_quality_score


def _score_result(
    result: SearchResult,
    query_tokens: set[str],
    cve_ids: set[str],
    intent: str,
) -> float:
    title = result.title.lower()
    description = result.description.lower()
    url = result.url.lower()
    domain = _get_domain(result.url)

    score = 0.0
    for token in query_tokens:
        if token in title:
            score += 1.8
        if token in url:
            score += 1.0
        if token in description:
            score += 0.5

    if intent == QUERY_INTENT_SECURITY:
        for cve_id in cve_ids:
            lowered_cve = cve_id.lower()
            if lowered_cve in title or lowered_cve in description or lowered_cve in url:
                score += 10.0
        score += _SECURITY_DOMAIN_BOOSTS.get(domain, 0.0)
    else:
        score += _GENERAL_DOMAIN_BOOSTS.get(domain, 0.0)

    if _is_low_signal_result(result):
        score -= 6.0

    if not result.description:
        score -= 0.25

    return score


def _quality_from_scores(scores: list[float]) -> float:
    if not scores:
        return 0.0

    top = scores[:3]
    positive_scores = [max(0.0, score) for score in top]
    return sum(positive_scores) / len(positive_scores)


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN_PATTERN.findall(text) if len(token) >= 2}


def _dedupe_key(url: str) -> str:
    normalized = normalize_url(url)
    return normalized or url


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.netloc:
        return url

    scheme = (parsed.scheme or "http").lower()
    netloc = parsed.netloc.lower()

    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    if scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    query_items = sorted(parse_qsl(parsed.query, keep_blank_values=True))
    query = urlencode(query_items)

    return urlunparse((scheme, netloc, path, "", query, ""))


def _is_low_signal_result(result: SearchResult) -> bool:
    lowered_url = result.url.lower()
    lowered_title = result.title.lower()

    if lowered_url.endswith(_LOW_SIGNAL_SUFFIXES):
        return True

    return any(token in lowered_title for token in _LOW_SIGNAL_TOKENS)


def _get_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower()
