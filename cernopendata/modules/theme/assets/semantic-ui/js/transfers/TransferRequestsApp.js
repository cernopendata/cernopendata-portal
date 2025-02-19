// TransferRequestsApp.jsx
import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";
import axios from "axios";
import { Dropdown, Pagination, Button } from "semantic-ui-react";
import DetailedTable from "./DetailedTable";
import SummaryTable from "./SummaryTable";
import SubscribeModal from "./SubscribeModal";

const TransferRequestsApp = ({ defaultRecid = null }) => {
  const [isModalOpen, setModalOpen] = useState(false);
  const [selectedRecid, setSelectedRecid] = useState(null);
  const [selectedTransferid, setSelectedTransferid] = useState(null);
  const [email, setEmail] = useState("");

  const [statusFilters, setStatusFilters] = useState([]);
  const [actionFilter, setActionFilter] = useState([]);
  const [recordFilter, setRecordFilter] = useState(defaultRecid || "");

  const [summary, setSummary] = useState([]);
  const [details, setDetails] = useState([]);
  const [pagination, setPagination] = useState({ total: 0, pages: 0, current_page: 1, per_page: 50 });
  const [sortField, setSortField] = useState(null);
  const [sortDirection, setSortDirection] = useState(null);


  useEffect(() => {
    const fetchData = async () => {
      try {
        const params = new URLSearchParams({
          page: pagination.current_page,
          per_page: pagination.per_page,
          ...(sortField && { sort: sortField }),
          ...(sortDirection && { direction: sortDirection }),
          ...(statusFilters.length > 0 && { status: statusFilters.join(",") }),
          ...(actionFilter.length > 0 && { action: actionFilter.join(",") }),
          ...(recordFilter && { record: recordFilter })
        });

        const res = await axios.get(`/transfer_requests_content?${params}`);
        setSummary(res.data.summary);
        setDetails(res.data.details);
        setPagination(res.data.pagination || { ...pagination, total: res.data.details.length });
      } catch (err) {
        console.error("Failed to fetch transfer data", err);
      }
    };
    fetchData();
  }, [statusFilters, actionFilter, recordFilter, sortField, sortDirection, pagination.current_page]);

  const formatBytes = (bytes) => {
    if (typeof bytes !== "number" || isNaN(bytes) || bytes <= 0) {
        return "";
    }
    const sizes = ["B", "KB", "MB", "GB", "TB", "PB"];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    const value = bytes / Math.pow(1024, i);
    return `${value.toFixed(2)} ${sizes[i]}`;
  };

  const abbreviateNumber = (num) => {
    if (typeof num !== "number" || isNaN(num)) return "";
    if (num >= 1e9) return (num / 1e9).toFixed(1).replace(/\.0$/, "") + "B";
    if (num >= 1e6) return (num / 1e6).toFixed(1).replace(/\.0$/, "") + "M";
    if (num >= 1e3) return (num / 1e3).toFixed(1).replace(/\.0$/, "") + "K";
    return num.toString();
  };

  const openSubscribeModal = (recid, transferid) => {
    console.log("Opening modal for", recid, transferid);
    setSelectedRecid(recid);
    setSelectedTransferid(transferid);
    setModalOpen(true);
  };

  const handleSubscribe = async () => {
    if (!email) {
      alert("Please enter a valid email.");
      return;
    }
    try {
      await axios.post(`/record/${selectedRecid}/subscribe`, { email, transfer_id: selectedTransferid });
      setModalOpen(false);
    } catch (error) {
      alert(`Error subscribing:  ${error.response.data}`);
      console.error("Error:", error);
    }
  };

  return (
    <div>
      <h2>Transfer Requests</h2>
        <h3>Summary</h3>
          <SummaryTable summary={summary}
            formatBytes={formatBytes}
            abbreviateNumber={abbreviateNumber}
          />

        <h3>Details</h3>
          <DetailedTable
              summary={summary}
              details={details}
              pagination={pagination}
              openSubscribeModal={openSubscribeModal}
              formatBytes={formatBytes}
              initialRecordFilter={recordFilter}
              statusFilters={statusFilters}
              setStatusFilters={setStatusFilters}
              actionFilter={actionFilter}
              setActionFilter={setActionFilter}
              recordFilter={recordFilter}
              setRecordFilter={setRecordFilter}
              abbreviateNumber={abbreviateNumber}
              sortField={sortField}
              sortDirection={sortDirection}
              onSort={(field, direction) => {
                setSortField(field);
                setSortDirection(direction);
                setPagination((prev) => ({ ...prev, current_page: 1 }));
              }}
              onPageChange={(newPage) => {
                setPagination((prev) => ({ ...prev, current_page: newPage }));
              }}
          />
        <SubscribeModal
          isModalOpen={isModalOpen}
          closeModal={() => setModalOpen(false)}
          handleSubscribe={handleSubscribe}
          email={email}
          setEmail={setEmail}
        />
    </div>
  );
};

export default TransferRequestsApp;

const container = document.querySelector("#transfer-requests-react-app");
if (container) {
  const initialRecid = container.dataset.recordId;

  ReactDOM.render(<TransferRequestsApp
        defaultRecid={initialRecid}
        />,
        container);
}
