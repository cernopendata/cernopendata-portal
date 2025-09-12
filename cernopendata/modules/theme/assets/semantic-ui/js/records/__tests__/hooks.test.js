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

import { renderHook, act, waitFor } from '@testing-library/react';
import {
  useFileData,
  useCitations,
  useModal,
  useFormValidation,
  useFileAvailability
} from '../hooks';

// Mock the config module
jest.mock('../config', () => ({
  RECORD_FILEPAGE_URL: jest.fn((pid, page, type) => 
    `/api/record/${pid}/filepage/${page}${type ? `?type=${type}` : '?group=1'}`
  )
}));

describe('useFileData hook', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('should initialize with default values', async () => {
    const { result } = renderHook(() => useFileData('test-pid', 1));
    
    expect(result.current.files).toEqual({ total: 0, files: [] });
    expect(result.current.indexFiles).toEqual({ total: 0, files: [] });
    // Hook starts loading immediately when pidValue is provided
    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBe(null);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it('should not fetch when pidValue is empty', () => {
    renderHook(() => useFileData('', 1));
    expect(fetch).not.toHaveBeenCalled();
  });

  it('should fetch data successfully', async () => {
    const mockData = {
      files: { total: 2, files: [{ key: 'file1.root' }, { key: 'file2.root' }] },
      index_files: { total: 1, files: [{ key: 'index.json' }] }
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    const { result } = renderHook(() => useFileData('test-pid', 1));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.files).toEqual(mockData.files);
    expect(result.current.indexFiles).toEqual(mockData.index_files);
    expect(result.current.error).toBe(null);
  });

  it('should handle fetch errors', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useFileData('test-pid', 1));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Network error');
    expect(result.current.files).toEqual({ total: 0, files: [] });
    expect(result.current.indexFiles).toEqual({ total: 0, files: [] });
  });

  it('should handle HTTP errors', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 404
    });

    const { result } = renderHook(() => useFileData('test-pid', 1));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('HTTP error! status: 404');
  });

  it('should refetch when pidValue or page changes', async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ files: { total: 0, files: [] }, index_files: { total: 0, files: [] } })
    });

    const { rerender } = renderHook(
      ({ pidValue, page }) => useFileData(pidValue, page),
      { initialProps: { pidValue: 'test-pid-1', page: 1 } }
    );

    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));

    rerender({ pidValue: 'test-pid-2', page: 1 });
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));

    rerender({ pidValue: 'test-pid-2', page: 2 });
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
  });
});

describe('useCitations hook', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('should initialize with default values', async () => {
    const { result } = renderHook(() => useCitations('10.1234/test', 'test-recid'));
    
    expect(result.current.references).toBe(0);
    expect(result.current.message).toBe('');
    // Hook starts loading immediately when doi and recid are provided
    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBe(null);
    expect(result.current.inspireURL).toContain('inspirehep.net');
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it('should not fetch when doi or recid is missing', () => {
    renderHook(() => useCitations('', 'test-recid'));
    renderHook(() => useCitations('10.1234/test', ''));
    expect(fetch).not.toHaveBeenCalled();
  });

  it('should fetch citations successfully with single reference', async () => {
    const mockData = { hits: { total: 1 } };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    const { result } = renderHook(() => useCitations('10.1234/test', 'test-recid'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.references).toBe(1);
    expect(result.current.message).toBe('There is one publication referring to these data');
    expect(result.current.error).toBe(null);
  });

  it('should fetch citations successfully with multiple references', async () => {
    const mockData = { hits: { total: 5 } };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    const { result } = renderHook(() => useCitations('10.1234/test', 'test-recid'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.references).toBe(5);
    expect(result.current.message).toBe('There are 5 publications referring to these data');
  });

  it('should handle fetch errors gracefully', async () => {
    fetch.mockRejectedValueOnce(new Error('API error'));

    const { result } = renderHook(() => useCitations('10.1234/test', 'test-recid'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('API error');
    expect(result.current.references).toBe(0);
    expect(result.current.message).toBe('');
  });
});

describe('useModal hook', () => {
  it('should initialize with default closed state', () => {
    const { result } = renderHook(() => useModal());
    
    expect(result.current.isOpen).toBe(false);
    expect(result.current.modalProps.open).toBe(false);
  });

  it('should initialize with custom initial state', () => {
    const { result } = renderHook(() => useModal(true));
    
    expect(result.current.isOpen).toBe(true);
    expect(result.current.modalProps.open).toBe(true);
  });

  it('should open modal', () => {
    const { result } = renderHook(() => useModal());
    
    act(() => {
      result.current.openModal();
    });
    
    expect(result.current.isOpen).toBe(true);
  });

  it('should close modal', () => {
    const { result } = renderHook(() => useModal(true));
    
    act(() => {
      result.current.closeModal();
    });
    
    expect(result.current.isOpen).toBe(false);
  });

  it('should toggle modal', () => {
    const { result } = renderHook(() => useModal());
    
    act(() => {
      result.current.toggleModal();
    });
    expect(result.current.isOpen).toBe(true);
    
    act(() => {
      result.current.toggleModal();
    });
    expect(result.current.isOpen).toBe(false);
  });

  it('should provide modalProps with onClose handler', () => {
    const { result } = renderHook(() => useModal(true));
    
    act(() => {
      result.current.modalProps.onClose();
    });
    
    expect(result.current.isOpen).toBe(false);
  });
});

describe('useFormValidation hook', () => {
  const initialValues = { email: '', name: '' };
  const validationRules = {
    email: {
      required: true,
      pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
      message: 'Please enter a valid email'
    },
    name: {
      required: true,
      message: 'Name is required'
    }
  };

  it('should initialize with default values', () => {
    const { result } = renderHook(() => 
      useFormValidation(initialValues, validationRules)
    );
    
    expect(result.current.values).toEqual(initialValues);
    // Validation runs immediately, so errors should exist for required empty fields
    expect(result.current.errors).toEqual({
      email: 'Please enter a valid email',
      name: 'Name is required'
    });
    expect(result.current.isValid).toBe(false); // Required fields are empty
  });

  it('should validate required fields', async () => {
    const { result } = renderHook(() => 
      useFormValidation(initialValues, validationRules)
    );
    
    act(() => {
      result.current.updateValue('email', 'test@example.com');
    });

    await waitFor(() => {
      expect(result.current.errors.name).toBe('Name is required');
      expect(result.current.isValid).toBe(false);
    });
  });

  it('should validate pattern matching', async () => {
    const { result } = renderHook(() => 
      useFormValidation(initialValues, validationRules)
    );
    
    act(() => {
      result.current.updateValue('email', 'invalid-email');
      result.current.updateValue('name', 'Test User');
    });

    await waitFor(() => {
      expect(result.current.errors.email).toBe('Please enter a valid email');
      expect(result.current.isValid).toBe(false);
    });
  });

  it('should mark form as valid when all rules pass', async () => {
    const { result } = renderHook(() => 
      useFormValidation(initialValues, validationRules)
    );
    
    act(() => {
      result.current.updateValue('email', 'test@example.com');
      result.current.updateValue('name', 'Test User');
    });

    await waitFor(() => {
      expect(result.current.errors).toEqual({});
      expect(result.current.isValid).toBe(true);
    });
  });

  it('should reset form', () => {
    const { result } = renderHook(() => 
      useFormValidation(initialValues, validationRules)
    );
    
    act(() => {
      result.current.updateValue('email', 'test@example.com');
      result.current.updateValue('name', 'Test User');
    });

    act(() => {
      result.current.resetForm();
    });
    
    expect(result.current.values).toEqual(initialValues);
    // After reset, validation runs again on empty values
    expect(result.current.errors).toEqual({
      email: 'Please enter a valid email',
      name: 'Name is required'
    });
  });
});

describe('useFileAvailability hook', () => {
  it('should correctly identify on-demand files', () => {
    const { result } = renderHook(() => useFileAvailability());
    
    const onDemandFile1 = { availability: 'on demand' };
    const onDemandFile2 = { availability: { 'on demand': true } };
    const onlineFile = { availability: 'online' };
    
    expect(result.current.isOnDemand(onDemandFile1)).toBe(true);
    expect(result.current.isOnDemand(onDemandFile2)).toBe(true);
    expect(result.current.isOnDemand(onlineFile)).toBe(false);
  });

  it('should correctly identify online-only files', () => {
    const { result } = renderHook(() => useFileAvailability());
    
    const onlineOnlyFile = { availability: { online: true } };
    const mixedFile = { availability: { online: true, 'on demand': true } };
    const stringFile = { availability: 'online' };
    
    expect(result.current.isOnline(onlineOnlyFile)).toBe(true);
    expect(result.current.isOnline(mixedFile)).toBe(false);
    expect(result.current.isOnline(stringFile)).toBe(false);
  });

  it('should provide correct availability messages', () => {
    const { result } = renderHook(() => useFileAvailability());
    
    const onlineFile = { availability: { online: true } };
    const onDemandFile = { availability: 'on demand' };
    
    expect(result.current.getAvailabilityMessage(onlineFile)).toBe(
      'Some files of the dataset are available for immediate download'
    );
    expect(result.current.getAvailabilityMessage(onDemandFile)).toBe(
      'The files have to be requested before they are available'
    );
  });
});
