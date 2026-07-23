import React, { useState } from "react";
import { Icon } from "semantic-ui-react";
import FormRow from "./FormRow";
import { isVisible } from "./visibility";

function GroupTitle({ label, required, count, open, onToggle }) {
  return (
    <button
      type="button"
      className={`schema-form-group-title${open ? " is-open" : ""}`}
      aria-expanded={open}
      onClick={onToggle}
    >
      <Icon name="caret right" />
      <span>{label}</span>
      {required && <span className="schema-form-required">*</span>}
      {count !== undefined && (
        <span className="schema-form-count">{count}</span>
      )}
    </button>
  );
}

export default function SchemaNode({
  schema,
  model,
  name = "",
  visibilityMode,
  selectedSet,
  label = null,
  required = false,
}) {
  const [open, setOpen] = useState(name === "");

  if (!schema) return null;

  const isObject = schema.type === "object" && schema.properties;
  const isArray = schema.type === "array" && schema.items;

  if (!isVisible({ schema, model, path: name, visibilityMode, selectedSet }))
    return null;
  if (!label) label = name;

  if (!isObject && !isArray) {
    if (schema.type === "object" || schema.type === "array") return null;
    return <FormRow label={label} name={name} required={required} />;
  }

  if (isObject) {
    const requiredFields = new Set(schema.required || []);
    const children = Object.entries(schema.properties)
      .sort(([a], [b]) => {
        const aReq = requiredFields.has(a);
        const bReq = requiredFields.has(b);
        if (aReq !== bReq) return aReq ? -1 : 1;
        return a.localeCompare(b);
      })
      .map(([key, subSchema]) => (
        <SchemaNode
          key={key}
          name={name ? `${name}.${key}` : key}
          schema={subSchema}
          model={model?.[key]}
          label={key}
          required={requiredFields.has(key)}
          visibilityMode={visibilityMode}
          selectedSet={selectedSet}
        />
      ));

    if (name === "") {
      return <div>{children}</div>;
    }

    return (
      <div className="schema-form-group">
        <GroupTitle
          label={label}
          required={required}
          open={open}
          onToggle={() => setOpen(!open)}
        />
        {open && <div className="schema-form-group-body">{children}</div>}
      </div>
    );
  }

  if (isArray) {
    const items = model || [];

    return (
      <div className="schema-form-group">
        <GroupTitle
          label={label}
          required={required}
          count={items.length}
          open={open}
          onToggle={() => setOpen(!open)}
        />
        {open && (
          <div className="schema-form-group-body">
            {items.map((item, index) => (
              <SchemaNode
                key={`${name}.${index}`}
                schema={schema.items}
                model={item}
                name={`${name}.${index}`}
                label={index + 1}
                visibilityMode={visibilityMode}
                selectedSet={selectedSet}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  return null;
}
