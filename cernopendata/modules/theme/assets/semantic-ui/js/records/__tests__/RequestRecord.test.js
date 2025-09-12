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
import axios from 'axios';
import RequestRecordApp from '../components/RequestRecord';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock the hooks
jest.mock('../hooks', () => ({
  useModal: jest.fn()
}));

jest.mock('../utils', () => ({
  toHumanReadableSize: jest.fn((size) => `${size} bytes`)
}));

import { useModal } from '../hooks';

describe('RequestRecordApp', () => {
  const defaultProps = {
    recordId: 'test-record-123',
    availability: 'partial',
    num_files: '5',
    size: '1024'
  };

  const mockModalFunctions = {
    isOpen: false,
    openModal: jest.fn(),
    closeModal: jest.fn()
  };

  beforeEach(() => {
    useModal.mockReturnValue(mockModalFunctions);
    mockedAxios.post.mockClear();
    mockModalFunctions.openModal.mockClear();
    mockModalFunctions.closeModal.mockClear();
  });

  describe('Rendering based on availability', () => {
    it('should render for partial availability', () => {
      render(<RequestRecordApp {...defaultProps} availability="partial" />);
      
      expect(screen.getByText(/Availability:/)).toBeInTheDocument();
      expect(screen.getByText('PARTIAL')).toBeInTheDocument();
      expect(screen.getByText('Request all files')).toBeInTheDocument();
    });

    it('should render for on demand availability', () => {
      render(<RequestRecordApp {...defaultProps} availability="on demand" />);
      
      expect(screen.getByText('ON DEMAND')).toBeInTheDocument();
      expect(screen.getByText('Request all files')).toBeInTheDocument();
    });

    it('should render for requested availability', () => {
      render(<RequestRecordApp {...defaultProps} availability="requested" />);
      
      expect(screen.getByText('REQUESTED')).toBeInTheDocument();
      expect(screen.getByText('See request status')).toBeInTheDocument();
    });

    it('should not render for online availability', () => {
      const { container } = render(<RequestRecordApp {...defaultProps} availability="online" />);
      
      expect(container.firstChild).toBeNull();
    });
  });

  describe('File-specific requests', () => {
    it('should render only button for file-specific requests', () => {
      render(<RequestRecordApp {...defaultProps} file="test-file.root" />);
      
      expect(screen.getByText('Request file')).toBeInTheDocument();
      expect(screen.queryByText(/Availability:/)).not.toBeInTheDocument();
    });
  });

  describe('Requested state', () => {
    it('should render status link for requested state', () => {
      render(<RequestRecordApp {...defaultProps} availability="requested" />);
      
      const statusLink = screen.getByRole('link');
      expect(statusLink).toHaveAttribute('href', '/transfer_requests?record_id=test-record-123');
      expect(screen.getByText('See request status')).toBeInTheDocument();
    });
  });

  describe('Modal interactions', () => {
    it('should open modal when request button is clicked', async () => {
      const user = userEvent.setup();
      
      render(<RequestRecordApp {...defaultProps} />);
      
      const requestButton = screen.getByText('Request all files');
      await user.click(requestButton);
      
      expect(mockModalFunctions.openModal).toHaveBeenCalled();
    });

    it('should render modal when open', () => {
      useModal.mockReturnValue({
        ...mockModalFunctions,
        isOpen: true
      });
      
      render(<RequestRecordApp {...defaultProps} />);
      
      expect(screen.getByText('Request to make data available')).toBeInTheDocument();
      expect(screen.getByText(/Please confirm you want to request/)).toBeInTheDocument();
    });

    it('should render correct confirmation text for all files', () => {
      useModal.mockReturnValue({
        ...mockModalFunctions,
        isOpen: true
      });
      
      render(<RequestRecordApp {...defaultProps} />);
      
      expect(screen.getByText(/all files of the record/)).toBeInTheDocument();
      expect(screen.getByText(/I confirm that I want to request 5 files/)).toBeInTheDocument();
    });

    it('should render correct confirmation text for single file', () => {
      useModal.mockReturnValue({
        ...mockModalFunctions,
        isOpen: true
      });
      
      render(<RequestRecordApp {...defaultProps} file="test-file.root" />);
      
      expect(screen.getByText(/this file/)).toBeInTheDocument();
      // The checkbox still shows the num_files from props, not "this file"
      expect(screen.getByText(/I confirm that I want to request 5 files/)).toBeInTheDocument();
    });
  });

  describe('Form interactions', () => {
    beforeEach(() => {
      useModal.mockReturnValue({
        ...mockModalFunctions,
        isOpen: true
      });
    });

    it('should handle email input', async () => {
      const user = userEvent.setup();
      
      render(<RequestRecordApp {...defaultProps} />);
      
      const emailInput = screen.getByPlaceholderText('Enter your email');
      await user.type(emailInput, 'test@example.com');
      
      expect(emailInput).toHaveValue('test@example.com');
    });

    it('should handle checkbox confirmation', async () => {
      const user = userEvent.setup();
      
      render(<RequestRecordApp {...defaultProps} />);
      
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).not.toBeChecked();
      
      await user.click(checkbox);
      expect(checkbox).toBeChecked();
    });

    it('should disable OK button when not confirmed', () => {
      render(<RequestRecordApp {...defaultProps} />);
      
      const okButton = screen.getByText('OK');
      expect(okButton).toBeDisabled();
    });

    it('should enable OK button when confirmed', async () => {
      const user = userEvent.setup();
      
      render(<RequestRecordApp {...defaultProps} />);
      
      const checkbox = screen.getByRole('checkbox');
      await user.click(checkbox);
      
      const okButton = screen.getByText('OK');
      expect(okButton).not.toBeDisabled();
    });
  });

  describe('Form submission', () => {
    beforeEach(() => {
      useModal.mockReturnValue({
        ...mockModalFunctions,
        isOpen: true
      });
    });

    it('should submit form with correct data for all files', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValue({});
      
      // Mock window.location.reload
      delete window.location;
      window.location = { reload: jest.fn() };
      
      render(<RequestRecordApp {...defaultProps} />);
      
      // Fill form
      const emailInput = screen.getByPlaceholderText('Enter your email');
      await user.type(emailInput, 'test@example.com');
      
      const checkbox = screen.getByRole('checkbox');
      await user.click(checkbox);
      
      const okButton = screen.getByText('OK');
      await user.click(okButton);
      
      expect(mockedAxios.post).toHaveBeenCalledWith('/record/test-record-123/stage', {
        email: 'test@example.com'
      });
      
      await waitFor(() => {
        expect(window.location.reload).toHaveBeenCalled();
      });
    });

    it('should submit form with file parameter for single file request', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValue({});
      
      delete window.location;
      window.location = { reload: jest.fn() };
      
      render(<RequestRecordApp {...defaultProps} file="test-file.root" />);
      
      const checkbox = screen.getByRole('checkbox');
      await user.click(checkbox);
      
      const okButton = screen.getByText('OK');
      await user.click(okButton);
      
      expect(mockedAxios.post).toHaveBeenCalledWith('/record/test-record-123/stage', {
        email: '',
        file: 'test-file.root'
      });
    });

    it('should handle submission errors', async () => {
      const user = userEvent.setup();
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      mockedAxios.post.mockRejectedValue(new Error('Network error'));
      
      render(<RequestRecordApp {...defaultProps} />);
      
      const checkbox = screen.getByRole('checkbox');
      await user.click(checkbox);
      
      const okButton = screen.getByText('OK');
      await user.click(okButton);
      
      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith('Request failed', expect.any(Error));
      });
      
      consoleErrorSpy.mockRestore();
    });

    it('should show loading state during submission', async () => {
      const user = userEvent.setup();
      
      // Mock axios to return a promise that we can control
      let resolvePromise;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });
      mockedAxios.post.mockReturnValue(promise);
      
      render(<RequestRecordApp {...defaultProps} />);
      
      const checkbox = screen.getByRole('checkbox');
      await user.click(checkbox);
      
      const okButton = screen.getByText('OK');
      await user.click(okButton);
      
      // Button should show loading state
      expect(okButton).toHaveClass('loading');
      expect(okButton).toBeDisabled();
      
      // Resolve the promise
      resolvePromise({});
    });
  });

  describe('Availability messages', () => {
    it('should show correct message for partial availability', () => {
      render(<RequestRecordApp {...defaultProps} availability="partial" />);
      
      expect(screen.getByText(/only a subset of files are available/)).toBeInTheDocument();
    });

    it('should show correct message for on demand availability', () => {
      render(<RequestRecordApp {...defaultProps} availability="on demand" />);
      
      expect(screen.getByText(/dataset is currently not available/)).toBeInTheDocument();
    });

    it('should show correct message for requested availability', () => {
      render(<RequestRecordApp {...defaultProps} availability="requested" />);
      
      expect(screen.getByText(/files for this record are being staged/)).toBeInTheDocument();
    });
  });
});
