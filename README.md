# PlotFontManager

A tiny helper to consistently apply custom / local fonts in matplotlib.

Researchers, designers, and labs often want figures to match their visual identity
(Helvetica Neue, Futura, Hiragino, etc.), but matplotlib keeps falling back to DejaVu.
`PlotFontManager` solves that by:

- Mapping human-readable font names to actual font files on your system
- Registering those fonts with matplotlib at runtime
- Forcing `rcParams['font.family']` so plots render in the intended font
- Letting you grab a `FontProperties` object for per-label overrides (e.g. Japanese axis labels)

MIT licensed.


## Why?

- You want presentation / paper / slide plots to use the same typography as the rest of your lab or org.
- You don't want to fight `matplotlibrc` or the global font cache every time.
- You have commercial fonts installed locally (Helvetica, Optima, etc.) that you legally can't bundle in a public repo, but still want an easy way for teammates to point to them.

This module gives you a small, explicit API instead of “try a dozen rcParams tweaks and hope it sticks.”


## Installation

For now, just drop `PlotFontManager.py` into your project and import it:

```
from PlotFontManager import PlotFontManager
````

(You can also vendor it as a tiny internal utility package.)

## Quick Start

```python
import matplotlib.pyplot as plt
from PlotFontManager import PlotFontManager

pfm = PlotFontManager()
```

## Set global matplotlib font to "Futura ND Book"

```python
pfm.set_font("Futura ND Book")

plt.plot([0, 1, 2], [0, 1, 4])
plt.title("Sample figure")
plt.xlabel("Time (s)")
plt.ylabel("Amplitude")
plt.show()
```

After calling `set_font()`, all subsequent plots in that session will use that font (unless overridden).

## Per-label override (e.g. multilingual axes)

Sometimes you want a different font for a specific label (like Japanese text on the y-axis).
Use `get_fontprop()`:

```python
import matplotlib.pyplot as plt
from PlotFontManager import PlotFontManager

pfm = PlotFontManager()

jp_prop = pfm.get_fontprop("Hiragino")

plt.plot([1, 2, 3], [10, 20, 15])
plt.ylabel("サンプル番号", fontproperties=jp_prop)
plt.title("Measurement Result")
plt.show()
```

## Listing available logical names

```python
pfm = PlotFontManager()
print(pfm.list_available())
# -> ["Helvetica Neue", "Helvetica", "Futura", "Futura ND Book", ...]
```

## How it works under the hood

* The class keeps an internal `font_map` dictionary:

  ```python
  {
      "Helvetica Neue": "HelveticaNeue.ttc",
      "Helvetica": "Helvetica.ttc",
      "Futura": "Futura.ttc",
      "Futura ND Book": "Neufville Digital - Futura ND Book.ttf",
      "Futura ND Bold": "Neufville Digital - Futura ND Bold.ttf",
      "Optima": "Optima.ttc",
      "Baskerville": "Baskerville.ttc",
      "Myriad": "MyriadPro-Regular.otf",
      "Hiragino": "ヒラギノ角ゴシック W3.ttc"
  }
  ```

* Each key (logical name) maps to either:

  * a filename under `font_dir` (default: `/usr/local/share/fonts`), or
  * an absolute path to the font file.

* When you call `set_font("Futura ND Book")`:

  1. We resolve the file path.
  2. We `addfont()` it to matplotlib (so matplotlib knows it exists).
  3. We ask matplotlib what the internal family name is.
  4. We set `rcParams['font.family'] = <that internal name>`.

* The resolved “internal name” is what matplotlib will actually use.
  You can check it via:

  ```python
  pfm.get_current_font()
  ```

## Customizing with `pfm.json` (lab / team overrides)

You can override or extend the built-in `font_map` without editing the Python code.

If a file named `pfm.json` exists **in the same directory as `your_script_file`**, it will be loaded at initialization and merged into the font map.

Example `pfm.json`:

```json
{
  "Lab Sans": "/lab/fonts/BrandSans-Regular.otf",
  "Paper Serif": "/lab/fonts/JournalSerif-Italic.ttf",
  "Futura ND Book": "/custom/fonts/FuturaNDBook.ttf"
}
```

Notes:

* Keys are the logical names you will use in code:

  ```python
  pfm.set_font("Lab Sans")
  ```

* Values can be either:

  * absolute paths (`"/lab/fonts/BrandSans-Regular.otf"`)
  * or filenames that live under `font_dir` (e.g. `"BrandSans-Regular.otf"`)

* If `pfm.json` redefines an existing key (e.g. `"Futura ND Book"`), that new path wins.

* If `pfm.json` is malformed JSON or not a dict, initialization will still continue, and you'll just get a warning printed to stdout.
  In other words, a bad `pfm.json` should not break your plotting pipeline.

This design lets you:

* Ship this repo publicly (MIT) **without** bundling any commercial fonts.
* Internally distribute only a small `pfm.json` that maps your lab/brand fonts to their actual locations.
* Keep everyone consistent: “Use `Lab Sans` for slides” becomes a one-liner instead of a Slack thread.

## API reference

#### `PlotFontManager(font_dir="/usr/local/share/fonts", default_font="Helvetica Neue", extra_map=None)`

* `font_dir`
  Default directory used when a mapped filename is relative, not absolute.

* `default_font`
  Logical fallback font name if the specified name isn't found.

* `extra_map` (dict or None)
  Optional mapping passed directly in code. This is merged first.
  After that, if `pfm.json` exists, its mapping is merged on top (so `pfm.json` wins).

---

#### `.set_font(fontname) -> str`

Resolve `fontname`, register that font with matplotlib (if needed), and update
`matplotlib.rcParams` globally.

Returns the internal family name that matplotlib is now using.

---

#### `.get_current_font() -> Optional[str]`

Return the internal family name currently active in `rcParams['font.family']`.

---

#### `.list_available() -> list[str]`

Return a list of logical names currently known (after applying any overrides from `extra_map` and/or `pfm.json`).

---

#### `.get_fontprop(fontname) -> matplotlib.font_manager.FontProperties`

Return a `FontProperties` for that font file, without touching global `rcParams`.

Useful for local overrides on specific labels or text elements.

## Typical workflow in a lab

1. Sysadmin / PI / “font police” prepares:

   * `pfm.json` with canonical font names and paths
   * maybe a short style guide (“Use `Lab Sans` for titles, `Paper Serif` for figure captions”)

2. Everyone else just does:

   ```python
   from PlotFontManager import PlotFontManager
   pfm = PlotFontManager()
   pfm.set_font("Lab Sans")
   ```

3. Every plot in the paper / slide deck / poster matches the lab branding automatically.



## Bootstrapping `pfm.json` automatically

We ship a small helper script `pfm_build_map.py`.
It calls `fc-list`, extracts available font families and their file paths,
and prints a ready-to-edit `pfm.json` mapping.

```bash
python pfm_build_map.py --filter "Futura|Helvetica|Hiragino" > pfm.json
```

Then you can load `PlotFontManager()` and it will automatically merge that `pfm.json` into its internal map at import time, so you can immediately do:

```python
pfm.set_font("Hiragino")
```

Clean up the generated file before committing (you usually don't want to expose your entire system font list).

## License

MIT License

Copyright (c) 2025 Hiroki Funashima

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

