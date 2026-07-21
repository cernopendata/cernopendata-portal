import React, { useState, useEffect } from "react";
import { Modal, Form, Input, Button, Icon, Message } from "semantic-ui-react";
import { fetchJson } from "../shared/utils";

export default function EditImageModal({
  image,
  onClose,
  experiment,
  releaseId,
  onRenamed,
  onDeleted,
}) {
  const [name, setName] = useState("");
  const [error, setError] = useState(null);

  useEffect(() => {
    if (image) setName(image.filename);
    setError(null);
  }, [image]);

  const handleDelete = async () => {
    if (!window.confirm(`Delete ${image.filename}?`)) return;
    setError(null);
    try {
      await fetchJson(
        `/releases/${experiment}/${releaseId}/images/${image.parent_slug}/${image.filename}`,
        { method: "DELETE" },
      );
      onDeleted(image);
      onClose();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleRename = async () => {
    const newName = name.trim();
    if (!newName || newName === image.filename) return;
    setError(null);
    try {
      const result = await fetchJson(
        `/releases/${experiment}/${releaseId}/images/${image.parent_slug}/${image.filename}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filename: newName }),
        },
      );
      onRenamed(image, result.image);
      onClose();
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <Modal open={!!image} onClose={onClose} closeIcon size="small">
      <Modal.Header>Edit Image</Modal.Header>
      <Modal.Content>
        {error && (
          <Message negative>
            <Icon name="warning circle" /> {error}
          </Message>
        )}
        <Form>
          <Form.Field>
            <label htmlFor="image-edit-name">Filename</label>
            <Input
              id="image-edit-name"
              fluid
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </Form.Field>
        </Form>
      </Modal.Content>
      <Modal.Actions>
        <Button floated="left" color="red" onClick={handleDelete}>
          <Icon name="trash" /> Delete
        </Button>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          primary
          disabled={!name.trim() || name.trim() === image?.filename}
          onClick={handleRename}
        >
          <Icon name="save" /> Save
        </Button>
      </Modal.Actions>
    </Modal>
  );
}
