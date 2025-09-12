/*
 * -*- coding: utf-8 -*-
 *
 * This file is part of CERN Open Data Portal.
 * Copyright (C) 2021 CERN.
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

import React, { useState } from "react";
import { Pagination, Dimmer, Loader, Message } from "semantic-ui-react";
import PropTypes from "prop-types";

import { FileTable } from "./components";
import { useFileData } from "./hooks";
import { ITEMS_PER_PAGE, TABLE_TYPES } from "./constants";
import config from "./config";

/**
 * Component for rendering file tables with pagination
 */
const FileTableWithPagination = ({ items, tableType, page, onPageChange, recordAvailability }) => {
  const { pidValue } = config;

  if (items.total === 0) {
    return null;
  }

  return (
    <>
      <FileTable 
        items={items} 
        pidValue={pidValue} 
        table_type={tableType} 
        recordAvailability={recordAvailability}
      />
      {items.total > ITEMS_PER_PAGE && (
        <Pagination
          activePage={page}
          onPageChange={onPageChange}
          totalPages={Math.ceil(items.total / ITEMS_PER_PAGE)}
        />
      )}
    </>
  );
};

FileTableWithPagination.propTypes = {
  items: PropTypes.shape({
    total: PropTypes.number.isRequired,
    files: PropTypes.array.isRequired
  }).isRequired,
  tableType: PropTypes.string.isRequired,
  page: PropTypes.number.isRequired,
  onPageChange: PropTypes.func.isRequired,
  recordAvailability: PropTypes.string.isRequired
};

/**
 * Main Files Box Application component
 */
const FilesBoxApp = ({ recordAvailability }) => {
  const [page, setPage] = useState(1);
  const { pidValue } = config;
  const { files, indexFiles, loading, error } = useFileData(pidValue, page);

  const handlePaginationChange = (e, { activePage }) => {
    setPage(activePage);
  };

  if (loading) {
    return (
      <Dimmer active inverted>
        <Loader inverted>Loading files...</Loader>
      </Dimmer>
    );
  }

  if (error) {
    return (
      <Message negative>
        <Message.Header>Error loading files</Message.Header>
        <p>{error}</p>
      </Message>
    );
  }

  return (
    <>
      <FileTableWithPagination
        items={files}
        tableType={TABLE_TYPES.FILES}
        page={page}
        onPageChange={handlePaginationChange}
        recordAvailability={recordAvailability}
      />
      <FileTableWithPagination
        items={indexFiles}
        tableType={TABLE_TYPES.FILE_INDEX}
        page={page}
        onPageChange={handlePaginationChange}
        recordAvailability={recordAvailability}
      />
    </>
  );
};

FilesBoxApp.propTypes = {
  recordAvailability: PropTypes.string.isRequired
};

export default FilesBoxApp;
