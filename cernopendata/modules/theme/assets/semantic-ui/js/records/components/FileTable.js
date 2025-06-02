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
import React, { useState, useMemo, useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { Popup, Button, Icon, Table, Dropdown } from "semantic-ui-react";
import $ from "jquery"; // You need jQuery for Semantic UI's JS

import { IndexFilesModal, DownloadWarningModal } from "../components";
import { toHumanReadableSize } from "../utils";
import config from "../config";

import "./FileTable.scss";


function FileActionsDropdown({ file, table_type, setOpenModal, setSelectedFile, getFileUri }) {
  const dropdownRef = useRef(null);

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (dropdownRef.current) {
        $(dropdownRef.current).dropdown();
      }
    }, 0);
    return () => clearTimeout(timeout);
  }, []);
  const isOnline = Object.keys(file.availability).length === 1 && file.availability.hasOwnProperty('online');

  return (
    <div
      className="ui floating dropdown labeled button mini blue icon"
      ref={dropdownRef}
    >
      Download index<i className="download icon" style={{ marginLeft: "0.5em" }} />
      <div className="menu">
        <a
          className="item ui fluid button"
          href={getFileUri(table_type, file.key, "txt")}
          target="_blank"
          rel="noopener noreferrer"
          title="Download this file in plain text format"
          download
        >
          Format: txt
        </a>
        { !isOnline && (
            <a
              className="item ui fluid button"
              href={`${getFileUri(table_type, file.key, 'txt')}?qos=hot`}
              target="_blank"
              rel="noopener noreferrer"
              title="Download this file in plain text format"
              download
            >
              Format: txt (online files only)
            </a>
        )}
        <a
          className="item ui fluid button"
          href={getFileUri(table_type, file.key)}
          target="_blank"
          rel="noopener noreferrer"
          title="Download this file in JSON format"
          download
        >
          Format: json
        </a>
        { !isOnline && (
            <a
              className="item ui fluid button"
              href={`${getFileUri(table_type, file.key)}?qos=hot`}
              target="_blank"
              rel="noopener noreferrer"
              title="Download this file in JSON format"
              download
            >
              Format: json (online files only)
            </a>
         )}
      </div>
    </div>
  );
}

export default function FileTable({ items, table_type, recordAvailability }) {
  const [openModal, setOpenModal] = useState(false);
  const [openDownloadModal, setOpenDownloadModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState();

  const getFileUri = (table_type, fileKey, format) => {
    let url = `/record/${config.pidValue}/${table_type}/${fileKey}`;
    if (table_type === "file_index" && format === "txt") {
      url = url.replace(".json", ".txt");
    }
    return url;
  };

  const hasOnDemandColumn = useMemo(() => {
    return table_type === "file_index" && items.files.some(file => file.availability?.ondemand);
  }, [items.files, table_type]);

  return (
    <Table singleLine>
      <Table.Header>
        <Table.Row>
          <Table.HeaderCell>{table_type === 'file_index' ? 'Index description' : 'Filename'}</Table.HeaderCell>
          <Table.HeaderCell>{table_type === 'file_index' ? 'Index size' : 'Size'}</Table.HeaderCell>
          {hasOnDemandColumn && <Table.HeaderCell>Availability</Table.HeaderCell>}
          <Table.HeaderCell></Table.HeaderCell>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {items.files.map((file) => {
          const downloadProp =
            table_type !== 'file_index' && file.size > config.downloadThreshold
              ? {
                  onClick: () => {
                    setSelectedFile(file);
                    setOpenDownloadModal(true);
                  },
                }
              : { href: getFileUri(table_type, file.key) };

          return (
            <Table.Row key={file.version_id}>
              <Table.Cell className="filename-cell">
                {table_type === 'file_index' ? file.description : file.key}
              </Table.Cell>
              <Table.Cell collapsing>
                {toHumanReadableSize(file.size)}
              </Table.Cell>
              {hasOnDemandColumn && (
                <Table.Cell>
                  {file.availability?.ondemand && (
                    <Popup
                        content={file.availability.online ? "Some files of the dataset are available for immediate download" : "The files have to be requested before they are available"}
                        trigger={<div className="ui mini message">{file.availability.online ? "Partially" : "On demand"}</div>}
                        position="top center"
                    />
                  )}
                </Table.Cell>
              )}
              <Table.Cell collapsing>
                {table_type === 'file_index' ? (
                   <>
                     <Button
                       className="mini blue"
                       onClick={() => {
                         setSelectedFile(file);
                         setOpenModal(true);
                       }}
                       title="Preview the content of this index file"
                     >
                       <i className="list icon" />
                       List files
                     </Button>
                     <FileActionsDropdown
                       file={file}
                       table_type={table_type}
                       setOpenModal={setOpenModal}
                       setSelectedFile={setSelectedFile}
                       getFileUri={getFileUri}
                     />
                   </>
                ) : (
                  <Button as="a" icon size="mini" primary {...downloadProp}>
                    <Icon name="download" /> Download
                  </Button>
                )}
              </Table.Cell>
            </Table.Row>
          );
        })}
      </Table.Body>
      {openModal && (
        <IndexFilesModal
          open={openModal}
          setOpen={setOpenModal}
          indexFile={selectedFile}
          recordAvailability={recordAvailability}
        />
      )}
      {openDownloadModal && (
        <DownloadWarningModal
          open={openDownloadModal}
          setOpen={setOpenDownloadModal}
          filename={selectedFile.key}
          size={selectedFile.size}
          uri={getFileUri(table_type, selectedFile.key)}
        />
      )}
    </Table>
  );
}


FileTable.propTypes = {
  items: PropTypes.object.isRequired,
};
