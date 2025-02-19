import React, { useState, useEffect } from "react";
import axios from "axios";

const SummaryTable = ({summary, formatBytes }) => {
  return (
    <table className="ui celled table">
        <thead>
            <tr><th>Status</th><th>Count</th><th>Number of files</th><th>Size</th></tr>
        </thead>
        <tbody>
            {summary.map((item) => (
                <tr key={item.status}>
                    <td>{item.status}</td>
                    <td>{item.count}</td>
                    <td>{item.files}</td>
                    <td>{formatBytes(item.size)}</td>
                </tr>
            ))}
        </tbody>
    </table>
)};

export default SummaryTable;