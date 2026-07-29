import React from "react";

export default function ReleaseStats({ counts }) {
  const stats = [
    { label: "Records", value: counts.num_records },
    { label: "File indices", value: counts.num_file_indices },
    { label: "Files", value: counts.num_files },
    { label: "Documents", value: counts.num_docs },
  ];

  return (
    <div className="ui four statistics">
      {stats.map((stat) => (
        <div className="statistic" key={stat.label}>
          <div className="value">{stat.value}</div>
          <div className="label">{stat.label}</div>
        </div>
      ))}
    </div>
  );
}
