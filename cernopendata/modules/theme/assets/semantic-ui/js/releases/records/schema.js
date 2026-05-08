import Ajv from "ajv";
import { JSONSchemaBridge } from "uniforms-bridge-json-schema";

const ajv = new Ajv({
  allErrors: true,
  jsonPointers: true,
  strict: false,
});

function stripUnsupported(schema) {
  if (!schema || typeof schema !== "object") return schema;

  const result = { ...schema };

  delete result.additionalProperties;
  delete result.uniqueItems;

  if (result.properties) {
    Object.keys(result.properties).forEach((key) => {
      result.properties[key] = stripUnsupported(result.properties[key]);
    });
  }

  if (result.items) {
    result.items = stripUnsupported(result.items);
  }

  return result;
}

function createValidator(schema) {
  const validate = ajv.compile(schema);

  return (model) => {
    validate(model);

    if (!validate.errors) return null;

    return {
      details: validate.errors.map((error) => ({
        name: error.dataPath?.replace(/^\./, ""),
        message: error.message,
      })),
    };
  };
}

export default function createBridge(schema) {
  const cleanedSchema = stripUnsupported(schema);
  const validator = createValidator(cleanedSchema);
  const bridge = new JSONSchemaBridge({
    schema: cleanedSchema,
    validator: validator,
  });
  return [cleanedSchema, bridge];
}
