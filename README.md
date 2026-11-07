# contrast-pairs

A small local CI check for text/background color pairs in design tokens. Python 3.10+, standard library only. Produces JSON with exact contrast ratios and per-pair pass/fail results; no uploads or browser required.

Create `pairs.json`:

```json
[{"foreground":"#222222","background":"#ffffff"}]
```

```sh
python contrast_pairs.py pairs.json
python contrast_pairs.py pairs.json --level large
python -m unittest -v
```

Exit 0: all pairs pass; 1: one or more pairs fail; 2: invalid/unreadable input. `normal` uses 4.5:1, `large` 3:1, and `enhanced` 7:1. Ratios are compared before rounding. Use `large` only when your text actually meets the large-text definition; the tool does not inspect typography.

Supports opaque sRGB `#RGB` and `#RRGGBB` colors only. Alpha, gradients, images, CSS variables, rendered-page sampling and complete accessibility compliance are outside scope. This checks supplied pairs, so include all actual foreground/background combinations yourself. Output indexes correspond to zero-based input array positions.

Formula and thresholds follow [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html). Inspired by design tooling on [GitHub Trending](https://github.com/trending); independently implemented, no upstream code copied. MIT license.

Python callers can use `audit(pairs, threshold=4.5)`. The threshold must be a finite number from 1 to 21; invalid values raise `ValueError` rather than producing misleading results or nonstandard JSON.

Roadmap: named pairs and optional design-token import. CLI integration and invalid-threshold regression tests are included.

Invalid pair diagnostics identify the zero-based input position and field, for example
`contrast-pairs: pair[1].background: expected #RGB or #RRGGBB` means the second
pair has an invalid background. Missing fields and non-object entries are also
located. Errors go to stderr with exit 2 and no partial JSON on stdout; invalid
values and file paths are not echoed. Unreadable files and malformed JSON retain
a generic input error.
