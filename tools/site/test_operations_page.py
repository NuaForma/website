"""Keep operator policies separate from request options and historical benchmarks."""
from pathlib import Path
import unittest

SITE = Path(__file__).resolve().parents[2] / 'site'


class OperationsPageTest(unittest.TestCase):
    def test_font_selection_and_operator_boundaries(self):
        source = (SITE / 'operations.html').read_text(encoding='utf-8')
        for phrase in ['"fontMode": "embed"', '"fontSelection": "used"',
                       'not restricted to Arial-like', '/opt/nuaforma/custom-fonts',
                       'resource.&lt;id&gt;', 'NUAFORMA_PDFA_VALIDATION',
                       'Only exact <code>false</code>', 'PDFBox',
                       'NUAFORMA_PDF_PARALLELISM', 'defaults to <code>1</code>',
                       'PDF/A conformance is not checked by NuaForma',
                       'cannot be changed by request JSON', 'No unrestricted OpenShift',
                       'Document content', 'performance.html']:
            self.assertIn(phrase.lower(), source.lower())
        self.assertIn('href="operations.html"', (SITE / 'index.html').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
