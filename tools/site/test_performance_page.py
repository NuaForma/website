"""Keep published trial arithmetic and limitations distinct from capacity promises."""
import pathlib
import unittest
from html.parser import HTMLParser

SITE = pathlib.Path(__file__).resolve().parents[2] / 'site'


class TrialTables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.rows = []
        self.cells = []
        self.cell = None

    def handle_starttag(self, tag, attributes):
        if tag == 'table':
            self.rows = []
        elif tag == 'tr':
            self.cells = []
        elif tag in ('th', 'td'):
            self.cell = ''

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag):
        if tag in ('th', 'td'):
            self.cells.append(self.cell.strip())
            self.cell = None
        elif tag == 'tr':
            self.rows.append(self.cells)
        elif tag == 'table':
            self.tables.append(self.rows)


class PerformancePageTest(unittest.TestCase):
    def test_trial_counts_and_caveats(self):
        source = (SITE / 'performance.html').read_text(encoding='utf-8')
        parser = TrialTables()
        parser.feed(source)
        self.assertEqual(len(parser.tables), 3)
        self.assertEqual(parser.tables[0][1:], [
            ['2 CPU / 3 GiB', '749', '717', '32', '0'],
            ['5 CPU / 8 GiB', '155', '155', '0', '0'],
            ['Total', '904', '872', '32', '0'],
        ])
        self.assertEqual(parser.tables[1][1:], [
            ['2', '36.59', '16.66', '109 / 128'],
            ['3', '34.48', '16.24', '115 / 128'],
            ['4', '39.13', '20.45', '124 / 128'],
        ])
        self.assertEqual(parser.tables[2][1:], [
            ['With veraPDF', '24', '111.702 s', '12.89', '8.222 s'],
            ['Without veraPDF; PDFBox retained', '24', '56.900 s', '25.31', '4.126 s'],
        ])
        for phrase in ['not large-scale load tests', 'not new alpha.2 measurements',
                       'not a REST load test', 'Normal API validation was never disabled',
                       'cannot be compared directly', 'temporarily stopped',
                       'c5d87746e3ef95a80a1950a4b9c05a88ced0521c', '/issues/93']:
            self.assertIn(phrase, source)
        self.assertIn('href="performance.html"', (SITE / 'index.html').read_text(encoding='utf-8'))
        self.assertEqual(source.count('<caption>'), 3)
        self.assertEqual(source.count('role="region"'), 3)
        self.assertNotIn('nuaforma-dev.hictsapps.nl', source)


if __name__ == '__main__':
    unittest.main()
