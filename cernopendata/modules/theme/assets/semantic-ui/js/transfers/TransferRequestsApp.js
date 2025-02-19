import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";
import axios from "axios";

const getVisiblePages = (current, total, maxVisible = 10) => {
    const pages = [];

    if (total <= maxVisible + 2) {
        for (let i = 1; i <= total; i++) pages.push(i);
        return pages;
    }

    const start = Math.max(2, current - Math.floor(maxVisible / 2));
    const end = Math.min(total - 1, start + maxVisible - 1);

    pages.push(1);

    if (start > 2) pages.push("ellipsis-start");

    for (let i = start; i <= end; i++) {
        pages.push(i);
    }

    if (end < total - 1) pages.push("ellipsis-end");

    pages.push(total);

    return pages;
};

const TransferRequestsApp = () => {
    const [results, setResults] = useState([]);
    const [pagination, setPagination] = useState({ total: 0, pages: 0, current_page: 1, per_page: 10 });
    const [loading, setLoading] = useState(true);

    // State for subscription modal
    const [isModalOpen, setModalOpen] = useState(false);
    const [selectedRecid, setSelectedRecid] = useState(null);
    const [selectedTransferid, setSelectedTransferid] = useState(null);
    const [email, setEmail] = useState("");

    const fetchData = async (page = 1, perPage = 200) => {
        try {
            setLoading(true);
            const response = await axios.get(`/stage_requests_table?page=${page}&per_page=${perPage}`);
            setResults(response.data.results || []);
            setPagination(response.data.pagination || { total: 0, pages: 0, current_page: 1, per_page: 200 });
        } catch (error) {
            console.error("Error fetching data:", error);
            setResults([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData(pagination.current_page, pagination.per_page);
    }, []);

    const handlePageChange = (newPage) => {
        if (newPage >= 1 && newPage <= pagination.pages) {
            fetchData(newPage, pagination.per_page);
        }
    };

    // Open subscription modal
    const openSubscribeModal = (recid, transferid) => {
        setSelectedRecid(recid);
        setSelectedTransferid(transferid);
        setModalOpen(true);
    };

    // Handle subscription submission
    const handleSubscribe = async () => {
        if (!email) {
            alert("Please enter a valid email.");
            return;
        }

        try {
            await axios.post(`/record/${selectedRecid}/subscribe`, {
                email: email,
                transfer_id: selectedTransferid
            });
            setModalOpen(false); // Close modal after successful subscription
        } catch (error) {
            alert(`Error subscribing:  ${error.response.data}`);
            console.error("Error:", error);
        }
    };

    return (
        <div>
            <h2>Transfer Requests</h2>
            {loading ? (
                <p>Loading...</p>
            ) : (
                <>
                    <table className="ui celled table">
                        <thead>
                            <tr>
                                <th>Record</th>
                                <th># files</th>
                                <th>Status</th>
                                <th>Request date</th>
                                <th>Started date</th>
                                <th>Completion date</th>
                                <th>Cleaned date</th>
                                <th>Subscribe</th>
                            </tr>
                        </thead>
                        <tbody>
                            {results.length > 0 ? (
                                results.map((item) => (
                                    <tr key={item.id}>
                                        <td><a href={`/record/${item.recid}`}>{item.recid}</a></td>
                                        <td>{item.num_files}</td>
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
                                    <td colSpan="8">No transfer requests found.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>

                    {/* Pagination Controls */}
                    <div className="ui pagination menu">
                        <button
                            className={`item ${pagination.current_page === 1 ? "disabled" : ""}`}
                            onClick={() => handlePageChange(pagination.current_page - 1)}
                        >
                            Previous
                        </button>

                        {getVisiblePages(pagination.current_page, pagination.pages).map((page, idx) => {
                            if (page === "ellipsis-start" || page === "ellipsis-end") {
                                return (
                                    <div key={idx} className="item disabled">
                                        ...
                                    </div>
                                );
                            }
                            return (
                                <button
                                    key={page}
                                    className={`item ${pagination.current_page === page ? "active" : ""}`}
                                    onClick={() => handlePageChange(page)}
                                >
                                    {page}
                                </button>
                            );
                        })}

                        <button
                            className={`item ${pagination.current_page === pagination.pages ? "disabled" : ""}`}
                            onClick={() => handlePageChange(pagination.current_page + 1)}
                        >
                            Next
                        </button>
                    </div>

                    {/* Subscription Modal */}
                    {isModalOpen && (
                        <div className="ui modal active">
                            <div className="header">Subscribe for Updates</div>
                            <div className="content">
                                <p>Enter your email to subscribe to updates for this record.</p>
                                <div className="ui input fluid">
                                    <input
                                        type="email"
                                        placeholder="Enter your email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                    />
                                </div>
                            </div>
                            <div className="actions">
                                <button className="ui cancel button" onClick={() => setModalOpen(false)}>Cancel</button>
                                <button className="ui primary button" onClick={handleSubscribe}>Subscribe</button>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default TransferRequestsApp;

const container = document.querySelector("#transfer-requests-react-app");
if (container) {
    ReactDOM.render(<TransferRequestsApp />, container);
}
