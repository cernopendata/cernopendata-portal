from unittest.mock import MagicMock, patch

import pytest

from cernopendata.modules.releases.validations.doc_links import ValidDocLinks


def _doc(content, fmt="md", slug=None):
    doc = {"body": {"content": content, "format": fmt}}
    if slug:
        doc["slug"] = slug
    return doc


def _release(*docs):
    release = MagicMock()
    release.documents = list(docs)
    return release


def _validator_no_pids():
    """Return a ValidDocLinks instance whose PID check always returns False."""
    v = ValidDocLinks()
    v._is_registered_pid = lambda _: False
    return v


def test_passes_when_target_slug_in_release():
    release = _release(
        _doc("[see other](/docs/lhcb-stripping21-bhadron-foo)", slug="my-doc"),
        _doc("target doc", slug="lhcb-stripping21-bhadron-foo"),
    )
    assert _validator_no_pids().validate(release) == []


def test_passes_when_target_is_published_pid():
    release = _release(_doc("[see other](/docs/published-slug)", slug="my-doc"))
    v = ValidDocLinks()
    with patch.object(v, "_is_registered_pid", return_value=True):
        assert v.validate(release) == []


def test_fails_when_target_missing():
    release = _release(_doc("[see other](/docs/missing-slug)", slug="my-doc"))
    errors = _validator_no_pids().validate(release)
    assert len(errors) == 1
    assert "Document 1" in errors[0]
    assert "/docs/missing-slug" in errors[0]
    assert "not found" in errors[0]


def test_ignores_external_http_url():
    release = _release(_doc("[ext](https://example.com/docs/foo)", slug="my-doc"))
    assert _validator_no_pids().validate(release) == []


def test_ignores_mailto():
    release = _release(_doc("[mail](mailto:foo@example.com)", slug="my-doc"))
    assert _validator_no_pids().validate(release) == []


def test_ignores_fragment_only_link():
    release = _release(_doc("[anchor](#section)", slug="my-doc"))
    assert _validator_no_pids().validate(release) == []


def test_ignores_record_link():
    release = _release(_doc("[record](/record/1234)", slug="my-doc"))
    assert _validator_no_pids().validate(release) == []


def test_ignores_static_link():
    release = _release(_doc("[img](/static/upload/foo/bar.png)", slug="my-doc"))
    assert _validator_no_pids().validate(release) == []


def test_ignores_image_links():
    """Markdown image syntax ![text](url) must not be treated as a doc link."""
    release = _release(_doc("![fig](/docs/missing-slug)", slug="my-doc"))
    assert _validator_no_pids().validate(release) == []


def test_skips_non_md_format():
    release = _release(_doc("[see](/docs/missing-slug)", fmt="html", slug="my-doc"))
    assert _validator_no_pids().validate(release) == []


def test_skips_empty_content():
    release = _release({"body": {"format": "md", "content": ""}})
    assert _validator_no_pids().validate(release) == []


def test_fragment_and_query_stripped_before_lookup():
    """#anchor and ?query are stripped; the slug part must match."""
    release = _release(
        _doc("[see](/docs/target-slug#section?v=2)", slug="my-doc"),
        _doc("body", slug="target-slug"),
    )
    assert _validator_no_pids().validate(release) == []


def test_duplicate_links_reported_once():
    content = "[a](/docs/missing)\n[b](/docs/missing)"
    release = _release(_doc(content, slug="my-doc"))
    errors = _validator_no_pids().validate(release)
    assert len(errors) == 1


def test_per_document_indexing():
    release = _release(
        _doc("no links here", slug="doc-1"),
        _doc("[broken](/docs/missing-slug)", slug="doc-2"),
    )
    errors = _validator_no_pids().validate(release)
    assert len(errors) == 1
    assert errors[0].startswith("Document 2:")


def test_extract_absolute_slugs_ignores_non_docs_links():
    slugs = ValidDocLinks._extract_absolute_slugs(
        "[a](/record/1)\n[b](/docs/my-slug)\n[c](https://example.com)"
    )
    assert slugs == ["my-slug"]


def test_extract_absolute_slugs_deduplicates():
    slugs = ValidDocLinks._extract_absolute_slugs("[a](/docs/foo)\n[b](/docs/foo)")
    assert slugs == ["foo"]


def test_flags_bare_slug_with_known_target_as_fixable():
    release = _release(
        _doc("[see](lhcb-stripping21-bhadron-foo)", slug="my-doc"),
        _doc("target", slug="lhcb-stripping21-bhadron-foo"),
    )
    errors = _validator_no_pids().validate(release)
    assert len(errors) == 1
    assert "bare-slug" in errors[0]
    assert "lhcb-stripping21-bhadron-foo" in errors[0]
    assert "should be /docs/" in errors[0]


def test_flags_bare_slug_matching_published_pid_as_fixable():
    release = _release(_doc("[see](published-slug)", slug="my-doc"))
    validator = ValidDocLinks()
    with patch.object(validator, "_is_registered_pid", return_value=True):
        errors = validator.validate(release)
    assert len(errors) == 1
    assert "bare-slug" in errors[0]
    assert "should be /docs/" in errors[0]


def test_flags_bare_slug_with_no_match_as_non_fixable():
    release = _release(_doc("[see](unknown-slug)", slug="my-doc"))
    errors = _validator_no_pids().validate(release)
    assert len(errors) == 1
    assert "unknown-slug" in errors[0]
    assert "does not resolve" in errors[0]
    assert "bare-slug" not in errors[0]


def test_bare_slug_ignores_paths_with_slash():
    release = _release(_doc("[see](some/path)", slug="my-doc"))
    assert _validator_no_pids().validate(release) == []


def test_bare_slug_ignores_targets_with_colon():
    release = _release(_doc("[see](proto:value)", slug="my-doc"))
    assert _validator_no_pids().validate(release) == []


def test_bare_slug_ignores_targets_with_dot_extension():
    release = _release(_doc("[see](some-file.md)", slug="my-doc"))
    assert _validator_no_pids().validate(release) == []


def test_fix_rewrites_matched_bare_slugs():
    doc = _doc("[see](target-slug)", slug="my-doc")
    target = _doc("content", slug="target-slug")
    release = _release(doc, target)
    _validator_no_pids().fix(release)
    assert release.documents[0]["body"]["content"] == "[see](/docs/target-slug)"


def test_fix_preserves_anchor_suffix():
    doc = _doc("[see](target-slug#section)", slug="my-doc")
    target = _doc("content", slug="target-slug")
    release = _release(doc, target)
    _validator_no_pids().fix(release)
    assert release.documents[0]["body"]["content"] == "[see](/docs/target-slug#section)"


def test_fix_preserves_query_suffix():
    doc = _doc("[see](target-slug?v=2)", slug="my-doc")
    target = _doc("content", slug="target-slug")
    release = _release(doc, target)
    _validator_no_pids().fix(release)
    assert release.documents[0]["body"]["content"] == "[see](/docs/target-slug?v=2)"


def test_fix_leaves_unmatched_bare_slugs_alone():
    doc = _doc("[see](unknown-slug)", slug="my-doc")
    release = _release(doc)
    _validator_no_pids().fix(release)
    assert release.documents[0]["body"]["content"] == "[see](unknown-slug)"


def test_fix_returns_empty_list():
    doc = _doc("[see](target-slug)", slug="my-doc")
    target = _doc("content", slug="target-slug")
    release = _release(doc, target)
    assert _validator_no_pids().fix(release) == []


def test_mixed_body_with_canonical_and_bare_forms():
    content = "[a](/docs/canonical-slug)\n[b](bare-slug)"
    release = _release(
        _doc(content, slug="my-doc"),
        _doc("", slug="canonical-slug"),
        _doc("", slug="bare-slug"),
    )
    errors = _validator_no_pids().validate(release)
    assert len(errors) == 1
    assert "bare-slug" in errors[0]
    assert "should be /docs/" in errors[0]


def test_fixable_true_when_bare_slug_resolves():
    release = _release(
        _doc("[see](target-slug)", slug="my-doc"),
        _doc("content", slug="target-slug"),
    )
    assert _validator_no_pids().fixable(release) is True


def test_fixable_true_when_bare_slug_matches_published_pid():
    release = _release(_doc("[see](published-slug)", slug="my-doc"))
    validator = ValidDocLinks()
    with patch.object(validator, "_is_registered_pid", return_value=True):
        assert validator.fixable(release) is True


def test_fixable_false_when_only_unresolved_links():
    release = _release(
        _doc("[a](/docs/missing-slug)\n[b](unknown-bare)", slug="my-doc"),
    )
    assert _validator_no_pids().fixable(release) is False


def test_fix_leaves_non_slug_links_alone_when_rewriting():
    """When rewriting matched bare slugs, other (non-slug) links must stay untouched."""
    content = "[a](target-slug)\n[b](https://example.com)\n[c](/record/123)"
    doc = _doc(content, slug="my-doc")
    target = _doc("content", slug="target-slug")
    release = _release(doc, target)
    _validator_no_pids().fix(release)
    assert release.documents[0]["body"]["content"] == (
        "[a](/docs/target-slug)\n[b](https://example.com)\n[c](/record/123)"
    )


def test_is_registered_pid_true_when_query_matches():
    with patch(
        "cernopendata.modules.releases.validations.doc_links.PersistentIdentifier"
    ) as pid:
        pid.query.filter.return_value.first.return_value = MagicMock()
        assert ValidDocLinks._is_registered_pid("some-slug") is True


def test_is_registered_pid_false_when_query_returns_none():
    with patch(
        "cernopendata.modules.releases.validations.doc_links.PersistentIdentifier"
    ) as pid:
        pid.query.filter.return_value.first.return_value = None
        assert ValidDocLinks._is_registered_pid("some-slug") is False
