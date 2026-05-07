import { useState } from "react";

export default function usePagination(items, pageSize = 5) {
  const [page, setPage] = useState(0);
  const totalPages = Math.max(1, Math.ceil(items.length / pageSize));
  const visible = items.slice(page * pageSize, (page + 1) * pageSize);
  return { page, setPage, visible, totalPages };
}
