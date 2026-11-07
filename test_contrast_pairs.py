import unittest
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from contrast_pairs import audit, luminance


class ContrastTests(unittest.TestCase):
    def test_cli_locates_invalid_pair_without_echoing_input(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / 'private-file-name.json'
            command = [sys.executable, str(Path(__file__).with_name('contrast_pairs.py')), str(path)]
            valid = {'foreground': '#000', 'background': '#fff'}
            cases = [
                ({'foreground': '#000', 'background': 'PRIVATE_VALUE'},
                 'pair[1].background: expected #RGB or #RRGGBB'),
                ({'foreground': 'PRIVATE_VALUE', 'background': '#fff'},
                 'pair[1].foreground: expected #RGB or #RRGGBB'),
                ({'background': '#fff'}, 'pair[1].foreground: required field missing'),
                ({'foreground': '#000'}, 'pair[1].background: required field missing'),
                ('PRIVATE_VALUE', 'pair[1]: expected an object'),
            ]
            for invalid, diagnostic in cases:
                with self.subTest(diagnostic=diagnostic):
                    path.write_text(json.dumps([valid, invalid]), encoding='utf-8')
                    process = subprocess.run(command, capture_output=True, text=True)
                    self.assertEqual(process.returncode, 2)
                    self.assertEqual(process.stdout, '')
                    self.assertIn(diagnostic, process.stderr)
                    self.assertNotIn('PRIVATE_VALUE', process.stderr)
                    self.assertNotIn(path.name, process.stderr)
                    self.assertNotIn('Traceback', process.stderr)

    def test_invalid_thresholds_rejected(self):
        for threshold in [float('nan'), float('inf'), 0, 22, True, '4.5', None]:
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                audit([{'foreground': '#000', 'background': '#fff'}], threshold)

    def test_cli_exit_codes_and_json(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / 'color pairs.json'
            command = [sys.executable, str(Path(__file__).with_name('contrast_pairs.py')), str(path)]
            for foreground, expected in [('#000', 0), ('#fff', 1)]:
                path.write_text(json.dumps([{'foreground': foreground, 'background': '#fff'}]), encoding='utf-8')
                process = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(process.returncode, expected)
                self.assertEqual(json.loads(process.stdout)['ok'], expected == 0)
            path.write_text('{invalid', encoding='utf-8')
            process = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(process.returncode, 2)
            self.assertEqual(process.stdout, '')

    def test_black_white(self):
        self.assertEqual(audit([{'foreground':'#000','background':'#fff'}])['pairs'][0]['ratio'], 21)

    def test_same_color_fails(self):
        self.assertFalse(audit([{'foreground':'#abc','background':'#abc'}])['ok'])

    def test_shorthand(self):
        self.assertEqual(luminance('#abc'), luminance('#aabbcc'))

    def test_threshold_not_rounded(self):
        pair = [{'foreground':'#777','background':'#fff'}]
        self.assertFalse(audit(pair, 4.5)['ok'])
        self.assertTrue(audit(pair, 3)['ok'])

    def test_invalid(self):
        for value in [[], {}, [{'foreground':'red','background':'#fff'}], [{}], [{'foreground':123,'background':'#fff'}]]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                audit(value)


if __name__ == '__main__':
    unittest.main()
