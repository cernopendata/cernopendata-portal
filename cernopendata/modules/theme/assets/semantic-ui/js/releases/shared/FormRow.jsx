import React from "react";
import { Form } from "semantic-ui-react";
import { AutoField } from "uniforms-semantic";

export default function FormRow({ label, name, required = false }) {
  return (
    <Form.Field className="schema-form-row">
      <label htmlFor={name}>
        {label}
        {required && <span className="schema-form-required">*</span>}
      </label>
      <AutoField id={name} name={name} label={false} />
    </Form.Field>
  );
}
