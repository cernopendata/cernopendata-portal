// TransferRequestsApp.jsx
import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";
import axios from "axios";
import { Dropdown, Pagination, Button } from "semantic-ui-react";
import DetailedTable from "./DetailedTable";
import SummaryTable from "./SummaryTable";
import SubscribeModal from "./SubscribeModal";

const TransferRequestsApp = ({ defaultShowDetails = false, defaultRecid = null }) => {
  const [isModalOpen, setModalOpen] = useState(false);
  const [selectedRecid, setSelectedRecid] = useState(null);
  const [selectedTransferid, setSelectedTransferid] = useState(null);
  const [email, setEmail] = useState("");

  const [summary, setSummary] = useState([]);
  useEffect(() => {
    axios.get("/stage_requests_summary")
      .then((res) => setSummary(res.data))
      .catch((err) => console.error("Failed to fetch summary", err));
  }, []);

  const [showDetails, setShowDetails] = useState(defaultShowDetails);
  const toggleDetails = () => {
    setShowDetails((prev) => {
      const newState = !prev;

      const url = new URL(window.location);
      if (newState) {
        url.searchParams.set("details", "true");
      } else {
        url.searchParams.delete("details"); // or set to "false"
      }

      window.history.pushState({}, "", url); // updates the URL without reload
      return newState;
    });
  };
  const formatBytes = (bytes) => {
        if (!bytes) return "0 B";
        const sizes = ["B", "KB", "MB", "GB", "TB", "PB"];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        const value = bytes / Math.pow(1024, i);
        return `${value.toFixed(2)} ${sizes[i]}`;
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
             <SummaryTable summary={summary} formatBytes={formatBytes}/>

              <Button onClick={toggleDetails} primary>
                {showDetails ? 'Hide Details' : 'Show Details'}
              </Button>

            {showDetails && (<>
               <h3>Details</h3>
                 <DetailedTable summary={summary}
                   openSubscribeModal={openSubscribeModal}
                   formatBytes={formatBytes}
                   initialRecordFilter={defaultRecid}
                 />
            </>)
            }
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
  const showDetailsDefault = container.dataset.showDetails === "true";
  const initialRecid = container.dataset.recordId;

  ReactDOM.render(<TransferRequestsApp
        defaultShowDetails={showDetailsDefault}
        defaultRecid={initialRecid}
        />,
        container);
}
