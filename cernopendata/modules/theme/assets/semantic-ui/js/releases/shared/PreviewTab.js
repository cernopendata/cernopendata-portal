import React, { useEffect, useState } from "react";
import { Loader } from "semantic-ui-react";

export default function PreviewTab({ endpoint, data }) {
  const [html, setHtml] = useState("");
  const [loading, setLoading] = useState(false);

  const loadPreview = async () => {
    setLoading(true);

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      const json = await res.json();
      setHtml(json.html);
    } catch (e) {
      setHtml("<p style='color:red'>Preview failed</p>");
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

      <div
        style={{ marginTop: 10 }}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </div>
  );
}
