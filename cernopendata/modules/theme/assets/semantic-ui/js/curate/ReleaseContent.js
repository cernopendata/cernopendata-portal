import React from "react";
import { Tab } from "semantic-ui-react";

import RecordsTable from "./RecordsTable";
import DocumentsTable from "./DocumentsTable";

export default function ReleaseContent({
  experiment,
  releaseId,
  initialRecords,
  initialDocuments,
  editDisabled,
  viewDisabled,
  releaseStatus,
}) {
  const panes = [
    {
      menuItem: { key: "records", icon: "database", content: "Records" },
      render: () => (
        <Tab.Pane>
          <RecordsTable
            experiment={experiment}
            releaseId={releaseId}
            initialRecords={initialRecords}
            editDisabled={editDisabled}
            viewDisabled={viewDisabled}
            releaseStatus={releaseStatus}
          />
        </Tab.Pane>
      ),
    },
    {
      menuItem: { key: "documents", icon: "file alternate", content: "Documents" },
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
      <Tab panes={panes} />
    </div>
  );
}
