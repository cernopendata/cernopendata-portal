import React, { useState } from "react";
import { Tab } from "semantic-ui-react";

import RecordsTable from "./records/RecordsTable";
import DocumentsTable from "./documents/DocumentsTable";

export default function ReleaseContent({
  experiment,
  releaseId,
  initialRecords,
  initialDocuments,
  editDisabled,
  viewDisabled,
  releaseStatus,
}) {
  const [records, setRecords] = useState(initialRecords);
  const showDoiWarning =
    releaseStatus === "STAGED" && records.some((record) => !record.doi);

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
            editDisabled={editDisabled}
            viewDisabled={viewDisabled}
            releaseStatus={releaseStatus}
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
            initialDocuments={initialDocuments}
            editDisabled={editDisabled}
            viewDisabled={viewDisabled}
          />
        </Tab.Pane>
      ),
    },
  ];

  return (
    <div style={{ marginBottom: "2em" }}>
      {showDoiWarning && (
        <div className="ui warning message release-status-message">
          <p>
            <i className="info circle icon"></i>
            Some records do not have DOIs yet. You can generate them before
            publishing.
          </p>
        </div>
      )}
      <Tab panes={panes} />
    </div>
  );
}
