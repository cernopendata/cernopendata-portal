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

// Mock ReactDOM before importing the app
const mockRender = jest.fn();
jest.mock('react-dom', () => ({
  render: mockRender
}));

// Mock the components
jest.mock('../FilesBoxApp', () => {
  return function MockFilesBoxApp(props) {
    return `FilesBoxApp with recordAvailability: ${props.recordAvailability}`;
  };
});

jest.mock('../CitationsApp', () => {
  return function MockCitationsApp() {
    return 'CitationsApp';
  };
});

jest.mock('../components/RequestRecord', () => {
  return function MockRequestRecordApp(props) {
    return `RequestRecordApp with recordId: ${props.recordId}`;
  };
});

describe('App initialization', () => {
  let originalAddEventListener;
  let originalReadyState;
  let originalQuerySelector;

  beforeEach(() => {
    mockRender.mockClear();
    
    // Save originals
    originalAddEventListener = document.addEventListener;
    originalReadyState = document.readyState;
    originalQuerySelector = document.querySelector;
    
    // Mock addEventListener
    document.addEventListener = jest.fn();
    
    // Mock document.readyState
    Object.defineProperty(document, 'readyState', {
      writable: true,
      value: 'loading'
    });

    // Set up querySelector to return mock elements
    document.querySelector = jest.fn((selector) => {
      if (selector === '#citations-react-app' || 
          selector === '#files-box-react-app' || 
          selector === '#request-record-react-app') {
        return {
          dataset: {
            recordId: 'test-record-123',
            availability: 'online',
            size: '1024',
            files: '5',
            recordavailability: 'online'
          },
          getAttribute: jest.fn((attr) => {
            const attributes = {
              'data-doi': '10.1234/test-doi',
              'data-recid': 'test-recid-123'
            };
            return attributes[attr] || null;
          })
        };
      }
      return null;
    });
  });

  afterEach(() => {
    document.addEventListener = originalAddEventListener;
    document.querySelector = originalQuerySelector;
    Object.defineProperty(document, 'readyState', {
      writable: true,
      value: originalReadyState
    });
    
    // Clean up any modules that might be cached
    jest.resetModules();
  });

  describe('RecordsAppInitializer', () => {
    it('should add DOMContentLoaded event listener', () => {
      require('../app');
      expect(document.addEventListener).toHaveBeenCalledWith(
        'DOMContentLoaded',
        expect.any(Function)
      );
    });

    it('should initialize apps when DOM is loaded', () => {
      require('../app');
      
      // Get the callback function passed to addEventListener
      const domLoadedCallback = document.addEventListener.mock.calls
        .find(call => call[0] === 'DOMContentLoaded')[1];
      
      // Call the callback
      domLoadedCallback();
      
      // Should render all three apps
      expect(mockRender).toHaveBeenCalledTimes(3);
    });

    it('should initialize CitationsApp correctly', () => {
      require('../app');
      const domLoadedCallback = document.addEventListener.mock.calls
        .find(call => call[0] === 'DOMContentLoaded')[1];
      
      domLoadedCallback();
      
      // Check if CitationsApp was rendered
      expect(mockRender).toHaveBeenCalledWith(
        expect.objectContaining({
          type: expect.any(Function)
        }),
        expect.any(Object)
      );
    });

    it('should initialize RequestRecordApp with correct props', () => {
      require('../app');
      const domLoadedCallback = document.addEventListener.mock.calls
        .find(call => call[0] === 'DOMContentLoaded')[1];
      
      domLoadedCallback();
      
      // Should have called render for RequestRecordApp
      expect(mockRender).toHaveBeenCalledWith(
        expect.objectContaining({
          props: expect.objectContaining({
            recordId: 'test-record-123',
            availability: 'online'
          })
        }),
        expect.any(Object)
      );
    });

    it('should initialize FilesBoxApp with correct props', () => {
      require('../app');
      const domLoadedCallback = document.addEventListener.mock.calls
        .find(call => call[0] === 'DOMContentLoaded')[1];
      
      domLoadedCallback();
      
      // Should have called render for FilesBoxApp
      expect(mockRender).toHaveBeenCalledWith(
        expect.objectContaining({
          props: expect.objectContaining({
            recordAvailability: 'online'
          })
        }),
        expect.any(Object)
      );
    });

    it('should handle missing DOM elements gracefully', () => {
      // Mock querySelector to return null for all selectors
      document.querySelector.mockReturnValue(null);
      
      require('../app');
      const domLoadedCallback = document.addEventListener.mock.calls
        .find(call => call[0] === 'DOMContentLoaded')[1];
      
      // Should not throw an error
      expect(() => domLoadedCallback()).not.toThrow();
      
      // Should not render anything
      expect(mockRender).not.toHaveBeenCalled();
    });

    it('should handle errors during app initialization', () => {
      // Mock ReactDOM.render to throw an error
      mockRender.mockImplementation(() => {
        throw new Error('Render error');
      });
      
      // Spy on console.error to check if errors are logged
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      require('../app');
      const domLoadedCallback = document.addEventListener.mock.calls
        .find(call => call[0] === 'DOMContentLoaded')[1];
      
      // Should not throw, but should log errors
      expect(() => domLoadedCallback()).not.toThrow();
      
      // Should have attempted to render and logged errors
      expect(consoleErrorSpy).toHaveBeenCalled();
      
      consoleErrorSpy.mockRestore();
    });

    it('should initialize immediately if DOM is already loaded', () => {
      // Set document.readyState to 'complete'
      Object.defineProperty(document, 'readyState', {
        writable: true,
        value: 'complete'
      });
      
      // Re-require the app module
      require('../app');
      
      // Should render immediately without waiting for DOMContentLoaded
      expect(mockRender).toHaveBeenCalledTimes(3);
    });

    it('should initialize immediately if DOM is interactive', () => {
      Object.defineProperty(document, 'readyState', {
        writable: true,
        value: 'interactive'
      });
      
      require('../app');
      
      expect(mockRender).toHaveBeenCalledTimes(3);
    });

    it('should handle CitationsApp initialization errors', () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      // Make ReactDOM.render throw only for first call (CitationsApp)
      let callCount = 0;
      mockRender.mockImplementation(() => {
        callCount++;
        if (callCount === 1) {
          throw new Error('CitationsApp error');
        }
      });
      
      require('../app');
      const domLoadedCallback = document.addEventListener.mock.calls
        .find(call => call[0] === 'DOMContentLoaded')[1];
      
      domLoadedCallback();
      
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to initialize Citations app:',
        expect.any(Error)
      );
      
      consoleErrorSpy.mockRestore();
    });
  });
});
