import unittest

from main import parse_html, parse_and_write_to_file


class TestStringMethods(unittest.TestCase):

    def test_upper(self):
        with open("test/table.html", "r") as f:
            a = parse_html(''.join(f.readlines()))
            self.assertEqual('04.05.2020', a[0][0])
            self.assertEqual('10.05.2020', a[0][1])
            self.assertEqual('28518', a[0][2])

    # def test_write_to_file(self):
    #     with open("table.html", "r") as f:
    #         parse_and_write_to_file('тестовый запрос', ''.join(f.readlines()))


if __name__ == '__main__':
    unittest.main()
