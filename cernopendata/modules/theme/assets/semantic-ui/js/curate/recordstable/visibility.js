function isEmpty(value) {
  if (value === undefined || value === null) return true;
  if (typeof value === "string" && value.trim() === "") return true;
  if (Array.isArray(value) && value.length === 0) return true;
  return false;
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

  if (path.startsWith("_")) return false;

  if (visibilityMode === "all") {
    return true;
  }

  if (visibilityMode === "selected") {
    // match exact or parent path
    if (!path || selectedSet.size === 0) return true;
    return [...selectedSet].some((field) => path.includes(field));
  }

  if (!isObject && !isArray) {
    return !isEmpty(model);
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
