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
import PropTypes from "prop-types";
import { Button, Icon, Table } from "semantic-ui-react";

import { IndexFilesModal, DownloadWarningModal } from "../components";
import { toHumanReadableSize } from "../utils";
import config from "../config";

import "./FileTable.scss";

export default function FileTable({ items, table_type }) {
  const [openModal, setOpenModal] = useState(false);
  const [openDownloadModal, setOpenDownloadModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState();

  const getFileUri = (table_type, fileKey, format) => {
    var  url= `/record/${config.pidValue}/${table_type}/${fileKey}`;
    if (table_type=='file_index' && format== 'txt')
           url = url.replace('.json', '.txt');
    return url};
  return (
    <Table singleLine>
      <Table.Header>
        <Table.Row>
          <Table.HeaderCell>{table_type=='file_index' ? 'Index description' : 'Filename'}</Table.HeaderCell>
          <Table.HeaderCell>{table_type=='file_index' ? 'Index size' : 'Size'}</Table.HeaderCell>
          <Table.HeaderCell></Table.HeaderCell>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {items.files.map((file) => {
          const downloadProp =
            table_type != 'file_index' && file.size > config.downloadThreshold
              ? {
                  onClick: () => {
                    setSelectedFile(file);
                    setOpenDownloadModal(true);
                  },
                }
              : { href: getFileUri(table_type, file.key) };
          return (
            <Table.Row key={file.version_id}>
              <Table.Cell className="filename-cell">{table_type=='file_index' ? file.description :file.key}</Table.Cell>
              <Table.Cell collapsing>
                {toHumanReadableSize(file.size)}
              </Table.Cell>
              <Table.Cell collapsing>
                {table_type === "file_index"  ? ( <>
                  <Button
                    icon
                    size="mini"
                    onClick={() => {
                      setSelectedFile(file);
                      setOpenModal(true);
                    }}
                  >
                    <Icon name="list" /> List files
                  </Button>
                 <Button as="a" icon size="mini" primary href={getFileUri(table_type, file.key, 'txt') } >
                   <Icon name="download" /> Download txt
                  </Button>
                 <Button as="a" icon size="mini" primary href={getFileUri(table_type, file.key) }>
                   <Icon name="download" /> Download json
                  </Button></>
                ) :
                 <Button as="a" icon size="mini" primary {...downloadProp}>
                   <Icon name="download" /> Download
                  </Button>
                 }
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
