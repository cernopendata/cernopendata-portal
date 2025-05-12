import React, { useState, useEffect } from "react";
import axios from "axios";

const SummaryTable = ({summary, formatBytes, abbreviateNumber }) => {
  return (
    <table className="ui celled table">
        <thead>
            <tr><th>Action</th><th>Status</th><th>Count</th><th>Number of files</th><th>Size</th></tr>
        </thead>
        <tbody>
            {summary.map((item) => (
                <tr key="{item.action}_{item.status}">
                    <td>{item.action}</td>
                    <td>{item.status}</td>
                    <td>{abbreviateNumber(item.count)}</td>
                    <td>{abbreviateNumber(item.files)}</td>
                    <td>{formatBytes(item.size)}</td>
                </tr>
            ))}
        </tbody>
    </table>
)};

export default SummaryTable;