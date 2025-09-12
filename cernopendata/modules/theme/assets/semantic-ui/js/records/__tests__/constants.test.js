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

import {
  ITEMS_PER_PAGE,
  AVAILABILITY_STATES,
  FILE_FORMATS,
  TABLE_TYPES,
  SELECTORS,
  INSPIRE_HOST,
  API_ENDPOINTS,
  MESSAGES,
  BUTTON_LABELS,
  FORM_LABELS
} from '../constants';

describe('Constants', () => {
  describe('UI Constants', () => {
    it('should have correct ITEMS_PER_PAGE value', () => {
      expect(ITEMS_PER_PAGE).toBe(5);
    });
  });

  describe('AVAILABILITY_STATES', () => {
    it('should have all required availability states', () => {
      expect(AVAILABILITY_STATES.ONLINE).toBe('online');
      expect(AVAILABILITY_STATES.PARTIAL).toBe('partial');
      expect(AVAILABILITY_STATES.ON_DEMAND).toBe('on demand');
      expect(AVAILABILITY_STATES.REQUESTED).toBe('requested');
    });
  });

  describe('FILE_FORMATS', () => {
    it('should have all required file formats', () => {
      expect(FILE_FORMATS.TXT).toBe('txt');
      expect(FILE_FORMATS.JSON).toBe('json');
    });
  });

  describe('TABLE_TYPES', () => {
    it('should have all required table types', () => {
      expect(TABLE_TYPES.FILES).toBe('files');
      expect(TABLE_TYPES.FILE_INDEX).toBe('file_index');
    });
  });

  describe('SELECTORS', () => {
    it('should have all required DOM selectors', () => {
      expect(SELECTORS.CITATIONS_APP).toBe('#citations-react-app');
      expect(SELECTORS.REQUEST_RECORD_APP).toBe('#request-record-react-app');
      expect(SELECTORS.FILES_BOX_APP).toBe('#files-box-react-app');
    });
  });

  describe('External URLs', () => {
    it('should have correct INSPIRE_HOST', () => {
      expect(INSPIRE_HOST).toBe('https://inspirehep.net');
    });
  });

  describe('API_ENDPOINTS', () => {
    it('should have all required API endpoints', () => {
      expect(API_ENDPOINTS.LITERATURE_SEARCH).toBe('/literature');
      expect(API_ENDPOINTS.TRANSFER_REQUESTS).toBe('/transfer_requests');
    });
  });

  describe('MESSAGES', () => {
    it('should have correct static messages', () => {
      expect(MESSAGES.SINGLE_PUBLICATION).toBe('There is one publication referring to these data');
      expect(MESSAGES.PARTIAL_AVAILABILITY).toContain('only a subset of files are available');
      expect(MESSAGES.ON_DEMAND_AVAILABILITY).toContain('dataset is currently not available');
      expect(MESSAGES.REQUESTED_AVAILABILITY).toContain('files for this record are being staged');
      expect(MESSAGES.FILE_NOT_AVAILABLE).toBe('This file is not currently available.');
      expect(MESSAGES.SOME_FILES_AVAILABLE).toBe('Some files of the dataset are available for immediate download');
      expect(MESSAGES.FILES_MUST_BE_REQUESTED).toBe('The files have to be requested before they are available');
      expect(MESSAGES.REQUEST_TIME_WARNING).toBe('This action takes time. The more data requested, the longer it will take.');
    });

    it('should have function messages', () => {
      expect(typeof MESSAGES.MULTIPLE_PUBLICATIONS).toBe('function');
      expect(MESSAGES.MULTIPLE_PUBLICATIONS(5)).toBe('There are 5 publications referring to these data');
      
      expect(typeof MESSAGES.DOWNLOAD_WARNING).toBe('function');
      expect(MESSAGES.DOWNLOAD_WARNING('test.root', '1.5 GiB')).toContain('test.root');
      expect(MESSAGES.DOWNLOAD_WARNING('test.root', '1.5 GiB')).toContain('1.5 GiB');
    });

    it('should have information messages', () => {
      expect(MESSAGES.CONTAINER_INFO).toContain('container images or virtual machine images');
      expect(MESSAGES.MANUAL_DOWNLOAD_INFO).toContain('Manual download of files via HTTP');
      expect(MESSAGES.ALREADY_REQUESTED).toContain('already been requested');
      expect(MESSAGES.REQUEST_ALL_FILES).toContain('Request all files');
    });
  });

  describe('BUTTON_LABELS', () => {
    it('should have all required button labels', () => {
      expect(BUTTON_LABELS.REQUEST_FILE).toBe('Request file');
      expect(BUTTON_LABELS.REQUEST_ALL_FILES).toBe('Request all files');
      expect(BUTTON_LABELS.SEE_REQUEST_STATUS).toBe('See request status');
      expect(BUTTON_LABELS.LIST_FILES).toBe('List files');
      expect(BUTTON_LABELS.DOWNLOAD).toBe('Download');
      expect(BUTTON_LABELS.DOWNLOAD_INDEX).toBe('Download index');
      expect(BUTTON_LABELS.CANCEL).toBe('Cancel');
      expect(BUTTON_LABELS.OK).toBe('OK');
    });
  });

  describe('FORM_LABELS', () => {
    it('should have all required form labels', () => {
      expect(FORM_LABELS.EMAIL_NOTIFICATION).toBe('If you want to be notified, enter your email');
      expect(FORM_LABELS.EMAIL_PLACEHOLDER).toBe('Enter your email');
    });
  });

  describe('Constants consistency', () => {
    it('should not have undefined values', () => {
      const allConstants = {
        ITEMS_PER_PAGE,
        AVAILABILITY_STATES,
        FILE_FORMATS,
        TABLE_TYPES,
        SELECTORS,
        INSPIRE_HOST,
        API_ENDPOINTS,
        MESSAGES,
        BUTTON_LABELS,
        FORM_LABELS
      };

      function checkForUndefined(obj, path = '') {
        for (const [key, value] of Object.entries(obj)) {
          const currentPath = path ? `${path}.${key}` : key;
          
          if (value === undefined) {
            throw new Error(`Constant ${currentPath} is undefined`);
          }
          
          if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
            checkForUndefined(value, currentPath);
          }
        }
      }

      expect(() => checkForUndefined(allConstants)).not.toThrow();
    });

    it('should not have empty string values', () => {
      const stringConstants = [
        AVAILABILITY_STATES.ONLINE,
        AVAILABILITY_STATES.PARTIAL,
        AVAILABILITY_STATES.ON_DEMAND,
        AVAILABILITY_STATES.REQUESTED,
        FILE_FORMATS.TXT,
        FILE_FORMATS.JSON,
        TABLE_TYPES.FILES,
        TABLE_TYPES.FILE_INDEX,
        SELECTORS.CITATIONS_APP,
        SELECTORS.REQUEST_RECORD_APP,
        SELECTORS.FILES_BOX_APP,
        INSPIRE_HOST,
        API_ENDPOINTS.LITERATURE_SEARCH,
        API_ENDPOINTS.TRANSFER_REQUESTS
      ];

      stringConstants.forEach((constant, index) => {
        expect(constant).toBeTruthy();
        expect(typeof constant).toBe('string');
        expect(constant.trim()).not.toBe('');
      });
    });
  });
});
