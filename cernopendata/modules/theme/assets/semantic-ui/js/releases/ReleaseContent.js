import React, { useState } from "react";
import { Icon, Message, Tab } from "semantic-ui-react";

import RecordsTable from "./records/RecordsTable";
import DocumentsTable from "./documents/DocumentsTable";
import ValidationPanel from "./ValidationPanel";
import { fetchJson } from "./shared/utils";

export default function ReleaseContent({
  experiment,
  releaseId,
  initialRecords,
  initialDocuments,
  initialState,
  editDisabled,
  viewDisabled,
  releaseStatus,
  onCountsChanged,
}) {
  const [records, setRecords] = useState(initialRecords);
  const [documents, setDocuments] = useState(initialDocuments);
  const [releaseState, setReleaseState] = useState(initialState);
  const [fixSummary, setFixSummary] = useState(null);
  const [assignedRecids, setAssignedRecids] = useState(new Set());
  const [stateError, setStateError] = useState(null);

  const showDoiWarning =
    releaseStatus === "STAGED" && records.some((record) => !record.doi);

  const defaultActiveIndex =
    initialRecords.length === 0 && initialDocuments.length > 0 ? 1 : 0;

  async function refreshState() {
    setStateError(null);
    try {
      const state = await fetchJson(
        `/releases/${experiment}/${releaseId}/state`,
      );
      setReleaseState(state);
      onCountsChanged(state.counts);
    } catch (err) {
      setStateError(err.message);
    }
  }

  function handleContentChanged() {
    setFixSummary(null);
    setAssignedRecids(new Set());
    refreshState();
  }

  function handleFixed(summary) {
    setRecords(summary.records);
    setDocuments(summary.documents);
    setAssignedRecids(new Set(summary.assigned_recids));
    setFixSummary(summary);
    refreshState();
  }

  const panes = [
    {
      menuItem: { key: "records", icon: "database", content: "Records" },
      render: () => (
        <Tab.Pane>
          <RecordsTable
            experiment={experiment}
            releaseId={releaseId}
            records={records}
            setRecords={setRecords}
            assignedRecids={assignedRecids}
            editDisabled={editDisabled}
            viewDisabled={viewDisabled}
            releaseStatus={releaseStatus}
            onContentChanged={handleContentChanged}
          />
        </Tab.Pane>
      ),
    },
    {
      menuItem: {
        key: "documents",
        icon: "file alternate",
        content: "Documents",
      },
      render: () => (
        <Tab.Pane>
          <DocumentsTable
            experiment={experiment}
            releaseId={releaseId}
            documents={documents}
            setDocuments={setDocuments}
            editDisabled={editDisabled}
            viewDisabled={viewDisabled}
            onContentChanged={handleContentChanged}
          />
        </Tab.Pane>
      ),
    },
  ];

  return (
    <div style={{ marginBottom: "2em" }}>
      <ValidationPanel
        experiment={experiment}
        releaseId={releaseId}
        validations={releaseState.validations}
        errors={releaseState.errors}
        numErrors={releaseState.num_errors}
        releaseStatus={releaseStatus}
        hasRecords={records.length > 0}
        hasDocuments={documents.length > 0}
        onValidationsChanged={handleContentChanged}
        onFixed={handleFixed}
      />
      {stateError && (
        <Message negative>
          <Icon name="warning circle" />
          Could not refresh the validations: {stateError}
        </Message>
      )}
      {fixSummary && <FixSummaryMessage summary={fixSummary} />}
      {showDoiWarning && (
        <div className="ui warning message release-status-message">
          <p>
            <i className="info circle icon"></i>
            Some records do not have DOIs yet. You can generate them before
            publishing.
          </p>
        </div>
      )}
      <Tab panes={panes} defaultActiveIndex={defaultActiveIndex} />
    </div>
  );
}

function FixSummaryMessage({ summary }) {
  const { fixed, remaining, assigned_recids } = summary;
  const total = fixed.length + remaining.length;

  return (
    <Message positive={remaining.length === 0} info={remaining.length > 0}>
      <Message.Header>
        <Icon name="magic" />
        Auto-fixed {fixed.length} of {total} failing{" "}
        {total === 1 ? "validation" : "validations"}.
      </Message.Header>
      {fixed.length > 0 && <p>Now passing: {fixed.join(", ")}.</p>}
      {remaining.length > 0 && (
        <p>Still needing manual correction: {remaining.join(", ")}.</p>
      )}
      {assigned_recids.length > 0 && (
        <p>
          Assigned a recid to {assigned_recids.length}{" "}
          {assigned_recids.length === 1 ? "record" : "records"}.
        </p>
      )}
    </Message>
  );
}
