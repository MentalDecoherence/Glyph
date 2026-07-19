# Glyph
**A typing test that never left the terminal.**

### What is this
Every typing test lives in a browser tab nowadays. Glyph doesn’t.
It’s a fully functional typing test that runs entirely in your terminal - same ghost text you type over, same live stats - minus the tab, the ads, and the internet connection. Open a terminal, run one command, start typing.
No account. No telemetry. No JS. No TS. No BS. Just `curses` and a word list.

### Why it feels right
Most terminal typing tests either regenerate a whole new screen per test which is annoying, don’t show you a real prompt to type against which feels like a guessing game, or make you dig through a settings meny every single run (annoying again.) Glyph fixes all three.

### Features
<table>
<colgroup>
<col width="170.65625">
<col width="487.65625">
</colgroup>
<tr>
<td>True overlay text</td>
<td>Type directly on the prompt  - correct chars turn theme-green, mistakes turn red and underline, missed spaces show as _</td>
</tr>
<tr>
<td>Words or time</td>
<td>--words 50 or --time 30, switch live with F3</td>
</tr>
<tr>
<td>Live stats</td>
<td>WPM, raw WPM, accuracy, and elapsed/remaining time update as you type</td>
</tr>
<tr>
<td>Color palettes</td>
<td>Cycle color themes with F2, no restart needed</td>
</tr>
<tr>
<td>Instant restart</td>
<td>Tab generates a fresh passage with your current settings, no menus</td>
</tr>
<tr>
<td>Real editing</td>
<td>Backspace fixes a char, Ctrl+W deletes a whole word</td>
</tr>
<tr>
<td>Zero dependencies</td>
<td>Pure Python standard library (`curses`). If you’re on Windows, download the package using pip install windows-curses</td>
</tr>
</table>

### Install & Run
Glyph is a single file. No virtualenv required.

    git clone https://github.com/mentaldecoherence/glyph.git
    cd glyph
    python3 glyph.py

That’s it. python3 glyph.py and you’re typing.

<callout icon="i">
	**Windows users note**: curses isn’t included in the standard Windows Python install.
	**One-time setup**

	    pip install windows-curses

	Then run Glyph normally (same commands as above).
</callout>

### Usage

    python3 glyph.py                  # 25 words, classic theme
    python3 glyph.py --words 50       # 50 word test
    python3 glyph.py --time 30        # 30-second sprint
    python3 glyph.py --theme dracula  # pick a palette from the start
    python3 glyph.py --list-themes    # see all available palettes

#### Controls
<table>
<colgroup>
<col width="141.65625">
<col width="209.65625">
</colgroup>
<tr>
<td>*any character*</td>
<td>type it</td>
</tr>
<tr>
<td>Backspace</td>
<td>delete last character</td>
</tr>
<tr>
<td>Ctrl + W</td>
<td>delete last word</td>
</tr>
<tr>
<td>Tab</td>
<td>new test, same settings</td>
</tr>
<tr>
<td>F2</td>
<td>cycle color theme</td>
</tr>
<tr>
<td>F3</td>
<td>switch words ↔ time mode</td>
</tr>
<tr>
<td>F4</td>
<td>cycle length</td>
</tr>
<tr>
<td>Esc</td>
<td>quit</td>
</tr>
</table>

### How it’s built
Glyph is one dependency-free Python file built on `curses` . A few things worth knowing if you’re reading the source:
- Layout engine - a small word-wrap pass maps every character index in the target passage to a (row, col) on screen before rendering, so the ghost text, the typed overlay, and the real cursor position always agree with each other, even after a terminal resize.
- Time mode auto-extends - if you’re typing fast enough to reach the end of the buffered passage before your timer runs out, Glyph silently generates more text behind the scenes. You’ll never hit a wall mid-sprint.
- WPM math - standard `(correct characters ÷ 5) ÷ minutes elapsed`, plus a separate raw WPM that includes mistakes, so you can see both your real throughput and your typing accuracy trade-off.

### Contributing
Issues and PRs welcome - especially new themes and word lists. Keep it dependency-free, that’s the whole point.

### License
MIT. Do whatever you want with it. Seriously.
