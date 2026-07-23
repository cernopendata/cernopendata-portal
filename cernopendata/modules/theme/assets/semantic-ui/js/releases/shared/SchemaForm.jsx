import React, { useState, useMemo } from "react";
import { Dropdown, Input } from "semantic-ui-react";
import SchemaNode from "./SchemaNode";

const VISIBILITY_OPTIONS = [
  { key: "nonEmpty", value: "nonEmpty", text: "Show only fields with values" },
  { key: "all", value: "all", text: "Show all fields" },
  { key: "selected", value: "selected", text: "Show only selected fields" },
];

export default function SchemaForm({ schema, model, filterPlaceholder }) {
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

  const awaitingFilter =
    visibilityMode === "selected" && selectedSet.size === 0;

  return (
    <div className="schema-form">
      <div className="schema-form-toolbar">
        <Dropdown
          selection
          options={VISIBILITY_OPTIONS}
          value={visibilityMode}
          onChange={(event, { value }) => setVisibilityMode(value)}
        />
        {visibilityMode === "selected" && (
          <Input
            icon="filter"
            iconPosition="left"
            placeholder={filterPlaceholder}
            value={selectedFields}
            onChange={(event) => setSelectedFields(event.target.value)}
          />
        )}
      </div>

      {awaitingFilter ? (
        <p className="schema-form-hint">
          Type one or more comma-separated field names above to choose what to
          show.
        </p>
      ) : (
        <SchemaNode
          schema={schema}
          model={model}
          visibilityMode={visibilityMode}
          selectedSet={selectedSet}
        />
      )}
    </div>
  );
}
