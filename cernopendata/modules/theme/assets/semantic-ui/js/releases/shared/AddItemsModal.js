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

const CONFIG = {
  documents: {
    urlBody: (url) => ({ source: "urls", urls: [url] }),
    validateItem: (doc, file) => {
      const content = doc.body?.content;
      if (typeof content !== "string" || content.endsWith(".md")) {
        return "The JSON must have body.content inlined as markdown text, not a filename pointer.";
      }
      if (!doc._source_filename) {
        doc._source_filename = file.name;
      }
      return null;
    },
  },
  records: {
    urlBody: (url) => ({ source: "url", url }),
    validateItem: null,
  },
};

const capitalize = (s) => s.charAt(0).toUpperCase() + s.slice(1);

export default function AddItemsModal({
  collection,
  open,
  onClose,
  experiment,
  releaseId,
  onAdded,
}) {
  const config = CONFIG[collection];
  const endpoint = `add_${collection}`;
  const [source, setSource] = useState("file");
  const [url, setUrl] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filesChosen, setFilesChosen] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    setSource("file");
    setUrl("");
    setError(null);
    setLoading(false);
    setFilesChosen(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, [open]);

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);

    try {
      let requestBody;

      if (source === "file") {
        const file = fileInputRef.current?.files?.[0];
        if (!file) {
          setError("Please select a .json file.");
          return;
        }

        let payload;
        try {
          payload = JSON.parse(await file.text());
        } catch (e) {
          setError("Invalid JSON: " + e.message);
          return;
        }

        const items = Array.isArray(payload) ? payload : [payload];
        if (config.validateItem) {
          for (const item of items) {
            const err = config.validateItem(item, file);
            if (err) {
              setError(err);
              return;
            }
          }
        }

        requestBody = { source: "json", [collection]: items };
      } else {
        const trimmed = url.trim();
        if (!trimmed) {
          setError("Please enter a URL.");
          return;
        }
        requestBody = config.urlBody(trimmed);
      }

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
              <label htmlFor="add-items-file-input">File</label>
              <input
                id="add-items-file-input"
                type="file"
                accept=".json"
                ref={fileInputRef}
                onChange={() =>
                  setFilesChosen(!!fileInputRef.current?.files?.length)
                }
              />
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
          disabled={source === "file" ? !filesChosen : !url.trim()}
          onClick={handleSubmit}
        >
          <Icon name="plus" /> Add {collection}
        </Button>
      </Modal.Actions>
    </Modal>
  );
}
