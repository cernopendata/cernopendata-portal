import React, { useState, useEffect, useMemo } from "react";
import { Modal, Form, TextArea, Tab, Button, Message } from "semantic-ui-react";
import { AutoForm } from "uniforms-semantic";
import PreviewTab from "../shared/PreviewTab";
import SchemaNode from "./SchemaNode";
import createBridge from "./schema";

export default function EditRecordModal({
  editingRecord,
  setEditingRecord,
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

  const panes = [
    {
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
    },
    {
      menuItem: "Raw editor",
      render: () => (
        <Tab.Pane>
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
        </Tab.Pane>
      ),
    },
    {
      menuItem: "Preview",
      render: () => (
        <Tab.Pane>
          <PreviewTab
            endpoint="/releases/preview_record"
            data={editAllMode ? records : editingRecord}
          />
        </Tab.Pane>
      ),
    },
  ];

  const handleSave = () => {
    const updatedRecords = editAllMode
      ? records
      : (() => {
          const idx = records.findIndex(
            (r) => String(r.recid) === String(editingRecord.recid),
          );
          if (idx === -1) {
            alert("Record not found");
            return records;
          }
          const copy = [...records];
          copy[idx] = editingRecord;
          return copy;
        })();

    fetch(`/releases/${experiment}/${releaseId}/update_records`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ records: updatedRecords }),
    })
      .then(async (response) => {
        if (!response.ok) {
          const json = await response.json().catch(() => ({}));
          throw new Error(json.error || "Save failed");
        }
        setRecords(updatedRecords);
        onClose();
      })
      .catch((err) => alert(err.message));
  };

  return (
    <Modal
      open={!!editingRecord || editAllMode}
      onClose={onClose}
      closeIcon
      size="fullscreen"
    >
      <Modal.Header>
        {editAllMode
          ? "Edit all records"
          : `Edit record ${editingRecord?.recid}`}
      </Modal.Header>
      <Modal.Content>
        <Tab panes={panes} />
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={onClose}>Cancel</Button>
        <Button primary onClick={handleSave}>
          Save
        </Button>
      </Modal.Actions>
    </Modal>
  );
}
