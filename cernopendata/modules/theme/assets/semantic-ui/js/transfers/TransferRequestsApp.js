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
  const [actionFilter, setActionFilter] = useState(null);
  const [recordFilter, setRecordFilter] = useState(defaultRecid || "");

  const [summary, setSummary] = useState([]);
  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const params = new URLSearchParams();
        if (statusFilters.length > 0) params.set("status", statusFilters.join(","));
        if (actionFilter) params.set("action", actionFilter);
        if (recordFilter) params.set("record", recordFilter);
        const res = await axios.get(`/stage_requests_summary?${params}`);
        setSummary(res.data);
      } catch (err) {
        console.error("Failed to fetch summary", err);
      }
    };

    fetchSummary();
  }, [statusFilters, actionFilter, recordFilter]);

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
          <DetailedTable summary={summary}
            summary={summary}
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
