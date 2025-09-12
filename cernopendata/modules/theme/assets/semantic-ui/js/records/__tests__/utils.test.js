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
  toHumanReadableSize,
  isFileOnDemand,
  isFileOnlineOnly,
  getFileAvailabilityMessage,
  buildFileUri,
  isValidEmail,
  getElementDataset,
  getElementAttribute,
  paginateArray,
  calculateTotalPages
} from '../utils';

describe('File size utilities', () => {
  describe('toHumanReadableSize', () => {
    it('should handle zero bytes', () => {
      expect(toHumanReadableSize(0)).toBe('0 bytes');
    });

    it('should handle bytes', () => {
      expect(toHumanReadableSize(500)).toBe('500.0 bytes');
    });

    it('should handle KiB', () => {
      expect(toHumanReadableSize(1024)).toBe('1.0 KiB');
      expect(toHumanReadableSize(1536)).toBe('1.5 KiB');
    });

    it('should handle MiB', () => {
      expect(toHumanReadableSize(1048576)).toBe('1.0 MiB');
      expect(toHumanReadableSize(1572864)).toBe('1.5 MiB');
    });

    it('should handle GiB', () => {
      expect(toHumanReadableSize(1073741824)).toBe('1.0 GiB');
    });

    it('should handle custom precision', () => {
      expect(toHumanReadableSize(1536, 2)).toBe('1.50 KiB');
      expect(toHumanReadableSize(1536, 0)).toBe('2 KiB');
    });

    it('should handle string input', () => {
      expect(toHumanReadableSize('1024')).toBe('1.0 KiB');
    });

    it('should handle invalid input', () => {
      expect(toHumanReadableSize('invalid')).toBe('-');
      expect(toHumanReadableSize(null)).toBe('-');
      expect(toHumanReadableSize(undefined)).toBe('-');
      expect(toHumanReadableSize(-100)).toBe('-');
      expect(toHumanReadableSize(Infinity)).toBe('-');
    });
  });
});

describe('File availability utilities', () => {
  describe('isFileOnDemand', () => {
    it('should return true for on demand string availability', () => {
      const file = { availability: 'on demand' };
      expect(isFileOnDemand(file)).toBe(true);
    });

    it('should return true for on demand object availability', () => {
      const file = { availability: { 'on demand': true } };
      expect(isFileOnDemand(file)).toBe(true);
    });

    it('should return false for online availability', () => {
      const file = { availability: 'online' };
      expect(isFileOnDemand(file)).toBe(false);
    });

    it('should return false for null/undefined file', () => {
      expect(isFileOnDemand(null)).toBe(false);
      expect(isFileOnDemand(undefined)).toBe(false);
      expect(isFileOnDemand({})).toBe(false);
    });
  });

  describe('isFileOnlineOnly', () => {
    it('should return true for online-only availability', () => {
      const file = { availability: { online: true } };
      expect(isFileOnlineOnly(file)).toBe(true);
    });

    it('should return false for mixed availability', () => {
      const file = { availability: { online: true, 'on demand': true } };
      expect(isFileOnlineOnly(file)).toBe(false);
    });

    it('should return false for string availability', () => {
      const file = { availability: 'online' };
      expect(isFileOnlineOnly(file)).toBe(false);
    });

    it('should return false for null/undefined file', () => {
      expect(isFileOnlineOnly(null)).toBe(false);
      expect(isFileOnlineOnly(undefined)).toBe(false);
      expect(isFileOnlineOnly({})).toBe(false);
    });
  });

  describe('getFileAvailabilityMessage', () => {
    it('should return message for online files', () => {
      const file = { availability: { online: true } };
      expect(getFileAvailabilityMessage(file)).toBe(
        'Some files of the dataset are available for immediate download'
      );
    });

    it('should return message for on demand files', () => {
      const file = { availability: 'on demand' };
      expect(getFileAvailabilityMessage(file)).toBe(
        'The files have to be requested before they are available'
      );
    });

    it('should return empty string for invalid file', () => {
      expect(getFileAvailabilityMessage(null)).toBe('');
      expect(getFileAvailabilityMessage({})).toBe('');
    });
  });
});

describe('URL utilities', () => {
  describe('buildFileUri', () => {
    it('should build basic file URI', () => {
      const uri = buildFileUri('123', 'files', 'test.root');
      expect(uri).toBe('/record/123/files/test.root');
    });

    it('should build file index URI with TXT format', () => {
      const uri = buildFileUri('123', 'file_index', 'index.json', 'txt');
      expect(uri).toBe('/record/123/file_index/index.txt');
    });

    it('should build file index URI without format conversion', () => {
      const uri = buildFileUri('123', 'file_index', 'index.json', 'json');
      expect(uri).toBe('/record/123/file_index/index.json');
    });

    it('should not convert non-file_index types', () => {
      const uri = buildFileUri('123', 'files', 'test.json', 'txt');
      expect(uri).toBe('/record/123/files/test.json');
    });
  });
});

describe('Validation utilities', () => {
  describe('isValidEmail', () => {
    it('should validate correct email addresses', () => {
      expect(isValidEmail('test@example.com')).toBe(true);
      expect(isValidEmail('user.name@domain.co.uk')).toBe(true);
      expect(isValidEmail('user+tag@example.org')).toBe(true);
    });

    it('should reject invalid email addresses', () => {
      expect(isValidEmail('invalid')).toBe(false);
      expect(isValidEmail('invalid@')).toBe(false);
      expect(isValidEmail('@invalid.com')).toBe(false);
      expect(isValidEmail('invalid@.com')).toBe(false);
      expect(isValidEmail('invalid@domain')).toBe(false);
    });

    it('should handle edge cases', () => {
      expect(isValidEmail('')).toBe(false);
      expect(isValidEmail('   ')).toBe(false);
      expect(isValidEmail(null)).toBe(false);
      expect(isValidEmail(undefined)).toBe(false);
    });

    it('should trim whitespace', () => {
      expect(isValidEmail('  test@example.com  ')).toBe(true);
    });
  });
});

describe('DOM utilities', () => {
  describe('getElementDataset', () => {
    it('should return dataset when element exists', () => {
      // Mock the querySelector for this specific test
      const mockElement = {
        dataset: {
          pidValue: 'test-pid-123',
          recordavailability: 'online'
        }
      };
      
      document.querySelector.mockImplementation((selector) => {
        if (selector === '#files-box-react-app') {
          return mockElement;
        }
        return null;
      });

      const dataset = getElementDataset('#files-box-react-app');
      expect(dataset).toEqual(expect.objectContaining({
        pidValue: 'test-pid-123',
        recordavailability: 'online'
      }));
    });

    it('should return empty object when element does not exist', () => {
      document.querySelector.mockImplementation(() => null);
      
      const dataset = getElementDataset('#non-existent-element');
      expect(dataset).toEqual({});
    });
  });

  describe('getElementAttribute', () => {
    it('should return attribute when element exists', () => {
      // Mock the querySelector for this specific test
      const mockElement = {
        getAttribute: jest.fn((attr) => {
          if (attr === 'data-doi') return '10.1234/test-doi';
          return null;
        })
      };
      
      document.querySelector.mockImplementation((selector) => {
        if (selector === '#citations-react-app') {
          return mockElement;
        }
        return null;
      });

      const doi = getElementAttribute('#citations-react-app', 'data-doi');
      expect(doi).toBe('10.1234/test-doi');
    });

    it('should return null when element does not exist', () => {
      document.querySelector.mockImplementation(() => null);
      
      const attr = getElementAttribute('#non-existent-element', 'data-test');
      expect(attr).toBe(null);
    });

    it('should return null when attribute does not exist', () => {
      const mockElement = {
        getAttribute: jest.fn(() => null)
      };
      
      document.querySelector.mockImplementation((selector) => {
        if (selector === '#citations-react-app') {
          return mockElement;
        }
        return null;
      });

      const attr = getElementAttribute('#citations-react-app', 'data-nonexistent');
      expect(attr).toBe(null);
    });
  });
});

describe('Array utilities', () => {
  describe('paginateArray', () => {
    const testArray = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

    it('should paginate array correctly', () => {
      expect(paginateArray(testArray, 1, 3)).toEqual([1, 2, 3]);
      expect(paginateArray(testArray, 2, 3)).toEqual([4, 5, 6]);
      expect(paginateArray(testArray, 4, 3)).toEqual([10]);
    });

    it('should handle edge cases', () => {
      expect(paginateArray(testArray, 0, 3)).toEqual([]);
      expect(paginateArray(testArray, 1, 0)).toEqual([]);
      expect(paginateArray(testArray, 1, -1)).toEqual([]);
      expect(paginateArray([], 1, 3)).toEqual([]);
      expect(paginateArray(null, 1, 3)).toEqual([]);
    });

    it('should handle out of bounds pages', () => {
      expect(paginateArray(testArray, 10, 3)).toEqual([]);
    });
  });

  describe('calculateTotalPages', () => {
    it('should calculate total pages correctly', () => {
      expect(calculateTotalPages(10, 3)).toBe(4);
      expect(calculateTotalPages(9, 3)).toBe(3);
      expect(calculateTotalPages(3, 3)).toBe(1);
    });

    it('should handle edge cases', () => {
      expect(calculateTotalPages(0, 3)).toBe(0);
      expect(calculateTotalPages(10, 0)).toBe(0);
      expect(calculateTotalPages(-1, 3)).toBe(0);
      expect(calculateTotalPages(10, -1)).toBe(0);
    });
  });
});
