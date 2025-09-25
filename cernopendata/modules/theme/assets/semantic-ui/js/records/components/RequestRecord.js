import React, { useState } from "react";
import { Button, Modal, Form, Checkbox, Message } from "semantic-ui-react";
import axios from "axios";
import { toHumanReadableSize } from "../utils";

const RequestRecordApp = ({ recordId, availability, num_files, size, file }) => {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!confirmed) return;
    setLoading(true);
    try {
        await axios.post(`/record/${recordId}/stage`, {
          email: email.trim(),
          ...(file ? { file: file } : {}),
        });
        window.location.reload();
    } catch (error) {
      console.error("Request failed", error);
    } finally {
      setLoading(false);
      setOpen(false);
    }
  };

  if (
    availability !== "partial" &&
    availability !== "on demand" &&
    availability !== "requested"
  ) {
    return null;
  }

  let message = "";
  let actionButton = null;

  if (availability === "partial") {
    message =
      "Please note that only a subset of files are available for this dataset. If you are interested in accessing all of them, please request them. Note that the file transfer to online storage may take several weeks or months in case of a large amount of data.";
  } else if (availability === "on demand") {
    message =
      "Please note this dataset is currently not available. If you are interested in accessing all of them, please request them. Note that the file transfer to online storage may take several weeks or months in case of a large amount of data.";
  } else if (availability === "requested") {
    message =
      "The files for this record are being staged. This operation takes time. Click on the button above to see the status of the transfer.";
  }

  if (availability === "requested") {
    actionButton = (
      <a href={`/transfer_requests?record_id=${recordId}`} >
        <Button className="ml-10" size="tiny" color="blue">See request status</Button>
      </a>
    );
  } else {
    actionButton = (
      <>
        <Button className="ml-10" size="tiny" color="blue" onClick={() => setOpen(true)}>
          Request { (file)? 'file':'all files' }
        </Button>

        <Modal open={open} onClose={() => setOpen(false)} size="small">
          <Modal.Header>Request to make data available</Modal.Header>
          <Modal.Content>
            <p>Please confirm you want to request {(file)?'this file':'all files of the record'}.</p>
            <Message warning>
              <p>This action takes time. The more data requested, the longer it will take.</p>
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
                  If you want to be notified, enter your email
                </label>
                <input
                  id="email-input"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </Form.Field>
            </Form>
          </Modal.Content>
          <Modal.Actions>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button
              primary
              disabled={!confirmed || loading}
              loading={loading}
              onClick={handleSubmit}
            >
              OK
            </Button>
          </Modal.Actions>
        </Modal>
      </>
    );
  }
  if (file ) {
     /* If we want only a file, we just need the button */
     return actionButton;
  }


  return (
    <div className="ui info message">
      <div className="header" style={{ display: 'flex', alignItems: 'center' }}>
          Availability:&nbsp; <strong>{availability.toUpperCase()}</strong> {actionButton}
      </div>
      <p>{message}</p>
    </div>
  );
};

export default RequestRecordApp;
