import React, { useState } from "react";
import { Checkbox } from "semantic-ui-react";

function ValidationToggle({ validation, onToggle }) {
  const [loading, setLoading] = useState(false);

  const handleChange = async (e, data) => {
      const enabled = data.checked;
      setLoading(true);

      await fetch(`./${validation.release_id}/validations/${validation.id}/enable`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ enabled }),
      });

      setLoading(false);

      onToggle(validation.id, enabled);
  };

  return (
    <Checkbox
      toggle
      checked={validation.enabled}
      onChange={handleChange}
      disabled={loading}
      label={validation.enabled ? "Enabled" : "Disabled"}
    />
  );
}

export default ValidationToggle;