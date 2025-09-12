/*
 * -*- coding: utf-8 -*-
 *
 * This file is part of CERN Open Data Portal.
 * Copyright (C) 2025 CERN.
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

// UI Constants
export const ITEMS_PER_PAGE = 5;

// File availability states
export const AVAILABILITY_STATES = {
  ONLINE: 'online',
  PARTIAL: 'partial',
  ON_DEMAND: 'on demand',
  REQUESTED: 'requested'
};

// File formats
export const FILE_FORMATS = {
  TXT: 'txt',
  JSON: 'json'
};

// Table types
export const TABLE_TYPES = {
  FILES: 'files',
  FILE_INDEX: 'file_index'
};

// DOM selectors
export const SELECTORS = {
  CITATIONS_APP: '#citations-react-app',
  REQUEST_RECORD_APP: '#request-record-react-app',
  FILES_BOX_APP: '#files-box-react-app'
};

// External URLs
export const INSPIRE_HOST = 'https://inspirehep.net';

// API endpoints
export const API_ENDPOINTS = {
  LITERATURE_SEARCH: '/literature',
  TRANSFER_REQUESTS: '/transfer_requests'
};

// Messages
export const MESSAGES = {
  SINGLE_PUBLICATION: 'There is one publication referring to these data',
  MULTIPLE_PUBLICATIONS: (count) => `There are ${count} publications referring to these data`,
  PARTIAL_AVAILABILITY: 'Please note that only a subset of files are available for this dataset. If you are interested in accessing all of them, please request them. Note that the file transfer to online storage may take several weeks or months in case of a large amount of data.',
  ON_DEMAND_AVAILABILITY: 'Please note this dataset is currently not available. If you are interested in accessing all of them, please request them. Note that the file transfer to online storage may take several weeks or months in case of a large amount of data.',
  REQUESTED_AVAILABILITY: 'The files for this record are being staged. This operation takes time. Click on the button above to see the status of the transfer.',
  FILE_NOT_AVAILABLE: 'This file is not currently available.',
  ALREADY_REQUESTED: 'It has already been requested. Once it is ready, this button will become available.',
  REQUEST_ALL_FILES: 'If you want to access it, please request it using the button "Request all files".',
  DOWNLOAD_WARNING: (filename, size) => `Please note that the file you are going to download (${filename}) is ${size} big. On an average ADSL connection, it may take several hours to download it.`,
  CONTAINER_INFO: 'Most collaborations provide container images or virtual machine images allowing to perform analyses. If you use one of those, then you do not need to download datasets manually, because all the necessary file chunks will be accessed via the XRootD protocol during the live analysis.',
  MANUAL_DOWNLOAD_INFO: 'Manual download of files via HTTP is only necessary if you would prefer not to use the XRootD protocol for one reason or another.',
  SOME_FILES_AVAILABLE: 'Some files of the dataset are available for immediate download',
  FILES_MUST_BE_REQUESTED: 'The files have to be requested before they are available',
  REQUEST_TIME_WARNING: 'This action takes time. The more data requested, the longer it will take.'
};

// Button labels
export const BUTTON_LABELS = {
  REQUEST_FILE: 'Request file',
  REQUEST_ALL_FILES: 'Request all files',
  SEE_REQUEST_STATUS: 'See request status',
  LIST_FILES: 'List files',
  DOWNLOAD: 'Download',
  DOWNLOAD_INDEX: 'Download index',
  CANCEL: 'Cancel',
  OK: 'OK'
};

// Form labels
export const FORM_LABELS = {
  EMAIL_NOTIFICATION: 'If you want to be notified, enter your email',
  EMAIL_PLACEHOLDER: 'Enter your email'
};
