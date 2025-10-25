#!/usr/bin/env python3
#
# MIT License
#
# Copyright (c) 2025 Hiroki Funashima
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import os
import matplotlib.font_manager as fm
from matplotlib import rcParams


class PlotFontManager:
    """
    Small utility class to manage and apply custom fonts in matplotlib.

    This class lets you:
    - Map readable font names (e.g. "Futura ND Book") to actual font files.
    - Register those fonts with matplotlib at runtime.
    - Set rcParams["font.family"] to consistently use that font in all plots.
    - Retrieve FontProperties objects for per-label overrides.

    Typical usage:
        pfm = PlotFontManager()
        pfm.set_font("Futura ND Book")

        import matplotlib.pyplot as plt
        plt.plot([0, 1, 2], [2, 1, 3])
        plt.title("Demo figure using Futura ND Book")
        plt.xlabel("time [s]")
        plt.ylabel("response")
        plt.show()

    Author:
        Hiroki Funashima (2025)

    Parameters
    ----------
    font_dir : str
        Directory where your font files live. Defaults to '/usr/local/share/fonts'.
    default_font : str
        Logical font name to fall back to when an unknown name is requested.
        This should be a key of `self.font_map`.
    """

    def __init__(self, font_dir="/usr/local/share/fonts", default_font="Helvetica Neue"):
        self.font_dir = font_dir
        self.default_font = default_font

        # Mapping from logical font names to actual font file names (or absolute paths).
        # You should edit this dictionary for your own environment / branding.
        self.font_map = {
            "Helvetica Neue": "HelveticaNeue.ttc",
            "Helvetica": "Helvetica.ttc",
            "Futura": "Futura.ttc",
            "Futura ND Book": "Neufville Digital - Futura ND Book.ttf",
            "Futura ND Bold": "Neufville Digital - Futura ND Bold.ttf",
            "Optima": "Optima.ttc",
            "Baskerville": "Baskerville.ttc",
            "Myriad": "MyriadPro-Regular.otf",
            "Hiragino": "ヒラギノ角ゴシック W3.ttc",
        }

        # Cache of already-registered fonts.
        # key: logical name (e.g. "Futura ND Book")
        # val: internal matplotlib font family name (what rcParams['font.family'] expects)
        self.loaded_fonts = {}

        # The currently applied internal font name (what matplotlib "sees")
        self.current_internal_name = None

    def _resolve_path(self, fontname):
        """
        Resolve a logical font name (e.g. "Futura ND Book") to an actual font file path.

        If `fontname` is not found in the font_map, fall back to `self.default_font`.

        Parameters
        ----------
        fontname : str
            Logical font name.

        Returns
        -------
        str
            Absolute path to the font file.

        Raises
        ------
        FileNotFoundError
            If the resolved font file does not exist.
        """
        fname = self.font_map.get(fontname, self.font_map[self.default_font])
        font_path = os.path.join(self.font_dir, fname) if not os.path.isabs(fname) else fname
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"[PlotFontManager] Font file not found: {font_path}")
        return font_path

    def _register_font(self, font_path):
        """
        Register a font file with matplotlib and return its internal font family name.

        Internally, matplotlib assigns a "family name" string to each font file.
        We grab that name via FontProperties and later feed it into rcParams['font.family'].

        Parameters
        ----------
        font_path : str
            Absolute path to the font file.

        Returns
        -------
        str
            The internal matplotlib font family name associated with this font file.
        """
        # On recent matplotlib, fontManager.addfont() allows dynamic font registration.
        # Calling it more than once for the same path is generally harmless.
        if hasattr(fm.fontManager, "addfont"):
            fm.fontManager.addfont(font_path)

        prop = fm.FontProperties(fname=font_path)
        internal_name = prop.get_name()
        return internal_name

    def set_font(self, fontname):
        """
        High-level API to activate a font globally for matplotlib figures.

        What this does:
        1. Resolve `fontname` -> font path.
        2. Register that font with matplotlib if needed.
        3. Update rcParams['font.family'] so all new plots use that font.
        4. Cache the result so we don't re-register the same file each time.

        Parameters
        ----------
        fontname : str
            Logical font name (must exist in self.font_map, otherwise `default_font` is used).

        Returns
        -------
        str
            The internal matplotlib font family name that was applied.
        """
        font_path = self._resolve_path(fontname)

        # Use cached internal name if already registered.
        if fontname in self.loaded_fonts:
            internal_name = self.loaded_fonts[fontname]
        else:
            internal_name = self._register_font(font_path)
            self.loaded_fonts[fontname] = internal_name

        # Apply to global matplotlib defaults.
        rcParams['font.family'] = internal_name
        rcParams['axes.unicode_minus'] = False  # avoid minus sign issues with some fonts

        # Track state.
        self.current_internal_name = internal_name
        return internal_name

    def get_current_font(self):
        """
        Return the currently active internal font name (what matplotlib is using now).

        Returns
        -------
        str or None
            The internal matplotlib font family name currently stored in rcParams,
            or None if `set_font` has not been called yet.
        """
        return self.current_internal_name

    def list_available(self):
        """
        List all logical font names known to this manager.

        Returns
        -------
        list of str
            Keys of `self.font_map`. This is what you can pass to `set_font()`.
        """
        return list(self.font_map.keys())

    def get_fontprop(self, fontname):
        """
        Get a `matplotlib.font_manager.FontProperties` for a specific font,
        without switching the global rcParams.

        This is useful when you want:
            - One global default font via `set_font("Futura ND Book")`,
            - but override just a single label with a different font.

        Example
        -------
        >>> pfm = PlotFontManager()
        >>> en = pfm.get_fontprop("Futura ND Book")
        >>> jp = pfm.get_fontprop("Hiragino")
        >>> import matplotlib.pyplot as plt
        >>> plt.title("Mixed languages", fontproperties=en)
        >>> plt.ylabel("Sample index", fontproperties=jp)

        Parameters
        ----------
        fontname : str
            Logical font name.

        Returns
        -------
        matplotlib.font_manager.FontProperties
            A FontProperties instance pointing to that font file.
        """
        path = self._resolve_path(fontname)
        return fm.FontProperties(fname=path)

