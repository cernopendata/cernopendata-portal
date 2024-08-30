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

import React from "react";
import PropTypes from "prop-types";
import { Button, Modal } from "semantic-ui-react";

import { toHumanReadableSize } from "../utils";

export default function DownloadWarningModal({
  open,
  setOpen,
  filename,
  size,
  uri,
}) {
  return (
    <Modal
      onClose={() => setOpen(false)}
      onOpen={() => setOpen(true)}
      open={open}
      closeIcon
    >
      <Modal.Content>
        <p>
          Please note that the file you are going to download ({filename}) is{" "}
          <strong>{toHumanReadableSize(size)}</strong> big. On an average ADSL
          connection, it may take several hours to download it.
        </p>
        <p>
          Most collaborations provide container images or virtual machine images allowing to perform analyses.
          If you use one of those, then you do not need to download datasets manually,
          because all the necessary file chunks will be accessed via the XRootD protocol during the live analysis.
          Please check the corresponding <a href="/search?q=getting%20started&f=type%3ADocumentation%2Bsubtype%3AGuide">getting started</a> guides for more details.
        </p>
        <p>
          Manual download of files via HTTP is only necessary if you would
          prefer not to use the XRootD protocol for one reason or another.
        </p>
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={() => setOpen(false)}>Cancel</Button>
        <Button href={uri} onClick={() => setOpen(false)} positive>
          Download
        </Button>
      </Modal.Actions>
    </Modal>
  );
}

DownloadWarningModal.propTypes = {
  open: PropTypes.bool.isRequired,
  setOpen: PropTypes.func.isRequired,
  filename: PropTypes.string.isRequired,
  size: PropTypes.number.isRequired,
  uri: PropTypes.string.isRequired,
};
