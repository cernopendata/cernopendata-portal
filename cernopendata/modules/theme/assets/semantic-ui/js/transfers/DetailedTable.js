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
    const direction =
      sortField === field && sortDirection === "asc" ? "desc" : "asc";
    onSort(field, direction);
  };

  const handleRecordFilterChange = (event) => {
    const value = event.target.value;
    setRecordFilter(value);
    updateURLParam("record_id", value);
  };

  return (
    <>
      <Table
        celled
        sortable
        compact
        size="small"
        className="hoverable-row-table"
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
            <Table.HeaderCell rowSpan="2">Request date</Table.HeaderCell>
            <Table.HeaderCell rowSpan="2">Started date</Table.HeaderCell>
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
                sortField === "num_files"
                  ? sortDirection === "asc"
                    ? "ascending"
                    : "descending"
                  : null
              }
              onClick={() => handleSort("num_files")}
              rowSpan="2"
            >
              # issued
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
            <Table.HeaderCell rowSpan="2">
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
                  const value = e.target.value;
                  setRecordFilter(value);
                  updateURLParam("record_id", value);
                }}
                className="narrow-filter"
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
                  setActionFilter(value);
                  updateURLParam("action", value);
                }}
                className="narrow-filter"
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
                  setStatusFilters(value);
                  updateURLParam("status", value);
                }}
                className="narrow-filter"
              />
            </Table.HeaderCell>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {results.length > 0 ? (
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
                  <Table.Cell>{abbreviateNumber(item.num_files)}</Table.Cell>
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
        />
      )}
    </>
  );
};

export default DetailedTable;
