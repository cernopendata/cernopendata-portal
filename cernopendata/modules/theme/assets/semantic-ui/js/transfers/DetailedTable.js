import React, { useState, useEffect } from "react";
import { Dropdown, Pagination } from "semantic-ui-react";
import axios from "axios";

const DetailedTable = ({
    openSubscribeModal,
    formatBytes
}) => {
    const [results, setResults] = useState([]);
    const [pagination, setPagination] = useState({ total: 0, pages: 0, current_page: 1, per_page: 50 });

    const totalFiles = results.reduce((sum, item) => sum + (item.num_files || 0), 0);
    const totalSize = results.reduce((sum, item) => sum + (item.size || 0), 0);
    const [sortField, setSortField] = useState(null);
    const [sortDirection, setSortDirection] = useState(null);

    const [statusFilters, setStatusFilter] = useState([]);

    const statusOptions = [
        { key: 'submitted', text: 'Submitted', value: 'submitted' },
        { key: 'to_archive', text: 'To archive', value: 'to_archive' },
        { key: 'archiving', text: 'Archiving', value: 'archiving' },
        { key: 'completed', text: 'Completed', value: 'completed' },
    ];

    const handleSort = (field) => {
      const direction = (sortField === field && sortDirection === "asc") ? "desc" : "asc";
      setSortField(field);
      setSortDirection(direction);
      fetchData(pagination.current_page, pagination.per_page, { status:  statusFilters });
    };

    useEffect(() => {
      fetchData(1, pagination.per_page, { status: statusFilters });
    }, [statusFilters]);

  const fetchData = async (page = 1, perPage = 50, filters = {}) => {
    try {

      const { status = [] } = filters;
      const params = new URLSearchParams({
        page,
        per_page: perPage,
        ...(sortField && { sort: sortField }),
        ...(sortDirection && { direction: sortDirection }),
        ...(status.length ? { status: status.join(",") } : {})
      });
      const response = await axios.get(`/stage_requests_table?${params}`);
      setResults(response.data.results || []);
      setPagination(response.data.pagination || { total: 0, pages: 0, current_page: page, per_page: perPage });
    } catch (error) {
      console.error("Error fetching data:", error);
      setResults([]);
    }
  };

    const handlePageChange = (newPage) => {
      if (newPage >= 1 && newPage <= pagination.pages) {
        fetchData(newPage, pagination.per_page, { status:  statusFilters });
      }
    };

    return (
        <>
            <table className="ui celled table">
                <thead>
                    <tr>
                        <th>Record</th>
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
                        <th onClick={() => handleSort("status")} style={{ cursor: "pointer" }}>
                            Status {sortField === "status" && (
                                <i className={`sort ${sortDirection === "asc" ? "ascending" : "descending"} icon`} />
                            )}
                        </th>
                        <th>Request date</th>
                        <th>Started date</th>
                        <th>Completion date</th>
                        <th>Cleaned date</th>
                        <th>Subscribe</th>
                    </tr>
                    <tr>
                        <th />
                        <th />
                        <th />
                        <th>
                            <Dropdown
                                search
                                selection
                                multiple
                                placeholder="Filter by status"
                                options={statusOptions}
                                value={statusFilters}
                                onChange={(e, { value }) => setStatusFilter(value)}
                            />
                        </th>
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
                                <td>{item.num_files}</td>
                                <td>{formatBytes(item.size)}</td>
                                <td>{item.status}</td>
                                <td>{item.created_at ? new Date(item.created_at * 1000).toLocaleString() : ""}</td>
                                <td>{item.started_at ? new Date(item.started_at * 1000).toLocaleString() : ""}</td>
                                <td>{item.completed_at ? new Date(item.completed_at * 1000).toLocaleString() : ""}</td>
                                <td>{item.cleaned_at ? new Date(item.cleaned_at * 1000).toLocaleString() : ""}</td>
                                <td>
                                    {!item.completed_at && (
                                        <button className="ui blue button" onClick={() => openSubscribeModal(item.recid, item.id)}>
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
                            Showing {results.length} entries | Total files: {totalFiles} | Total size: {formatBytes(totalSize)}
                        </th>
                    </tr>
                </tfoot>
            </table>
            {/* Pagination Controls */}
            <Pagination
                activePage={pagination.current_page}
                totalPages={pagination.pages}
                onPageChange={(e, data) => handlePageChange(data.activePage)}
                siblingRange={1} // how many pages to show on each side
                boundaryRange={1} // how many boundary pages to show (start/end)
                ellipsisItem={{ content: '...', icon: true }}
                firstItem={null}
                lastItem={null}
            />
        </>
    );
};

export default DetailedTable;