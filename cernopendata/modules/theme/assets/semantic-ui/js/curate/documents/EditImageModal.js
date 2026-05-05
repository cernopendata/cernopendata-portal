import React, { useState, useEffect } from "react";
import { Modal, Form, Input, Button, Icon } from "semantic-ui-react";

export default function EditImageModal({
  image,
  onClose,
  experiment,
  releaseId,
  onRenamed,
  onDeleted,
}) {
  const [name, setName] = useState("");

  useEffect(() => {
    if (image) setName(image.filename);
  }, [image]);

  const handleDelete = async () => {
    if (!window.confirm(`Delete ${image.filename}?`)) return;
    try {
      const response = await fetch(
        `/releases/${experiment}/${releaseId}/images/${image.parent_slug}/${image.filename}`,
        { method: "DELETE" },
      );
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        alert("Failed to delete: " + (err.error || response.statusText));
        return;
      }
      onDeleted(image);
      onClose();
    } catch (e) {
      alert("Failed to delete: " + e.message);
    }
  };

  const handleRename = async () => {
    const newName = name.trim();
    if (!newName || newName === image.filename) return;
    try {
      const response = await fetch(
        `/releases/${experiment}/${releaseId}/images/${image.parent_slug}/${image.filename}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filename: newName }),
        },
      );
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        alert("Failed to rename: " + (err.error || response.statusText));
        return;
      }
      const result = await response.json();
      onRenamed(image, result.image);
      onClose();
    } catch (e) {
      alert("Failed to rename: " + e.message);
    }
  };

  return (
    <Modal open={!!image} onClose={onClose} closeIcon size="small">
      <Modal.Header>Edit Image</Modal.Header>
      <Modal.Content>
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
        <Button floated="left" className="red" onClick={handleDelete}>
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
