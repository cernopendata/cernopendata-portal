/*
 * -*- coding: utf-8 -*-
 *
 * This file is part of CERN Open Data Portal.
 * Copyright (C) 2024 CERN.
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


import React from "react";
import { Loader, Message } from "semantic-ui-react";
import PropTypes from "prop-types";

import { useCitations } from "./hooks";
import { SELECTORS } from "./constants";

/**
 * Citations application component that displays publication references
 */
const CitationsApp = () => {
  // Get DOI and record ID from DOM attributes
  const getDOMData = () => {
    const container = document.querySelector(SELECTORS.CITATIONS_APP);
    if (!container) return { doi: null, recid: null };
    
    return {
      doi: container.getAttribute("data-doi"),
      recid: container.getAttribute("data-recid")
    };
  };

  const { doi, recid } = getDOMData();
  const { references, message, loading, error, inspireURL } = useCitations(doi, recid);

  // Don't render anything if no DOI or record ID is available
  if (!doi || !recid) {
    return null;
  }

  if (loading) {
    return <Loader active inline size="mini">Loading citations...</Loader>;
  }

  if (error) {
    console.warn('Failed to load citations:', error);
    return null; // Fail silently for citations as it's not critical
  }

  if (references === 0) {
    return null;
  }

  return (
    <a href={inspireURL} target="_blank" rel="noopener noreferrer">
      {message}
    </a>
  );
};

CitationsApp.propTypes = {};

CitationsApp.displayName = 'CitationsApp';

export default CitationsApp;
