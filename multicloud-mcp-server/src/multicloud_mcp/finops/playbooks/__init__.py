"""Static FinOps Framework playbooks shipped with the server.

Playbooks are Markdown files with YAML front matter, packaged under
``multicloud_mcp/finops/playbooks/content``. They are read once, validated, and
kept in memory. They contain guidance only: no prices, no account data, and no
code that runs.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Any

import yaml

FINOPS_DOMAINS: tuple[str, ...] = (
    "Understand Usage & Cost",
    "Quantify Business Value",
    "Optimize Usage & Cost",
    "Manage the FinOps Practice",
)
FINOPS_PHASES: tuple[str, ...] = ("inform", "optimize", "operate")

_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
_REQUIRED_FIELDS = ("id", "title", "summary", "domain", "capabilities", "phases")

# Field weights for search scoring: metadata matches outrank body mentions.
_WEIGHT_TITLE = 5
_WEIGHT_TAG = 4
_WEIGHT_CAPABILITY = 3
_WEIGHT_SUMMARY = 2
_WEIGHT_BODY = 1


class PlaybookFormatError(ValueError):
    """A packaged playbook file is malformed."""


@dataclass(frozen=True)
class Playbook:
    """One FinOps playbook: validated metadata plus the Markdown body."""

    id: str
    title: str
    summary: str
    domain: str
    capabilities: tuple[str, ...]
    phases: tuple[str, ...]
    providers: tuple[str, ...]
    related_tools: tuple[str, ...]
    tags: tuple[str, ...]
    body: str

    def summary_dict(self) -> dict[str, Any]:
        """Return the metadata without the body."""
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "domain": self.domain,
            "capabilities": list(self.capabilities),
            "phases": list(self.phases),
            "providers": list(self.providers),
            "related_tools": list(self.related_tools),
            "tags": list(self.tags),
        }

    def full_dict(self) -> dict[str, Any]:
        """Return the metadata and the Markdown body."""
        return {**self.summary_dict(), "body": self.body}


def _tokens(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())


def _string_list(meta: Mapping[str, Any], key: str, source: str) -> tuple[str, ...]:
    value = meta.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PlaybookFormatError(f"{source}: '{key}' must be a list of strings")
    return tuple(item.strip() for item in value)


def parse_playbook(source: str, text: str) -> Playbook:
    """Parse and validate one Markdown playbook.

    Args:
        source: File name, used in error messages.
        text: File content with YAML front matter.

    Returns:
        The validated playbook.

    Raises:
        PlaybookFormatError: If the front matter is missing or invalid.
    """
    match = _FRONT_MATTER.match(text.replace("\r\n", "\n"))
    if match is None:
        raise PlaybookFormatError(f"{source}: missing YAML front matter")
    meta = yaml.safe_load(match.group(1))
    if not isinstance(meta, dict):
        raise PlaybookFormatError(f"{source}: front matter must be a mapping")
    for field in _REQUIRED_FIELDS:
        if not meta.get(field):
            raise PlaybookFormatError(f"{source}: missing required field '{field}'")

    playbook_id = str(meta["id"])
    if not _ID_PATTERN.match(playbook_id):
        raise PlaybookFormatError(f"{source}: invalid id '{playbook_id}'")
    domain = str(meta["domain"])
    if domain not in FINOPS_DOMAINS:
        raise PlaybookFormatError(f"{source}: unknown domain '{domain}'")
    phases = tuple(phase.lower() for phase in _string_list(meta, "phases", source))
    unknown_phases = set(phases) - set(FINOPS_PHASES)
    if unknown_phases:
        raise PlaybookFormatError(f"{source}: unknown phase(s) {sorted(unknown_phases)}")

    return Playbook(
        id=playbook_id,
        title=str(meta["title"]).strip(),
        summary=str(meta["summary"]).strip(),
        domain=domain,
        capabilities=_string_list(meta, "capabilities", source),
        phases=phases,
        providers=tuple(p.lower() for p in _string_list(meta, "providers", source)),
        related_tools=_string_list(meta, "related_tools", source),
        tags=tuple(tag.lower() for tag in _string_list(meta, "tags", source)),
        body=match.group(2).strip(),
    )


class PlaybookCatalog:
    """In-memory, read-only catalog of validated playbooks."""

    def __init__(self, playbooks: Iterable[Playbook]) -> None:
        self._playbooks: dict[str, Playbook] = {}
        for playbook in playbooks:
            if playbook.id in self._playbooks:
                raise PlaybookFormatError(f"duplicate playbook id '{playbook.id}'")
            self._playbooks[playbook.id] = playbook

    @classmethod
    def from_documents(cls, documents: Mapping[str, str]) -> PlaybookCatalog:
        """Build a catalog from ``{file name: Markdown text}``."""
        return cls(parse_playbook(name, text) for name, text in sorted(documents.items()))

    def all(self) -> list[Playbook]:
        """Return every playbook, ordered by id."""
        return [self._playbooks[key] for key in sorted(self._playbooks)]

    def get(self, playbook_id: str) -> Playbook | None:
        """Return one playbook by id, or None."""
        return self._playbooks.get(playbook_id)

    def search(self, query: str) -> list[tuple[Playbook, int]]:
        """Rank playbooks by weighted keyword overlap with ``query``.

        Returns:
            ``(playbook, score)`` pairs with a positive score, best first, ties by id.
        """
        terms = set(_tokens(query))
        if not terms:
            return []
        ranked: list[tuple[Playbook, int]] = []
        for playbook in self.all():
            score = self._score(playbook, terms)
            if score > 0:
                ranked.append((playbook, score))
        ranked.sort(key=lambda pair: (-pair[1], pair[0].id))
        return ranked

    @staticmethod
    def _score(playbook: Playbook, terms: set[str]) -> int:
        fields = (
            (_WEIGHT_TITLE, set(_tokens(playbook.title))),
            (_WEIGHT_TAG, set(_tokens(" ".join(playbook.tags)))),
            (_WEIGHT_CAPABILITY, set(_tokens(" ".join(playbook.capabilities)))),
            (_WEIGHT_SUMMARY, set(_tokens(playbook.summary))),
        )
        score = sum(weight * len(terms & field_terms) for weight, field_terms in fields)
        body_terms = _tokens(playbook.body)
        # Cap body hits per term so long playbooks do not win on length alone.
        score += _WEIGHT_BODY * sum(min(body_terms.count(term), 3) for term in terms)
        return score


@lru_cache(maxsize=1)
def load_default_catalog() -> PlaybookCatalog:
    """Load and cache the playbooks packaged with the server."""
    content = resources.files(__name__).joinpath("content")
    documents = {
        entry.name: entry.read_text(encoding="utf-8")
        for entry in content.iterdir()
        if entry.is_file() and entry.name.endswith(".md")
    }
    return PlaybookCatalog.from_documents(documents)


__all__ = [
    "FINOPS_DOMAINS",
    "FINOPS_PHASES",
    "Playbook",
    "PlaybookCatalog",
    "PlaybookFormatError",
    "load_default_catalog",
    "parse_playbook",
]
