import React, { useEffect, useMemo, useState } from "react";
import {
  Checkbox,
  Dropdown,
  Icon,
  Input,
  Label,
  Loader,
  Popup,
  Table,
} from "semantic-ui-react";

const statusToStep = {
  EDITING: "DRAFT",
  READY: "DRAFT",
  STAGING: "DRAFT",
  PUBLISHING: "STAGED",
};

function stepOf(release) {
  return statusToStep[release.status] || release.status;
}

function stepIcon(release) {
  switch (stepOf(release)) {
    case "PUBLISHED":
      return { name: "check circle outline", color: "green" };
    case "STAGED":
      return { name: "clock outline", color: "blue" };
    case "DRAFT":
      return { name: "circle outline", color: "grey" };
    default:
      return { name: "question circle outline", color: "grey" };
  }
}

function sortValue(release, field) {
  switch (field) {
    case "name":
      return release.name || "";
    case "step":
      return stepOf(release);
    case "last_update":
      return release.last_update
        ? new Date(release.last_update.timestamp).getTime()
        : null;
    case "num_records":
      return release.num_records;
    case "num_docs":
      return release.num_docs;
    default:
      return null;
  }
}

function compareReleases(left, right, field, direction) {
  const leftValue = sortValue(left, field);
  const rightValue = sortValue(right, field);

  if (leftValue == null && rightValue == null) return 0;
  if (leftValue == null) return 1;
  if (rightValue == null) return -1;

  const order =
    typeof leftValue === "string"
      ? leftValue.localeCompare(rightValue)
      : leftValue - rightValue;
  return direction === "asc" ? order : -order;
}

function formatLastUpdate(lastUpdate) {
  if (!lastUpdate) {
    return "-";
  }
  const when = new Date(lastUpdate.timestamp).toLocaleString();
  return lastUpdate.user ? `${when} by ${lastUpdate.user}` : when;
}

export default function ReleasesTable({ experiment }) {
  const [releases, setReleases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const [sortField, setSortField] = useState(null);
  const [sortDirection, setSortDirection] = useState("asc");
  const [nameFilter, setNameFilter] = useState("");
  const [stepFilters, setStepFilters] = useState([]);
  const [showPublished, setShowPublished] = useState(true);

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
      .catch((err) => {
        console.error(err);
        setError(true);
        setLoading(false);
      });
  }, []);

  const publishFilteredReleases = useMemo(
    () =>
      showPublished
        ? releases
        : releases.filter((release) => stepOf(release) !== "PUBLISHED"),
    [releases, showPublished],
  );

  const stepOptions = useMemo(() => {
    const steps = [...new Set(publishFilteredReleases.map(stepOf))];
    return steps.map((step) => ({ key: step, text: step, value: step }));
  }, [publishFilteredReleases]);

  const visibleReleases = useMemo(() => {
    const normalizedNameFilter = nameFilter.trim().toLowerCase();
    const filtered = publishFilteredReleases.filter((release) => {
      const matchesName =
        !normalizedNameFilter ||
        (release.name || "").toLowerCase().includes(normalizedNameFilter);
      const matchesStep =
        stepFilters.length === 0 || stepFilters.includes(stepOf(release));
      return matchesName && matchesStep;
    });

    if (!sortField) {
      return filtered;
    }
    return [...filtered].sort((left, right) =>
      compareReleases(left, right, sortField, sortDirection),
    );
  }, [
    publishFilteredReleases,
    nameFilter,
    stepFilters,
    sortField,
    sortDirection,
  ]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const sortedProp = (field) => {
    if (sortField !== field) {
      return null;
    }
    return sortDirection === "asc" ? "ascending" : "descending";
  };

  return (
    <>
      {loading ? (
        <Loader active inline="centered" />
      ) : (
        <Table
          celled
          selectable
          striped
          sortable
          size="small"
          className="hoverable-row-table releases-table"
        >
          <Table.Header>
            <Table.Row>
              <Table.HeaderCell
                sorted={sortedProp("name")}
                onClick={() => handleSort("name")}
              >
                Name
              </Table.HeaderCell>
              <Table.HeaderCell
                sorted={sortedProp("step")}
                onClick={() => handleSort("step")}
              >
                Step
              </Table.HeaderCell>
              <Table.HeaderCell
                rowSpan="2"
                sorted={sortedProp("last_update")}
                onClick={() => handleSort("last_update")}
              >
                Last update
              </Table.HeaderCell>
              <Table.HeaderCell
                rowSpan="2"
                className="col-count"
                sorted={sortedProp("num_records")}
                onClick={() => handleSort("num_records")}
              >
                Records
              </Table.HeaderCell>
              <Table.HeaderCell
                rowSpan="2"
                className="col-count"
                sorted={sortedProp("num_docs")}
                onClick={() => handleSort("num_docs")}
              >
                Documents
              </Table.HeaderCell>
              <Table.HeaderCell rowSpan="2" className="discussion-column">
                Discussion
              </Table.HeaderCell>
            </Table.Row>
            <Table.Row>
              <Table.HeaderCell>
                <Input
                  fluid
                  icon="search"
                  iconPosition="left"
                  placeholder="Filter by name"
                  value={nameFilter}
                  onChange={(_, data) => setNameFilter(data.value)}
                />
              </Table.HeaderCell>
              <Table.HeaderCell>
                <Dropdown
                  selection
                  multiple
                  search
                  fluid
                  placeholder="Filter by step"
                  options={stepOptions}
                  value={stepFilters}
                  onChange={(_, data) => setStepFilters(data.value)}
                />
              </Table.HeaderCell>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {error ? (
              <Table.Row>
                <Table.Cell colSpan="6" textAlign="center">
                  <Icon name="warning circle" /> Could not load releases.
                </Table.Cell>
              </Table.Row>
            ) : visibleReleases.length === 0 ? (
              <Table.Row>
                <Table.Cell colSpan="6" textAlign="center">
                  No releases found.
                </Table.Cell>
              </Table.Row>
            ) : (
              visibleReleases.map((release) => (
                <Table.Row
                  key={release.id}
                  onClick={() => {
                    window.location.href = `/releases/${experiment_lower}/${release.id}`;
                  }}
                  style={{ cursor: "pointer" }}
                >
                  <Table.Cell>{release.name}</Table.Cell>
                  <Table.Cell>
                    <div className="release-step">
                      <span className="release-step-icon">
                        <Icon {...stepIcon(release)} />
                      </span>
                      {stepOf(release)}
                      {release.num_errors > 0 && (
                        <Popup
                          size="tiny"
                          position="top center"
                          content={`${release.num_errors} error${release.num_errors !== 1 ? "s" : ""}`}
                          trigger={
                            <Label circular color="red" size="tiny">
                              {release.num_errors}
                            </Label>
                          }
                        />
                      )}
                    </div>
                  </Table.Cell>
                  <Table.Cell>
                    {formatLastUpdate(release.last_update)}
                  </Table.Cell>
                  <Table.Cell>{release.num_records}</Table.Cell>
                  <Table.Cell>{release.num_docs}</Table.Cell>
                  <Table.Cell textAlign="center" className="discussion-column">
                    {release.discussion && (
                      <a
                        href={release.discussion}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(event) => event.stopPropagation()}
                      >
                        <Icon name="linkify" />
                        Open discussion
                      </a>
                    )}
                  </Table.Cell>
                </Table.Row>
              ))
            )}
          </Table.Body>
          {!error && (
            <Table.Footer>
              <Table.Row>
                <Table.HeaderCell colSpan="6">
                  <div className="releases-table-footer">
                    <span>
                      {visibleReleases.length === releases.length
                        ? `Showing ${releases.length} releases`
                        : `Showing ${visibleReleases.length} of ${releases.length} releases`}
                    </span>
                    <Checkbox
                      className="show-published-filter"
                      label="Show published releases"
                      checked={showPublished}
                      onChange={(_, data) => setShowPublished(data.checked)}
                    />
                  </div>
                </Table.HeaderCell>
              </Table.Row>
            </Table.Footer>
          )}
        </Table>
      )}
    </>
  );
}
