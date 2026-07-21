import React, { useEffect, useState } from "react";
import { Loader, Message, Icon } from "semantic-ui-react";

export default function PreviewTab({ endpoint, data }) {
  const [html, setHtml] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadPreview = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        const json = await res.json().catch(() => ({}));
        setError(json.error || "Preview failed");
        return;
      }

      const json = await res.json();
      setHtml(json.html);
    } catch (e) {
      setError("Preview failed");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPreview();
  }, [data]);

  useEffect(() => {
    if (!html) return;

    const domContainer = document.querySelector("#files-box-react-app");

    if (domContainer) {
      domContainer.innerHTML =
        "<div style='padding:10px;color:#888'>The file box cannot be previewed</div>";
    }
  }, [html]);

  return (
    <div>
      {loading && <Loader active inline="centered" />}
      {error && (
        <Message negative>
          <Icon name="warning circle" /> {error}
        </Message>
      )}
      <div
        style={{ marginTop: 10 }}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </div>
  );
}
