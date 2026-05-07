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

export default function AddDocumentModal({
  open,
  onClose,
  experiment,
  releaseId,
  onAdded,
}) {
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
        for (const doc of items) {
          if (
            typeof doc.body?.content !== "string" ||
            doc.body.content.endsWith(".md")
          ) {
            setError(
              "The JSON must have body.content inlined as markdown text, not a filename pointer.",
            );
            return;
          }
          if (!doc._source_filename) {
            doc._source_filename = file.name;
          }
        }

        requestBody = { source: "json", documents: items };
      } else {
        const trimmed = url.trim();
        if (!trimmed) {
          setError("Please enter a .json URL.");
          return;
        }
        if (!trimmed.split("?")[0].endsWith(".json")) {
          setError("The URL must point to a .json file.");
          return;
        }
        requestBody = { source: "urls", urls: [trimmed] };
      }

      const response = await fetch(
        `/releases/${experiment}/${releaseId}/add_documents`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestBody),
        },
      );

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || "Failed to save documents");
      }

      const result = await response.json();
      onAdded(result.documents || []);
      onClose();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} closeIcon size="small">
      <Modal.Header>Add a new document</Modal.Header>
      <Modal.Content>
        <Form loading={loading}>
          <Form.Group grouped>
            <span className="field-group-label">Document source</span>
            <Form.Field>
              <Radio
                label="Upload files"
                name="addSource"
                value="file"
                checked={source === "file"}
                onChange={() => setSource("file")}
              />
            </Form.Field>
            <Form.Field>
              <Radio
                label="Load from URLs"
                name="addSource"
                value="url"
                checked={source === "url"}
                onChange={() => setSource("url")}
              />
            </Form.Field>
          </Form.Group>

          {source === "file" ? (
            <Form.Field>
              <label htmlFor="doc-files-input">File</label>
              <input
                id="doc-files-input"
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
              <label htmlFor="doc-url-input">URL</label>
              <Input
                id="doc-url-input"
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
          <Icon name="plus" /> Add document
        </Button>
      </Modal.Actions>
    </Modal>
  );
}
