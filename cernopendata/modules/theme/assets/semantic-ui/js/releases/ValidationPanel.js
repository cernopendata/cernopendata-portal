import React, { useState } from "react";
import { Button, Icon, Message } from "semantic-ui-react";

import ValidationToggle from "./ValidationToggle";
import { fetchJson } from "./shared/utils";

const EDITABLE_STATUSES = ["DRAFT", "READY", "EDITING"];
const ERROR_LIST_STATUSES = [...EDITABLE_STATUSES, "STAGED", "PUBLISHED"];

export default function ValidationPanel({
  experiment,
  releaseId,
  validations,
  errors,
  numErrors,
  releaseStatus,
  hasRecords,
  hasDocuments,
  onValidationsChanged,
  onFixed,
}) {
  const [fixing, setFixing] = useState(false);
  const [fixError, setFixError] = useState(null);
  const [retrying, setRetrying] = useState(false);
  const [retryError, setRetryError] = useState(null);

  const visible = validations
    .filter(
      (validation) =>
        !(validation.is_document_validation && !hasDocuments) &&
        !(validation.is_record_validation && !hasRecords),
    )
    .sort((a, b) => a.name.localeCompare(b.name));

  const failed = visible.filter(
    (validation) => validation.enabled && !validation.status,
  );
  const optional = visible.filter(
    (validation) => validation.optional && !validation.enabled,
  );
  const passed = visible.filter(
    (validation) => validation.enabled && validation.status,
  );

  const rows = [...failed, ...optional, ...passed];
  const hasAutomaticFix = failed.some((validation) => validation.fixable);
  const canRetryDois = releaseStatus === "PUBLISHED" && numErrors > 0;

  async function handleFix() {
    setFixing(true);
    setFixError(null);
    try {
      const summary = await fetchJson(
        `/releases/${experiment}/${releaseId}/fix_checks`,
        { method: "POST" },
      );
      onFixed(summary);
    } catch (err) {
      setFixError(err.message);
    } finally {
      setFixing(false);
    }
  }

  async function handleRetryDois() {
    setRetrying(true);
    setRetryError(null);
    try {
      await fetchJson(`/releases/${experiment}/${releaseId}/retry_dois`, {
        method: "POST",
      });
      onValidationsChanged();
    } catch (err) {
      setRetryError(err.message);
    } finally {
      setRetrying(false);
    }
  }

  return (
    <>
      {EDITABLE_STATUSES.includes(releaseStatus) && (
        <>
          <div className="ui segment validation-segment">
            <div className="validation-header">
              <strong>
                <Icon name="tasks" />
                Validations
              </strong>
              <div className="validation-header-labels">
                {failed.length > 0 && (
                  <span className="ui red label">{failed.length} failed</span>
                )}
                {passed.length > 0 && (
                  <span className="ui green label">{passed.length} passed</span>
                )}
                {optional.length > 0 && (
                  <span className="ui grey label">
                    {optional.length} optional
                  </span>
                )}
              </div>
            </div>

            {rows.map((validation, index) => (
              <div
                key={validation.id}
                className={`validation-row${index < rows.length - 1 ? " validation-row-bordered" : ""}`}
              >
                <div className="validation-row-icon">
                  {validation.enabled ? (
                    <Icon
                      name={validation.status ? "check circle" : "times circle"}
                      color={validation.status ? "green" : "red"}
                    />
                  ) : (
                    <Icon name="pause" color="grey" />
                  )}
                </div>

                <div className="validation-row-body">
                  {validation.enabled && !validation.status ? (
                    <b>{validation.name}</b>
                  ) : (
                    <span className="validation-name-ok">
                      {validation.name}
                    </span>
                  )}
                  {validation.enabled &&
                    !validation.status &&
                    validation.error_message && (
                      <div className="validation-error-message">
                        {validation.error_message}
                      </div>
                    )}
                </div>

                <div className="validation-row-actions">
                  {validation.optional && (
                    <ValidationToggle
                      validation={validation}
                      onToggle={onValidationsChanged}
                    />
                  )}
                  {validation.enabled &&
                    validation.fixable &&
                    !validation.status && (
                      <span
                        className="ui tiny blue label"
                        data-tooltip="Can be fixed automatically"
                        data-position="top center"
                      >
                        <Icon name="magic" /> Auto-fixable
                      </span>
                    )}
                </div>
              </div>
            ))}
          </div>

          {fixError && (
            <Message negative>
              <Icon name="warning circle" /> {fixError}
            </Message>
          )}

          {hasAutomaticFix && (
            <div className="ui info message validation-autofix-message">
              <div>
                <strong>
                  <Icon name="magic" /> Automatic fixes available
                </strong>
                <div>Some issues above can be resolved automatically.</div>
              </div>
              <Button
                primary
                loading={fixing}
                disabled={fixing}
                onClick={handleFix}
              >
                <Icon name="magic" /> Fix automatically
              </Button>
            </div>
          )}
        </>
      )}

      {errors.length > 0 && ERROR_LIST_STATUSES.includes(releaseStatus) && (
        <div className="ui negative message">
          <div className="header">
            Showing {errors.length} of {numErrors} errors
          </div>
          <ul className="list">
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {retryError && (
        <Message negative>
          <Icon name="warning circle" /> {retryError}
        </Message>
      )}

      {canRetryDois && (
        <div className="ui info message validation-autofix-message">
          <div>
            <strong>
              <Icon name="redo" /> Retry the DOI registration
            </strong>
            <div>
              The records whose DOI is not registered with DataCite yet will be
              sent again.
            </div>
          </div>
          <Button
            primary
            loading={retrying}
            disabled={retrying}
            onClick={handleRetryDois}
          >
            <Icon name="redo" /> Retry
          </Button>
        </div>
      )}
    </>
  );
}
