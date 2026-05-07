import React, { useState, useEffect } from "react";
import { Modal, Form, Table, Button, Icon } from "semantic-ui-react";

function DiffObject({ diff }) {
  return (
    <div className="ui list">
      {diff.values_changed &&
        Object.entries(diff.values_changed).map(([path, change], i) => (
          <div key={i} className="item">
            <span>
              <Icon name="circle" color="yellow" />
            </span>{" "}
            <strong>{path}</strong>
            <br />
            <span className="removed">
              - {JSON.stringify(change.old_value)}
            </span>
            <br />
            <span className="added">+ {JSON.stringify(change.new_value)}</span>
          </div>
        ))}
      {diff.type_changes &&
        Object.entries(diff.type_changes).map(([path, change], i) => (
          <div key={i} className="item">
            <span>
              <Icon name="circle" color="orange" />
            </span>{" "}
            <strong>{path}</strong>
            <br />
            <span className="removed">
              - {JSON.stringify(change.old_value)} ({change.old_type})
            </span>
            <br />
            <span className="added">
              + {JSON.stringify(change.new_value)} ({change.new_type})
            </span>
          </div>
        ))}
      {diff.dictionary_item_added &&
        diff.dictionary_item_added.map((path, i) => (
          <div key={i} className="item">
            <span>
              <Icon name="circle" color="green" />
            </span>{" "}
            <strong>{path}</strong> added
          </div>
        ))}
      {diff.dictionary_item_removed &&
        diff.dictionary_item_removed.map((path, i) => (
          <div key={i} className="item">
            <span>
              <Icon name="circle" color="red" />
            </span>{" "}
            <strong>{path}</strong> removed
          </div>
        ))}
    </div>
  );
}

export default function BulkEditModal({
  open,
  onClose,
  experiment,
  releaseId,
}) {
  const [bulkActions, setBulkActions] = useState([]);
  const [bulkPreview, setBulkPreview] = useState([]);
  const [bulkPreviewDone, setBulkPreviewDone] = useState(false);

  useEffect(() => {
    if (!open) return;
    setBulkActions([]);
    setBulkPreview([]);
    setBulkPreviewDone(false);
  }, [open]);

  function addBulkRow() {
    setBulkActions((prev) => [...prev, { mode: "set", key: "", value: "" }]);
    setBulkPreviewDone(false);
  }

  function removeBulkRow(idx) {
    setBulkActions((prev) => prev.filter((_, i) => i !== idx));
    setBulkPreviewDone(false);
  }

  function updateBulkRow(idx, field, newValue) {
    setBulkActions((prev) => {
      const updated = [...prev];
      updated[idx] = { ...updated[idx], [field]: newValue };
      return updated;
    });
    setBulkPreviewDone(false);
  }

  function collectBulkOperations() {
    const setOps = {};
    const deleteOps = [];

    bulkActions.forEach(({ mode, key, value }) => {
      if (!key.trim()) return;

      if (mode === "delete") {
        deleteOps.push(key.trim());
        return;
      }

      if (!value.trim()) throw new Error(`Missing value for key "${key}"`);

      try {
        setOps[key.trim()] = JSON.parse(value);
      } catch (e) {
        throw new Error(`Invalid JSON for key "${key}"`);
      }
    });

    return { set: setOps, delete: deleteOps };
  }

  async function previewBulk() {
    if (bulkActions.length === 0) return;

    let updates;
    try {
      updates = collectBulkOperations();
    } catch (e) {
      alert(e.message);
      return;
    }

    const res = await fetch(
      `/releases/${experiment}/${releaseId}/bulk_records/preview`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ updates }),
      },
    );

    if (!res.ok) {
      alert("Preview failed");
      return;
    }

    const data = await res.json();
    setBulkPreview(data.diffs || []);
    setBulkPreviewDone(true);
  }

  async function applyBulk() {
    if (!bulkPreviewDone) return;

    let updates;
    try {
      updates = collectBulkOperations();
    } catch (e) {
      alert(e.message);
      return;
    }

    const res = await fetch(
      `/releases/${experiment}/${releaseId}/bulk_records/apply`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ updates }),
      },
    );

    if (!res.ok) {
      alert("Apply failed");
      return;
    }

    window.location.reload();
  }

  return (
    <Modal open={open} onClose={onClose} closeIcon size="fullscreen">
      <Modal.Header>Bulk edit records</Modal.Header>
      <Modal.Content>
        <Form>
          <Table celled compact size="small">
            <thead>
              <tr>
                <th>Action</th>
                <th>Field</th>
                <th>Value (JSON)</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {bulkActions.map((row, idx) => (
                <tr key={idx}>
                  <td>
                    <select
                      className="ui compact dropdown"
                      value={row.mode}
                      onChange={(e) =>
                        updateBulkRow(idx, "mode", e.target.value)
                      }
                    >
                      <option value="set">Set / update</option>
                      <option value="delete">Delete field</option>
                    </select>
                  </td>
                  <td>
                    <input
                      type="text"
                      value={row.key}
                      onChange={(e) =>
                        updateBulkRow(idx, "key", e.target.value)
                      }
                      placeholder="field name"
                    />
                  </td>
                  <td>
                    <textarea
                      rows={1}
                      value={row.value}
                      onChange={(e) =>
                        updateBulkRow(idx, "value", e.target.value)
                      }
                      disabled={row.mode === "delete"}
                      placeholder="JSON value"
                    />
                  </td>
                  <td>
                    <Button
                      size="tiny"
                      color="red"
                      onClick={() => removeBulkRow(idx)}
                    >
                      <Icon name="trash" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
          <Button size="tiny" onClick={addBulkRow}>
            <Icon name="plus" /> Add action
          </Button>
        </Form>

        <div className="ui clearing segment" style={{ marginTop: "1em" }}>
          <div className="ui right floated buttons">
            <Button
              onClick={previewBulk}
              disabled={bulkActions.length === 0 || bulkPreviewDone}
            >
              Preview
            </Button>
            <Button primary disabled={!bulkPreviewDone} onClick={applyBulk}>
              Apply
            </Button>
            <Button onClick={onClose}>Cancel</Button>
          </div>
        </div>

        {bulkPreview.length > 0 && (
          <div className="ui segment" style={{ marginTop: "1em" }}>
            <h4 className="ui header">Preview changes (first 10 records)</h4>
            {bulkPreview.map((item, i) => (
              <div key={i} className="ui fluid card">
                <div className="content">
                  <div className="header">
                    Record {item.index + 1} ({item.recid || "no recid"})
                  </div>
                  <DiffObject diff={item.diff} />
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal.Content>
    </Modal>
  );
}
