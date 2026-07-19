#!/usr/bin/env python3
"""
glyph.py.py - a monkeytype-style typing speed test, in your terminal.

Features:
  - Real ghost text: the prompt is always visible (dimmed), and you type
    directly on top of it. Correct chars light up, mistakes turn red.
  - Word-count or time-based tests.
  - Live WPM + accuracy while you type.
  - Multiple color palettes (F2 to cycle).
  - Tab to instantly restart with a fresh prompt and the same settings
    (no re-picking options every run).
  - Backspace to fix mistakes, Ctrl+W / Ctrl+Backspace to delete a whole word.

Usage:
  python3 glyph.py                 # 25 words, classic theme
  python3 glyph.py --words 50
  python3 glyph.py --time 30
  python3 glyph.py --theme dracula
  python3 glyph.py --list-themes

Requires only the Python standard library. On Windows, install the
`windows-curses` package first: pip install windows-curses
"""

import argparse
import curses
import random
import sys
import time

# word bank, you can customize it however your pleasure tells you so wowzers
WORD_LIST = """
the be to of and a in that have i it for not on with he as you do at
but his by from they we say her she or an will my one all would
there their what so up out if about who get which go me when make can
like time no just him know take people into year your good some could
them see other than then now look only come its over think also back
after use two how our work first well way even new want because any
these give day most us is was are been has had were said did having
world life hand part child eye woman man place case week company system
program question government number night point home water room mother
area money story fact month lot right study book eye job word business
issue side kind head house service friend father power hour game line
end member law car city community name president team minute idea body
information back parent face others level office door health person art
war history party result change morning reason research girl guy moment
air teacher force education foot boss box red blue green light dark fast
slow small big tree bird fish cat dog run jump walk talk read write code
build learn play music movie sound light color shape size sky sun moon
star cloud rain snow wind fire earth stone river ocean mountain forest
desert island bridge road street town village country nation planet
space rocket robot machine engine wheel wing feather stone glass metal
wood paper cloth silk cotton wool leather plastic rubber steel gold
silver bronze copper iron coal oil gas power energy light dark shadow
mental decoherence made this wowzers tool 
"""

WORDS = WORD_LIST.split()


THEMES_256 = {
    "classic": {"ghost": 240, "correct": 114, "incorrect": 203, "accent": 81},
    "dracula": {"ghost": 61,  "correct": 84,  "incorrect": 203, "accent": 141},
    "ocean":   {"ghost": 24,  "correct": 50,  "incorrect": 167, "accent": 39},
    "sunset":  {"ghost": 95,  "correct": 216, "incorrect": 196, "accent": 209},
    "mono":    {"ghost": 240, "correct": 255, "incorrect": 250, "accent": 255},
}
THEME_NAMES = list(THEMES_256.keys())

FALLBACK_BASE = {
    "ghost": curses.COLOR_WHITE,
    "correct": curses.COLOR_GREEN,
    "incorrect": curses.COLOR_RED,
    "accent": curses.COLOR_CYAN,
}

WORD_COUNT_OPTIONS = [10, 25, 50, 100]
TIME_OPTIONS = [15, 30, 60, 120]


# text generation hereee
def generate_words(n):
    words = []
    last = None
    for _ in range(n):
        w = random.choice(WORDS)
        while w == last:
            w = random.choice(WORDS)
        words.append(w)
        last = w
    return words


def generate_text(n_words):
    return " ".join(generate_words(n_words))


# layout: map each char index in the target string to a (row, col) so the ghost text wraps cleanly and we can draw directly on top of it (dev was really dumb on that one)
def compute_layout(text, width):
    layout = []
    row = 0
    col = 0
    i = 0
    n = len(text)
    while i < n:
        j = i
        while j < n and text[j] != " ":
            j += 1
        word_len = j - i
        if col + word_len > width and col > 0:
            row += 1
            col = 0
        for k in range(i, j):
            layout.append((row, col))
            col += 1
        if j < n and text[j] == " ":
            layout.append((row, col))
            col += 1
            j += 1
        i = j
    return layout


# color setup
def init_theme(theme_name):
    curses.start_color()
    curses.use_default_colors()
    extended = curses.COLORS >= 256

    spec = THEMES_256[theme_name]

    def pair(idx, role, attr=0):
        if extended:
            curses.init_pair(idx, spec[role], -1)
            curses.init_pair(idx + 10, spec[role], -1)  # unused reserve
        else:
            curses.init_pair(idx, FALLBACK_BASE[role], -1)

    pair(1, "ghost")
    pair(2, "correct")
    pair(3, "incorrect")
    pair(4, "accent")

    ghost_attr = curses.color_pair(1) | curses.A_DIM
    correct_attr = curses.color_pair(2) | curses.A_BOLD
    incorrect_attr = curses.color_pair(3) | curses.A_BOLD | curses.A_UNDERLINE
    accent_attr = curses.color_pair(4) | curses.A_BOLD

    if not extended and theme_name == "mono":
        ghost_attr = curses.A_DIM
        correct_attr = curses.A_BOLD
        incorrect_attr = curses.A_BOLD | curses.A_UNDERLINE
        accent_attr = curses.A_BOLD | curses.A_REVERSE

    return {
        "ghost": ghost_attr,
        "correct": correct_attr,
        "incorrect": incorrect_attr,
        "accent": accent_attr,
    }


# cfg
class Config:
    def __init__(self, mode, value, theme):
        self.mode = mode      
        self.value = value    
        self.theme = theme

    def cycle_mode(self):
        self.mode = "time" if self.mode == "words" else "words"
        self.value = TIME_OPTIONS[0] if self.mode == "time" else WORD_COUNT_OPTIONS[0]

    def cycle_value(self):
        options = TIME_OPTIONS if self.mode == "time" else WORD_COUNT_OPTIONS
        try:
            idx = options.index(self.value)
        except ValueError:
            idx = -1
        self.value = options[(idx + 1) % len(options)]

    def cycle_theme(self):
        idx = THEME_NAMES.index(self.theme)
        self.theme = THEME_NAMES[(idx + 1) % len(THEME_NAMES)]

    def label(self):
        if self.mode == "words":
            return f"{self.value} words"
        return f"{self.value}s"


# the test itself
class TypingTest:
    def __init__(self, stdscr, config):
        self.stdscr = stdscr
        self.config = config
        self.attrs = init_theme(config.theme)
        self.reset()

    def reset(self):
        self.attrs = init_theme(self.config.theme)
        if self.config.mode == "words":
            self.target = generate_text(self.config.value)
        else:
            # very generous buffer
            self.target = generate_text(max(60, self.config.value * 2))
        self.typed_correct = []   
        self.pos = 0
        self.start_time = None
        self.end_time = None
        self.total_keystrokes = 0
        self.mistakes_total = 0
        self.finished = False

    def maybe_extend_text(self):
        if self.config.mode == "time" and len(self.target) - self.pos < 40:
            self.target += " " + generate_text(40)

    def elapsed(self):
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else time.time()
        return max(end - self.start_time, 0.0001)

    def time_remaining(self):
        if self.config.mode != "time":
            return None
        if self.start_time is None:
            return self.config.value
        return max(self.config.value - self.elapsed(), 0)

    def correct_chars(self):
        return sum(1 for c in self.typed_correct if c)

    def incorrect_chars(self):
        return sum(1 for c in self.typed_correct if not c)

    def wpm(self):
        minutes = self.elapsed() / 60
        if minutes <= 0:
            return 0.0
        return (self.correct_chars() / 5) / minutes

    def raw_wpm(self):
        minutes = self.elapsed() / 60
        if minutes <= 0:
            return 0.0
        return (len(self.typed_correct) / 5) / minutes

    def accuracy(self):
        if self.total_keystrokes == 0:
            return 100.0
        good = self.total_keystrokes - self.mistakes_total
        return max(good, 0) / self.total_keystrokes * 100

    def handle_char(self, ch):
        if self.start_time is None:
            self.start_time = time.time()
        if self.pos >= len(self.target):
            return
        expected = self.target[self.pos]
        correct = (ch == expected)
        self.typed_correct.append(correct)
        self.total_keystrokes += 1
        if not correct:
            self.mistakes_total += 1
        self.pos += 1
        self.maybe_extend_text()
        if self.config.mode == "words" and self.pos >= len(self.target):
            self.finish()

    def handle_backspace(self):
        if self.pos > 0 and self.typed_correct:
            self.pos -= 1
            self.typed_correct.pop()

    def handle_delete_word(self): # delete back to the previous word boundary
        while self.pos > 0 and self.target[self.pos - 1] == " ":
            self.pos -= 1
            if self.typed_correct:
                self.typed_correct.pop()
        while self.pos > 0 and self.target[self.pos - 1] != " ":
            self.pos -= 1
            if self.typed_correct:
                self.typed_correct.pop()

    def finish(self):
        if not self.finished:
            self.finished = True
            self.end_time = time.time()

    def tick_time_mode(self):
        if self.config.mode == "time" and self.start_time and not self.finished:
            if self.time_remaining() <= 0:
                self.finish()


# rendering
def draw_header(stdscr, config, attrs, width):
    theme_str = f"theme: {config.theme}"
    mode_str = f"mode: {config.label()}"
    header = f" Glyph   {mode_str}   {theme_str} "
    stdscr.addstr(0, max(0, (width - len(header)) // 2), header, attrs["accent"])


def draw_footer(stdscr, height, width, attrs):
    hints = "ESC quit   TAB restart   F2 theme   F3 mode   F4 length   ^W delete word"
    y = height - 1
    x = max(0, (width - len(hints)) // 2)
    try:
        stdscr.addstr(y, x, hints[: max(width - 1, 0)], curses.A_DIM)
    except curses.error:
        pass


def draw_stats(stdscr, test, y, width, attrs):
    if test.config.mode == "time":
        remaining = test.time_remaining()
        time_str = f"{remaining:5.1f}s left" if remaining is not None else ""
    else:
        time_str = f"{test.elapsed():5.1f}s elapsed"
    stats = f"WPM {test.wpm():5.1f}   acc {test.accuracy():5.1f}%   {time_str}"
    x = max(0, (width - len(stats)) // 2)
    try:
        stdscr.addstr(y, x, stats, attrs["accent"])
    except curses.error:
        pass


def draw_text(stdscr, test, top, left, width, attrs):
    layout = compute_layout(test.target, width)
    cursor_pos = None
    for i, ch in enumerate(test.target):
        if i >= len(layout):
            break
        row, col = layout[i]
        y = top + row
        x = left + col
        if y >= curses.LINES - 3:
            break
        if i < test.pos:
            attr = attrs["correct"] if test.typed_correct[i] else attrs["incorrect"]
        else:
            attr = attrs["ghost"]
        display_ch = ch if ch != " " else " "
        try:
            stdscr.addstr(y, x, display_ch if display_ch != " " else " ", attr)
            if ch == " " and i < test.pos and not test.typed_correct[i]:
                stdscr.addstr(y, x, "_", attrs["incorrect"])
        except curses.error:
            pass
        if i == test.pos:
            cursor_pos = (y, x)
    if cursor_pos is None and len(layout) > 0:
        last_row, last_col = layout[min(test.pos, len(layout) - 1)]
        if test.pos >= len(test.target):
            cursor_pos = (top + last_row, left + last_col + 1)
    return cursor_pos


def draw_results(stdscr, test, width, height, attrs):
    stdscr.erase()
    lines = [
        "Test complete!",
        "",
        f"WPM:        {test.wpm():.1f}",
        f"Raw WPM:    {test.raw_wpm():.1f}",
        f"Accuracy:   {test.accuracy():.1f}%",
        f"Time:       {test.elapsed():.1f}s",
        f"Correct:    {test.correct_chars()} chars",
        f"Mistakes:   {test.incorrect_chars()} chars",
        "",
        "TAB - new test        ESC - quit",
    ]
    top = max(0, height // 2 - len(lines) // 2)
    for idx, line in enumerate(lines):
        x = max(0, (width - len(line)) // 2)
        attr = attrs["accent"] if idx == 0 else curses.A_NORMAL
        try:
            stdscr.addstr(top + idx, x, line, attr)
        except curses.error:
            pass
    stdscr.refresh()


# main loop
def run(stdscr, config):
    curses.curs_set(1)
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.timeout(100)

    test = TypingTest(stdscr, config)

    while True:
        height, width = stdscr.getmaxyx()
        if height < 8 or width < 40:
            stdscr.erase()
            try:
                stdscr.addstr(0, 0, "Terminal too small - resize and try again.")
            except curses.error:
                pass
            stdscr.refresh()
            ch = stdscr.getch()
            if ch == 27:
                return
            continue

        test.tick_time_mode()

        if test.finished:
            draw_results(stdscr, test, width, height, test.attrs)
            ch = stdscr.getch()
            if ch == 27:
                return
            if ch == 9:  # TAB
                test.reset()
            continue

        stdscr.erase()
        draw_header(stdscr, config, test.attrs, width)
        text_top = 2
        text_left = max(2, (width - min(width - 4, 80)) // 2)
        text_width = min(width - text_left - 2, 80)
        cursor_pos = draw_text(stdscr, test, text_top, text_left, text_width, test.attrs)
        stats_y = min(height - 3, text_top + 6)
        draw_stats(stdscr, test, stats_y, width, test.attrs)
        draw_footer(stdscr, height, width, test.attrs)

        if cursor_pos:
            y, x = cursor_pos
            y = min(y, height - 1)
            x = min(x, width - 1)
            try:
                stdscr.move(y, x)
            except curses.error:
                pass

        stdscr.refresh()

        ch = stdscr.getch()
        if ch == -1:
            continue
        elif ch == 27:  # ESC
            return
        elif ch == 9:  # TAB
            test.reset()
        elif ch == curses.KEY_F2:
            config.cycle_theme()
            test.reset()
        elif ch == curses.KEY_F3:
            config.cycle_mode()
            test.reset()
        elif ch == curses.KEY_F4:
            config.cycle_value()
            test.reset()
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            test.handle_backspace()
        elif ch == 23:  # Ctrl+W
            test.handle_delete_word()
        elif ch == curses.KEY_RESIZE:
            continue
        elif 32 <= ch <= 126:
            test.handle_char(chr(ch))


def main():
    parser = argparse.ArgumentParser(description="A monkeytype-style typing test for your terminal.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--words", type=int, help="number of words per test (e.g. 25)")
    group.add_argument("--time", type=int, help="seconds per test (e.g. 30)")
    parser.add_argument("--theme", choices=THEME_NAMES, default="classic", help="color theme")
    parser.add_argument("--list-themes", action="store_true", help="list available themes and exit")
    args = parser.parse_args()

    if args.list_themes:
        print("Available themes:", ", ".join(THEME_NAMES))
        sys.exit(0)

    if args.time is not None:
        config = Config("time", args.time, args.theme)
    elif args.words is not None:
        config = Config("words", args.words, args.theme)
    else:
        config = Config("words", 25, args.theme)

    try:
        curses.wrapper(run, config)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()