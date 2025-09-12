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

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FilesBoxApp from '../FilesBoxApp';

// Mock the components and hooks
jest.mock('../components', () => ({
  FileTable: jest.fn(({ items, table_type }) => {
    // Only render if items has files
    if (!items || !items.files || items.files.length === 0) {
      return null;
    }
    
    return (
      <div data-testid={`file-table-${table_type}`}>
        <div>Files: {items.files.length}</div>
        <div>Total: {items.total}</div>
      </div>
    );
  })
}));

jest.mock('../hooks', () => ({
  useFileData: jest.fn()
}));

jest.mock('../config', () => ({
  __esModule: true,
  default: { pidValue: 'test-pid-123' }
}));

import { useFileData } from '../hooks';

describe('FilesBoxApp', () => {
  const defaultProps = {
    recordAvailability: 'online'
  };

  beforeEach(() => {
    useFileData.mockClear();
  });

  it('should render loading state', () => {
    useFileData.mockReturnValue({
      files: { total: 0, files: [] },
      indexFiles: { total: 0, files: [] },
      loading: true,
      error: null
    });

    render(<FilesBoxApp {...defaultProps} />);
    
    expect(screen.getByText('Loading files...')).toBeInTheDocument();
  });

  it('should render error state', () => {
    useFileData.mockReturnValue({
      files: { total: 0, files: [] },
      indexFiles: { total: 0, files: [] },
      loading: false,
      error: 'Network error'
    });

    render(<FilesBoxApp {...defaultProps} />);
    
    expect(screen.getByText('Error loading files')).toBeInTheDocument();
    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  it('should render file tables when data is loaded', () => {
    // Update the mock to always render when there are files
    const { FileTable } = require('../components');
    FileTable.mockImplementation(({ items, table_type }) => {
      if (items && items.files && items.files.length > 0) {
        return (
          <div data-testid={`file-table-${table_type}`}>
            <div>Files: {items.files.length}</div>
            <div>Total: {items.total}</div>
          </div>
        );
      }
      return null;
    });

    useFileData.mockReturnValue({
      files: { 
        total: 2, 
        files: [
          { key: 'file1.root', size: 1024 },
          { key: 'file2.root', size: 2048 }
        ]
      },
      indexFiles: { 
        total: 1, 
        files: [
          { key: 'index.json', size: 512 }
        ]
      },
      loading: false,
      error: null
    });

    render(<FilesBoxApp {...defaultProps} />);
    
    expect(screen.getByTestId('file-table-files')).toBeInTheDocument();
    expect(screen.getByTestId('file-table-file_index')).toBeInTheDocument();
    expect(screen.getByText('Files: 2')).toBeInTheDocument();
    expect(screen.getByText('Files: 1')).toBeInTheDocument();
  });

  it('should not render tables when no files are available', () => {
    useFileData.mockReturnValue({
      files: { total: 0, files: [] },
      indexFiles: { total: 0, files: [] },
      loading: false,
      error: null
    });

    render(<FilesBoxApp {...defaultProps} />);
    
    expect(screen.queryByTestId('file-table-files')).not.toBeInTheDocument();
    expect(screen.queryByTestId('file-table-file_index')).not.toBeInTheDocument();
  });

  it('should render pagination when files exceed page limit', () => {
    useFileData.mockReturnValue({
      files: { 
        total: 10, // More than ITEMS_PER_PAGE (5)
        files: Array.from({ length: 10 }, (_, i) => ({ 
          key: `file${i}.root`, 
          size: 1024 
        }))
      },
      indexFiles: { total: 0, files: [] },
      loading: false,
      error: null
    });

    render(<FilesBoxApp {...defaultProps} />);
    
    // Should render pagination component
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });

  it('should handle pagination changes', async () => {
    const user = userEvent.setup();
    
    useFileData.mockReturnValue({
      files: { 
        total: 10,
        files: Array.from({ length: 10 }, (_, i) => ({ 
          key: `file${i}.root`, 
          size: 1024 
        }))
      },
      indexFiles: { total: 0, files: [] },
      loading: false,
      error: null
    });

    render(<FilesBoxApp {...defaultProps} />);
    
    // Find and click page 2 button
    const page2Button = screen.getByText('2');
    await user.click(page2Button);
    
    // useFileData should be called with new page parameter
    await waitFor(() => {
      expect(useFileData).toHaveBeenLastCalledWith('test-pid-123', 2);
    });
  });

  it('should call useFileData with correct parameters', () => {
    useFileData.mockReturnValue({
      files: { total: 0, files: [] },
      indexFiles: { total: 0, files: [] },
      loading: false,
      error: null
    });

    render(<FilesBoxApp {...defaultProps} />);
    
    expect(useFileData).toHaveBeenCalledWith('test-pid-123', 1);
  });

  it('should pass correct props to FileTable components', () => {
    const mockFiles = { 
      total: 2, 
      files: [
        { key: 'file1.root', size: 1024 },
        { key: 'file2.root', size: 2048 }
      ]
    };
    
    const mockIndexFiles = { 
      total: 1, 
      files: [
        { key: 'index.json', size: 512 }
      ]
    };

    useFileData.mockReturnValue({
      files: mockFiles,
      indexFiles: mockIndexFiles,
      loading: false,
      error: null
    });

    render(<FilesBoxApp {...defaultProps} />);
    
    const { FileTable } = require('../components');
    
    expect(FileTable).toHaveBeenCalledWith({
      items: mockFiles,
      pidValue: 'test-pid-123',
      table_type: 'files',
      recordAvailability: 'online'
    }, {});
    
    expect(FileTable).toHaveBeenCalledWith({
      items: mockIndexFiles,
      pidValue: 'test-pid-123',
      table_type: 'file_index',
      recordAvailability: 'online'
    }, {});
  });
});
