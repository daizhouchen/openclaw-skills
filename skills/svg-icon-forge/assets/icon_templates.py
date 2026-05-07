#!/usr/bin/env python3
"""Parameterized SVG icon templates for common categories.

Each template function accepts a `style` parameter and returns a complete SVG string.
Supported styles: outline, filled, duotone, hand-drawn, pixel
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SVG_OPEN = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
    'viewBox="0 0 24 24"'
)

OUTLINE_ATTRS = (
    ' fill="none" stroke="currentColor" stroke-width="2"'
    ' stroke-linecap="round" stroke-linejoin="round"'
)

FILLED_ATTRS = ' fill="currentColor" stroke="none"'


def _wrap(title: str, inner: str, extra_attrs: str = "") -> str:
    return f'{SVG_OPEN}{extra_attrs}><title>{title}</title>{inner}</svg>'


def _outline(title: str, paths: str) -> str:
    return _wrap(title, paths, OUTLINE_ATTRS)


def _filled(title: str, paths: str) -> str:
    return _wrap(title, paths, FILLED_ATTRS)


def _duotone(title: str, bg_paths: str, fg_paths: str) -> str:
    inner = (
        f'<g fill="currentColor" opacity="0.3">{bg_paths}</g>'
        f'<g fill="currentColor">{fg_paths}</g>'
    )
    return _wrap(title, inner, ' fill="none"')


def _hand_drawn(title: str, paths: str) -> str:
    attrs = (
        ' fill="none" stroke="currentColor" stroke-width="1.8"'
        ' stroke-linecap="round" stroke-linejoin="round"'
    )
    return _wrap(title, paths, attrs)


def _pixel(title: str, rects: str) -> str:
    return _wrap(title, rects, ' fill="currentColor"')


# ---------------------------------------------------------------------------
# Navigation Icons
# ---------------------------------------------------------------------------

def arrow_right(style: str = "outline") -> str:
    """Right arrow icon."""
    templates = {
        "outline": _outline("Arrow Right",
            '<path d="M5 12h14"/><path d="M12 5l7 7-7 7"/>'),
        "filled": _filled("Arrow Right",
            '<path d="M5 11h11.17l-4.88-4.88a1 1 0 011.42-1.42l6.59 6.59a1 1 0 010 1.42l-6.59 6.59a1 1 0 01-1.42-1.42L16.17 13H5a1 1 0 010-2z"/>'),
        "duotone": _duotone("Arrow Right",
            '<rect x="3" y="10" width="14" height="4" rx="1"/>',
            '<path d="M12 5l7 7-7 7z"/>'),
        "hand-drawn": _hand_drawn("Arrow Right",
            '<path d="M5.2 12.1c4.5-0.2 9.1 0.1 13.6-0.1"/>'
            '<path d="M12.1 5.2c2.2 2.1 4.6 4.5 6.8 6.9-2.3 2.2-4.5 4.6-6.9 6.8"/>'),
        "pixel": _pixel("Arrow Right",
            '<rect x="4" y="11" width="14" height="2"/>'
            '<rect x="14" y="7" width="2" height="2"/><rect x="16" y="9" width="2" height="2"/>'
            '<rect x="18" y="11" width="2" height="2"/><rect x="16" y="13" width="2" height="2"/>'
            '<rect x="14" y="15" width="2" height="2"/>'),
    }
    return templates.get(style, templates["outline"])


def menu(style: str = "outline") -> str:
    """Hamburger menu icon."""
    templates = {
        "outline": _outline("Menu",
            '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>'),
        "filled": _filled("Menu",
            '<rect x="3" y="5" width="18" height="2" rx="1"/>'
            '<rect x="3" y="11" width="18" height="2" rx="1"/>'
            '<rect x="3" y="17" width="18" height="2" rx="1"/>'),
        "duotone": _duotone("Menu",
            '<rect x="3" y="5" width="18" height="2" rx="1"/>'
            '<rect x="3" y="17" width="18" height="2" rx="1"/>',
            '<rect x="3" y="11" width="18" height="2" rx="1"/>'),
        "hand-drawn": _hand_drawn("Menu",
            '<path d="M4.1 6.1c5.3-0.1 10.7 0.2 15.8-0.1"/>'
            '<path d="M4.0 12.2c5.4 0.1 10.6-0.2 15.9 0.0"/>'
            '<path d="M4.2 17.9c5.2 0.2 10.8-0.1 15.7 0.1"/>'),
        "pixel": _pixel("Menu",
            '<rect x="4" y="6" width="16" height="2"/>'
            '<rect x="4" y="11" width="16" height="2"/>'
            '<rect x="4" y="16" width="16" height="2"/>'),
    }
    return templates.get(style, templates["outline"])


def close(style: str = "outline") -> str:
    """Close / X icon."""
    templates = {
        "outline": _outline("Close",
            '<path d="M18 6L6 18"/><path d="M6 6l12 12"/>'),
        "filled": _filled("Close",
            '<path d="M13.41 12l4.3-4.29a1 1 0 00-1.42-1.42L12 10.59 7.71 6.29a1 1 0 00-1.42 1.42L10.59 12l-4.3 4.29a1 1 0 001.42 1.42L12 13.41l4.29 4.3a1 1 0 001.42-1.42z"/>'),
        "duotone": _duotone("Close",
            '<circle cx="12" cy="12" r="9"/>',
            '<path d="M15 9l-6 6M9 9l6 6"/>'),
        "hand-drawn": _hand_drawn("Close",
            '<path d="M6.1 6.2c3.9 3.8 7.8 7.9 11.8 11.7"/>'
            '<path d="M17.9 6.1c-4.0 3.9-7.8 7.8-11.7 11.8"/>'),
        "pixel": _pixel("Close",
            '<rect x="6" y="6" width="2" height="2"/><rect x="8" y="8" width="2" height="2"/>'
            '<rect x="10" y="10" width="2" height="2"/><rect x="12" y="10" width="2" height="2"/>'
            '<rect x="14" y="8" width="2" height="2"/><rect x="16" y="6" width="2" height="2"/>'
            '<rect x="6" y="16" width="2" height="2"/><rect x="8" y="14" width="2" height="2"/>'
            '<rect x="14" y="14" width="2" height="2"/><rect x="16" y="16" width="2" height="2"/>'),
    }
    return templates.get(style, templates["outline"])


def search(style: str = "outline") -> str:
    """Search / magnifying glass icon."""
    templates = {
        "outline": _outline("Search",
            '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/>'),
        "filled": _filled("Search",
            '<path d="M11 2a9 9 0 106.32 15.49l3.6 3.6a1 1 0 001.41-1.42l-3.59-3.59A9 9 0 0011 2zm0 2a7 7 0 110 14 7 7 0 010-14z"/>'),
        "duotone": _duotone("Search",
            '<circle cx="11" cy="11" r="7"/>',
            '<path d="M21 21l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'),
        "hand-drawn": _hand_drawn("Search",
            '<path d="M11 4.1c3.8-0.1 7.1 3.1 6.9 6.9-0.1 3.8-3.2 6.9-6.9 6.9-3.8 0-7-3.1-6.9-6.9 0.1-3.8 3.1-7.0 6.9-6.9z"/>'
            '<path d="M16.2 16.1c1.6 1.5 3.1 3.2 4.7 4.8"/>'),
        "pixel": _pixel("Search",
            '<rect x="8" y="4" width="6" height="2"/>'
            '<rect x="6" y="6" width="2" height="2"/><rect x="14" y="6" width="2" height="2"/>'
            '<rect x="4" y="8" width="2" height="6"/><rect x="16" y="8" width="2" height="6"/>'
            '<rect x="6" y="14" width="2" height="2"/><rect x="14" y="14" width="2" height="2"/>'
            '<rect x="8" y="16" width="6" height="2"/>'
            '<rect x="16" y="16" width="2" height="2"/><rect x="18" y="18" width="2" height="2"/><rect x="20" y="20" width="2" height="2"/>'),
    }
    return templates.get(style, templates["outline"])


# ---------------------------------------------------------------------------
# Action Icons
# ---------------------------------------------------------------------------

def edit(style: str = "outline") -> str:
    """Edit / pencil icon."""
    templates = {
        "outline": _outline("Edit",
            '<path d="M17 3l4 4L7 21H3v-4L17 3z"/>'),
        "filled": _filled("Edit",
            '<path d="M16.29 2.29a1 1 0 011.42 0l4 4a1 1 0 010 1.42l-14 14A1 1 0 017 22H3a1 1 0 01-1-1v-4a1 1 0 01.29-.71l14-14z"/>'),
        "duotone": _duotone("Edit",
            '<path d="M3 17v4h4L17 11l-4-4L3 17z"/>',
            '<path d="M17 3l4 4-3 3-4-4 3-3z"/>'),
        "hand-drawn": _hand_drawn("Edit",
            '<path d="M17.1 3.1c1.3 1.2 2.7 2.7 3.9 3.9L7.1 20.9H3.1v-3.9L17.1 3.1z"/>'),
        "pixel": _pixel("Edit",
            '<rect x="16" y="2" width="2" height="2"/><rect x="18" y="4" width="2" height="2"/>'
            '<rect x="14" y="4" width="2" height="2"/><rect x="16" y="6" width="2" height="2"/>'
            '<rect x="12" y="6" width="2" height="2"/><rect x="14" y="8" width="2" height="2"/>'
            '<rect x="10" y="8" width="2" height="2"/><rect x="12" y="10" width="2" height="2"/>'
            '<rect x="8" y="10" width="2" height="2"/><rect x="10" y="12" width="2" height="2"/>'
            '<rect x="6" y="12" width="2" height="2"/><rect x="8" y="14" width="2" height="2"/>'
            '<rect x="4" y="14" width="2" height="2"/><rect x="6" y="16" width="2" height="2"/>'
            '<rect x="2" y="16" width="2" height="6"/><rect x="4" y="20" width="4" height="2"/>'),
    }
    return templates.get(style, templates["outline"])


def delete(style: str = "outline") -> str:
    """Trash / delete icon."""
    templates = {
        "outline": _outline("Delete",
            '<path d="M3 6h18"/><path d="M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2"/>'
            '<path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>'),
        "filled": _filled("Delete",
            '<path d="M8 4a2 2 0 012-2h4a2 2 0 012 2v1h5a1 1 0 010 2h-1l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 7H4a1 1 0 010-2h4V4z"/>'),
        "duotone": _duotone("Delete",
            '<path d="M5 6l1 14a2 2 0 002 2h8a2 2 0 002-2l1-14H5z"/>',
            '<path d="M3 6h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
            '<path d="M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2"/>'),
        "hand-drawn": _hand_drawn("Delete",
            '<path d="M3.1 6.0h17.8"/>'
            '<path d="M8.0 5.9V4.1c0.1-1.1 0.9-2.0 2.1-2.0h3.9c1.1 0.1 2.0 0.9 2.0 2.0v1.9"/>'
            '<path d="M18.9 6.1l-0.9 13.8c-0.1 1.1-0.9 2.0-2.1 2.0H8.1c-1.1-0.1-2.0-0.9-2.0-2.0L5.1 6.0"/>'),
        "pixel": _pixel("Delete",
            '<rect x="4" y="6" width="16" height="2"/>'
            '<rect x="8" y="2" width="8" height="2"/><rect x="8" y="4" width="2" height="2"/><rect x="14" y="4" width="2" height="2"/>'
            '<rect x="6" y="8" width="2" height="12"/><rect x="16" y="8" width="2" height="12"/>'
            '<rect x="8" y="20" width="8" height="2"/>'),
    }
    return templates.get(style, templates["outline"])


def save(style: str = "outline") -> str:
    """Save / floppy disk icon."""
    templates = {
        "outline": _outline("Save",
            '<path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>'
            '<path d="M17 21v-8H7v8"/><path d="M7 3v5h8"/>'),
        "filled": _filled("Save",
            '<path d="M5 2a2 2 0 00-2 2v16a2 2 0 002 2h14a2 2 0 002-2V7l-5-5H5zm2 2h8v4H7V4zm0 8h10v10H7V12z"/>'),
        "duotone": _duotone("Save",
            '<path d="M5 3h11l5 5v11a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2z"/>',
            '<path d="M7 13h10v8H7v-8zM7 3h8v5H7V3z"/>'),
        "hand-drawn": _hand_drawn("Save",
            '<path d="M5.1 3.1h10.8l4.9 4.9v11.0c0 1.0-0.9 1.9-2.0 1.9H5.1c-1.1 0-2.0-0.9-2.0-2.0V5.1c0-1.1 0.9-1.9 2.0-2.0z"/>'
            '<path d="M7.0 3.1v5.0h8.0V3.0"/><path d="M7.0 13.0v8.0h10.0v-8.0"/>'),
        "pixel": _pixel("Save",
            '<rect x="4" y="2" width="12" height="2"/><rect x="16" y="4" width="2" height="2"/><rect x="18" y="6" width="2" height="2"/>'
            '<rect x="4" y="4" width="2" height="16"/><rect x="18" y="8" width="2" height="12"/>'
            '<rect x="6" y="20" width="12" height="2"/>'
            '<rect x="8" y="4" width="6" height="4"/>'
            '<rect x="8" y="12" width="8" height="2"/><rect x="8" y="14" width="8" height="6"/>'),
    }
    return templates.get(style, templates["outline"])


def share(style: str = "outline") -> str:
    """Share icon (network nodes)."""
    templates = {
        "outline": _outline("Share",
            '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>'
            '<path d="M8.59 13.51l6.83 3.98"/><path d="M15.41 6.51l-6.82 3.98"/>'),
        "filled": _filled("Share",
            '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>'
            '<path d="M8.59 13.51l6.83 3.98M15.41 6.51l-6.82 3.98" stroke="currentColor" stroke-width="1.5"/>'),
        "duotone": _duotone("Share",
            '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>',
            '<path d="M8.59 13.51l6.83 3.98M15.41 6.51l-6.82 3.98" stroke="currentColor" stroke-width="2"/>'),
        "hand-drawn": _hand_drawn("Share",
            '<circle cx="18" cy="5" r="2.9"/><circle cx="6" cy="12" r="3.1"/><circle cx="18" cy="19" r="2.9"/>'
            '<path d="M8.7 13.6c2.2 1.3 4.5 2.6 6.7 3.9"/><path d="M15.3 6.6c-2.3 1.3-4.5 2.6-6.7 3.9"/>'),
        "pixel": _pixel("Share",
            '<rect x="16" y="4" width="4" height="4"/><rect x="4" y="10" width="4" height="4"/><rect x="16" y="16" width="4" height="4"/>'
            '<rect x="8" y="12" width="2" height="2"/><rect x="10" y="14" width="2" height="2"/>'
            '<rect x="12" y="16" width="2" height="2"/><rect x="14" y="18" width="2" height="2"/>'
            '<rect x="8" y="10" width="2" height="2"/><rect x="10" y="8" width="2" height="2"/>'
            '<rect x="12" y="6" width="2" height="2"/><rect x="14" y="4" width="2" height="2"/>'),
    }
    return templates.get(style, templates["outline"])


# ---------------------------------------------------------------------------
# Status Icons
# ---------------------------------------------------------------------------

def check(style: str = "outline") -> str:
    """Checkmark icon."""
    templates = {
        "outline": _outline("Check",
            '<path d="M20 6L9 17l-5-5"/>'),
        "filled": _filled("Check",
            '<path d="M9 18.29a1 1 0 01-.71-.29l-5-5a1 1 0 011.42-1.42L9 15.88l10.29-10.3a1 1 0 011.42 1.42l-11 11a1 1 0 01-.71.29z"/>'),
        "duotone": _duotone("Check",
            '<circle cx="12" cy="12" r="10"/>',
            '<path d="M9 17l-5-5M9 17l11-11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'),
        "hand-drawn": _hand_drawn("Check",
            '<path d="M4.1 11.1c1.6 1.5 3.2 3.3 4.8 4.9 3.7-3.6 7.2-7.4 10.9-11.0"/>'),
        "pixel": _pixel("Check",
            '<rect x="4" y="10" width="2" height="2"/><rect x="6" y="12" width="2" height="2"/>'
            '<rect x="8" y="14" width="2" height="2"/><rect x="10" y="12" width="2" height="2"/>'
            '<rect x="12" y="10" width="2" height="2"/><rect x="14" y="8" width="2" height="2"/>'
            '<rect x="16" y="6" width="2" height="2"/><rect x="18" y="4" width="2" height="2"/>'),
    }
    return templates.get(style, templates["outline"])


def warning(style: str = "outline") -> str:
    """Warning / triangle-alert icon."""
    templates = {
        "outline": _outline("Warning",
            '<path d="M12 2L1 21h22L12 2z"/><path d="M12 9v4"/><path d="M12 17h0"/>'),
        "filled": _filled("Warning",
            '<path d="M12 2L1 21h22L12 2z"/>'
            '<rect x="11" y="9" width="2" height="4" fill="white"/>'
            '<rect x="11" y="16" width="2" height="2" fill="white"/>'),
        "duotone": _duotone("Warning",
            '<path d="M12 2L1 21h22L12 2z"/>',
            '<path d="M12 9v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
            '<circle cx="12" cy="17" r="1"/>'),
        "hand-drawn": _hand_drawn("Warning",
            '<path d="M12.1 2.2L1.2 20.9h21.7L12.1 2.2z"/>'
            '<path d="M12.0 9.1v3.8"/><path d="M12.0 16.9v0.2"/>'),
        "pixel": _pixel("Warning",
            '<rect x="10" y="2" width="4" height="2"/>'
            '<rect x="8" y="4" width="2" height="2"/><rect x="14" y="4" width="2" height="2"/>'
            '<rect x="6" y="6" width="2" height="2"/><rect x="16" y="6" width="2" height="2"/>'
            '<rect x="4" y="8" width="2" height="4"/><rect x="18" y="8" width="2" height="4"/>'
            '<rect x="2" y="12" width="2" height="4"/><rect x="20" y="12" width="2" height="4"/>'
            '<rect x="0" y="16" width="2" height="4"/><rect x="22" y="16" width="2" height="4"/>'
            '<rect x="2" y="20" width="20" height="2"/>'
            '<rect x="11" y="8" width="2" height="4"/><rect x="11" y="14" width="2" height="2"/>'),
    }
    return templates.get(style, templates["outline"])


def error(style: str = "outline") -> str:
    """Error / circle-X icon."""
    templates = {
        "outline": _outline("Error",
            '<circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6"/><path d="M9 9l6 6"/>'),
        "filled": _filled("Error",
            '<path d="M12 2a10 10 0 100 20 10 10 0 000-20zm3.71 12.29a1 1 0 01-1.42 1.42L12 13.41l-2.29 2.3a1 1 0 01-1.42-1.42L10.59 12 8.29 9.71a1 1 0 011.42-1.42L12 10.59l2.29-2.3a1 1 0 011.42 1.42L13.41 12l2.3 2.29z"/>'),
        "duotone": _duotone("Error",
            '<circle cx="12" cy="12" r="10"/>',
            '<path d="M15 9l-6 6M9 9l6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'),
        "hand-drawn": _hand_drawn("Error",
            '<circle cx="12" cy="12" r="9.8"/>'
            '<path d="M15.1 9.1l-5.9 5.9"/><path d="M9.1 9.0l5.9 6.0"/>'),
        "pixel": _pixel("Error",
            '<rect x="8" y="2" width="8" height="2"/>'
            '<rect x="6" y="4" width="2" height="2"/><rect x="16" y="4" width="2" height="2"/>'
            '<rect x="4" y="6" width="2" height="2"/><rect x="18" y="6" width="2" height="2"/>'
            '<rect x="2" y="8" width="2" height="8"/><rect x="20" y="8" width="2" height="8"/>'
            '<rect x="4" y="16" width="2" height="2"/><rect x="18" y="16" width="2" height="2"/>'
            '<rect x="6" y="18" width="2" height="2"/><rect x="16" y="18" width="2" height="2"/>'
            '<rect x="8" y="20" width="8" height="2"/>'
            '<rect x="8" y="8" width="2" height="2"/><rect x="14" y="8" width="2" height="2"/>'
            '<rect x="10" y="10" width="4" height="2"/>'
            '<rect x="10" y="12" width="4" height="2"/>'
            '<rect x="8" y="14" width="2" height="2"/><rect x="14" y="14" width="2" height="2"/>'),
    }
    return templates.get(style, templates["outline"])


def info(style: str = "outline") -> str:
    """Info / circle-i icon."""
    templates = {
        "outline": _outline("Info",
            '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h0"/>'),
        "filled": _filled("Info",
            '<path d="M12 2a10 10 0 100 20 10 10 0 000-20zm1 15a1 1 0 01-2 0v-4a1 1 0 012 0v4zm-1-8a1 1 0 110-2 1 1 0 010 2z"/>'),
        "duotone": _duotone("Info",
            '<circle cx="12" cy="12" r="10"/>',
            '<path d="M12 16v-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
            '<circle cx="12" cy="8" r="1"/>'),
        "hand-drawn": _hand_drawn("Info",
            '<circle cx="12" cy="12" r="9.9"/>'
            '<path d="M12.0 16.0v-3.9"/><path d="M12.0 8.0v0.1"/>'),
        "pixel": _pixel("Info",
            '<rect x="8" y="2" width="8" height="2"/>'
            '<rect x="6" y="4" width="2" height="2"/><rect x="16" y="4" width="2" height="2"/>'
            '<rect x="4" y="6" width="2" height="2"/><rect x="18" y="6" width="2" height="2"/>'
            '<rect x="2" y="8" width="2" height="8"/><rect x="20" y="8" width="2" height="8"/>'
            '<rect x="4" y="16" width="2" height="2"/><rect x="18" y="16" width="2" height="2"/>'
            '<rect x="6" y="18" width="2" height="2"/><rect x="16" y="18" width="2" height="2"/>'
            '<rect x="8" y="20" width="8" height="2"/>'
            '<rect x="11" y="7" width="2" height="2"/><rect x="11" y="11" width="2" height="5"/>'),
    }
    return templates.get(style, templates["outline"])


# ---------------------------------------------------------------------------
# Media Icons
# ---------------------------------------------------------------------------

def play(style: str = "outline") -> str:
    """Play button icon."""
    templates = {
        "outline": _outline("Play",
            '<polygon points="5,3 19,12 5,21"/>'),
        "filled": _filled("Play",
            '<path d="M5 3l14 9-14 9V3z"/>'),
        "duotone": _duotone("Play",
            '<circle cx="12" cy="12" r="10"/>',
            '<path d="M10 8l6 4-6 4V8z"/>'),
        "hand-drawn": _hand_drawn("Play",
            '<path d="M5.1 3.2v17.7L18.9 12.1 5.1 3.2z"/>'),
        "pixel": _pixel("Play",
            '<rect x="6" y="4" width="2" height="16"/>'
            '<rect x="8" y="6" width="2" height="12"/>'
            '<rect x="10" y="8" width="2" height="8"/>'
            '<rect x="12" y="10" width="2" height="4"/>'
            '<rect x="14" y="11" width="2" height="2"/>'),
    }
    return templates.get(style, templates["outline"])


def pause(style: str = "outline") -> str:
    """Pause button icon."""
    templates = {
        "outline": _outline("Pause",
            '<rect x="6" y="4" width="4" height="16" rx="1"/>'
            '<rect x="14" y="4" width="4" height="16" rx="1"/>'),
        "filled": _filled("Pause",
            '<rect x="6" y="4" width="4" height="16" rx="1"/>'
            '<rect x="14" y="4" width="4" height="16" rx="1"/>'),
        "duotone": _duotone("Pause",
            '<circle cx="12" cy="12" r="10"/>',
            '<rect x="8" y="7" width="3" height="10" rx="1"/>'
            '<rect x="13" y="7" width="3" height="10" rx="1"/>'),
        "hand-drawn": _hand_drawn("Pause",
            '<path d="M6.1 4.1h3.8v15.8H6.1z"/>'
            '<path d="M14.1 4.0h3.9v15.9H14.0z"/>'),
        "pixel": _pixel("Pause",
            '<rect x="6" y="4" width="4" height="16"/>'
            '<rect x="14" y="4" width="4" height="16"/>'),
    }
    return templates.get(style, templates["outline"])


def volume(style: str = "outline") -> str:
    """Volume / speaker icon."""
    templates = {
        "outline": _outline("Volume",
            '<path d="M11 5L6 9H2v6h4l5 4V5z"/>'
            '<path d="M15.54 8.46a5 5 0 010 7.07"/>'
            '<path d="M19.07 4.93a10 10 0 010 14.14"/>'),
        "filled": _filled("Volume",
            '<path d="M11 5L6 9H2v6h4l5 4V5z"/>'
            '<path d="M15.54 8.46a5 5 0 010 7.07" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>'
            '<path d="M19.07 4.93a10 10 0 010 14.14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>'),
        "duotone": _duotone("Volume",
            '<path d="M11 5L6 9H2v6h4l5 4V5z"/>',
            '<path d="M15.54 8.46a5 5 0 010 7.07M19.07 4.93a10 10 0 010 14.14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>'),
        "hand-drawn": _hand_drawn("Volume",
            '<path d="M10.9 5.1L6.1 9.0H2.1v6.0h4.0l4.9 3.9V5.1z"/>'
            '<path d="M15.5 8.5c1.5 1.4 1.9 3.4 1.1 5.2-0.3 0.7-0.7 1.3-1.2 1.8"/>'
            '<path d="M19.0 5.0c3.9 3.8 3.9 10.2 0.1 14.0"/>'),
        "pixel": _pixel("Volume",
            '<rect x="2" y="8" width="4" height="8"/>'
            '<rect x="6" y="6" width="2" height="2"/><rect x="8" y="4" width="2" height="2"/><rect x="10" y="2" width="2" height="20"/>'
            '<rect x="6" y="16" width="2" height="2"/><rect x="8" y="18" width="2" height="2"/>'
            '<rect x="14" y="8" width="2" height="2"/><rect x="14" y="14" width="2" height="2"/>'
            '<rect x="16" y="10" width="2" height="4"/>'
            '<rect x="18" y="4" width="2" height="2"/><rect x="18" y="18" width="2" height="2"/>'
            '<rect x="20" y="6" width="2" height="12"/>'),
    }
    return templates.get(style, templates["outline"])


# ---------------------------------------------------------------------------
# Registry for programmatic access
# ---------------------------------------------------------------------------

ALL_ICONS = {
    "navigation": {"arrow_right": arrow_right, "menu": menu, "close": close, "search": search},
    "actions": {"edit": edit, "delete": delete, "save": save, "share": share},
    "status": {"check": check, "warning": warning, "error": error, "info": info},
    "media": {"play": play, "pause": pause, "volume": volume},
}

STYLES = ["outline", "filled", "duotone", "hand-drawn", "pixel"]


def get_icon(name: str, style: str = "outline") -> str:
    """Look up an icon by name across all categories."""
    for category in ALL_ICONS.values():
        if name in category:
            return category[name](style)
    raise KeyError(f"Unknown icon: {name}")


if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "arrow_right"
    style = sys.argv[2] if len(sys.argv) > 2 else "outline"
    print(get_icon(name, style))
