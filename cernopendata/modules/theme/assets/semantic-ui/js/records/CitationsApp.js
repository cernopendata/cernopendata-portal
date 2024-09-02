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


import React, { useEffect, useState } from "react";
const CitationsApp = () => {
  const [references, setReferences] = useState(0);
  const [message, setMessage] = useState("");

  const doi = document.querySelector("#citations-react-app").getAttribute("data-doi");
  const recid = document.querySelector("#citations-react-app").getAttribute("data-recid");
  
  const inspireHost = "https://inspirehep.net"
  const inspireURL = `/literature?sort=mostrecent&size=1&page=1&q=references.reference.dois%3A${doi}%20or%20references.reference.urls.value%3Ahttps%3A%2F%2Fopendata.cern.ch%2Frecord%2F${recid}`;
  const inspireFullPath = `${inspireHost}${inspireURL}`;

  useEffect(() => {
    fetch(`${inspireHost}/api${inspireURL}`)
      .then((response) => response.json())
      .then((data) => {
        setReferences(data.hits.total);
        if (data.hits.total == 1) {
           setMessage("There is one publication referring to these data");
         } else {
           setMessage("There are "+data.hits.total+" publications referring to these data");
         }
      });
  }, []);

  return (
    <>
        { references > 0 &&
          <a href={inspireFullPath}>{message}</a>
        }
    </>
  );
};

export default CitationsApp;