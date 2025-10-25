#!/usr/bin/env python3
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
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import json
import matplotlib.font_manager as fm
from matplotlib import rcParams


class PlotFontManager:
    """
    PlotFontManager
    ----------------
    A tiny helper to consistently apply custom / local fonts in matplotlib.

    Features:
    - Map human-friendly logical names
       (e.g. "Futura ND Book") to actual font files.
    - Dynamically register those fonts with matplotlib at runtime.
    - Update rcParams to use that font globally.
    - Provide FontProperties objects for per-label
      overrides in multilingual plots.

    Optional extension:
    If a file named `pfm.json` exists in the same directory as this module
    (plot_font_manager.py), its contents will be merged into/override the
    built-in font_map. This allows teams/labs to customize font mappings
    without editing the Python source.

    Author: Hiroki Funashima (2025)
    """

    def __init__(
        self,
        font_dir="/usr/local/share/fonts",
        default_font="Helvetica Neue",
        extra_map=None,
    ):
        """
        Parameters
        ----------
        font_dir : str
            Default directory where font files live. Relative filenames in
            font_map will be joined with this dir. Absolute paths are respected
            as-is.
        default_font : str
            Logical font name to fall back to if a given name isn't found.
        extra_map : dict or None
            Optional dict to extend/override `self.font_map` at init time.
            This has lower priority than pfm.json (pfm.json wins last).
        """
        self.font_dir = font_dir
        self.default_font = default_font

        # Built-in baseline mapping.
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

        # 1) merge user-provided mapping (if any)
        if extra_map and isinstance(extra_map, dict):
            self.font_map.update(extra_map)

        # 2) try to load pfm.json sitting next to this module
        #    (this is the "lab override" mechanism)
        self._load_local_json_override()

        # State tracking
        self.loaded_fonts = {}          # {logical_name: internal_name}
        self.current_internal_name = None

    def _load_local_json_override(self):
        """
        Look for pfm.json in the same directory as this module.
        If found and valid, merge its mapping into self.font_map.

        Expected format in pfm.json:
        {
            "Logical Font Name": "filename-or-absolute-path.ttf",
            "My Lab Sans": "/abs/path/to/CustomSans-Regular.otf"
        }

        Values can be relative filenames (joined with self.font_dir)
        or absolute paths.
        """
        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(module_dir, "pfm.json")
            if not os.path.exists(json_path):
                return

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                self.font_map.update(data)
            else:
                print(
                    "[PlotFontManager] Warning:\
                    pfm.json exists but is not a dict; "
                    "ignoring."
                )

        except Exception as e:
            # Soft failure: never kill init because of a bad override file
            print(f"[PlotFontManager] Warning: failed to load pfm.json: {e}")

    def _resolve_path(self, fontname):
        """
        Map a logical font name (e.g. 'Futura ND Book')
        to a real font file path.

        If the mapped value is an absolute path, return it as-is.
        Otherwise, treat it as a filename under self.font_dir.

        Raises
        ------
        FileNotFoundError
            If the resolved path does not exist.
        """
        # get filename (or absolute path) from font_map.
        fname = self.font_map.get(fontname, self.font_map[self.default_font])

        # If fname is absolute (starts with / or drive letter), just trust it.
        font_path = (
            fname if os.path.isabs(fname)
            else os.path.join(self.font_dir, fname)
        )

        if not os.path.exists(font_path):
            raise FileNotFoundError(
                f"[PlotFontManager] Font file not found: {font_path}"
            )
        return font_path

    def _register_font(self, font_path):
        """
        Register the given font file with matplotlib (if supported by this
        matplotlib version) and return the internal family name that matplotlib
        will use for rcParams['font.family'].

        Notes
        -----
        - Calling `addfont()` multiple times on the same file is usually safe.
        - We then create a FontProperties from this file and ask it for
          the "internal" family name, which is what matplotlib expects in
          rcParams['font.family'].
        """
        if hasattr(fm.fontManager, "addfont"):
            fm.fontManager.addfont(font_path)

        prop = fm.FontProperties(fname=font_path)
        internal_name = prop.get_name()
        return internal_name

    def set_font(self, fontname):
        """
        High-level API:
        - Resolve the physical font file path for `fontname`.
        - Register it with matplotlib if needed.
        - Update matplotlib.rcParams to use it globally.
        - Cache the internal name for inspection.

        Returns
        -------
        internal_name : str
            The name matplotlib will recognize as the active font family.
        """
        font_path = self._resolve_path(fontname)

        if fontname in self.loaded_fonts:
            internal_name = self.loaded_fonts[fontname]
        else:
            internal_name = self._register_font(font_path)
            self.loaded_fonts[fontname] = internal_name

        rcParams["font.family"] = internal_name
        rcParams["axes.unicode_minus"] = False
        self.current_internal_name = internal_name
        return internal_name

    def get_current_font(self):
        """
        Return the internal family name currently set
        in rcParams['font.family'].

        Returns
        -------
        str or None
            Internal name if `set_font()` has been called, else None.
        """
        return self.current_internal_name

    def list_available(self):
        """
        Return a list of logical font names known to this manager.

        Use this for UI / dropdowns / debugging.
        """
        return list(self.font_map.keys())

    def get_fontprop(self, fontname):
        """
        Return a matplotlib.font_manager.FontProperties
        object for the given font.

        This does NOT modify global rcParams.
        It's meant for per-label overrides,
        e.g.:

            pfm = PlotFontManager()
            jp = pfm.get_fontprop("Hiragino")
            plt.ylabel("サンプル番号", fontproperties=jp)

        Returns
        -------
        matplotlib.font_manager.FontProperties
        """
        path = self._resolve_path(fontname)
        return fm.FontProperties(fname=path)
