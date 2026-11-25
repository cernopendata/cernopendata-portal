import React, { useState } from "react";
import { Checkbox, Popup, Icon } from "semantic-ui-react";

function ValidationToggle({ validation, onToggle }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = async (e, data) => {
    const enabled = data.checked;
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `./${validation.release_id}/validations/${validation.id}/enable`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled }),
        },
      );

      if (!response.ok) {
        const json = await response.json().catch(() => ({}));
        setError(json.error || "Could not update validation.");
        setLoading(false);
        return;
      }
    } catch (e) {
      setError("Network error: " + e.message);
      setLoading(false);
      return;
    }

    setLoading(false);
    onToggle(validation.id, enabled);
  };

  return (
    <Popup
      open={!!error}
      onClose={() => setError(null)}
      position="top center"
      trigger={
        <Checkbox
          toggle
          checked={validation.enabled}
          onChange={handleChange}
          disabled={loading}
          label={validation.enabled ? "Enabled" : "Disabled"}
        />
      }
      content={
        <span>
          <Icon name="warning circle" /> {error}
        </span>
      }
    />
  );
}

export default ValidationToggle;
