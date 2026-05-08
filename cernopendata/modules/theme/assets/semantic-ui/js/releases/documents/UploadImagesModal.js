import React, { useState, useRef, useEffect } from "react";
import {
  Modal,
  Form,
  Dropdown,
  Message,
  Button,
  Icon,
} from "semantic-ui-react";

export default function UploadImagesModal({
  open,
  onClose,
  experiment,
  releaseId,
  documents,
  onUploaded,
}) {
  const [parentSlug, setParentSlug] = useState("");
  const [filesChosen, setFilesChosen] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    setParentSlug(documents.length === 1 ? documents[0].slug : "");
    setFilesChosen(false);
    setError(null);
    setLoading(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, [open, documents]);

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);

    try {
      const files = fileInputRef.current?.files;
      if (!files || files.length === 0) {
        setError("Please select at least one image.");
        return;
      }
      if (!parentSlug) {
        setError("Please choose a parent document.");
        return;
      }

      const formData = new FormData();
      formData.append("parent_slug", parentSlug);
      for (const file of files) {
        formData.append("images", file);
      }

      const response = await fetch(
        `/releases/${experiment}/${releaseId}/upload_image`,
        { method: "POST", body: formData },
      );

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || "Failed to upload images");
      }

      const result = await response.json();
      onUploaded(result.images || []);
      onClose();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} closeIcon size="small">
      <Modal.Header>Upload images</Modal.Header>
      <Modal.Content>
        <Form loading={loading}>
          <Form.Field>
            <label htmlFor="image-parent-slug">Parent document</label>
            {documents.length === 1 ? (
              <div id="image-parent-slug">
                {`${documents[0].slug} — ${documents[0].title || "(untitled)"}`}
              </div>
            ) : (
              <Dropdown
                id="image-parent-slug"
                fluid
                selection
                placeholder="Choose a document"
                options={documents.map((doc) => ({
                  key: doc.slug,
                  value: doc.slug,
                  text: `${doc.slug} — ${doc.title || "(untitled)"}`,
                }))}
                value={parentSlug}
                onChange={(_, { value }) => setParentSlug(value)}
              />
            )}
          </Form.Field>
          <Form.Field>
            <label htmlFor="image-files-input">Images</label>
            <input
              id="image-files-input"
              type="file"
              accept=".png,.gif,.jpg,.jpeg"
              multiple
              ref={fileInputRef}
              onChange={() =>
                setFilesChosen(!!fileInputRef.current?.files?.length)
              }
            />
          </Form.Field>
          {error && <Message negative>{error}</Message>}
        </Form>
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          primary
          disabled={!filesChosen || !parentSlug}
          onClick={handleSubmit}
        >
          <Icon name="upload" /> Upload
        </Button>
      </Modal.Actions>
    </Modal>
  );
}
