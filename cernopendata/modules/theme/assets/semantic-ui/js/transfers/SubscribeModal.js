import React from "react";
import { Modal, Button, Form } from "semantic-ui-react";

const SubscribeModal = ({
  isModalOpen,
  email,
  setEmail,
  emailError,
  handleSubscribe,
  closeModal,
  isLoading,
}) => (
  <Modal open={isModalOpen} onClose={closeModal} size="small">
    <Modal.Header>Subscribe for Updates</Modal.Header>
    <Modal.Content>
      <p>Enter your email to subscribe to updates for this record.</p>
      <Form>
        <Form.Input
          fluid
          type="email"
          placeholder="Enter your email"
          value={email}
          error={
            emailError
              ? {
                  content: "Please enter a valid email address",
                  pointing: "below",
                }
              : null
          }
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSubscribe();
          }}
          onChange={(e) => setEmail(e.target.value)}
        />
      </Form>
    </Modal.Content>
    <Modal.Actions>
      <Button onClick={closeModal} disabled={isLoading}>
        Cancel
      </Button>
      <Button
        primary
        onClick={handleSubscribe}
        loading={isLoading}
        disabled={isLoading}
      >
        Subscribe
      </Button>
    </Modal.Actions>
  </Modal>
);

export default SubscribeModal;
