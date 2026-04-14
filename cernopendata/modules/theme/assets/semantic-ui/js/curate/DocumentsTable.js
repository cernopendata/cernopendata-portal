import React, { useState, useRef } from "react";
import {
  Table,
  Button,
  Icon,
  Pagination,
  Modal,
  Form,
  TextArea,
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
  const [editBuffer, setEditBuffer] = useState("");

  const [page, setPage] = useState(0);
  const pageSize = 5;
  const totalPages = Math.max(1, Math.ceil(documents.length / pageSize));
  const visible = documents.slice(page * pageSize, (page + 1) * pageSize);

  const [addModalOpen, setAddModalOpen] = useState(false);
  const [addSource, setAddSource] = useState("file");
  const [addUrls, setAddUrls] = useState([""]);
  const [addError, setAddError] = useState(null);
  const [addLoading, setAddLoading] = useState(false);
  const fileInputRef = useRef(null);
  const [filesChosen, setFilesChosen] = useState(false);

  const resetAddModal = () => {
    setAddSource("file");
    setAddUrls([""]);
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
        const files = Array.from(fileInputRef.current?.files || []);
        const jsonFiles = files.filter((f) => f.name.endsWith(".json"));
        const mdFiles = files.filter((f) => f.name.endsWith(".md"));

        if (!jsonFiles.length) {
          setAddError("Please include a .json metadata file.");
          return;
        }
        if (!mdFiles.length) {
          setAddError("Please include a .md body file.");
          return;
        }

        const docs = [];
        for (const jsonFile of jsonFiles) {
          const payload = JSON.parse(await jsonFile.text());
          const items = Array.isArray(payload) ? payload : [payload];
          const stem = jsonFile.name.replace(/\.json$/, "");
          for (const doc of items) {
            const bodyRef =
              typeof doc.body?.content === "string" &&
              doc.body.content.endsWith(".md")
                ? doc.body.content.split("/").pop()
                : null;
            const mdFile =
              (bodyRef && mdFiles.find((f) => f.name === bodyRef)) ||
              mdFiles.find((f) => f.name === stem + ".md") ||
              (mdFiles.length === 1 ? mdFiles[0] : null);
            if (!mdFile) {
              setAddError(
                `Could not match a .md file for document "${doc.slug || doc.title}".`,
              );
              return;
            }
            doc.body = { content: await mdFile.text(), format: "md" };
            docs.push(doc);
          }
        }

        requestBody = { source: "json", documents: docs };
      } else {
        const urls = addUrls.filter((u) => u.trim());
        const jsonUrls = urls.filter((u) => u.split("?")[0].endsWith(".json"));
        const mdUrls = urls.filter((u) => !u.split("?")[0].endsWith(".json"));

        if (!jsonUrls.length) {
          setAddError("Please include a .json URL for the metadata.");
          return;
        }
        if (!mdUrls.length) {
          setAddError("Please include a .md URL for the body content.");
          return;
        }
        requestBody = { source: "urls", urls };
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
    setEditBuffer(JSON.stringify(doc, null, 2));
  };

  const handleSave = async () => {
    let updated;
    try {
      updated = JSON.parse(editBuffer);
    } catch (e) {
      alert("Invalid JSON: " + e.message);
      return;
    }

    try {
      const response = await fetch(
        `/releases/${experiment}/${releaseId}/update_document`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ slug: editingDoc.slug, document: updated }),
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
                <label htmlFor="doc-files-input">Files</label>
                <input
                  id="doc-files-input"
                  type="file"
                  multiple
                  accept=".json,.md"
                  ref={fileInputRef}
                  onChange={() =>
                    setFilesChosen(!!fileInputRef.current?.files?.length)
                  }
                />
                <p className="doc-hint">
                  Select <strong>.json</strong> metadata and{" "}
                  <strong>.md</strong> body files.
                </p>
              </Form.Field>
            ) : (
              <Form.Field>
                <span className="field-group-label">URLs</span>
                {addUrls.map((url, i) => (
                  <div key={i} className="doc-url-row">
                    <Input
                      fluid
                      type="url"
                      placeholder="https://raw.githubusercontent.com/..."
                      value={url}
                      onChange={(e) => {
                        const next = [...addUrls];
                        next[i] = e.target.value;
                        setAddUrls(next);
                      }}
                    />
                    {addUrls.length > 1 && (
                      <Button
                        icon
                        basic
                        type="button"
                        onClick={() =>
                          setAddUrls(addUrls.filter((_, idx) => idx !== i))
                        }
                      >
                        <Icon name="times" />
                      </Button>
                    )}
                    {i === addUrls.length - 1 && (
                      <Button
                        basic
                        type="button"
                        style={{ whiteSpace: "nowrap" }}
                        onClick={() => setAddUrls([...addUrls, ""])}
                      >
                        <Icon name="plus" /> Add URL
                      </Button>
                    )}
                  </div>
                ))}
                <p className="doc-hint">
                  Add <strong>.json</strong> metadata and <strong>.md</strong>{" "}
                  body URLs.
                </p>
              </Form.Field>
            )}

            {addError && <Message negative>{addError}</Message>}
          </Form>
        </Modal.Content>
        <Modal.Actions>
          <Button onClick={() => setAddModalOpen(false)}>Cancel</Button>
          <Button
            primary
            disabled={
              addSource === "file"
                ? !filesChosen
                : !addUrls.some((u) => u.trim())
            }
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
            <TextArea
              rows={20}
              value={editBuffer}
              onChange={(e) => setEditBuffer(e.target.value)}
              className="doc-textarea"
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
