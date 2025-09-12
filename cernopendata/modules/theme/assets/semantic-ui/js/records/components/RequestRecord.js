import React, { useState } from "react";
import { Button, Modal, Form, Checkbox, Message } from "semantic-ui-react";
import PropTypes from "prop-types";
import axios from "axios";

import { toHumanReadableSize } from "../utils";
import { useModal } from "../hooks";
import { 
  AVAILABILITY_STATES, 
  MESSAGES, 
  BUTTON_LABELS, 
  FORM_LABELS 
} from "../constants";
import { RECORD_STAGE_URL, TRANSFER_REQUESTS_URL } from "../config";

/**
 * Request confirmation modal component
 */
const RequestModal = ({ 
  open, 
  onClose, 
  onSubmit, 
  loading, 
  file, 
  num_files, 
  size, 
  email, 
  setEmail, 
  confirmed, 
  setConfirmed 
}) => (
  <Modal open={open} onClose={onClose} size="small">
    <Modal.Header>Request to make data available</Modal.Header>
    <Modal.Content>
      <p>
        Please confirm you want to request {file ? 'this file' : 'all files of the record'}.
      </p>
      <Message warning>
        <p>{MESSAGES.REQUEST_TIME_WARNING}</p>
        <Checkbox
          label={`I confirm that I want to request ${
            num_files ? `${num_files} files` : "this file"
          }${size ? ` (${toHumanReadableSize(size)} of data)` : ""}`}
          checked={confirmed}
          onChange={(e, data) => setConfirmed(data.checked)}
        />
      </Message>
      <Form>
        <Form.Field>
          <label htmlFor="email-input">
            {FORM_LABELS.EMAIL_NOTIFICATION}
          </label>
          <input
            id="email-input"
            type="email"
            placeholder={FORM_LABELS.EMAIL_PLACEHOLDER}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Form.Field>
      </Form>
    </Modal.Content>
    <Modal.Actions>
      <Button onClick={onClose}>{BUTTON_LABELS.CANCEL}</Button>
      <Button
        primary
        disabled={!confirmed || loading}
        loading={loading}
        onClick={onSubmit}
      >
        {BUTTON_LABELS.OK}
      </Button>
    </Modal.Actions>
  </Modal>
);

RequestModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onSubmit: PropTypes.func.isRequired,
  loading: PropTypes.bool.isRequired,
  file: PropTypes.string,
  num_files: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  size: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  email: PropTypes.string.isRequired,
  setEmail: PropTypes.func.isRequired,
  confirmed: PropTypes.bool.isRequired,
  setConfirmed: PropTypes.func.isRequired
};

/**
 * Main Request Record Application component
 */
const RequestRecordApp = ({ recordId, availability, num_files, size, file }) => {
  const { isOpen, openModal, closeModal } = useModal();
  const [email, setEmail] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!confirmed) return;
    
    setLoading(true);
    try {
      await axios.post(RECORD_STAGE_URL(recordId), {
        email: email.trim(),
        ...(file ? { file } : {}),
      });
      window.location.reload();
    } catch (error) {
      console.error("Request failed", error);
      // TODO: Add proper error handling/display
    } finally {
      setLoading(false);
      closeModal();
    }
  };

  const getAvailabilityMessage = () => {
    switch (availability) {
      case AVAILABILITY_STATES.PARTIAL:
        return MESSAGES.PARTIAL_AVAILABILITY;
      case AVAILABILITY_STATES.ON_DEMAND:
        return MESSAGES.ON_DEMAND_AVAILABILITY;
      case AVAILABILITY_STATES.REQUESTED:
        return MESSAGES.REQUESTED_AVAILABILITY;
      default:
        return "";
    }
  };

  const renderActionButton = () => {
    if (availability === AVAILABILITY_STATES.REQUESTED) {
      return (
        <a href={TRANSFER_REQUESTS_URL(recordId)}>
          <Button className="ml-10" size="tiny" color="blue">
            {BUTTON_LABELS.SEE_REQUEST_STATUS}
          </Button>
        </a>
      );
    }

    return (
      <>
        <Button className="ml-10" size="tiny" color="blue" onClick={openModal}>
          {file ? BUTTON_LABELS.REQUEST_FILE : BUTTON_LABELS.REQUEST_ALL_FILES}
        </Button>
        <RequestModal
          open={isOpen}
          onClose={closeModal}
          onSubmit={handleSubmit}
          loading={loading}
          file={file}
          num_files={num_files}
          size={size}
          email={email}
          setEmail={setEmail}
          confirmed={confirmed}
          setConfirmed={setConfirmed}
        />
      </>
    );
  };

  // Only render for specific availability states
  if (![
    AVAILABILITY_STATES.PARTIAL,
    AVAILABILITY_STATES.ON_DEMAND,
    AVAILABILITY_STATES.REQUESTED
  ].includes(availability)) {
    return null;
  }

  const actionButton = renderActionButton();

  // If requesting only a specific file, return just the button
  if (file) {
    return actionButton;
  }

  return (
    <div className="ui info message">
      <div className="header" style={{ display: 'flex', alignItems: 'center' }}>
        Availability:&nbsp; <strong>{availability.toUpperCase()}</strong> {actionButton}
      </div>
      <p>{getAvailabilityMessage()}</p>
    </div>
  );
};

RequestRecordApp.propTypes = {
  recordId: PropTypes.string.isRequired,
  availability: PropTypes.oneOf(Object.values(AVAILABILITY_STATES)).isRequired,
  num_files: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  size: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  file: PropTypes.string
};

RequestRecordApp.defaultProps = {
  num_files: null,
  size: null,
  file: null
};

export default RequestRecordApp;
