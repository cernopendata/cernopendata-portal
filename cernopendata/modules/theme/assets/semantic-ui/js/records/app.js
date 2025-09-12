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
import { SELECTORS } from './constants';
import FilesBoxApp from "./FilesBoxApp";
import CitationsApp from "./CitationsApp";
import RequestRecordApp from "./components/RequestRecord";

/**
 * Application initializer for React components
 */
class RecordsAppInitializer {
  /**
   * Initialize all React applications
   */
  static init() {
    this.initCitationsApp();
    this.initRequestRecordApp();
    this.initFilesBoxApp();
  }

  /**
   * Initialize Citations React app
   */
  static initCitationsApp() {
    const container = document.querySelector(SELECTORS.CITATIONS_APP);
    if (!container) return;

    try {
      ReactDOM.render(<CitationsApp />, container);
    } catch (error) {
      console.error('Failed to initialize Citations app:', error);
    }
  }

  /**
   * Initialize Request Record React app
   */
  static initRequestRecordApp() {
    const container = document.querySelector(SELECTORS.REQUEST_RECORD_APP);
    if (!container) return;

    try {
      const { recordId, availability, size, files } = container.dataset;
      
      ReactDOM.render(
        <RequestRecordApp 
          recordId={recordId}
          availability={availability}
          num_files={files}
          size={size}
        />,
        container
      );
    } catch (error) {
      console.error('Failed to initialize Request Record app:', error);
    }
  }

  /**
   * Initialize Files Box React app
   */
  static initFilesBoxApp() {
    const container = document.querySelector(SELECTORS.FILES_BOX_APP);
    if (!container) return;

    try {
      const { recordavailability } = container.dataset;
      
      ReactDOM.render(
        <FilesBoxApp recordAvailability={recordavailability} />,
        container
      );
    } catch (error) {
      console.error('Failed to initialize Files Box app:', error);
    }
  }
}

// Initialize all React applications when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  RecordsAppInitializer.init();
});

// Fallback initialization if DOMContentLoaded has already fired
if (document.readyState !== 'loading') {
  RecordsAppInitializer.init();
}

