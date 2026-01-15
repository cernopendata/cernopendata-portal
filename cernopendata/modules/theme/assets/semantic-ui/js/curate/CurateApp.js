import $ from "jquery";


import React from "react";
import ReactDOM from "react-dom";

import ReleasesTable from "./ReleasesTable";

const container = document.getElementById("releases-react-root");

if (container) {
  const experiment = container.dataset.experiment || null;
  ReactDOM.render(
    <ReleasesTable experiment={experiment} />,
    container
  );
 }




  $('#fileInput').on('change', function() {
    if (this.files.length) {
      $('#uploadButton').removeClass('disabled');
    } else {
      $('#uploadButton').addClass('disabled');
    }
  });

  document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("toggle-create-release");
    const form = document.getElementById("create-release-form");
    if (toggle) {
        toggle.addEventListener("click", function () {
          const isHidden = form.style.display === "none";

          form.style.display = isHidden ? "block" : "none";

          // Optional: rotate icon / visual feedback
          const icon = toggle.querySelector("i.icon");
          if (icon) {
            icon.classList.toggle("plus", !isHidden);
            icon.classList.toggle("minus", isHidden);
          }
        });
    };

    // Source switch
    if (form) {
        const uploadButton = document.getElementById("uploadButton");

        const fileInput = document.getElementById("fileInput");
        const urlInput = form.querySelector('input[name="url"]');

        const fileSource = document.getElementById("file-source");
        const urlSource = document.getElementById("url-source");
        form.querySelectorAll('input[name="source"]').forEach((radio) => {
          radio.addEventListener("change", () => {
              const isFile = radio.value === "file";

              fileSource.style.disabled = ! isFile;
              urlSource.style.disabled = isFile;

              uploadButton.classList.add("disabled");
          });
        });

        // Enable button logic
        fileInput.addEventListener("change", () => {
          uploadButton.classList.toggle("disabled", !fileInput.files.length);
        });

        urlInput.addEventListener("input", () => {
          uploadButton.classList.toggle("disabled", !urlInput.value.trim());
        });
    }
  });