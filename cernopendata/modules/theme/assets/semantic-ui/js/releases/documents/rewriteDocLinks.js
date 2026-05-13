function splitSuffix(url) {
  // split into [path, anchor/query] e.g. "/docs/foo#bar" → ["/docs/foo", "#bar"]
  const match = url.match(/^([^#?]*)([#?][\s\S]*)$/);
  return match ? [match[1], match[2]] : [url, ""];
}

function rewriteLink(url, knownSlugs) {
  const [path, suffix] = splitSuffix(url.trim());

  // leave external links, anchors, and absolute paths unchanged
  if (/^(https?:|#)/.test(url) || path.startsWith("/")) {
    return { url, changed: false };
  }

  // rewrite relative paths (./slug, ../folder/slug)
  if (path.startsWith("./") || path.startsWith("../")) {
    return { url: `/docs/${slugFromFilename(path)}${suffix}`, changed: true };
  }

  // rewrite bare slugs only when they match a known doc
  if (!path.includes("/") && path.length > 0 && knownSlugs.has(path)) {
    return { url: `/docs/${path}${suffix}`, changed: true };
  }

  return { url, changed: false };
}

export function slugFromFilename(filename) {
  const base = (filename || "").split("/").pop();
  return base.endsWith(".json") ? base.slice(0, -5) : base;
}

export function rewriteDocLinks(documents, knownSlugs) {
  const rewritten = documents.map((doc) => {
    const content = doc.body?.content;
    if (typeof content !== "string") return doc;

    let docChanged = false;
    const newContent = content.replace(
      /(\[[^\]]*\]\()([^)]+)(\))/g,
      (match, open, url, close) => {
        const result = rewriteLink(url, knownSlugs);
        if (!result.changed) return match;
        docChanged = true;
        return open + result.url + close;
      },
    );

    if (!docChanged) return doc;
    return { ...doc, body: { ...doc.body, content: newContent } };
  });

  return { documents: rewritten };
}
