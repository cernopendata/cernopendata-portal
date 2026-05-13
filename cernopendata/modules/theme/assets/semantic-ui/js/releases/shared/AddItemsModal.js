import React, { useState, useRef, useEffect } from "react";
import {
  Modal,
  Form,
  Radio,
  Input,
  Message,
  Button,
  Icon,
} from "semantic-ui-react";
import {
  rewriteDocLinks,
  slugFromFilename,
} from "../documents/rewriteDocLinks";

const CONFIG = {
  documents: {
    multi: true,
    postParseTransform: rewriteDocLinks,
    urlBody: (url) => ({ source: "urls", urls: [url] }),
    validateItem: (doc, file) => {
      const content = doc.body?.content;
      if (typeof content !== "string" || content.endsWith(".md")) {
        return "The JSON must have body.content inlined as markdown text, not a filename pointer.";
      }
      if (!doc._source_filename) {
        doc._source_filename = file.webkitRelativePath || file.name;
      }
      return null;
    },
  },
  records: {
    multi: false,
    postParseTransform: null,
    urlBody: (url) => ({ source: "url", url }),
    validateItem: null,
  },
};

async function parseMultipleFiles(jsonFiles, config, existingItems) {
  const allItems = [];
  for (const file of jsonFiles) {
    let payload;
    try {
      payload = JSON.parse(await file.text());
    } catch (e) {
      throw new Error(`${file.name}: Invalid JSON: ${e.message}`);
    }
    const items = Array.isArray(payload) ? payload : [payload];
    if (config.validateItem) {
      for (const item of items) {
        const err = config.validateItem(item, file);
        if (err) throw new Error(`${file.name}: ${err}`);
      }
    }
    allItems.push(...items);
  }

  if (config.postParseTransform) {
    const incomingSlugs = allItems.map(
      (d) => d.slug || slugFromFilename(d._source_filename),
    );
    const existingSlugs = existingItems.map((d) => d.slug).filter(Boolean);
    const knownSlugs = new Set([...incomingSlugs, ...existingSlugs]);
    return config.postParseTransform(allItems, knownSlugs);
  }
  return { documents: allItems, rewrites: 0, unresolved: 0 };
}

async function parseSingleFile(file, config) {
  let payload;
  try {
    payload = JSON.parse(await file.text());
  } catch (e) {
    throw new Error("Invalid JSON: " + e.message);
  }
  const items = Array.isArray(payload) ? payload : [payload];
  if (config.validateItem) {
    for (const item of items) {
      const err = config.validateItem(item, file);
      if (err) throw new Error(err);
    }
  }
  return items;
}

const capitalize = (s) => s.charAt(0).toUpperCase() + s.slice(1);

export default function AddItemsModal({
  collection,
  open,
  onClose,
  experiment,
  releaseId,
  onAdded,
  existingItems = [],
}) {
  const config = CONFIG[collection];
  const endpoint = `add_${collection}`;
  const [source, setSource] = useState("file");
  const [url, setUrl] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [jsonFileCount, setJsonFileCount] = useState(0);
  const [skippedFileCount, setSkippedFileCount] = useState(0);
  const [folderMode, setFolderMode] = useState(false);

  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    setSource("file");
    setUrl("");
    setError(null);
    setLoading(false);
    setJsonFileCount(0);
    setSkippedFileCount(0);
    setFolderMode(false);

    if (fileInputRef.current) fileInputRef.current.value = "";
  }, [open]);

  const handleFilesChange = () => {
    const files = Array.from(fileInputRef.current?.files ?? []);
    const jsonFiles = files.filter((f) => f.name.endsWith(".json"));
    setJsonFileCount(jsonFiles.length);
    setSkippedFileCount(files.length - jsonFiles.length);
  };

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      const requestBody = await buildRequestBody();
      const response = await fetch(
        `/releases/${experiment}/${releaseId}/${endpoint}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestBody),
        },
      );
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || `Failed to save ${collection}`);
      }
      const result = await response.json();
      onAdded(result[collection] || []);
      onClose();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  async function buildRequestBody() {
    if (source === "url") {
      const trimmed = url.trim();
      if (!trimmed) throw new Error("Please enter a URL.");
      return config.urlBody(trimmed);
    }

    if (config.multi) {
      const allFiles = Array.from(fileInputRef.current?.files ?? []);
      const jsonFiles = allFiles.filter((f) => f.name.endsWith(".json"));
      if (jsonFiles.length === 0)
        throw new Error("No .json files found in selection.");
      const { documents } = await parseMultipleFiles(
        jsonFiles,
        config,
        existingItems,
      );
      return { source: "json", [collection]: documents };
    }

    const file = fileInputRef.current?.files?.[0];
    if (!file) throw new Error("Please select a .json file.");
    const items = await parseSingleFile(file, config);
    return { source: "json", [collection]: items };
  }

  return (
    <Modal open={open} onClose={onClose} closeIcon size="small">
      <Modal.Header>Add {collection}</Modal.Header>
      <Modal.Content>
        <Form loading={loading}>
          <Form.Group grouped>
            <span className="field-group-label">
              {capitalize(collection.slice(0, -1))} source
            </span>
            <Form.Field>
              <Radio
                label="Upload file"
                name="addSource"
                value="file"
                checked={source === "file"}
                onChange={() => setSource("file")}
              />
            </Form.Field>
            <Form.Field>
              <Radio
                label="Load from URL"
                name="addSource"
                value="url"
                checked={source === "url"}
                onChange={() => setSource("url")}
              />
            </Form.Field>
          </Form.Group>

          {source === "file" ? (
            <Form.Field>
              {config.multi ? (
                <div style={{ marginBottom: "0.5em" }}>
                  <Button.Group size="tiny">
                    <Button
                      type="button"
                      active={!folderMode}
                      onClick={() => {
                        setFolderMode(false);
                        setJsonFileCount(0);
                        setSkippedFileCount(0);
                        if (fileInputRef.current)
                          fileInputRef.current.value = "";
                      }}
                    >
                      File upload
                    </Button>
                    <Button
                      type="button"
                      active={folderMode}
                      onClick={() => {
                        setFolderMode(true);
                        setJsonFileCount(0);
                        setSkippedFileCount(0);
                        if (fileInputRef.current)
                          fileInputRef.current.value = "";
                      }}
                    >
                      Folder upload
                    </Button>
                  </Button.Group>
                </div>
              ) : (
                <label htmlFor="add-items-file-input">File</label>
              )}
              <input
                key={config.multi ? (folderMode ? "folder" : "file") : "single"}
                id="add-items-file-input"
                aria-label="Choose files"
                type="file"
                accept=".json"
                ref={fileInputRef}
                onChange={handleFilesChange}
                {...(config.multi ? { multiple: true } : {})}
                {...(config.multi && folderMode ? { webkitdirectory: "" } : {})}
              />
              {config.multi && jsonFileCount > 0 && (
                <Message info style={{ marginTop: "0.5em" }}>
                  {jsonFileCount} JSON file{jsonFileCount !== 1 ? "s" : ""}{" "}
                  selected
                  {skippedFileCount > 0 &&
                    ` — ${skippedFileCount} non-JSON file${skippedFileCount !== 1 ? "s" : ""} will be skipped`}
                </Message>
              )}
            </Form.Field>
          ) : (
            <Form.Field>
              <label htmlFor="add-items-url-input">URL</label>
              <Input
                id="add-items-url-input"
                fluid
                type="url"
                placeholder="https://raw.githubusercontent.com/..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </Form.Field>
          )}

          {error && <Message negative>{error}</Message>}
        </Form>
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          primary
          disabled={source === "file" ? jsonFileCount === 0 : !url.trim()}
          onClick={handleSubmit}
        >
          <Icon name="plus" /> Add {collection}
        </Button>
      </Modal.Actions>
    </Modal>
  );
}
