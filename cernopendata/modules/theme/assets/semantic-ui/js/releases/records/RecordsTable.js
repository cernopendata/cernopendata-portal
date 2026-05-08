import React, { useEffect, useState, useRef } from "react";
import { Table, Button, Icon, Pagination } from "semantic-ui-react";
import EditRecordModal from "./EditRecordModal";
import BulkEditModal from "./BulkEditModal";
import usePagination from "../shared/usePagination";
import RowActions from "../shared/RowActions";

export default function RecordsTable({
  experiment,
  releaseId,
  initialRecords,
  editDisabled = false,
  viewDisabled = false,
  releaseStatus = null,
}) {
  const [records, setRecords] = useState(initialRecords);
  const [editingRecord, setEditingRecord] = useState(null);
  const [editAllMode, setEditAllMode] = useState(false);

  const tableRef = useRef(null);
  const pageSize = 5;
  const { page, setPage, visible, totalPages } = usePagination(
    records,
    pageSize,
  );

  const [bulkModalOpen, setBulkModalOpen] = useState(false);

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
    setEditAllMode(false);
  };

  return (
    <>
      <div>
        <div className="records-table-toolbar">
          {releaseStatus === "STAGED" && records.length > 0 && (
            <div className="ui checkbox">
              <input
                type="checkbox"
                name="generate_doi"
                id="generate-doi-checkbox"
                value="1"
                form="primary-action-form"
              />
              <label htmlFor="generate-doi-checkbox">
                Generate DOI for all entries
              </label>
            </div>
          )}
          <div className="records-table-toolbar-buttons">
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
                        onEdit={() => setEditingRecord(record)}
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
        editAllMode={editAllMode}
        records={records}
        setRecords={setRecords}
        onClose={closeEditModal}
        experiment={experiment}
        releaseId={releaseId}
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
