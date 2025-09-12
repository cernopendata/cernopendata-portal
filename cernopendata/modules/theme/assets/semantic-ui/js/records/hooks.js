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

import { useState, useEffect } from 'react';
import { INSPIRE_HOST, API_ENDPOINTS, AVAILABILITY_STATES } from './constants';
import { RECORD_FILEPAGE_URL } from './config';

/**
 * Custom hook for fetching file data with pagination
 */
export const useFileData = (pidValue, page) => {
  // Initialize with proper default structure to avoid PropTypes warnings
  const defaultFileData = { total: 0, files: [] };
  
  const [files, setFiles] = useState(defaultFileData);
  const [indexFiles, setIndexFiles] = useState(defaultFileData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!pidValue) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const type = getFileType(files, indexFiles);
        const response = await fetch(RECORD_FILEPAGE_URL(pidValue, page, type));
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (type === 'files') {
          setFiles(data);
        } else if (type === 'index_files') {
          setIndexFiles(data);
        } else {
          setFiles(data.files || defaultFileData);
          setIndexFiles(data.index_files || defaultFileData);
        }
      } catch (err) {
        setError(err.message);
        console.error('Error fetching file data:', err);
        // Reset to default structure on error
        setFiles(defaultFileData);
        setIndexFiles(defaultFileData);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [pidValue, page]);

  const getFileType = (files, indexFiles) => {
    if (files.total) return 'files';
    if (indexFiles.total) return 'index_files';
    return null;
  };

  return { files, indexFiles, loading, error };
};

/**
 * Custom hook for fetching citation data from INSPIRE
 */
export const useCitations = (doi, recid) => {
  const [references, setReferences] = useState(0);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!doi || !recid) return;

    const fetchCitations = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const inspireURL = `${API_ENDPOINTS.LITERATURE_SEARCH}?sort=mostrecent&page=1&q=references.reference.dois%3A${doi}%20or%20references.reference.urls.value%3Ahttps%3A%2F%2Fopendata.cern.ch%2Frecord%2F${recid}&size=1`;
        const response = await fetch(`${INSPIRE_HOST}/api${inspireURL}`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const total = data.hits.total;
        
        setReferences(total);
        setMessage(total === 1 
          ? 'There is one publication referring to these data'
          : `There are ${total} publications referring to these data`
        );
      } catch (err) {
        setError(err.message);
        console.error('Error fetching citations:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCitations();
  }, [doi, recid]);

  const getInspireURL = () => {
    const inspireURL = `${API_ENDPOINTS.LITERATURE_SEARCH}?sort=mostrecent&page=1&q=references.reference.dois%3A${doi}%20or%20references.reference.urls.value%3Ahttps%3A%2F%2Fopendata.cern.ch%2Frecord%2F${recid}`;
    return `${INSPIRE_HOST}${inspireURL}`;
  };

  return { references, message, loading, error, inspireURL: getInspireURL() };
};

/**
 * Custom hook for managing modal state
 */
export const useModal = (initialState = false) => {
  const [isOpen, setIsOpen] = useState(initialState);

  const openModal = () => setIsOpen(true);
  const closeModal = () => setIsOpen(false);
  const toggleModal = () => setIsOpen(!isOpen);

  return {
    isOpen,
    openModal,
    closeModal,
    toggleModal,
    modalProps: {
      open: isOpen,
      onClose: closeModal
    }
  };
};

/**
 * Custom hook for form validation
 */
export const useFormValidation = (initialValues, validationRules) => {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [isValid, setIsValid] = useState(false);

  useEffect(() => {
    validateForm();
  }, [values]);

  const validateForm = () => {
    const newErrors = {};
    let formIsValid = true;

    Object.keys(validationRules).forEach(field => {
      const rule = validationRules[field];
      const value = values[field];

      if (rule.required && (!value || value.trim() === '')) {
        newErrors[field] = rule.message || `${field} is required`;
        formIsValid = false;
      } else if (rule.pattern && value && !rule.pattern.test(value)) {
        newErrors[field] = rule.message || `${field} is invalid`;
        formIsValid = false;
      }
    });

    setErrors(newErrors);
    setIsValid(formIsValid);
  };

  const updateValue = (field, value) => {
    setValues(prev => ({ ...prev, [field]: value }));
  };

  const resetForm = () => {
    setValues(initialValues);
    setErrors({});
  };

  return {
    values,
    errors,
    isValid,
    updateValue,
    resetForm
  };
};

/**
 * Custom hook for file availability checking
 */
export const useFileAvailability = () => {
  const isOnDemand = (file) => {
    return (
      file.availability === AVAILABILITY_STATES.ON_DEMAND ||
      (typeof file.availability === 'object' && file.availability?.[AVAILABILITY_STATES.ON_DEMAND])
    );
  };

  const isOnline = (file) => {
    return Object.keys(file.availability).length === 1 && 
           file.availability.hasOwnProperty(AVAILABILITY_STATES.ONLINE);
  };

  const getAvailabilityMessage = (file) => {
    if (typeof file.availability === 'object' && file.availability.online) {
      return 'Some files of the dataset are available for immediate download';
    }
    return 'The files have to be requested before they are available';
  };

  return {
    isOnDemand,
    isOnline,
    getAvailabilityMessage
  };
};
