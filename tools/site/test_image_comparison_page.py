"""Verify project links, release claims and provenance of the real comparison example."""
import hashlib
import json
import pathlib
import re
import unittest
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[2]
SITE = ROOT / 'site'
PROJECT = SITE / 'image-comparison'


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.references.extend(attrs[key] for key in ('href', 'src') if key in attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])


class ImageComparisonPageTest(unittest.TestCase):
    def test_new_pages_have_resolvable_local_links_and_unique_ids(self):
        for page in PROJECT.rglob('*.html'):
            parser = References()
            parser.feed(page.read_text(encoding='utf-8'))
            self.assertEqual(len(parser.ids), len(set(parser.ids)), page)
            for ref in parser.references:
                url = urlsplit(ref)
                if url.scheme or url.netloc:
                    continue
                target = (page.parent / unquote(url.path)).resolve() if url.path else page
                self.assertTrue(target.is_relative_to(SITE.resolve()), ref)
                self.assertTrue(target.is_file(), ref)
                if url.fragment:
                    linked = References()
                    linked.feed(target.read_text(encoding='utf-8'))
                    self.assertIn(unquote(url.fragment), linked.ids, ref)

    def test_navigation_and_release_status_remain_explicit(self):
        for name in ('index.html', 'templates.html', 'extensions.html', 'operations.html', 'performance.html'):
            self.assertIn('href="image-comparison/index.html"', (SITE / name).read_text(encoding='utf-8'))
        for name in ('index.html', 'docs/index.html', 'releases/index.html'):
            text = (PROJECT / name).read_text(encoding='utf-8')
            self.assertIn('5.0.0', text)
            self.assertNotIn('in preparation', text.lower())
            self.assertNotIn('installation preview', text.lower())
            self.assertIn('id="theme-toggle"', text)
            self.assertIn('id="nav-toggle"', text)
        docs = (PROJECT / 'docs/index.html').read_text(encoding='utf-8')
        self.assertIn('dev.nuaforma:image-comparison-kotlin:5.0.0', docs)
        self.assertIn('dev.nuaforma.image.comparison.ImageComparison', docs)
        self.assertNotIn('com.github.romankh3.image.comparison', docs)
        self.assertIn('https://central.sonatype.com/artifact/dev.nuaforma/image-comparison/5.0.0', docs)
        self.assertIn('https://central.sonatype.com/artifact/dev.nuaforma/image-comparison-kotlin/5.0.0', docs)
        for language in ('java', 'kotlin'):
            for tool in ('maven', 'gradle'):
                self.assertIn('id="panel-ic-' + language + '-' + tool + '"', docs)

    def test_demo_assets_and_visible_metrics_match_the_recorded_engine_result(self):
        record = json.loads((PROJECT / 'comparison.json').read_text())
        self.assertEqual('5.0.0', record['version'])
        self.assertRegex(record['sourceCommit'], r'^[a-f0-9]{40}$')
        self.assertEqual(record['generatorSha256'], hashlib.sha256((ROOT / 'tools/site/ImageComparisonDemo.java').read_bytes()).hexdigest())
        self.assertEqual({'expected.png', 'actual.png', 'all-pixels.png', 'exclude-date.png'}, set(record['images']))
        for name, digest in record['images'].items():
            self.assertEqual(digest, hashlib.sha256((PROJECT / name).read_bytes()).hexdigest(), name)
        self.assertNotEqual(record['images']['actual.png'], record['images']['expected.png'])
        self.assertNotEqual(record['images']['all-pixels.png'], record['images']['exclude-date.png'])
        javascript = (PROJECT / 'demo.js').read_text()
        for case, result in record['cases'].items():
            self.assertEqual('MISMATCH', result['state'])
            self.assertGreater(result['differencePercent'], 0)
            entry = re.search(r'"' + case + r'": \{([^}]+)\}', javascript)[1]
            self.assertIn('regions: "' + str(result['regions']) + '"', entry)
            percent = float(re.search(r'percent: "([0-9.]+)%"', entry)[1])
            self.assertAlmostEqual(result['differencePercent'], percent, places=5)
        self.assertEqual(3, record['cases']['all-pixels']['regions'])
        self.assertEqual(2, record['cases']['exclude-date']['regions'])


if __name__ == '__main__':
    unittest.main()
