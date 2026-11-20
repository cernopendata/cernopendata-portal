# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2026 CERN.
#
# CERN Open Data Portal is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CERN Open Data Portal is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CERN Open Data Portal; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Tests for clean_latex_title utility."""

from cernopendata.modules.records.latex import clean_latex_title


def test_clean_latex_title_empty_or_none():
    assert clean_latex_title(None) is None
    assert clean_latex_title("") == ""
    assert clean_latex_title("   ") == ""


def test_clean_latex_title_plain_text():
    assert clean_latex_title("Normal Title") == "Normal Title"
    assert clean_latex_title("CMS Run 2016 Data") == "CMS Run 2016 Data"


def test_clean_latex_title_sqrt():
    assert clean_latex_title(r"$\sqrt{s} = 13$ TeV") == "√(s) = 13 TeV"


def test_clean_latex_title_decay_and_greek():
    raw = r"[$\Omega_c^0 \to \Xi_c^+ (\to K^- p \pi^+) K^-$]CC Ntuples 4413"
    expected = "[Ω_c^0 →Ξ_c^+ (→ K^- p π^+) K^-]CC Ntuples 4413"
    assert clean_latex_title(raw) == expected


def test_clean_latex_title_subscripts_superscripts():
    assert clean_latex_title(r"$B^0 \to K^{*0} \mu^+ \mu^-$") == "B^0 → K^*0μ^+ μ^-"


if __name__ == "__main__":
    test_clean_latex_title_empty_or_none()
    test_clean_latex_title_plain_text()
    test_clean_latex_title_sqrt()
    test_clean_latex_title_decay_and_greek()
    test_clean_latex_title_subscripts_superscripts()
    print("ALL TESTS PASSED!")
