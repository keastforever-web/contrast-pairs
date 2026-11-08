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
                ({'name': None, 'foreground': '#000', 'background': '#fff'},
                 'pair[1].name: expected a nonempty string'),
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

    def test_cli_preserves_pair_names_for_failed_token_reports(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / 'named pairs.json'
            pairs = [
                {'name': 'button.primary', 'foreground': '#fff', 'background': '#fff'},
                {'name': 'button.primary', 'foreground': '#000', 'background': '#fff'},
                {'foreground': '#000', 'background': '#fff'},
            ]
            path.write_text(json.dumps(pairs), encoding='utf-8')
            process = subprocess.run([sys.executable, str(Path(__file__).with_name('contrast_pairs.py')), str(path)], capture_output=True, text=True)
            self.assertEqual(process.returncode, 1)
            report = json.loads(process.stdout)
            self.assertEqual([p.get('name') for p in report['pairs']], ['button.primary', 'button.primary', None])
            self.assertEqual([p['index'] for p in report['pairs']], [0, 1, 2])
            self.assertEqual([p['passes'] for p in report['pairs']], [False, True, True])
            self.assertEqual(set(report['pairs'][2]), {'index', 'ratio', 'passes'})

    def test_pair_names_round_trip_and_validate(self):
        label = '  primary \u6587\u672c \"quoted\"  '
        self.assertEqual(audit([{'name': label, 'foreground': '#000', 'background': '#fff'}])['pairs'][0]['name'], label)
        for invalid in [None, 42, True, [], {}, '', '   ', '\t\n']:
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, r'pair\[0\].name: expected a nonempty string'):
                audit([{'name': invalid, 'foreground': '#000', 'background': '#fff'}])

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
