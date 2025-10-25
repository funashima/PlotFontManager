# PlotFontManager

`PlotFontManager` is a tiny utility class to make matplotlib use *your* fonts
(Helvetica, Futura, Hiragino, etc.) instead of the default DejaVu stack.

It is designed for:
- researchers who care about typography in figures,
- teams that want consistent visual identity in slides/papers,
- people who are tired of matplotlib silently falling back to random fonts.

This tool lets you:
1. Map human-friendly font names (e.g. `"Futura ND Book"`) to actual font files on disk.
2. Dynamically register those fonts in matplotlib at runtime.
3. Apply them globally via `rcParams`.
4. Optionally get `FontProperties` handles for per-label overrides (e.g. English title in Futura, axis label in Hiragino).

---

## Features

- No system install / `matplotlibrc` editing required.
- Works in notebooks, scripts, and slide-generation code.
- Lets you standardize typography across a whole lab/company.
- Helps you keep Japanese and Latin text readable in the same plot.

---

## Quick Start

### 1. Install / include

Right now this is just a single Python file. You can:
- copy `plot_font_manager.py` into your project, **or**
- install it as an internal utility module in your lab tooling repo.

```python
from plot_font_manager import PlotFontManager
import matplotlib.pyplot as plt

# Create a manager. You can customize font_dir (default: /usr/local/share/fonts)
pfm = PlotFontManager()

# Apply a global font for all future plots
pfm.set_font("Futura ND Book")

# Create a test figure
plt.plot([0, 1, 2], [2, 1, 3])
plt.title("Demo figure using Futura ND Book")
plt.xlabel("time [s]")
plt.ylabel("response")
plt.show()
````

If everything works, the plot text should render in your chosen font (not DejaVu).

---

## How it works

### 1. Logical names → actual files

Inside the class there is a dictionary like:

```python
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
```

You can (and should) edit this mapping for your environment:

* keys are what you pass to `set_font("...")`
* values are filenames or absolute paths

By default we assume these font files live in `/usr/local/share/fonts`.
If your fonts live somewhere else, pass `font_dir=...` when you construct the object.

```python
pfm = PlotFontManager(font_dir="/Users/alice/Library/Fonts")
```

---

### 2. Registration

When you call `pfm.set_font("Futura ND Book")`:

1. The class figures out the font file path.
2. It calls `matplotlib.font_manager.addfont(...)` (if available in your matplotlib).
3. It builds a `FontProperties` from that file and extracts the internal family name that matplotlib assigns.
4. It sets:

   ```python
   rcParams['font.family'] = that_internal_name
   rcParams['axes.unicode_minus'] = False
   ```

After that, any new matplotlib figure will use that font automatically.

---

## Mixed-language usage (per-label override)

Sometimes you want:

* English titles in Futura (geometric sans),
* Axis labels in Hiragino (CJK-safe).

Global font alone can't do that; you need explicit font properties for some labels.

Use `get_fontprop()`:

```python
import matplotlib.pyplot as plt
pfm = PlotFontManager()

title_font = pfm.get_fontprop("Futura ND Book")
axis_font  = pfm.get_fontprop("Hiragino")

plt.plot([0, 1, 2], [3, 2, 4])

plt.title("Signal overview", fontproperties=title_font)
plt.xlabel("Sample index", fontproperties=axis_font)
plt.ylabel("Output level", fontproperties=axis_font)

plt.show()
```

This does **not** change `rcParams`.
It only affects the labels where you explicitly pass `fontproperties=...`.

---

## API Reference

### `class PlotFontManager(font_dir="/usr/local/share/fonts", default_font="Helvetica Neue")`

Creates a font manager bound to a directory containing your fonts.

* `font_dir`
  Base directory where the font files live.
  If you put absolute paths in `font_map`, they will be used as-is.

* `default_font`
  Logical font name to fall back to when you request something unknown.

---

### `set_font(fontname) -> str`

High-level "make this the default for all plots".

* Resolves `fontname` → font file path.
* Registers with matplotlib.
* Sets `matplotlib.rcParams['font.family']`.
* Stores the internal family name in `self.current_internal_name`.
* Returns that internal family name.

```python
pfm.set_font("Baskerville")
```

---

### `get_current_font() -> str | None`

Returns the internal family name currently applied to `rcParams['font.family']`,
or `None` if you haven't called `set_font()` yet.

---

### `list_available() -> list[str]`

Returns all logical font names known to this manager.

```python
pfm.list_available()
# -> ["Helvetica Neue", "Helvetica", "Futura", "Futura ND Book", ...]
```

You can expose this in a UI (dropdown, etc.) so collaborators can pick a house style.

---

### `get_fontprop(fontname) -> matplotlib.font_manager.FontProperties`

Returns a `FontProperties` object tied to a given font file, without touching global rcParams.

Useful for mixing languages or styles inside one figure.

```python
jp_label = pfm.get_fontprop("Hiragino")
plt.ylabel("Sample index", fontproperties=jp_label)
```

---

## Why not just set `rcParams['font.family'] = "Some Font"`?

Matplotlib can *only* use font families it already knows about.
Custom / commercial / CJK fonts aren't always auto-detected.

`PlotFontManager` solves that by:

1. Calling `addfont()` to explicitly register a font file.
2. Asking matplotlib what internal family name it assigned.
3. Feeding that name back into rcParams in a reliable way.

This avoids:

* mysterious fallback to DejaVu Sans,
* missing glyph boxes for Japanese,
* inconsistent output between machines.

---

## Troubleshooting

### 1. "Font file not found"

You might see:

```text
FileNotFoundError: [PlotFontManager] Font file not found: /usr/local/share/fonts/Futura.ttc
```

Fix:

* Check that the file really exists at that path.
* Update `font_dir` in the constructor.
* Or update the `self.font_map` entry with the correct filename.

---

### 2. "It still looks like DejaVu Sans"

Possible causes:

* Notebook already rendered the figure before you called `set_font()`.
  → Call `set_font(...)` *before* creating figures / calling `plt.subplots()` etc.
* Glyph fallback: your chosen font doesn’t have the characters you’re drawing, so matplotlib is substituting.
  → For multilingual plots, try per-label `get_fontprop(...)` to force a font that actually supports those glyphs.

---

### 3. Unicode minus (−) shows up weird

`set_font()` sets:

```python
rcParams['axes.unicode_minus'] = False
```

This forces matplotlib to use a plain ASCII hyphen-minus `-` instead of the Unicode minus symbol `−`.
Some fonts don’t have a proper Unicode minus glyph, which otherwise gives you empty squares.

If you *want* the Unicode minus, you can set it back:

```python
from matplotlib import rcParams
rcParams['axes.unicode_minus'] = True
```

---

## Best practices in a team / lab

* Put this file (and maybe a custom `font_map`) in a shared repo, e.g. `labviz/plot_font_manager.py`.
* Add a tiny helper like `pfm.set_font("Futura ND Book")` at the top of every figure script / notebook.
* Decide on:

  * 1 default sans font (slides / posters),
  * 1 default serif font (papers),
  * 1 CJK-capable font for axis labels, if you publish in Japanese/Chinese/Korean.

Now everyone’s plots match, which helps with:

* conference posters,
* paper figures,
* internal review slides,
* public talks / branding.

---

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

---

## Author / Contact

Hiroki Funashima, 2025

Contributions / PRs welcome. Please add OS/font/env details in issues so we can reproduce.
