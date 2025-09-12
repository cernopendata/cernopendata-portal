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
import { render, screen } from '@testing-library/react';
import CitationsApp from '../CitationsApp';

// Mock the hooks
jest.mock('../hooks', () => ({
  useCitations: jest.fn()
}));

import { useCitations } from '../hooks';

describe('CitationsApp', () => {
  beforeEach(() => {
    useCitations.mockClear();
    
    // Reset document.querySelector mock
    document.querySelector.mockImplementation((selector) => {
      if (selector === '#citations-react-app') {
        return {
          getAttribute: (attr) => {
            if (attr === 'data-doi') return '10.1234/test-doi';
            if (attr === 'data-recid') return 'test-recid-123';
            return null;
          }
        };
      }
      return null;
    });
  });

  it('should render citation link when references are found', () => {
    useCitations.mockReturnValue({
      references: 3,
      message: 'There are 3 publications referring to these data',
      loading: false,
      error: null,
      inspireURL: 'https://inspirehep.net/literature?test=query'
    });

    render(<CitationsApp />);
    
    const link = screen.getByRole('link');
    expect(link).toHaveTextContent('There are 3 publications referring to these data');
    expect(link).toHaveAttribute('href', 'https://inspirehep.net/literature?test=query');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('should render single reference message correctly', () => {
    useCitations.mockReturnValue({
      references: 1,
      message: 'There is one publication referring to these data',
      loading: false,
      error: null,
      inspireURL: 'https://inspirehep.net/literature?test=query'
    });

    render(<CitationsApp />);
    
    expect(screen.getByText('There is one publication referring to these data')).toBeInTheDocument();
  });

  it('should render loading state', () => {
    useCitations.mockReturnValue({
      references: 0,
      message: '',
      loading: true,
      error: null,
      inspireURL: ''
    });

    render(<CitationsApp />);
    
    expect(screen.getByText('Loading citations...')).toBeInTheDocument();
  });

  it('should not render anything when there are no references', () => {
    useCitations.mockReturnValue({
      references: 0,
      message: '',
      loading: false,
      error: null,
      inspireURL: ''
    });

    const { container } = render(<CitationsApp />);
    
    expect(container.firstChild).toBeNull();
  });

  it('should not render anything when there is an error', () => {
    useCitations.mockReturnValue({
      references: 0,
      message: '',
      loading: false,
      error: 'Network error',
      inspireURL: ''
    });

    const { container } = render(<CitationsApp />);
    
    expect(container.firstChild).toBeNull();
  });

  it('should not render when DOM element is not found', () => {
    document.querySelector.mockReturnValue(null);
    
    useCitations.mockReturnValue({
      references: 0,
      message: '',
      loading: false,
      error: null,
      inspireURL: ''
    });

    const { container } = render(<CitationsApp />);
    
    expect(container.firstChild).toBeNull();
  });

  it('should not render when DOI is missing', () => {
    document.querySelector.mockImplementation((selector) => {
      if (selector === '#citations-react-app') {
        return {
          getAttribute: (attr) => {
            if (attr === 'data-doi') return null; // Missing DOI
            if (attr === 'data-recid') return 'test-recid-123';
            return null;
          }
        };
      }
      return null;
    });
    
    useCitations.mockReturnValue({
      references: 0,
      message: '',
      loading: false,
      error: null,
      inspireURL: ''
    });

    const { container } = render(<CitationsApp />);
    
    expect(container.firstChild).toBeNull();
  });

  it('should not render when record ID is missing', () => {
    document.querySelector.mockImplementation((selector) => {
      if (selector === '#citations-react-app') {
        return {
          getAttribute: (attr) => {
            if (attr === 'data-doi') return '10.1234/test-doi';
            if (attr === 'data-recid') return null; // Missing record ID
            return null;
          }
        };
      }
      return null;
    });
    
    useCitations.mockReturnValue({
      references: 0,
      message: '',
      loading: false,
      error: null,
      inspireURL: ''
    });

    const { container } = render(<CitationsApp />);
    
    expect(container.firstChild).toBeNull();
  });

  it('should call useCitations with correct parameters', () => {
    useCitations.mockReturnValue({
      references: 0,
      message: '',
      loading: false,
      error: null,
      inspireURL: ''
    });

    render(<CitationsApp />);
    
    expect(useCitations).toHaveBeenCalledWith('10.1234/test-doi', 'test-recid-123');
  });

  it('should handle console.warn for errors gracefully', () => {
    const consoleSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
    
    useCitations.mockReturnValue({
      references: 0,
      message: '',
      loading: false,
      error: 'API error',
      inspireURL: ''
    });

    render(<CitationsApp />);
    
    expect(consoleSpy).toHaveBeenCalledWith('Failed to load citations:', 'API error');
    
    consoleSpy.mockRestore();
  });
});
