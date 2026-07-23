import React, { useState, useEffect } from "react";
import {
  Modal,
  Form,
  TextArea,
  Tab,
  Button,
  Icon,
  Message,
} from "semantic-ui-react";
import { AutoForm } from "uniforms-semantic";
import PreviewTab from "../shared/PreviewTab";
import SchemaForm from "../shared/SchemaForm";
import createBridge from "../shared/schema";
import { fetchJson } from "../shared/utils";

export default function EditDocumentModal({
  doc,
  onClose,
  experiment,
  releaseId,
  onSaved,
}) {
  const [metaDataBuffer, setMetaDataBuffer] = useState("");
  const [metaData, setMetaData] = useState(null);
  const [bodyBuffer, setBodyBuffer] = useState("");
  const [error, setError] = useState(null);

  const [bridge, setBridge] = useState(null);
  const [origSchema, setOrigSchema] = useState(null);
  const [schemaError, setSchemaError] = useState(false);

  useEffect(() => {
    fetch("/schema/records/docs-v1.0.0.json")
      .then((response) => {
        if (!response.ok) throw new Error("Schema not found");
        return response.json();
      })
      .then((data) => {
        const [schema, bridge] = createBridge(data);
        let formSchema = schema;
        if (schema.properties?.body?.properties) {
          const bodyProperties = { ...schema.properties.body.properties };
          delete bodyProperties.content;
          formSchema = {
            ...schema,
            properties: {
              ...schema.properties,
              body: { ...schema.properties.body, properties: bodyProperties },
            },
          };
        }
        setOrigSchema(formSchema);
        setBridge(bridge);
      })
      .catch((err) => {
        console.error(err);
        setSchemaError(true);
      });
  }, []);

  useEffect(() => {
    if (!doc) return;
    const { body, ...rest } = doc;
    const metaData = { ...rest };
    if (body) {
      metaData.body = { ...body };
      delete metaData.body.content;
    }
    setMetaData(metaData);
    setMetaDataBuffer(JSON.stringify(metaData, null, 2));
    setBodyBuffer(body?.content || "");
    setError(null);
  }, [doc]);

  const handleSave = async () => {
    setError(null);

    let updated;
    try {
      updated = JSON.parse(metaDataBuffer);
    } catch (e) {
      setError("Invalid JSON: " + e.message);
      return;
    }
    updated.body = {
      format: "md",
      ...(updated.body || {}),
      content: bodyBuffer,
    };

    try {
      await fetchJson(
        `/releases/${experiment}/${releaseId}/documents/${doc.slug}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ document: updated }),
        },
      );
    } catch (e) {
      setError(e.message);
      return;
    }

    onSaved(updated);
    onClose();
  };

  const previewData = (() => {
    try {
      const meta = JSON.parse(metaDataBuffer);
      return {
        ...meta,
        body: { format: "md", ...(meta.body || {}), content: bodyBuffer },
      };
    } catch {
      return null;
    }
  })();

  return (
    <Modal open={!!doc} onClose={onClose} closeIcon size="large">
      <Modal.Header>
        {doc?.slug ? `Edit document ${doc.slug}` : "Edit document"}
      </Modal.Header>
      <Modal.Content scrolling>
        {error && (
          <Message negative>
            <Icon name="warning circle" /> {error}
          </Message>
        )}
        <Tab
          panes={[
            {
              menuItem: "Form",
              render: () => (
                <Tab.Pane>
                  {schemaError ? (
                    <Message negative>
                      Could not load the document schema. Use the Raw editor tab
                      to make changes.
                    </Message>
                  ) : bridge ? (
                    <AutoForm
                      schema={bridge}
                      model={metaData}
                      onChangeModel={(m) => {
                        setMetaData(m);
                        setMetaDataBuffer(JSON.stringify(m, null, 2));
                      }}
                    >
                      <SchemaForm
                        schema={origSchema}
                        model={metaData}
                        filterPlaceholder="e.g. title, type.primary"
                      />
                    </AutoForm>
                  ) : null}
                </Tab.Pane>
              ),
            },
            {
              menuItem: "Raw editor",
              render: () => (
                <Tab.Pane>
                  <Form>
                    <TextArea
                      rows={20}
                      value={metaDataBuffer}
                      onChange={(e) => {
                        const text = e.target.value;
                        setMetaDataBuffer(text);
                        try {
                          setMetaData(JSON.parse(text));
                        } catch {}
                      }}
                      className="doc-textarea"
                    />
                  </Form>
                </Tab.Pane>
              ),
            },
            {
              menuItem: "Content",
              render: () => (
                <Tab.Pane>
                  <Form>
                    <TextArea
                      rows={20}
                      value={bodyBuffer}
                      onChange={(e) => setBodyBuffer(e.target.value)}
                      className="doc-textarea"
                    />
                  </Form>
                </Tab.Pane>
              ),
            },
            {
              menuItem: "Preview",
              render: () => (
                <Tab.Pane>
                  {previewData ? (
                    <PreviewTab
                      endpoint="/releases/preview_document"
                      data={previewData}
                    />
                  ) : (
                    <p>
                      Invalid JSON in Raw editor tab — fix it to see the
                      preview.
                    </p>
                  )}
                </Tab.Pane>
              ),
            },
          ]}
        />
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={onClose}>Cancel</Button>
        <Button primary onClick={handleSave}>
          <Icon name="save" /> Save
        </Button>
      </Modal.Actions>
    </Modal>
  );
}
