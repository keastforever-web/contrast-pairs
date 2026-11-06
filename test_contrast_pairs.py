import unittest
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from contrast_pairs import audit, luminance


class ContrastTests(unittest.TestCase):
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
