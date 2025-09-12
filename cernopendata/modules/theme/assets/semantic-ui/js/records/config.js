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

import { SELECTORS, ITEMS_PER_PAGE, FILE_FORMATS } from './constants';

// Get configuration from DOM dataset
const getConfig = () => {
  const configElement = document.querySelector(SELECTORS.FILES_BOX_APP);
  return configElement ? configElement.dataset : {};
};

const config = getConfig();

// URL builders
export const RECORD_FILEPAGE_URL = (pid, page, type = null) =>
  `/record/${pid}/filepage/${page}?${type ? `type=${type}` : "group=1"}`;

export const INDEX_FILES_URL = (pid, indexFile) => {
  if (indexFile.endsWith(`index.${FILE_FORMATS.TXT}`)) {
    const fileKey = indexFile.replace(`.${FILE_FORMATS.TXT}`, `.${FILE_FORMATS.JSON}`);
    return `/record/${pid}/files/${fileKey}`;
  }
  return null;
};

export const RECORD_FILES_URL = (pid, fileKey) => `/record/${pid}/files/${fileKey}`;

export const RECORD_STAGE_URL = (pid) => `/record/${pid}/stage`;

export const TRANSFER_REQUESTS_URL = (recordId) => `/transfer_requests?record_id=${recordId}`;

// Re-export constants for backwards compatibility
export { ITEMS_PER_PAGE };

export default config;
