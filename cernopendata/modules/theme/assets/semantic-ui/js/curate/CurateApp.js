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