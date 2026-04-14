import React, { useState, useRef } from "react";
import {
  Table,
  Button,
  Icon,
  Pagination,
  Modal,
  Form,
  TextArea,
  Tab,
  Radio,
  Input,
  Message,
} from "semantic-ui-react";

export default function DocumentsTable({
  experiment,
  releaseId,
  initialDocuments = [],
  editDisabled = false,
  viewDisabled = false,
}) {
  const [documents, setDocuments] = useState(initialDocuments);
  const [editingDoc, setEditingDoc] = useState(null);
  const [metaDataBuffer, setMetaDataBuffer] = useState("");
  const [bodyBuffer, setBodyBuffer] = useState("");

  const [page, setPage] = useState(0);
  const pageSize = 5;
  const totalPages = Math.max(1, Math.ceil(documents.length / pageSize));
  const visible = documents.slice(page * pageSize, (page + 1) * pageSize);

  const [addModalOpen, setAddModalOpen] = useState(false);
  const [addSource, setAddSource] = useState("file");
  const [addUrl, setAddUrl] = useState("");
  const [addError, setAddError] = useState(null);
  const [addLoading, setAddLoading] = useState(false);
  const fileInputRef = useRef(null);
  const [filesChosen, setFilesChosen] = useState(false);

  const resetAddModal = () => {
    setAddSource("file");
    setAddUrl("");
    setAddError(null);
    setAddLoading(false);
    setFilesChosen(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleAddOpen = () => {
    resetAddModal();
    setAddModalOpen(true);
  };

  const handleAddSubmit = async () => {
    setAddError(null);
    setAddLoading(true);

    try {
      let requestBody;

      if (addSource === "file") {
        const file = fileInputRef.current?.files?.[0];
        if (!file) {
          setAddError("Please select a .json file.");
          return;
        }

        let payload;
        try {
          payload = JSON.parse(await file.text());
        } catch (e) {
          setAddError("Invalid JSON: " + e.message);
          return;
        }

        const items = Array.isArray(payload) ? payload : [payload];
        for (const doc of items) {
          if (
            typeof doc.body?.content !== "string" ||
            doc.body.content.endsWith(".md")
          ) {
            setAddError(
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
        const url = addUrl.trim();
        if (!url) {
          setAddError("Please enter a .json URL.");
          return;
        }
        if (!url.split("?")[0].endsWith(".json")) {
          setAddError("The URL must point to a .json file.");
          return;
        }
        requestBody = { source: "urls", urls: [url] };
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
      setDocuments((prev) => [...prev, ...result.documents]);
      setAddModalOpen(false);
    } catch (e) {
      setAddError(e.message);
    } finally {
      setAddLoading(false);
    }
  };

  const openEditModal = (doc) => {
    setEditingDoc(doc);
    const { body, ...rest } = doc;
    const metaData = { ...rest };
    if (body) {
      metaData.body = { ...body };
      delete metaData.body.content;
    }
    setMetaDataBuffer(JSON.stringify(metaData, null, 2));
    setBodyBuffer(body?.content || "");
  };

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
        `/releases/${experiment}/${releaseId}/documents/${editingDoc.slug}`,
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

    const idx = documents.indexOf(editingDoc);
    if (idx !== -1) {
      const next = [...documents];
      next[idx] = updated;
      setDocuments(next);
    }
    setEditingDoc(null);
  };

  return (
    <>
      <div>
        <div className="records-table-toolbar">
          <div className="records-table-toolbar-buttons">
            <Button
              className="blue"
              disabled={editDisabled}
              onClick={handleAddOpen}
            >
              <Icon name="plus" /> Add Document
            </Button>
          </div>
        </div>
        <Table celled compact>
          <Table.Header>
            <Table.Row>
              <Table.HeaderCell>Slug</Table.HeaderCell>
              <Table.HeaderCell>Title</Table.HeaderCell>
              <Table.HeaderCell>Type</Table.HeaderCell>
              <Table.HeaderCell collapsing>Actions</Table.HeaderCell>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {visible.length === 0 ? (
              <Table.Row>
                <Table.Cell colSpan="4" textAlign="center">
                  No documents in this release.
                </Table.Cell>
              </Table.Row>
            ) : (
              visible.map((doc, i) => (
                <Table.Row key={doc.slug || i}>
                  <Table.Cell className="no-glossary">
                    {doc.slug || "—"}
                  </Table.Cell>
                  <Table.Cell>{doc.title || "—"}</Table.Cell>
                  <Table.Cell>{doc.type?.primary || "—"}</Table.Cell>
                  <Table.Cell collapsing>
                    <Button
                      className="blue"
                      disabled={editDisabled}
                      onClick={() => openEditModal(doc)}
                    >
                      Edit
                    </Button>
                    <Button
                      className="blue"
                      disabled={viewDisabled}
                      as="a"
                      onClick={() => {
                        if (doc.slug) {
                          window.location.href = `/docs/${doc.slug}`;
                        }
                      }}
                    >
                      View
                    </Button>
                  </Table.Cell>
                </Table.Row>
              ))
            )}
          </Table.Body>
        </Table>

        {documents.length > pageSize && (
          <div className="records-table-pagination">
            <Pagination
              totalPages={totalPages}
              activePage={page + 1}
              onPageChange={(_, d) => setPage(d.activePage - 1)}
            />
          </div>
        )}
      </div>

      <Modal
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        closeIcon
        size="small"
      >
        <Modal.Header>Add a new document</Modal.Header>
        <Modal.Content>
          <Form loading={addLoading}>
            <Form.Group grouped>
              <span className="field-group-label">Document source</span>
              <Form.Field>
                <Radio
                  label="Upload files"
                  name="addSource"
                  value="file"
                  checked={addSource === "file"}
                  onChange={() => setAddSource("file")}
                />
              </Form.Field>
              <Form.Field>
                <Radio
                  label="Load from URLs"
                  name="addSource"
                  value="url"
                  checked={addSource === "url"}
                  onChange={() => setAddSource("url")}
                />
              </Form.Field>
            </Form.Group>

            {addSource === "file" ? (
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
                  value={addUrl}
                  onChange={(e) => setAddUrl(e.target.value)}
                />
              </Form.Field>
            )}

            {addError && <Message negative>{addError}</Message>}
          </Form>
        </Modal.Content>
        <Modal.Actions>
          <Button onClick={() => setAddModalOpen(false)}>Cancel</Button>
          <Button
            primary
            disabled={addSource === "file" ? !filesChosen : !addUrl.trim()}
            onClick={handleAddSubmit}
          >
            <Icon name="plus" /> Add document
          </Button>
        </Modal.Actions>
      </Modal>

      <Modal
        open={!!editingDoc}
        onClose={() => setEditingDoc(null)}
        closeIcon
        size="large"
      >
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
              ]}
            />
          </Form>
        </Modal.Content>
        <Modal.Actions>
          <Button onClick={() => setEditingDoc(null)}>Cancel</Button>
          <Button primary onClick={handleSave}>
            <Icon name="save" /> Save
          </Button>
        </Modal.Actions>
      </Modal>
    </>
  );
}
