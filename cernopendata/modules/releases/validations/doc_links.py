"""Validation that all /docs/ links in document bodies resolve."""

import re

from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from .base import Validation

MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
SLUG_CHARS = re.compile(r"^[A-Za-z0-9_-]+$")


class ValidDocLinks(Validation):
    """Check that document links in markdown bodies resolve."""

    name = "Valid document links"
    error_message = "Some document links do not resolve."
    applies_to = {"documents"}

    def validate(self, release):
        """Check each doc link resolves: it can be a slug in the current release or a registered PID."""
        release_slugs = self._get_release_slugs(release)
        errors = []
        for i, doc in enumerate(release.documents or []):
            content = self._get_content(doc)
            for slug in self._extract_absolute_slugs(content):
                if slug in release_slugs or self._is_registered_pid(slug):
                    continue
                errors.append(f"Document {i + 1}: link to /docs/{slug} not found")
            for slug in self._extract_bare_slugs(content):
                # Bare slugs need addressing: fixable if the target is known, broken otherwise.
                if slug in release_slugs or self._is_registered_pid(slug):
                    errors.append(
                        f"Document {i + 1}: bare-slug link '{slug}' should be /docs/{slug}"
                    )
                else:
                    errors.append(
                        f"Document {i + 1}: link '{slug}' does not resolve to a known document"
                    )
        return errors

    def fixable(self, release):
        """Return True if there are any auto-fixable links."""
        release_slugs = self._get_release_slugs(release)
        for doc in release.documents or []:
            content = self._get_content(doc)
            for slug in self._extract_bare_slugs(content):
                if slug in release_slugs or self._is_registered_pid(slug):
                    return True
        return False

    def fix(self, release):
        """Fix links to existing documents by rewriting with absolute paths."""
        release_slugs = self._get_release_slugs(release)
        for doc in release.documents or []:
            content = self._get_content(doc)
            known_bare = {
                slug
                for slug in self._extract_bare_slugs(content)
                if slug in release_slugs or self._is_registered_pid(slug)
            }
            if not known_bare:
                continue
            doc["body"]["content"] = self._rewrite_bare_slugs(content, known_bare)
        return []

    @staticmethod
    def _get_release_slugs(release):
        """Get the slugs of all the documents in the current release."""
        return {doc.get("slug") for doc in (release.documents or []) if doc.get("slug")}

    @staticmethod
    def _get_content(doc):
        """Return the markdown body content of a document, or None if not applicable."""
        body = doc.get("body") or {}
        if body.get("format") != "md":
            return None
        content = body.get("content")
        if not isinstance(content, str) or not content:
            return None
        return content

    @classmethod
    def _extract_absolute_slugs(cls, content):
        """Return unique slugs from absolute /docs/<slug> links."""
        if not isinstance(content, str) or not content:
            return []
        slugs = []
        for match in MARKDOWN_LINK.finditer(content):
            raw = match.group(1).strip()
            clean_slug = raw.split("#", 1)[0].split("?", 1)[0]
            if not clean_slug.startswith("/docs/"):
                continue
            slug = clean_slug[len("/docs/"):].strip("/")  # fmt: skip
            if slug and slug not in slugs:
                slugs.append(slug)
        return slugs

    @classmethod
    def _extract_bare_slugs(cls, content):
        """Return unique slugs from bare-slug links (no /docs/ prefix)."""
        if not isinstance(content, str) or not content:
            return []
        slugs = []
        for match in MARKDOWN_LINK.finditer(content):
            raw = match.group(1).strip()
            slug_part = raw.split("#", 1)[0].split("?", 1)[0]
            if SLUG_CHARS.match(slug_part) and slug_part not in slugs:
                slugs.append(slug_part)
        return slugs

    @staticmethod
    def _rewrite_bare_slugs(content, known_slugs):
        """Rewrite bare-slug links to absolute /docs/<slug> paths."""

        def rewrite(match):
            link_text = match.group(1)
            raw_target = match.group(2).strip()
            slug_part = raw_target.split("#", 1)[0].split("?", 1)[0]
            if not SLUG_CHARS.match(slug_part) or slug_part not in known_slugs:
                return match.group(0)
            suffix = raw_target[len(slug_part):]  # fmt: skip
            return f"[{link_text}](/docs/{slug_part}{suffix})"

        return re.sub(r"(?<!!)\[([^\]]*)\]\(([^)]+)\)", rewrite, content)

    @staticmethod
    def _is_registered_pid(slug):
        """Return True if slug is a registered docid PID."""
        return (
            PersistentIdentifier.query.filter(
                PersistentIdentifier.pid_type == "docid",
                PersistentIdentifier.pid_value == slug,
                PersistentIdentifier.status == PIDStatus.REGISTERED,
            ).first()
            is not None
        )
