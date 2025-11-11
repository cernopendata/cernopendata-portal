import React from "react";
import {
  Dropdown,
  Pagination,
  Popup,
  Table,
  Input,
  Button,
} from "semantic-ui-react";

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
  setRecordFilter,
  isLoading,
}) => {
  const results = details || [];

  const actions = [
    ...new Set(summary.map((entry) => entry.action).filter(Boolean)),
  ];
  const statuses = [...new Set(summary.map((entry) => entry.status))];

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
    if (isLoading) {
      return;
    }
    const direction =
      sortField === field && sortDirection === "asc" ? "desc" : "asc";
    onSort(field, direction);
  };

  const getSuccessfulTransferCount = (item) => {
    if (item.num_failed_transfers !== null) {
      return item.num_transfers - item.num_failed_transfers;
    }
    return item.num_transfers;
  };

  return (
    <>
      <Table
        celled
        sortable={!isLoading}
        compact
        size="small"
        className="hoverable-row-table"
        style={isLoading ? { pointerEvents: "none", opacity: 0.8 } : {}}
      >
        <Table.Header>
          <Table.Row>
            <Table.HeaderCell>Record</Table.HeaderCell>
            <Table.HeaderCell>Action</Table.HeaderCell>
            <Table.HeaderCell
              sorted={
                sortField === "status"
                  ? sortDirection === "asc"
                    ? "ascending"
                    : "descending"
                  : null
              }
              onClick={() => handleSort("status")}
            >
              Status
            </Table.HeaderCell>
            <Table.HeaderCell
              rowSpan="2"
              sorted={
                sortField === "created_at"
                  ? sortDirection === "asc"
                    ? "ascending"
                    : "descending"
                  : null
              }
              onClick={() => handleSort("created_at")}
            >
              Request date
            </Table.HeaderCell>
            <Table.HeaderCell
              rowSpan="2"
              sorted={
                sortField === "started_at"
                  ? sortDirection === "asc"
                    ? "ascending"
                    : "descending"
                  : null
              }
              onClick={() => handleSort("started_at")}
            >
              Started date
            </Table.HeaderCell>
            <Table.HeaderCell
              sorted={
                sortField === "num_record_files"
                  ? sortDirection === "asc"
                    ? "ascending"
                    : "descending"
                  : null
              }
              onClick={() => handleSort("num_record_files")}
              rowSpan="2"
              singleLine
            >
              # files
            </Table.HeaderCell>
            <Table.HeaderCell
              sorted={
                sortField === "record_size"
                  ? sortDirection === "asc"
                    ? "ascending"
                    : "descending"
                  : null
              }
              onClick={() => handleSort("record_size")}
              rowSpan="2"
              singleLine
            >
              Size
            </Table.HeaderCell>
            <Table.HeaderCell
              sorted={
                sortField === "num_transfers"
                  ? sortDirection === "asc"
                    ? "ascending"
                    : "descending"
                  : null
              }
              onClick={() => handleSort("num_transfers")}
              rowSpan="2"
            >
              # successful
              <br />
              transfers
            </Table.HeaderCell>
            <Table.HeaderCell
              sorted={
                sortField === "size"
                  ? sortDirection === "asc"
                    ? "ascending"
                    : "descending"
                  : null
              }
              onClick={() => handleSort("size")}
              rowSpan="2"
            >
              Size of issued
              <br />
              transfers
            </Table.HeaderCell>
            <Table.HeaderCell
              rowSpan="2"
              sorted={
                sortField === "completed_at"
                  ? sortDirection === "asc"
                    ? "ascending"
                    : "descending"
                  : null
              }
              onClick={() => handleSort("completed_at")}
            >
              Completion
              <br />
              date
            </Table.HeaderCell>
            <Table.HeaderCell rowSpan="2">Subscribe</Table.HeaderCell>
          </Table.Row>
          <Table.Row>
            <Table.HeaderCell>
              <Input
                type="text"
                placeholder="Filter by record"
                defaultValue={recordFilter}
                onChange={(e) => {
                  if (isLoading) return;
                  const value = e.target.value;
                  setRecordFilter(value);
                  updateURLParam("record_id", value);
                }}
                className="narrow-filter"
                disabled={isLoading}
              ></Input>
            </Table.HeaderCell>
            <Table.HeaderCell>
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
                  if (isLoading) return;
                  setActionFilter(value);
                  updateURLParam("action", value);
                }}
                className="narrow-filter"
                disabled={isLoading}
              />
            </Table.HeaderCell>
            <Table.HeaderCell>
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
                  if (isLoading) return;
                  setStatusFilters(value);
                  updateURLParam("status", value);
                }}
                className="narrow-filter"
                disabled={isLoading}
              />
            </Table.HeaderCell>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {isLoading ? (
            <Table.Row>
              <Table.Cell colSpan="11" textAlign="center">
                <i className="spinner loading icon large" />
                Loading transfer requests...
              </Table.Cell>
            </Table.Row>
          ) : results.length > 0 ? (
            results.map((item) => {
              const hasHotFiles = item.num_hot_files != null;
              const hasColdFiles = item.num_cold_files != null;
              const rowContent = (
                <Table.Row key={item.id}>
                  <Table.Cell>
                    <a href={`/record/${item.recid}`}>{item.recid}</a>
                  </Table.Cell>
                  <Table.Cell>{item.action}</Table.Cell>
                  <Table.Cell>{item.status}</Table.Cell>
                  <Table.Cell>
                    {item.created_at
                      ? new Date(item.created_at).toLocaleString()
                      : ""}
                  </Table.Cell>
                  <Table.Cell>
                    {item.started_at
                      ? new Date(item.started_at).toLocaleString()
                      : ""}
                  </Table.Cell>
                  <Table.Cell>
                    {abbreviateNumber(item.num_record_files)}
                  </Table.Cell>
                  <Table.Cell singleLine>
                    {formatBytes(item.record_size)}
                  </Table.Cell>
                  <Table.Cell>
                    {abbreviateNumber(getSuccessfulTransferCount(item))}
                  </Table.Cell>
                  <Table.Cell singleLine>{formatBytes(item.size)}</Table.Cell>
                  <Table.Cell>
                    {item.completed_at
                      ? new Date(item.completed_at).toLocaleString()
                      : ""}
                  </Table.Cell>
                  <Table.Cell>
                    {!item.completed_at && (
                      <Button
                        color="blue"
                        size="mini"
                        onClick={() => openSubscribeModal(item.recid, item.id)}
                        disabled={isLoading}
                      >
                        Subscribe
                      </Button>
                    )}
                  </Table.Cell>
                </Table.Row>
              );

              return (
                <Popup
                  key={`popup-${item.id}`}
                  trigger={rowContent}
                  position="top center"
                  on="hover"
                  content={
                    <div style={{ textAlign: "left" }}>
                      <>
                        {(hasHotFiles || hasColdFiles) && (
                          <>
                            {hasHotFiles && (
                              <span>{item.num_hot_files} files on hot</span>
                            )}
                            {hasColdFiles && (
                              <>
                                {hasHotFiles && <br />}
                                <span>{item.num_cold_files} files on cold</span>
                              </>
                            )}
                            <div
                              style={{
                                margin: "10px 0",
                                borderTop: "1px solid #ccc",
                              }}
                            />
                          </>
                        )}

                        <span>
                          {item.file
                            ? "One file requested"
                            : "All files requested"}
                        </span>

                        {item.num_failed_transfers > 0 && (
                          <>
                            <div
                              style={{
                                margin: "10px 0",
                                borderTop: "1px solid #ccc",
                              }}
                            />
                            <span>
                              {abbreviateNumber(item.num_failed_transfers)}{" "}
                              failed transfers
                            </span>
                          </>
                        )}
                      </>
                    </div>
                  }
                />
              );
            })
          ) : (
            <Table.Row>
              <Table.Cell colSpan="11">No transfer requests found.</Table.Cell>
            </Table.Row>
          )}
        </Table.Body>
        <Table.Footer>
          <Table.Row>
            <Table.HeaderCell colSpan="11">
              Showing {results.length} entries
            </Table.HeaderCell>
          </Table.Row>
        </Table.Footer>
      </Table>
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
          disabled={isLoading}
        />
      )}
    </>
  );
};

export default DetailedTable;
