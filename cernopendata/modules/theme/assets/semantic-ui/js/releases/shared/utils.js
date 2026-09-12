import { useState } from "react";

export async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.error || `Request failed (${response.status})`);
  }
  return response.json();
}

export function usePagination(items, pageSize = 5) {
  const [page, setPage] = useState(0);
  const totalPages = Math.max(1, Math.ceil(items.length / pageSize));
  const visible = items.slice(page * pageSize, (page + 1) * pageSize);
  return { page, setPage, visible, totalPages };
}

export function pruneEmpty(value) {
  if (value === null || value === undefined) return undefined;
  if (typeof value === "string") {
    return value.trim() === "" ? undefined : value;
  }
  if (Array.isArray(value)) {
    const cleanedArray = value
      .map(pruneEmpty)
      .filter((item) => item !== undefined);
    return cleanedArray.length === 0 ? undefined : cleanedArray;
  }
  if (typeof value === "object") {
    const cleanedObj = {};
    for (const [k, v] of Object.entries(value)) {
      const cleanedVal = pruneEmpty(v);
      if (cleanedVal !== undefined) {
        cleanedObj[k] = cleanedVal;
      }
    }
    return Object.keys(cleanedObj).length === 0 ? undefined : cleanedObj;
  }
  return value;
}
