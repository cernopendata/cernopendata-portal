import React from "react";
import { Form, Grid } from "semantic-ui-react";
import { AutoField } from "uniforms-semantic";

export default function FormRow({ label, name }) {
  return (
    <Form.Field>
      <Grid verticalAlign="middle">
        <Grid.Row>
          <Grid.Column width={2}>
            <label>{label}</label>
          </Grid.Column>

          <Grid.Column width={14}>
            <AutoField name={name} label={false} />
          </Grid.Column>
        </Grid.Row>
      </Grid>
    </Form.Field>
  );
}
