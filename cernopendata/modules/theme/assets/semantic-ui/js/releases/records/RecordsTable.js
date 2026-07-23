import React, { useEffect, useState, useRef } from "react";
import {
  Table,
  Button,
  Icon,
  Pagination,
  Popup,
  Message,
} from "semantic-ui-react";
import EditRecordModal from "./EditRecordModal";
import BulkEditModal from "./BulkEditModal";
import AddItemsModal from "../shared/AddItemsModal";
import RowActions from "../shared/RowActions";
import { fetchJson, usePagination } from "../shared/utils";

export default function RecordsTable({
  experiment,
  releaseId,
  records,
  setRecords,
  editDisabled = false,
  viewDisabled = false,
  releaseStatus = null,
}) {
  const [editingRecord, setEditingRecord] = useState(null);
  const [editingIndex, setEditingIndex] = useState(null);
  const [editAllMode, setEditAllMode] = useState(false);

  const tableRef = useRef(null);
  const pageSize = 5;
  const { page, setPage, visible, totalPages } = usePagination(
    records,
    pageSize,
  );

  const [addModalOpen, setAddModalOpen] = useState(false);
  const [bulkModalOpen, setBulkModalOpen] = useState(false);
  const [doiLoading, setDoiLoading] = useState(false);
  const [doiErrors, setDoiErrors] = useState([]);
  const [error, setError] = useState(null);

  const allHaveDoi =
    records.length > 0 && records.every((record) => record.doi);

  async function handleGenerateDoi() {
    setDoiLoading(true);
    setError(null);
    const recidsWithoutDoi = records
      .filter((record) => !record.doi)
      .map((record) => record.recid);
    try {
      const data = await fetchJson(
        `/releases/${experiment}/${releaseId}/generate_doi`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ recids: recidsWithoutDoi }),
        },
      );
      setRecords(data.records);
      setDoiErrors(data.errors || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setDoiLoading(false);
    }
  }

  function typesetMath() {
    if (window.MathJax && window.MathJax.Hub) {
      window.MathJax.Hub.Queue([
        "Typeset",
        window.MathJax.Hub,
        tableRef.current,
      ]);
    }
  }

  useEffect(() => {
    typesetMath();
  }, [page, records]);

  const closeEditModal = () => {
    setEditingRecord(null);
    setEditingIndex(null);
    setEditAllMode(false);
  };

  return (
    <>
      {error && (
        <Message negative>
          <Icon name="warning circle" /> {error}
        </Message>
      )}
      {doiErrors.length > 0 && (
        <div className="ui segment validation-segment">
          <div className="validation-header">
            <strong>
              <i className="tasks icon"></i>DOI validation
            </strong>
            <div className="validation-header-labels">
              <span className="ui red label">{doiErrors.length} failed</span>
            </div>
          </div>
          {doiErrors.map((validationError, index) => (
            <div
              key={validationError.recid}
              className={`validation-row${index < doiErrors.length - 1 ? " validation-row-bordered" : ""}`}
            >
              <div className="validation-row-icon">
                <i className="times circle red icon"></i>
              </div>
              <div className="validation-row-body">
                <b>
                  recid {validationError.recid}: {validationError.error}
                </b>
              </div>
            </div>
          ))}
        </div>
      )}
      <div>
        <div className="records-table-toolbar">
          {releaseStatus === "STAGED" && records.length > 0 && (
            <Popup
              content="All records already have DOIs"
              disabled={!allHaveDoi}
              position="top center"
              trigger={
                <span>
                  <Button
                    color="teal"
                    disabled={allHaveDoi || doiLoading}
                    loading={doiLoading}
                    onClick={handleGenerateDoi}
                  >
                    <Icon name="id card" /> Generate DOIs
                  </Button>
                </span>
              }
            />
          )}
          <div className="records-table-toolbar-buttons">
            <Button
              color="blue"
              disabled={editDisabled}
              onClick={() => setAddModalOpen(true)}
            >
              <Icon name="plus" /> Add Records
            </Button>
            <Button
              color="blue"
              disabled={editDisabled}
              onClick={() => setEditAllMode(true)}
            >
              <Icon name="edit" /> Edit Records
            </Button>
            <Button
              color="teal"
              disabled={editDisabled}
              onClick={() => setBulkModalOpen(true)}
            >
              <Icon name="tasks" /> Bulk Edit
            </Button>
          </div>
        </div>
        <div ref={tableRef}>
          <Table celled compact>
            <Table.Header>
              <Table.Row>
                <Table.HeaderCell>RecId</Table.HeaderCell>
                <Table.HeaderCell>DOI</Table.HeaderCell>
                <Table.HeaderCell>Title</Table.HeaderCell>
                <Table.HeaderCell collapsing>Actions</Table.HeaderCell>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {visible.length === 0 ? (
                <Table.Row>
                  <Table.Cell colSpan="4" textAlign="center">
                    No records in this release.
                  </Table.Cell>
                </Table.Row>
              ) : (
                visible.map((record) => (
                  <Table.Row key={record.recid}>
                    <Table.Cell className="no-glossary">
                      {record.recid}
                    </Table.Cell>
                    <Table.Cell className="no-glossary">
                      {record.doi}
                    </Table.Cell>
                    <Table.Cell>{record.title || "—"}</Table.Cell>
                    <Table.Cell collapsing>
                      <RowActions
                        onEdit={() => {
                          setEditingRecord(record);
                          setEditingIndex(records.indexOf(record));
                        }}
                        editDisabled={editDisabled}
                        viewDisabled={viewDisabled}
                        viewHref={`/record/${record.recid}`}
                      />
                    </Table.Cell>
                  </Table.Row>
                ))
              )}
            </Table.Body>
          </Table>
        </div>
        {records.length > pageSize && (
          <div className="records-table-pagination">
            <Pagination
              totalPages={totalPages}
              activePage={page + 1}
              onPageChange={(_, d) => setPage(d.activePage - 1)}
            />
          </div>
        )}
      </div>

      <EditRecordModal
        editingRecord={editingRecord}
        setEditingRecord={setEditingRecord}
        editingIndex={editingIndex}
        editAllMode={editAllMode}
        records={records}
        setRecords={setRecords}
        onClose={closeEditModal}
        experiment={experiment}
        releaseId={releaseId}
      />

      <AddItemsModal
        collection="records"
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        experiment={experiment}
        releaseId={releaseId}
        onAdded={(newRecords) => setRecords((prev) => [...prev, ...newRecords])}
      />

      <BulkEditModal
        open={bulkModalOpen}
        onClose={() => setBulkModalOpen(false)}
        experiment={experiment}
        releaseId={releaseId}
      />
    </>
  );
}
