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

// jest-dom adds custom jest matchers for asserting on DOM nodes.
import '@testing-library/jest-dom';
import 'jest-environment-jsdom';

// Mock global fetch
global.fetch = jest.fn();

// Mock console methods to avoid noise in tests
global.console = {
  ...console,
  // Uncomment to ignore a specific log level
  // log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};

// Mock DOM elements that components expect
const mockElement = {
  dataset: {
    pidValue: 'test-pid-123',
    recordavailability: 'online',
    recordId: 'test-record-123',
    availability: 'online',
    size: '1024',
    files: '5'
  },
  getAttribute: jest.fn((attr) => {
    const attributes = {
      'data-doi': '10.1234/test-doi',
      'data-recid': 'test-recid-123'
    };
    return attributes[attr] || null;
  })
};

// Mock document.querySelector
const originalQuerySelector = document.querySelector;
document.querySelector = jest.fn((selector) => {
  if (selector === '#citations-react-app' || 
      selector === '#files-box-react-app' || 
      selector === '#request-record-react-app') {
    return mockElement;
  }
  return originalQuerySelector.call(document, selector) || null;
});

// Mock window.location.reload
Object.defineProperty(window, 'location', {
  value: {
    reload: jest.fn(),
  },
  writable: true,
});

// Mock jQuery for Semantic UI components
global.$ = jest.fn(() => ({
  dropdown: jest.fn(),
}));

// Setup intersection observer mock
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

beforeEach(() => {
  fetch.mockClear();
  console.debug.mockClear();
  console.info.mockClear();
  console.warn.mockClear();
  console.error.mockClear();
});
