import importlib.util
import tempfile
import unittest
from pathlib import Path
from test_contract import sample


class SiteTests(unittest.TestCase):
    def test_build_empty_site_and_real_issue_with_base_path(self):
        p = Path(__file__).parents[1] / "build.py"
        self.assertTrue(p.exists(), "site builder not implemented")
        spec = importlib.util.spec_from_file_location("builder", p)
        b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); (root/"content/issues").mkdir(parents=True); (root/"content/manifests").mkdir()
            b.build(root, root/"dist")
            self.assertIn("首期正在准备", (root/"dist/index.html").read_text())
            d = sample(); data = b.canonical(d)
            (root/"content/issues"/(d["id"]+".json")).write_bytes(data)
            m = {"schema_version":1,"issue_id":d["id"],"files":{"content/issues/"+d["id"]+".json":b.digest(data)}}
            (root/"content/manifests"/(d["id"]+".json")).write_bytes(b.canonical(m))
            b.build(root, root/"dist")
            page=(root/"dist/issues"/d["id"]/"index.html").read_text()
            self.assertIn("/opensource-radar/assets/style.css", page)
            self.assertIn("Public README", page)
            self.assertTrue((root/"dist/feed.xml").exists())

if __name__ == "__main__": unittest.main()
