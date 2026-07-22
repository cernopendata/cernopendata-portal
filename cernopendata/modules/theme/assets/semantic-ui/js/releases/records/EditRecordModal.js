import React, { useState, useEffect, useMemo } from "react";
import {
  Modal,
  Form,
  TextArea,
  Tab,
  Button,
  Message,
  Icon,
} from "semantic-ui-react";
import { AutoForm } from "uniforms-semantic";
import PreviewTab from "../shared/PreviewTab";
import SchemaNode from "../shared/SchemaNode";
import createBridge from "../shared/schema";
import { fetchJson } from "../shared/utils";

export default function EditRecordModal({
  editingRecord,
  setEditingRecord,
  editingIndex,
  editAllMode,
  records,
  setRecords,
  onClose,
  experiment,
  releaseId,
}) {
  const [bridge, setBridge] = useState(null);
  const [origSchema, setOrigSchema] = useState(null);
  const [schemaError, setSchemaError] = useState(false);
  const [error, setError] = useState(null);

  const open = !!editingRecord || editAllMode;
  useEffect(() => {
    if (open) setError(null);
  }, [open]);

  useEffect(() => {
    fetch("/schema/records/record-v1.0.0.json")
      .then((response) => {
        if (!response.ok) throw new Error("Schema not found");
        return response.json();
      })
      .then((data) => {
        const [schema, bridge] = createBridge(data);
        setOrigSchema(schema);
        setBridge(bridge);
      })
      .catch((err) => {
        console.error(err);
        setSchemaError(true);
      });
  }, []);

  const [visibilityMode, setVisibilityMode] = useState("nonEmpty");
  const [selectedFields, setSelectedFields] = useState("");
  const selectedSet = useMemo(() => {
    return new Set(
      selectedFields
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    );
  }, [selectedFields]);

  const [jsonText, setJsonText] = useState("");
  useEffect(() => {
    const data = editAllMode ? records : editingRecord;
    setJsonText(JSON.stringify(data, null, 2));
  }, [editAllMode, records, editingRecord]);

  const formPane = {
    menuItem: "Form",
    render: () => (
      <Tab.Pane>
        {schemaError ? (
          <Message negative>
            Could not load the record schema. Use the Raw editor tab to make
            changes.
          </Message>
        ) : bridge ? (
          <AutoForm
            schema={bridge}
            model={editingRecord}
            onChangeModel={(m) => setEditingRecord(m)}
          >
            <div style={{ marginBottom: 10 }}>
              <select
                value={visibilityMode}
                onChange={(e) => setVisibilityMode(e.target.value)}
              >
                <option value="all">Show all fields</option>
                <option value="nonEmpty">Show only fields with values</option>
                <option value="selected">Show only selected fields</option>
              </select>

              {visibilityMode === "selected" && (
                <input
                  type="text"
                  placeholder="e.g. doi, files.checksum"
                  value={selectedFields}
                  onChange={(e) => setSelectedFields(e.target.value)}
                  style={{ marginLeft: 10, width: 300 }}
                />
              )}
            </div>
            <SchemaNode
              schema={origSchema}
              model={editingRecord}
              visibilityMode={visibilityMode}
              selectedSet={selectedSet}
            />
          </AutoForm>
        ) : null}
      </Tab.Pane>
    ),
  };

  const rawEditor = (
    <Form>
      <TextArea
        value={jsonText}
        onChange={(e) => {
          const text = e.target.value;
          setJsonText(text);
          try {
            const parsed = JSON.parse(text);
            editAllMode ? setRecords(parsed) : setEditingRecord(parsed);
          } catch {}
        }}
        rows={20}
        style={{ width: "100%" }}
      />
    </Form>
  );

  const rawEditorPane = {
    menuItem: "Raw editor",
    render: () => <Tab.Pane>{rawEditor}</Tab.Pane>,
  };

  const previewPane = {
    menuItem: "Preview",
    render: () => (
      <Tab.Pane>
        <PreviewTab endpoint="/releases/preview_record" data={editingRecord} />
      </Tab.Pane>
    ),
  };

  const handleSave = async () => {
    setError(null);

    let updatedRecords;
    if (editAllMode) {
      updatedRecords = records;
    } else {
      if (
        editingIndex == null ||
        editingIndex < 0 ||
        editingIndex >= records.length
      ) {
        setError("Record not found.");
        return;
      }
      updatedRecords = [...records];
      updatedRecords[editingIndex] = editingRecord;
    }

    try {
      await fetchJson(`/releases/${experiment}/${releaseId}/update_records`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ records: updatedRecords }),
      });
      setRecords(updatedRecords);
      onClose();
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <Modal open={open} onClose={onClose} closeIcon size="fullscreen">
      <Modal.Header>
        {editAllMode
          ? "Edit all records"
          : `Edit record ${editingRecord?.recid}`}
      </Modal.Header>
      <Modal.Content>
        {error && (
          <Message negative>
            <Icon name="warning circle" /> {error}
          </Message>
        )}
        {editAllMode ? (
          rawEditor
        ) : (
          <Tab panes={[formPane, rawEditorPane, previewPane]} />
        )}
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
