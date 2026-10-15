"""Independent website ownership and checked main-only deployment are explicit."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class WorkflowTest(unittest.TestCase):
    def test_deployment_remains_checked_main_only_even_for_direct_pushes(self):
        workflow = (ROOT / '.github/workflows/pages.yml').read_text()
        self.assertIn('branches: [main, develop]', workflow)
        self.assertIn("github.repository == 'NuaForma/website'", workflow)
        self.assertIn("github.event_name != 'pull_request'", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn('needs: check', workflow)
        self.assertNotIn('if: always()', workflow)
        self.assertIn('path: site', workflow)

    def test_current_tree_contains_no_product_build_or_implicit_qualification_checkout(self):
        self.assertFalse((ROOT / 'build.gradle.kts').exists())
        self.assertFalse((ROOT / 'nuaforma-server').exists())
        self.assertFalse((ROOT / 'tools/container/qualify_service.py').exists())
        self.assertFalse((ROOT / 'tools/site/verify_example_kit.py').exists())
        self.assertFalse((ROOT / 'tools/site/verify_client_collections.py').exists())


if __name__ == '__main__':
    unittest.main()
