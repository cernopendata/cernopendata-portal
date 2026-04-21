import $ from "jquery";

import {
  AccordionField,
  CustomFields,
  FieldLabel,
  RemoteSelectField,
  SelectField,
  TextField,
  TextAreaField,
  AffiliationsSuggestions,
} from "react-invenio-forms";




import React from "react";
import ReactDOM from "react-dom";

import ReleasesTable from "./ReleasesTable";
import RecordsTable from "./RecordsTable";
import ValidationToggle from "./ValidationToggle";

const container = document.getElementById("releases-react-root");

if (container) {
    const experiment = container.dataset.experiment || null;
    ReactDOM.render(
    <ReleasesTable experiment={experiment} />,
    container
    );

    $('.ui.checkbox').checkbox();

    $('#open-create-release').on('click', () => {
      $('#create-release-modal').modal('show');
    });

    function updateSource() {
      const source = $('input[name="source"]:checked').val();

      if (source === 'file') {
        $('#file-source').show();
        $('#url-source').hide();
      } else {
        $('#file-source').hide();
        $('#url-source').show();
      }

      validateForm();
    }

    function validateForm() {
      const source = $('input[name="source"]:checked').val();
      let valid = false;

      if (source === 'file') {
        valid = $('input[name="file"]').val() !== '';
      } else {
        valid = $('input[name="url"]').val().trim() !== '';
      }

      $('#uploadButton').toggleClass('disabled', !valid);
    }

    $('input[name="source"]').on('change', updateSource);
    $('input[name="file"], input[name="url"]').on('input change', validateForm);

    updateSource();
 }

 const records_table = document.getElementById('records-table-root');
 if (records_table) {
     ReactDOM.render(
       <RecordsTable
         experiment= {records_table.dataset.experiment}
         releaseId = {records_table.dataset.releaseId}
         initialRecords={JSON.parse(records_table.dataset.records)}
         editDisabled={records_table.dataset.editDisabled === 'true'}
         viewDisabled={records_table.dataset.viewDisabled === 'true'}
       />,
       records_table
     );
 }

document.querySelectorAll(".validation-toggle-root").forEach((el) => {
  const validation = JSON.parse(el.dataset.validation);

  ReactDOM.render(
    <ValidationToggle
      validation={validation}
      onToggle={(id, enabled) => window.location.reload()}
    />,
    el
  );
});


$(document).on('click', '#history-button', function () {
    $('#history-modal').modal('show');
});

$('#edit-metadata-action').on('click', function () {
  $('#meta-name').val($('#release-name').text() || '');
  $('#meta-link').val($('#release-discussion-url').attr('href') || '');
  $('#meta-description').val($('#release-description').text() || '');
  $('#edit-metadata-modal').modal('show');
});

$('#save-metadata').on('click', function () {
  const payload = {
    name: $('#meta-name').val(),
    discussion_url: $('#meta-link').val(),
    description: $('#meta-description').val()
  };
  const releaseId= $('#meta-release-id').val();

  fetch(`./${releaseId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(res => {
  console.log(res.ok);
    if (!res.ok) throw new Error('Update failed');
    console.log("We get here");
    return res.json();
  })
  .then(updated => {
    // 🟢 1. Update title
    if (updated.name) {
      $('#release-name').text(updated.name);
    }

    // 🟢 2. Update link
    if (updated.discussion_url) {
      $('#release-discussion-url')
        .attr('href', updated.discussion_url);
    }

    // 🟢 3. Update description
    if (updated.description) {
      $('#release-description').text(updated.description);
    }

    // 🟢 4. Close modal
    $('#edit-metadata-modal').modal('hide');

  })
  .catch(err => {
    console.error(err);
    alert('Could not save changes');
  });
});