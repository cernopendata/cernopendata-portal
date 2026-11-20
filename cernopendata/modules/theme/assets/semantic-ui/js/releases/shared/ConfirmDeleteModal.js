import React, { useState, useEffect } from "react";
import { Modal, Button, Icon, Message } from "semantic-ui-react";

export default function ConfirmDeleteModal({
  open,
  itemLabel,
  details,
  onConfirm,
  onClose,
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setError(null);
  }, [open]);

  const handleConfirm = async () => {
    setLoading(true);
    setError(null);
    try {
      await onConfirm();
      onClose();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} closeIcon size="tiny">
      <Modal.Header>Confirm deletion</Modal.Header>
      <Modal.Content>
        {error && (
          <Message negative>
            <Icon name="warning circle" /> {error}
          </Message>
        )}
        <p>
          Are you sure you want to delete {itemLabel} from the release?
          {details && ` ${details}`}
        </p>
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          color="red"
          loading={loading}
          disabled={loading}
          onClick={handleConfirm}
        >
          <Icon name="trash" /> Delete
        </Button>
      </Modal.Actions>
    </Modal>
  );
}
