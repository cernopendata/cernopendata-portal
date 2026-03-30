import React, { useEffect, useState, useRef } from "react";
import { Icon, Table, Loader, Button, Pagination, Modal, Form, TextArea } from "semantic-ui-react";
import $ from 'jquery';

export default function RecordsTable({
    experiment, releaseId,
    initialRecords,   editDisabled = false,
                      viewDisabled = false,}) {
  const [records, setRecords] = useState(initialRecords);
  const [editingRecord, setEditingRecord] = useState(null);
  const [editAllMode, setEditAllMode] = useState(false);


const tableRef = useRef(null);
  const [page, setPage] = useState(0);

  const pageSize = 5;
  const visible = records.slice(page * pageSize, (page + 1) * pageSize);

    const [bulkModalOpen, setBulkModalOpen] = useState(false);
    const [bulkActions, setBulkActions] = useState([]); // each action: { mode, key, value }
    const [bulkPreview, setBulkPreview] = useState([]); // preview diffs
    const [bulkPreviewDone, setBulkPreviewDone] = useState(false);

function typesetMath() {
  if (window.MathJax && window.MathJax.Hub) {

    window.MathJax.Hub.Queue(['Typeset', window.MathJax.Hub, tableRef.current]);
  }
}

  useEffect(() => {
      typesetMath();
  }, [page, records]);

  const openEditModal = record => {
      // reuse your existing global logic
      window.editingRecordId = record.recid;

      $('#records-json-textarea').val(
        JSON.stringify(record, null, 2)
      );

      $('#edit-records-modal').modal('show');
  };

    function addBulkRow() {
      setBulkActions([...bulkActions, { mode: 'set', key: '', value: '' }]);
      setBulkPreviewDone(false);
    }

    function removeBulkRow(idx) {
      const updated = bulkActions.filter((_, i) => i !== idx);
      setBulkActions(updated);
      setBulkPreviewDone(false);
    }

    function updateBulkRow(idx, field, newValue) {
      const updated = [...bulkActions];
      updated[idx][field] = newValue;
      setBulkActions(updated);
      setBulkPreviewDone(false);
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

     const res = await fetch(`/releases/${experiment}/${releaseId}/bulk_records/preview`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ updates })
     });

     if (!res.ok) {
       alert('Preview failed');
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

     const res = await fetch(`/releases/${experiment}/${releaseId}/bulk_records/apply`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ updates })
     });

     if (!res.ok) {
       alert('Apply failed');
       return;
     }

     window.location.reload();
   }

   function collectBulkOperations() {
     const setOps = {};
     const deleteOps = [];

     bulkActions.forEach(({ mode, key, value }) => {
       if (!key.trim()) return;

       if (mode === 'delete') {
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

function DiffObject({ diff }) {
  return (
    <div className="ui list">
      {diff.values_changed &&
        Object.entries(diff.values_changed).map(([path, change], i) => (
          <div key={i} className="item">
            🟡 <strong>{path}</strong><br />
            <span className="removed">- {JSON.stringify(change.old_value)}</span><br />
            <span className="added">+ {JSON.stringify(change.new_value)}</span>
          </div>
        ))
      }
      {diff.type_changes &&
        Object.entries(diff.type_changes).map(([path, change], i) => (
          <div key={i} className="item">
            🟠 <strong>{path}</strong><br />
            <span className="removed">- {JSON.stringify(change.old_value)} ({change.old_type})</span><br />
            <span className="added">+ {JSON.stringify(change.new_value)} ({change.new_type})</span>
          </div>
        ))
      }
      {diff.dictionary_item_added &&
        diff.dictionary_item_added.map((path, i) => (
          <div key={i} className="item">🟢 <strong>{path}</strong> added</div>
        ))
      }
      {diff.dictionary_item_removed &&
        diff.dictionary_item_removed.map((path, i) => (
          <div key={i} className="item">🔴 <strong>{path}</strong> removed</div>
        ))
      }
    </div>
  );
}

  return (
    <>
    <Button className="small blue"  disabled={editDisabled} onClick={() => setEditAllMode(true)}>
        <i className="edit icon"></i>
        Edit Records
    </Button>
    <Button
      color="teal"
      disabled={editDisabled}
      onClick={() => setBulkModalOpen(true)}
    >
      <i className="tasks icon"></i> Bulk edit
    </Button>
    <div ref={tableRef}>
      <Table celled compact>
       <Table.Header>
          <Table.Row>
            <Table.HeaderCell>RecId</Table.HeaderCell>
            <Table.HeaderCell>DOI</Table.HeaderCell>
            <Table.HeaderCell>Title</Table.HeaderCell>
            <Table.HeaderCell textAlign="right">
              Actions
            </Table.HeaderCell>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {visible.map(record => (
            <Table.Row key={record.recid}>
              <Table.Cell className="no-glossary">{record.recid}</Table.Cell>
              <Table.Cell className="no-glossary">{record.doi}</Table.Cell>
              <Table.Cell>{record.title || '—'}</Table.Cell>
              <Table.Cell textAlign="right">
                <Button className="small blue" disabled={editDisabled} onClick={() => setEditingRecord(record)}>
                  Edit
                </Button>
                <Button className="small blue" disabled={viewDisabled} as="a" onClick={() => {
                                                                                                         if (!viewDisabled) {
                                                                                                           window.location.href = `/record/${record.recid}`;
                                                                                                         }
                                                                                                       }}>
                  View
                </Button>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table>
</div>
      <Pagination
        totalPages={Math.ceil(records.length / pageSize)}
        activePage={page + 1}
        onPageChange={(_, d) => setPage(d.activePage - 1)}
      />

      <Modal
        open={!!editingRecord|| editAllMode}
        onClose={() => {
        setEditingRecord(null);
        setEditAllMode(false);
        }}
        closeIcon
        size="fullscreen"
      >
        <Modal.Header>    {editAllMode
                            ? `Edit all records`
                            : `Edit record ${editingRecord?.recid}`}</Modal.Header>
        <Modal.Content>
          <Form>
            <TextArea
                value={
                  editAllMode
                    ? JSON.stringify(records, null, 2)
                    : JSON.stringify(editingRecord, null, 2)
                }
              onChange={e => {
                try {
                  const parsed = JSON.parse(e.target.value);
                    if (editAllMode) {
                      setRecords(parsed);
                    } else {
                      setEditingRecord(parsed);
                    }
                } catch {
                  // invalid JSON, ignore or show an error
                }
              }}
              rows={20}
              style={{ width: '100%' }}
            />
          </Form>
        </Modal.Content>
        <Modal.Actions>
              <Button
                onClick={() => {
                  setEditingRecord(null);
                  setEditAllMode(false);
                }}
              >
                Cancel
                </Button>
          <Button primary onClick={() => {

                  const updatedRecords = editAllMode ? records : (() => {
                    const idx = records.findIndex(
                      r => String(r.recid) === String(editingRecord.recid)
                    );
                    if (idx === -1) {
                      alert('Record not found');
                      return records;
                    }
                    const copy = [...records];
                    copy[idx] = editingRecord;
                    return copy;
                  })();
                  // send updatedRecords as JSON
                  fetch(`/releases/${experiment}/${releaseId}/update_records`, {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                      },
                      body: JSON.stringify({ records: updatedRecords }),
                  })
                      .then(res => {
                        if (!res.ok) throw new Error('Save failed');
                        setRecords(updatedRecords);
                        setEditingRecord(null);
                        setEditAllMode(false);
                      })
                      .catch(err => alert(err.message));
                }}>
            Save
          </Button>
        </Modal.Actions>
      </Modal>


    <Modal
      open={bulkModalOpen}
      onClose={() => setBulkModalOpen(false)}
      closeIcon
      size="fullscreen"
    >
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
                      onChange={e => updateBulkRow(idx, 'mode', e.target.value)}
                    >
                      <option value="set">Set / update</option>
                      <option value="delete">Delete field</option>
                    </select>
                  </td>
                  <td>
                    <input
                      type="text"
                      value={row.key}
                      onChange={e => updateBulkRow(idx, 'key', e.target.value)}
                      placeholder="field name"
                    />
                  </td>
                  <td>
                    <textarea
                      rows={1}
                      value={row.value}
                      onChange={e => updateBulkRow(idx, 'value', e.target.value)}
                      disabled={row.mode === 'delete'}
                      placeholder='JSON value'
                    />
                  </td>
                  <td>
                    <Button size="tiny" color="red" onClick={() => removeBulkRow(idx)}>
                      <i className="trash icon" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
          <Button size="tiny" onClick={addBulkRow}>
            <i className="plus icon" /> Add action
          </Button>
        </Form>

        <div className="ui clearing segment" style={{ marginTop: '1em' }}>
          <div className="ui right floated buttons">
            <Button
              onClick={previewBulk}
              disabled={bulkActions.length === 0 || bulkPreviewDone}
            >
              Preview
            </Button>
            <Button
              primary
              disabled={!bulkPreviewDone}
              onClick={applyBulk}
            >
              Apply
            </Button>
            <Button onClick={() => setBulkModalOpen(false)}>Cancel</Button>
          </div>
        </div>

        {bulkPreview.length > 0 && (
          <div className="ui segment" style={{ marginTop: '1em' }}>
            <h4 className="ui header">Preview changes (first 10 records)</h4>
            {bulkPreview.map((item, i) => (
              <div key={i} className="ui fluid card">
                <div className="content">
                  <div className="header">Record {item.index + 1} ({item.recid || 'no recid'})</div>
                  <DiffObject diff={item.diff} />
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal.Content>
    </Modal>

    </>
  );
}