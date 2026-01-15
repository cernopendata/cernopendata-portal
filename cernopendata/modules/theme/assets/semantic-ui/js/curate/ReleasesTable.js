import React, { useEffect, useState } from "react";
import { Icon, Table, Loader } from "semantic-ui-react";
import { useNavigate } from "react-router-dom"; // if using React Router

export default function ReleasesTable({experiment}) {
  const [releases, setReleases] = useState([]);
  const [loading, setLoading] = useState(true);
  const experiment_lower = experiment.toLowerCase();
  useEffect(() => {
      let url = `/releases/api/list/${experiment_lower}`;

    fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to fetch releases");
        }
        return response.json();
      })
      .then((data) => {
        setReleases(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error(error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <Loader active inline="centered" />;
  }

  return (
    <Table celled>
      <Table.Header>
        <Table.Row>
          <Table.HeaderCell className="no-glossary">ID</Table.HeaderCell>
          <Table.HeaderCell>Name</Table.HeaderCell>
          <Table.HeaderCell>Status</Table.HeaderCell>
          <Table.HeaderCell>Last update</Table.HeaderCell>
          <Table.HeaderCell>Records</Table.HeaderCell>
          <Table.HeaderCell>Documents</Table.HeaderCell>
          <Table.HeaderCell>Number of errors</Table.HeaderCell>
          <Table.HeaderCell>Discussion</Table.HeaderCell>
        </Table.Row>
      </Table.Header>

      <Table.Body>
        {releases.map((r) => (
          <Table.Row key={r.id}         onClick={() => {
                                          window.location.href = `/releases/${experiment_lower}/${r.id}`;
                                        }}
                                  style={{ cursor: "pointer" }}
                                  className="hoverable">
            <Table.Cell>{r.id}</Table.Cell>
            <Table.Cell>{r.name}</Table.Cell>
            <Table.Cell>{r.last_update.status}</Table.Cell>
            <Table.Cell>{formatDate(r.last_update.timestamp)} by {r.last_update.user}</Table.Cell>
            <Table.Cell>{r.num_records}</Table.Cell>
            <Table.Cell>{r.num_docs}</Table.Cell>
            <Table.Cell>{r.num_errors}</Table.Cell>
            <Table.Cell>{r.dicussion_url}</Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table>
  );
}

function renderUser(user) {
  if (!user) {
    return "–";
  }
  return user.email || user.id;
}

function formatDate(value) {
  if (!value) {
    return "–";
  }
  return new Date(value).toLocaleString();
}
