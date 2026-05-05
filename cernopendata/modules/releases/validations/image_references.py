"""Validation that all images referenced in document bodies are available."""

import re
from pathlib import Path
from urllib.parse import unquote

from flask import current_app

import cernopendata

from .base import Validation


class ValidImageReferences(Validation):
    """Check that images referenced in a markdown body are available."""

    name = "Valid image references"
    error_message = (
        "Some images referenced in document bodies are not available. "
        "Upload the missing images or correct the path."
    )
    applies_to = {"documents"}

    def validate(self, release):
        """Walk every markdown body and check each image reference."""
        errors = []
        uploaded_image_storage = Path(
            current_app.config["CERNOPENDATA_IMAGES_PATH"]
        ).resolve()
        repo_images = (
            Path(cernopendata.__file__).parent / "modules" / "theme" / "static" / "docs"
        ).resolve()
        for i, doc in enumerate(release.documents or []):
            body = doc.get("body") or {}
            if body.get("format") != "md":
                continue
            content = body.get("content")
            if not isinstance(content, str) or not content:
                continue
            for url in self._extract_image_urls(content):
                error = self._check_url(url, uploaded_image_storage, repo_images)
                if error:
                    errors.append(f"Document {i + 1}: {error}")
        return errors

    @staticmethod
    def _extract_image_urls(content):
        """Return image URLs referenced in the content."""
        html_urls = re.findall(
            r"""<img\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']""",
            content,
            re.IGNORECASE,
        )
        md_urls = re.findall(r"!\[[^\]]*\]\(\s*([^)\s]+)", content)
        image_urls = []
        for url in (*html_urls, *md_urls):
            url = url.strip()
            if url and url not in image_urls:
                image_urls.append(url)
        return image_urls

    @staticmethod
    def _check_url(url, uploaded_image_storage, repo_images):
        """Return an error string if the URL points to a missing local image."""
        cleaned_url = url.split("#", 1)[0].split("?", 1)[0]
        for prefix, root in (
            ("/static/upload/", uploaded_image_storage),
            ("/static/docs/", repo_images),
        ):
            if not cleaned_url.startswith(prefix):
                continue
            relative_path = unquote(cleaned_url[len(prefix):])  # fmt: skip
            if not relative_path:
                return f"image referenced in body has invalid path: {url}"
            full_path = (root / relative_path).resolve()
            try:
                full_path.relative_to(root)
            except ValueError:
                return f"image referenced in body has invalid path: {url}"
            if not full_path.is_file():
                return f"image referenced in body not found: {url}"
            return None
        if cleaned_url.startswith("/") and not cleaned_url.startswith("//"):
            return (
                f"image referenced in body uses an unrecognised local path: {url} "
                "(use /static/upload/<slug>/<file> for uploaded images)"
            )
        return None
