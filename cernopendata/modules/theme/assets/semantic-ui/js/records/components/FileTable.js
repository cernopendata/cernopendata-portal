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
import React, { useState, useMemo } from "react";
import PropTypes from "prop-types";
import { Button, Icon, Table, Dropdown } from "semantic-ui-react";

import { IndexFilesModal, DownloadWarningModal } from "../components";
import { toHumanReadableSize } from "../utils";
import config from "../config";

import "./FileTable.scss";

export default function FileTable({ items, table_type }) {
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
          {hasOnDemandColumn && <Table.HeaderCell>Status</Table.HeaderCell>}
          <Table.HeaderCell>{table_type === 'file_index' ? 'Index description' : 'Filename'}</Table.HeaderCell>
          <Table.HeaderCell>{table_type === 'file_index' ? 'Index size' : 'Size'}</Table.HeaderCell>
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
              {hasOnDemandColumn && (
                <Table.Cell>
                  {file.availability?.ondemand && (
                    <div className="ui label brown">
                      <Icon name={file.availability.online ? "clone" : "archive"} />
                      {file.availability.online ? "Sample files" : "On demand"}
                    </div>
                  )}
                </Table.Cell>
              )}
              <Table.Cell className="filename-cell">
                {table_type === 'file_index' ? file.description : file.key}
              </Table.Cell>
              <Table.Cell collapsing>
                {toHumanReadableSize(file.size)}
              </Table.Cell>
              <Table.Cell collapsing>
                {table_type === 'file_index' ? (
                  <Dropdown
                    text="Actions"
                    icon="ellipsis horizontal"
                    floating
                    labeled
                    button
                    className="mini blue icon"
                  >
                    <Dropdown.Menu>
                      <Dropdown.Item
                        icon="list"
                        text="List files"
                        title="List all the files inside the file index"
                        onClick={() => {
                          setSelectedFile(file);
                          setOpenModal(true);
                        }}
                      />
                      <Dropdown.Item
                        icon="download"
                        text="Download txt"
                        title="Download the list of files in txt format"
                        onClick={() => {
                          window.open(getFileUri(table_type, file.key, 'txt'), '_blank');
                        }}
                      />
                      <Dropdown.Item
                        icon="download"
                        text="Download json"
                        title="Download the information of the files in the file index in json format"
                        onClick={() => {
                          window.open(getFileUri(table_type, file.key), '_blank');
                        }}
                      />
                    </Dropdown.Menu>
                  </Dropdown>
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
