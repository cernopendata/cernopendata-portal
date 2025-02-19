import React, { useState, useEffect } from "react";
import { Dropdown, Pagination } from "semantic-ui-react";
import axios from "axios";

const DetailedTable = ({
  summary,
  details,
  pagination,
  onSort,
  sortField,
  sortDirection,
  onPageChange,
  openSubscribeModal,
  formatBytes,
  abbreviateNumber,
  initialRecordFilter = "",
  statusFilters,
  setStatusFilters,
  actionFilter,
  setActionFilter,
  recordFilter,
  setRecordFilter
}) => {
    const results = details || [];

    const actions = [...new Set(summary.map(entry => entry.action).filter(Boolean))];
    const statuses = [...new Set(summary.map(entry => entry.status))];

    const updateURLParam = (key, value) => {
      const url = new URL(window.location);
      if (value) {
        url.searchParams.set(key, value);
      } else {
        url.searchParams.delete(key);
      }
      window.history.replaceState({}, "", url);
    };

    // handle sorting
      const handleSort = (field) => {
        const direction = sortField === field && sortDirection === "asc" ? "desc" : "asc";
        onSort(field, direction);
      };


    const handleRecordFilterChange = (event) => {
        const value = event.target.value;
        setRecordFilter(value);
        updateURLParam("record_id", value);
    };

    return (
        <>
            <table className="ui celled table">
                <thead>
                    <tr>
                        <th>Record</th>
                        <th>Action</th>
                        <th onClick={() => handleSort("status")} style={{ cursor: "pointer" }}>
                            Status {sortField === "status" && (
                                <i className={`sort ${sortDirection === "asc" ? "ascending" : "descending"} icon`} />
                            )}
                        </th>
                        <th>Request date</th>
                        <th>Started date</th>
                        <th onClick={() => handleSort("num_files")} style={{ cursor: "pointer" }}>
                            # files {sortField === "num_files" && (
                                <i className={`sort ${sortDirection === "asc" ? "ascending" : "descending"} icon`} />
                            )}
                        </th>
                        <th onClick={() => handleSort("size")} style={{ cursor: "pointer" }}>
                            Size {sortField === "size" && (
                                <i className={`sort ${sortDirection === "asc" ? "ascending" : "descending"} icon`} />
                            )}
                        </th>
                        <th>Completion date</th>
                        <th>Subscribe</th>
                    </tr>
                    <tr>
                        <th>
                            <input
                              type="text"
                              placeholder="Filter by record"
                              value={recordFilter}
                              onChange={(e) => {
                                const value = e.target.value;
                                setRecordFilter(value);
                                updateURLParam("record_id", value);
                              }}
                            />
                        </th>
                        <th>
                            <Dropdown
                              search
                              selection
                              multiple
                              placeholder="Filter by action"
                              options={actions.map((a) => ({
                                key: a,
                                text: a,
                                value: a,
                              }))}
                              value={actionFilter}
                              onChange={(e, { value }) => {
                                setActionFilter(value);
                                updateURLParam("action", value);
                              }}
                            />
                        </th>
                        <th>
                            <Dropdown
                              search
                              selection
                              multiple
                              placeholder="Filter by status"
                              options={statuses.map((status) => ({
                                key: status,
                                text: status,
                                value: status,
                              }))}
                              value={statusFilters}
                              onChange={(e, { value }) => {
                                setStatusFilters(value);
                                updateURLParam("status", value);
                              }}
                            />
                        </th>
                        <th />
                        <th />
                        <th />
                        <th />
                        <th />
                        <th />
                        <th />
                    </tr>
                </thead>
                <tbody>
                    {results.length > 0 ? (
                        results.map((item) => (
                            <tr key={item.id}>
                                <td><a href={`/record/${item.recid}`}>{item.recid}</a></td>
                                <td>{item.action}</td>
                                <td>{item.status}</td>
                                <td>{item.created_at ? new Date(item.created_at).toLocaleString() : ""}</td>
                                <td>{item.started_at ? new Date(item.started_at).toLocaleString() : ""}</td>
                                <td>{abbreviateNumber(item.num_files)}</td>
                                <td>{formatBytes(item.size)}</td>
                                <td>{item.completed_at ? new Date(item.completed_at).toLocaleString() : ""}</td>
                                <td>
                                    {!item.completed_at && (
                                        <button className="ui blue mini button" onClick={() => openSubscribeModal(item.recid, item.id)}>
                                            Subscribe
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan="9">No transfer requests found.</td>
                        </tr>
                    )}
                </tbody>
                <tfoot>
                    <tr>
                        <th colSpan="9">
                            Showing {results.length} entries
                        </th>
                    </tr>
                </tfoot>
            </table>
            {/* Pagination Controls */}
            {pagination && (
                <Pagination
                    activePage={pagination.current_page}
                    totalPages={pagination.pages}
                    onPageChange={(e, data) => onPageChange(data.activePage)}
                    siblingRange={2}
                    boundaryRange={1}
                    ellipsisItem={{ content: "...", icon: true }}
                    firstItem={null}
                    lastItem={null}
                />
            )}
        </>
    );
};

export default DetailedTable;
