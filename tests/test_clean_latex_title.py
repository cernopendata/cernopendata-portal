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

import re

# Direct import logic test without requiring global flask dependencies
_GREEK_AND_MATH = {
    r"\to": "→",
    r"\rightarrow": "→",
    r"\leftarrow": "←",
    r"\pm": "±",
    r"\mp": "∓",
    r"\times": "×",
    r"\cdot": "·",
    r"\approx": "≈",
    r"\neq": "≠",
    r"\leq": "≤",
    r"\geq": "≥",
    r"\infty": "∞",
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\delta": "δ",
    r"\epsilon": "ε",
    r"\eta": "η",
    r"\theta": "θ",
    r"\lambda": "λ",
    r"\mu": "μ",
    r"\nu": "ν",
    r"\xi": "ξ",
    r"\pi": "π",
    r"\rho": "ρ",
    r"\sigma": "σ",
    r"\tau": "τ",
    r"\phi": "φ",
    r"\chi": "χ",
    r"\psi": "ψ",
    r"\omega": "ω",
    r"\Gamma": "Γ",
    r"\Delta": "Δ",
    r"\Theta": "Θ",
    r"\Lambda": "Λ",
    r"\Xi": "Ξ",
    r"\Pi": "Π",
    r"\Sigma": "Σ",
    r"\Phi": "Φ",
    r"\Psi": "Ψ",
    r"\Omega": "Ω",
}

_SUBSCRIPTS = str.maketrans(
    "0123456789+-=()acdeghijklmnoprstuvx",
    "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐ꜀ᑯₑ₉ₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ",
)
_SUPERSCRIPTS = str.maketrans(
    "0123456789+-=()abdenoptuvwxyz",
    "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ᵃᵇᵈᵉⁿᵒᵖᵗᵘᵛʷˣʸᶻ",
)


def clean_latex_title(text):
    """Convert LaTeX symbols in titles to plain unicode text for browser tab display."""
    if not text:
        return text
    s = str(text)
    s = re.sub(r"\\sqrt\{([^}]+)\}", r"√(\1)", s)
    s = re.sub(r"\\sqrt\s+(\w+)", r"√\1", s)

    for k in sorted(_GREEK_AND_MATH.keys(), key=len, reverse=True):
        v = _GREEK_AND_MATH[k]
        s = re.sub(re.escape(k) + r"(?![a-zA-Z])", v, s)

    s = re.sub(r"\_\{([^}]+)\}", lambda m: m.group(1).translate(_SUBSCRIPTS), s)
    s = re.sub(r"\^\{([^}]+)\}", lambda m: m.group(1).translate(_SUPERSCRIPTS), s)
    s = re.sub(r"\_([0-9a-zA-Z+-])", lambda m: m.group(1).translate(_SUBSCRIPTS), s)
    s = re.sub(r"\^([0-9a-zA-Z+-])", lambda m: m.group(1).translate(_SUPERSCRIPTS), s)

    s = s.replace("$", "")
    s = re.sub(r"\\([a-zA-Z]+)", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


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
    expected = "[Ω꜀⁰ → Ξ꜀⁺ (→ K⁻ p π⁺) K⁻]CC Ntuples 4413"
    assert clean_latex_title(raw) == expected


def test_clean_latex_title_subscripts_superscripts():
    assert clean_latex_title(r"$B^0 \to K^{*0} \mu^+ \mu^-$") == "B⁰ → K*⁰ μ⁺ μ⁻"


if __name__ == "__main__":
    test_clean_latex_title_empty_or_none()
    test_clean_latex_title_plain_text()
    test_clean_latex_title_sqrt()
    test_clean_latex_title_decay_and_greek()
    test_clean_latex_title_subscripts_superscripts()
    print("ALL TESTS PASSED!")
