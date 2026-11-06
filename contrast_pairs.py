"""Check opaque sRGB color pairs from a JSON file. Python 3.10+."""
import argparse
import json
import math
import re
from pathlib import Path


def luminance(color):
    if not isinstance(color, str) or not re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?', color):
        raise ValueError('colors must use #RGB or #RRGGBB')
    value = color[1:]
    if len(value) == 3:
        value = ''.join(c * 2 for c in value)
    channels = [int(value[i:i+2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def audit(pairs, threshold=4.5):
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not 1 <= threshold <= 21:
        raise ValueError('threshold must be a finite number from 1 to 21')
    if not isinstance(pairs, list) or not pairs:
        raise ValueError('input must be a nonempty array of color pairs')
    results = []
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or 'foreground' not in pair or 'background' not in pair:
            raise ValueError('each pair needs foreground and background')
        a, b = sorted([luminance(pair['foreground']), luminance(pair['background'])])
        ratio = (b + 0.05) / (a + 0.05)
        results.append({'index': index, 'ratio': ratio, 'passes': ratio >= threshold})
    return {'ok': all(item['passes'] for item in results), 'threshold': threshold, 'pairs': results}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', help='JSON array of foreground/background objects')
    parser.add_argument('--level', choices=['normal', 'large', 'enhanced'], default='normal')
    args = parser.parse_args(argv)
    try:
        data = json.loads(Path(args.file).read_text(encoding='utf-8-sig'))
        report = audit(data, {'normal': 4.5, 'large': 3.0, 'enhanced': 7.0}[args.level])
    except (OSError, ValueError, TypeError):
        parser.exit(2, 'contrast-pairs: invalid input; expected a readable JSON array with opaque hex colors\n')
    print(json.dumps(report))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
