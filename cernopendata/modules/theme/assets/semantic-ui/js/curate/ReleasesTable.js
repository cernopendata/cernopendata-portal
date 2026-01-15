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
          <Table.HeaderCell>ID</Table.HeaderCell>
          <Table.HeaderCell>Status</Table.HeaderCell>
          <Table.HeaderCell>Created</Table.HeaderCell>
          <Table.HeaderCell>Created by</Table.HeaderCell>
          <Table.HeaderCell>Updated</Table.HeaderCell>
          <Table.HeaderCell>Updated by</Table.HeaderCell>
          <Table.HeaderCell>Records</Table.HeaderCell>
          <Table.HeaderCell>Documents</Table.HeaderCell>
          <Table.HeaderCell>Glossaries</Table.HeaderCell>
          <Table.HeaderCell>Valid RECID</Table.HeaderCell>
          <Table.HeaderCell>Valid DOI</Table.HeaderCell>
          <Table.HeaderCell>Valid Files</Table.HeaderCell>
          <Table.HeaderCell>Number of errors</Table.HeaderCell>
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
            <Table.Cell>{r.status}</Table.Cell>
            <Table.Cell>{formatDate(r.created_at)}</Table.Cell>
            <Table.Cell>{renderUser(r.created_by)}</Table.Cell>
            <Table.Cell>{formatDate(r.updated_at)}</Table.Cell>
            <Table.Cell>{renderUser(r.updated_by)}</Table.Cell>
            <Table.Cell>{r.num_records}</Table.Cell>
            <Table.Cell>{r.num_docs}</Table.Cell>
            <Table.Cell>{r.num_glossaries}</Table.Cell>
            <Table.Cell textAlign="center">
              <Icon
                name={r.valid_recid ? "check" : "close"}
                color={r.valid_recid ? "green" : "red"}
              />
            </Table.Cell>
            <Table.Cell textAlign="center">
              <Icon
                name={r.valid_doi ? "check" : "close"}
                color={r.valid_doi ? "green" : "red"}
              />
            </Table.Cell>
            <Table.Cell textAlign="center">
              <Icon
                name={r.valid_files ? "check" : "close"}
                color={r.valid_files ? "green" : "red"}
              />
            </Table.Cell>
            <Table.Cell>{r.num_errors}</Table.Cell>
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
