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
  RECORD_FILEPAGE_URL,
  INDEX_FILES_URL,
  RECORD_FILES_URL,
  RECORD_STAGE_URL,
  TRANSFER_REQUESTS_URL,
  ITEMS_PER_PAGE
} from '../config';

describe('Configuration and URL builders', () => {
  describe('RECORD_FILEPAGE_URL', () => {
    it('should build URL with type parameter', () => {
      const url = RECORD_FILEPAGE_URL('test-pid', 2, 'files');
      expect(url).toBe('/record/test-pid/filepage/2?type=files');
    });

    it('should build URL without type parameter', () => {
      const url = RECORD_FILEPAGE_URL('test-pid', 1);
      expect(url).toBe('/record/test-pid/filepage/1?group=1');
    });

    it('should handle null type parameter', () => {
      const url = RECORD_FILEPAGE_URL('test-pid', 1, null);
      expect(url).toBe('/record/test-pid/filepage/1?group=1');
    });
  });

  describe('INDEX_FILES_URL', () => {
    it('should convert TXT index file to JSON URL', () => {
      const url = INDEX_FILES_URL('test-pid', 'index.txt');
      expect(url).toBe('/record/test-pid/files/index.json');
    });

    it('should return null for non-TXT files', () => {
      const url = INDEX_FILES_URL('test-pid', 'index.json');
      expect(url).toBe(null);
    });

    it('should return null for files not ending with index.txt', () => {
      const url = INDEX_FILES_URL('test-pid', 'data.txt');
      expect(url).toBe(null);
    });
  });

  describe('RECORD_FILES_URL', () => {
    it('should build record files URL', () => {
      const url = RECORD_FILES_URL('test-pid', 'test-file.root');
      expect(url).toBe('/record/test-pid/files/test-file.root');
    });
  });

  describe('RECORD_STAGE_URL', () => {
    it('should build record stage URL', () => {
      const url = RECORD_STAGE_URL('test-pid');
      expect(url).toBe('/record/test-pid/stage');
    });
  });

  describe('TRANSFER_REQUESTS_URL', () => {
    it('should build transfer requests URL', () => {
      const url = TRANSFER_REQUESTS_URL('test-record-123');
      expect(url).toBe('/transfer_requests?record_id=test-record-123');
    });
  });

  describe('Constants', () => {
    it('should have correct ITEMS_PER_PAGE value', () => {
      expect(ITEMS_PER_PAGE).toBe(5);
    });
  });

  describe('Config object', () => {
    it('should get config from DOM element', () => {
      // This is already mocked in setupTests.js
      const config = require('../config').default;
      expect(config).toEqual(expect.objectContaining({
        pidValue: 'test-pid-123',
        recordavailability: 'online'
      }));
    });
  });
});
