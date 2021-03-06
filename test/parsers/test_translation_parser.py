import unittest

from translate import translate, translation_parser


class TranslateParserTest(unittest.TestCase):
    def setUp(self):
        self.parser = translation_parser()

    def test_valid_path(self):
        self.assertIs(self.parser.parse_args(["--path", "results"]).path, "results")

    def test_file(self):
        self.assertIs(self.parser.parse_args(["--file", "translation.txt"]).file_dir, "translation.txt")

    def empty_path(self):
        self.assertFalse(translate(""))