function isEmpty(value) {
  if (value === undefined || value === null) return true;
  if (typeof value === "string" && value.trim() === "") return true;
  if (Array.isArray(value) && value.length === 0) return true;
  return false;
}

function matchesSelection(path, selectedSet) {
  const normalised = path
    .split(".")
    .filter((segment) => !/^\d+$/.test(segment))
    .join(".");

  return [...selectedSet].some(
    (field) =>
      normalised === field ||
      normalised.startsWith(`${field}.`) ||
      field.startsWith(`${normalised}.`),
  );
}

export function isVisible({
  schema,
  model,
  path,
  visibilityMode,
  selectedSet,
}) {
  const isObject = schema.type === "object" && schema.properties;
  const isArray = schema.type === "array" && schema.items;

  if (path.startsWith("_") || path.startsWith("$")) return false;

  if (visibilityMode === "all") {
    return true;
  }

  const selecting = visibilityMode === "selected";

  if (selecting) {
    if (!path || selectedSet.size === 0) return true;
    if (matchesSelection(path, selectedSet)) return true;
  }

  if (!isObject && !isArray) {
    return selecting ? false : !isEmpty(model);
  }

  if (isObject) {
    return Object.entries(schema.properties).some(([key, subSchema]) =>
      isVisible({
        schema: subSchema,
        model: model?.[key],
        path: path ? `${path}.${key}` : key,
        visibilityMode,
        selectedSet,
      }),
    );
  }

  if (isArray) {
    return (
      Array.isArray(model) &&
      model.some((item, index) =>
        isVisible({
          schema: schema.items,
          model: item,
          path: `${path}.${index}`,
          visibilityMode,
          selectedSet,
        }),
      )
    );
  }

  return false;
}
