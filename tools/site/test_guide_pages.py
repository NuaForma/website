"""Guide navigation, safe multi-page initialization and published syntax regressions."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import unittest

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'site'


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids = []
        self.links = []
        self.headings = []
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag == 'h1':
            self.headings.append(tag)


class GuidePagesTest(unittest.TestCase):
    def test_all_pages_have_unique_ids_and_resolvable_local_links(self):
        pages = {path: Page(path) for path in SITE.glob('*.html')}
        self.assertEqual({path.name for path in pages}, {'index.html', 'templates.html', 'extensions.html', 'performance.html', 'operations.html'})
        for path, page in pages.items():
            self.assertEqual(len(page.ids), len(set(page.ids)), path.name)
            self.assertEqual(len(page.headings), 1, path.name)
            for link in page.links:
                url = urlsplit(link)
                if url.scheme or url.netloc:
                    continue
                target = path.parent / unquote(url.path) if url.path else path
                self.assertTrue(target.exists(), (path.name, link))
                if url.fragment:
                    self.assertIn(unquote(url.fragment), pages[target].ids)

    def test_template_syntax_and_extension_boundaries_are_explicit(self):
        templates = (SITE / 'templates.html').read_text(encoding='utf-8')
        for marker in ['{#each projects as project}', '{#each project.tasks as task}',
                       '{#if project.active}', '{#if task.include}',
                       'image(40, 20, true)', 'number("#,##0.00")',
                       '(name ?? null) == null', 'Content pipes cannot be chained']:
            self.assertIn(marker, templates)
        extension = (SITE / 'extensions.html').read_text(encoding='utf-8')
        for marker in ['META-INF/services/dev.nuaforma.contracts.TemplatePipe',
                       'META-INF/nuaforma/pipes/example.PrefixPipe.properties',
                       'contract.minor=2', '/opt/nuaforma/extensions',
                       'not automatically activated', 'not sandboxed']:
            self.assertIn(marker, extension)

    def test_shared_header_and_page_specific_initialization(self):
        for name in ['index.html', 'templates.html', 'extensions.html', 'performance.html', 'operations.html']:
            html = (SITE / name).read_text(encoding='utf-8')
            self.assertIn('class="site-masthead"', html)
            self.assertIn('href="templates.html"', html)
            self.assertIn('href="extensions.html"', html)
            self.assertIn('id="theme-toggle"', html)
            self.assertIn('id="nav-toggle"', html)
            self.assertIn('aria-expanded="false" aria-controls="main-navigation"', html)
            self.assertIn('id="copy-status"', html)
        css = (SITE / 'styles.css').read_text(encoding='utf-8')
        self.assertIn('.site-masthead{position:sticky;top:0;', css)
        self.assertIn('scroll-padding-top:230px', css)
        self.assertIn('.site-header nav.is-open{display:flex}', css)
        javascript = (SITE / 'app.js').read_text(encoding='utf-8')
        self.assertIn('if (document.querySelector("#scenario-list")) loadExamples()', javascript)
        self.assertIn('if (document.querySelector("#release-link")) latestRelease()', javascript)


if __name__ == '__main__':
    unittest.main()
