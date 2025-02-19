import React, { useState, useEffect } from "react";
import axios from "axios";

const SummaryTable = ({onStatusSelect }) => {

  const [summary, setSummary] = useState([]);

  useEffect(() => {
    axios.get("/stage_requests_summary").then((res) => setSummary(res.data));
  }, []);

  return (
    <table className="ui celled table">
        <thead>
            <tr><th>Status</th><th>Count</th><th>Number of files</th><th>Size</th></tr>
        </thead>
        <tbody>
            {summary.map((item) => (
                <tr key={item.status} onClick={() => onStatusSelect(item.status)} style={{ cursor: "pointer" }}>
                    <td>{item.status}</td>
                    <td>{item.count}</td>
                    <td>{item.files}</td>
                    <td>{item.size}</td>
                </tr>
            ))}
        </tbody>
    </table>
)};

export default SummaryTable;