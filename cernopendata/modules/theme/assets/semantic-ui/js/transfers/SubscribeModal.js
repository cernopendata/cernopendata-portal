import React from "react";

const SubscribeModal = ({ isModalOpen, email, setEmail, handleSubscribe, closeModal }) => (
    isModalOpen && (
        <div className="ui modal active">
            <div className="header">Subscribe for Updates</div>
            <div className="content">
                <p>Enter your email to subscribe to updates for this record.</p>
                <div className="ui input fluid">
                    <input
                        type="email"
                        placeholder="Enter your email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />
                </div>
            </div>
            <div className="actions">
                <button className="ui cancel button" onClick={closeModal}>Cancel</button>
                <button className="ui primary button" onClick={handleSubscribe}>Subscribe</button>
            </div>
        </div>
    )
);

export default SubscribeModal;