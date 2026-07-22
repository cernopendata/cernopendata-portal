import React, { useState } from "react";
import { Accordion, Icon } from "semantic-ui-react";
import FormRow from "./FormRow";
import { isVisible } from "./visibility";

function sortFields(schema) {
  const required = new Set(schema.required || []);

  return (a, b) => {
    const aReq = required.has(a[0]);
    const bReq = required.has(b[0]);

    // required first
    if (aReq !== bReq) return aReq ? -1 : 1;

    // alphabetical inside group
    return a[0].localeCompare(b[0]);
  };
}

export default function SchemaNode({
  schema,
  model,
  name = "",
  visibilityMode,
  selectedSet,
  label = null,
}) {
  const [open, setOpen] = useState(name === "");

  if (!schema) return null;

  const isObject = schema.type === "object" && schema.properties;
  const isArray = schema.type === "array" && schema.items;

  if (!isVisible({ schema, model, path: name, visibilityMode, selectedSet }))
    return null;
  if (!label) label = name;

  if (!isObject && !isArray) {
    return <FormRow label={label} name={name} />;
  }

  if (isObject) {
    const children = Object.entries(schema.properties)
      .sort(sortFields(schema))
      .map(([key, subSchema]) => (
        <SchemaNode
          key={key}
          name={name ? `${name}.${key}` : key}
          schema={subSchema}
          model={model?.[key]}
          label={key}
          visibilityMode={visibilityMode}
          selectedSet={selectedSet}
        />
      ));

    if (name === "") {
      return <div style={{ paddingLeft: 12 }}>{children}</div>;
    }
    return (
      <Accordion fluid>
        <Accordion.Title active={open} onClick={() => setOpen(!open)}>
          <Icon name="dropdown" />
          {label}
        </Accordion.Title>

        <Accordion.Content active={open}>
          <div style={{ paddingLeft: 20 }}>{children}</div>
        </Accordion.Content>
      </Accordion>
    );
  }

  if (isArray) {
    const items = model || [];

    return (
      <Accordion fluid>
        <Accordion.Title active={open} onClick={() => setOpen(!open)}>
          <Icon name="dropdown" />
          {label}
        </Accordion.Title>
        <Accordion.Content active={open}>
          <div style={{ paddingLeft: 20 }}>
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
        </Accordion.Content>
      </Accordion>
    );
  }

  return null;
}
