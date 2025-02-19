// TransferRequestsApp.jsx
import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";
import axios from "axios";
import { Dropdown, Pagination } from "semantic-ui-react";
import DetailedTable from "./DetailedTable";
import SummaryTable from "./SummaryTable";
import SubscribeModal from "./SubscribeModal";

const TransferRequestsApp = () => {
  const [isModalOpen, setModalOpen] = useState(false);
  const [selectedRecid, setSelectedRecid] = useState(null);
  const [selectedTransferid, setSelectedTransferid] = useState(null);
  const [email, setEmail] = useState("");

  const [statusSelected, setStatusSelected] = useState(null);

  const formatBytes = (bytes) => {
        if (!bytes) return "0 B";
        const sizes = ["B", "KB", "MB", "GB", "TB", "PB"];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        const value = bytes / Math.pow(1024, i);
        return `${value.toFixed(2)} ${sizes[i]}`;
  };


  const openSubscribeModal = (recid, transferid) => {
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
             <SummaryTable
                onStatusSelect={setStatusSelected}
             />

            {statusSelected && (<>
               <h3>Details</h3>
                 <DetailedTable
                                       openSubscribeModal={openSubscribeModal}
                                       formatBytes={formatBytes}
                                     />
            </>) }
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
  ReactDOM.render(<TransferRequestsApp />, container);
}
