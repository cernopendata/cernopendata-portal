/*
 * -*- coding: utf-8 -*-
 *
 * This file is part of CERN Open Data Portal.
 * Copyright (C) 2021 CERN.
 *
 * CERN Open Data Portal is free software; you can redistribute it
 * and/or modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * CERN Open Data Portal is distributed in the hope that it will be
 * useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with CERN Open Data Portal; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
 * MA 02111-1307, USA.
 *
 * In applying this license, CERN does not
 * waive the privileges and immunities granted to it by virtue of its status
 * as an Intergovernmental Organization or submit itself to any jurisdiction.
 */

import React from "react";
import ReactDOM from "react-dom";

import FilesBoxApp from "./FilesBoxApp";

import CitationsApp from "./CitationsApp";

import RequestRecordApp from "./components/RequestRecord"

const citeContainer = document.querySelector("#citations-react-app");
if (citeContainer) {
    ReactDOM.render(React.createElement(CitationsApp), citeContainer);
};
const requestContainer = document.querySelector("#request-record-react-app");
if (requestContainer) {
    const recordId = requestContainer.dataset.recordId;
    const availability = requestContainer.dataset.availability;
    const size = requestContainer.dataset.size;
    const files = requestContainer.dataset.files;
    ReactDOM.render(
      <RequestRecordApp recordId={recordId}  availability={availability} files={files} size={size}/>,
      requestContainer
    );
};
const domContainer = document.querySelector("#files-box-react-app");
ReactDOM.render(React.createElement(FilesBoxApp), domContainer);

