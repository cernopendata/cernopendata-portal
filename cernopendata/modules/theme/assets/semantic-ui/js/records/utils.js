/*
 * -*- coding: utf-8 -*-
 *
 * This file is part of CERN Open Data Portal.
 * Copyright (C) 2021, 2023 CERN.
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

import { AVAILABILITY_STATES, FILE_FORMATS, TABLE_TYPES } from './constants';

/**
 * File size utilities
 */

/**
 * Converts size in bytes to human readable expression.
 * @param {number|string} bytes - Bytes to convert
 * @param {number} [precision=1] - Number of decimals
 * @returns {string} Human readable size string
 */
export function toHumanReadableSize(bytes, precision = 1) {
  const numBytes = parseFloat(bytes);
  
  if (isNaN(numBytes) || !isFinite(numBytes) || numBytes < 0) {
    return "-";
  }
  
  if (numBytes === 0) {
    return "0 bytes";
  }
  
  const units = ["bytes", "KiB", "MiB", "GiB", "TiB", "PiB"];
  const unitIndex = Math.floor(Math.log(numBytes) / Math.log(1024));
  const clampedIndex = Math.min(unitIndex, units.length - 1);
  
  return `${(numBytes / Math.pow(1024, clampedIndex)).toFixed(precision)} ${units[clampedIndex]}`;
}

/**
 * File availability utilities
 */

/**
 * Checks if a file is available on demand
 * @param {Object} file - File object with availability property
 * @returns {boolean} True if file is on demand
 */
export function isFileOnDemand(file) {
  if (!file || !file.availability) {
    return false;
  }
  
  return (
    file.availability === AVAILABILITY_STATES.ON_DEMAND ||
    (typeof file.availability === 'object' && file.availability?.[AVAILABILITY_STATES.ON_DEMAND])
  );
}

/**
 * Checks if a file is available online only
 * @param {Object} file - File object with availability property
 * @returns {boolean} True if file is online only
 */
export function isFileOnlineOnly(file) {
  if (!file || !file.availability || typeof file.availability !== 'object') {
    return false;
  }
  
  return Object.keys(file.availability).length === 1 && 
         file.availability.hasOwnProperty(AVAILABILITY_STATES.ONLINE);
}

/**
 * Gets availability message for a file
 * @param {Object} file - File object with availability property
 * @returns {string} Availability message
 */
export function getFileAvailabilityMessage(file) {
  if (!file || !file.availability) {
    return '';
  }
  
  if (typeof file.availability === 'object' && file.availability.online) {
    return 'Some files of the dataset are available for immediate download';
  }
  
  return 'The files have to be requested before they are available';
}

/**
 * URL utilities
 */

/**
 * Builds a file URI for download
 * @param {string} pidValue - Record PID value
 * @param {string} tableType - Table type (files or file_index)
 * @param {string} fileKey - File key/name
 * @param {string} [format] - File format (txt, json)
 * @returns {string} File URI
 */
export function buildFileUri(pidValue, tableType, fileKey, format = null) {
  let url = `/record/${pidValue}/${tableType}/${fileKey}`;
  
  if (tableType === TABLE_TYPES.FILE_INDEX && format === FILE_FORMATS.TXT) {
    url = url.replace(`.${FILE_FORMATS.JSON}`, `.${FILE_FORMATS.TXT}`);
  }
  
  return url;
}

/**
 * Validation utilities
 */

/**
 * Validates an email address
 * @param {string} email - Email to validate
 * @returns {boolean} True if email is valid
 */
export function isValidEmail(email) {
  if (!email || typeof email !== 'string') {
    return false;
  }
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.trim());
}

/**
 * DOM utilities
 */

/**
 * Safely gets dataset attributes from a DOM element
 * @param {string} selector - CSS selector for the element
 * @returns {Object} Dataset object or empty object if element not found
 */
export function getElementDataset(selector) {
  const element = document.querySelector(selector);
  return element ? element.dataset : {};
}

/**
 * Safely gets an attribute from a DOM element
 * @param {string} selector - CSS selector for the element
 * @param {string} attribute - Attribute name to get
 * @returns {string|null} Attribute value or null if not found
 */
export function getElementAttribute(selector, attribute) {
  const element = document.querySelector(selector);
  return element ? element.getAttribute(attribute) : null;
}

/**
 * Array utilities
 */

/**
 * Paginates an array
 * @param {Array} array - Array to paginate
 * @param {number} page - Current page (1-based)
 * @param {number} itemsPerPage - Items per page
 * @returns {Array} Paginated array slice
 */
export function paginateArray(array, page, itemsPerPage) {
  if (!Array.isArray(array) || page < 1 || itemsPerPage < 1) {
    return [];
  }
  
  const start = (page - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  
  return array.slice(start, end);
}

/**
 * Calculates total pages for pagination
 * @param {number} totalItems - Total number of items
 * @param {number} itemsPerPage - Items per page
 * @returns {number} Total number of pages
 */
export function calculateTotalPages(totalItems, itemsPerPage) {
  if (totalItems <= 0 || itemsPerPage <= 0) {
    return 0;
  }
  
  return Math.ceil(totalItems / itemsPerPage);
}
