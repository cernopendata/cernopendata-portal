import React from "react";
import { Modal, Button, Input } from "semantic-ui-react";

const SubscribeModal = ({ isModalOpen, email, setEmail, handleSubscribe, closeModal }) => (
    <Modal open={isModalOpen} onClose={closeModal} size="small">
        <Modal.Header>Subscribe for Updates</Modal.Header>
        <Modal.Content>
          <p>Enter your email to subscribe to updates for this record.</p>
          <Input
            fluid
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Modal.Content>
        <Modal.Actions>
          <Button onClick={closeModal}>Cancel</Button>
          <Button primary onClick={handleSubscribe}>Subscribe</Button>
        </Modal.Actions>
    </Modal>

);

export default SubscribeModal;