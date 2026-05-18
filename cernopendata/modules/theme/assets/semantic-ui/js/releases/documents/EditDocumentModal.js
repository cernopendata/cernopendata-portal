import React, { useState, useEffect } from "react";
import { Modal, Form, TextArea, Tab, Button, Icon } from "semantic-ui-react";
import PreviewTab from "../shared/PreviewTab";

export default function EditDocumentModal({
  doc,
  onClose,
  experiment,
  releaseId,
  onSaved,
}) {
  const [metaDataBuffer, setMetaDataBuffer] = useState("");
  const [bodyBuffer, setBodyBuffer] = useState("");

  useEffect(() => {
    if (!doc) return;
    const { body, ...rest } = doc;
    const metaData = { ...rest };
    if (body) {
      metaData.body = { ...body };
      delete metaData.body.content;
    }
    setMetaDataBuffer(JSON.stringify(metaData, null, 2));
    setBodyBuffer(body?.content || "");
  }, [doc]);

  const handleSave = async () => {
    let updated;
    try {
      updated = JSON.parse(metaDataBuffer);
    } catch (e) {
      alert("Invalid JSON: " + e.message);
      return;
    }
    updated.body = {
      format: "md",
      ...(updated.body || {}),
      content: bodyBuffer,
    };

    try {
      const response = await fetch(
        `/releases/${experiment}/${releaseId}/documents/${doc.slug}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ document: updated }),
        },
      );
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        alert("Failed to save: " + (err.error || response.statusText));
        return;
      }
    } catch (e) {
      alert("Failed to save: " + e.message);
      return;
    }

    onSaved(updated);
    onClose();
  };

  const previewData = (() => {
    try {
      const meta = JSON.parse(metaDataBuffer);
      return {
        ...meta,
        body: { format: "md", ...(meta.body || {}), content: bodyBuffer },
      };
    } catch {
      return null;
    }
  })();

  return (
    <Modal open={!!doc} onClose={onClose} closeIcon size="large">
      <Modal.Header>Edit Document</Modal.Header>
      <Modal.Content scrolling>
        <Form>
          <Tab
            panes={[
              {
                menuItem: "Metadata",
                render: () => (
                  <Tab.Pane>
                    <TextArea
                      rows={20}
                      value={metaDataBuffer}
                      onChange={(e) => setMetaDataBuffer(e.target.value)}
                      className="doc-textarea"
                    />
                  </Tab.Pane>
                ),
              },
              {
                menuItem: "Content",
                render: () => (
                  <Tab.Pane>
                    <TextArea
                      rows={20}
                      value={bodyBuffer}
                      onChange={(e) => setBodyBuffer(e.target.value)}
                      className="doc-textarea"
                    />
                  </Tab.Pane>
                ),
              },
              {
                menuItem: "Preview",
                render: () => (
                  <Tab.Pane>
                    {previewData ? (
                      <PreviewTab
                        endpoint="/releases/preview_document"
                        data={previewData}
                      />
                    ) : (
                      <p>
                        Invalid JSON in Metadata tab — fix it to see the
                        preview.
                      </p>
                    )}
                  </Tab.Pane>
                ),
              },
            ]}
          />
        </Form>
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={onClose}>Cancel</Button>
        <Button primary onClick={handleSave}>
          <Icon name="save" /> Save
        </Button>
      </Modal.Actions>
    </Modal>
  );
}
