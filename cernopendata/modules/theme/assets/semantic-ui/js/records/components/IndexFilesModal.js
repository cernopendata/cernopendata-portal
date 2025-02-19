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

import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import {
  Button,
  Dimmer,
  Icon,
  Loader,
  Message,
  Modal,
  Pagination,
  Table,
} from "semantic-ui-react";

import { DownloadWarningModal } from "../components";
import config, { ITEMS_PER_PAGE, INDEX_FILES_URL } from "../config";
import { toHumanReadableSize } from "../utils";

import "./IndexFilesModal.scss";

export default function IndexFilesModal({ open, setOpen, indexFile }) {
  const files = indexFile.files;
  const [page, setPage] = useState(1);
  const [openDownloadModal, setOpenDownloadModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState();
  const getPageFiles = () => {
    const start = (page - 1) * ITEMS_PER_PAGE;
    const end = page * ITEMS_PER_PAGE;
    return files.slice(start, end);
  };
  const getFileUri = (file_key) => `/record/${config.pidValue}/files/${file_key}`;

  return (
    <>
      <Modal
        onClose={() => {
          setOpen(false);
          setPage(1);
        }}
        onOpen={() => setOpen(true)}
        open={open}
        closeIcon
      >
        <Modal.Header>List of files</Modal.Header>
        <Modal.Content>

            <div>
                <Table singleLine>
                  <Table.Header>
                    <Table.Row>
                      <Table.HeaderCell>Filename</Table.HeaderCell>
                      <Table.HeaderCell>Size</Table.HeaderCell>
                      <Table.HeaderCell></Table.HeaderCell>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {getPageFiles().map((file) => {
                      const downloadProp =
                        file.size > config.downloadThreshold
                          ? {
                              onClick: () => {
                                setSelectedFile(file.key);
                                setOpenDownloadModal(true);
                              },
                            }
                          : {
                              href: getFileUri(file.key),
                            };
                      return (
                        <Table.Row key={file.checksum}>
                          <Table.Cell>{file.filename}</Table.Cell>
                          <Table.Cell collapsing>
                            {toHumanReadableSize(file.size)}
                          </Table.Cell>
                          <Table.Cell collapsing>
                            {file.availability === "ondemand" ? (
                              <div className="ui label brown" title="This file is not currently available. If you want to access it, please request it using the button Request all files">
                               <Icon name="archive" /> On demand
                              </div>
                            ) : (
                              <Button as="a" icon size="mini" primary {...downloadProp}>
                               <Icon name="download" />
                              </Button>
                            )}
                          </Table.Cell>
                        </Table.Row>
                      );
                    })}
                  </Table.Body>
                </Table>
            </div>

          {files.length > ITEMS_PER_PAGE && (
            <Pagination
              className="index-files-pagination"
              activePage={page}
              onPageChange={(e, { activePage }) => setPage(activePage)}
              totalPages={Math.ceil(files.length / ITEMS_PER_PAGE)}
            />
          )}
        </Modal.Content>
      </Modal>
      {openDownloadModal && (
        <DownloadWarningModal
          open={openDownloadModal}
          setOpen={setOpenDownloadModal}
          filename={selectedFile.filename}
          size={selectedFile.size}
          uri={getFileUri(selectedFile)}
        />
      )}
    </>
  );
}

IndexFilesModal.propTypes = {
  open: PropTypes.bool.isRequired,
  setOpen: PropTypes.func.isRequired,
  indexFile: PropTypes.object,
};

IndexFilesModal.defaultProps = {
  indexFile: {},
};
