import copy
import importlib.util
import unittest
import tempfile
from pathlib import Path


def sample():
    return {"schema_version": 1, "id": "weekly-2026-10-22", "edition": "weekly",
            "scheduled_for": "2026-10-22", "observed_at": "2026-10-22T01:17:00Z",
            "title": "值得尝试的开源项目", "summary": "以公开证据为基础的观察。",
            "baseline_note": "首次观察，无历史基线。", "projects": [{
                "repository_id": 123, "full_name": "example/project",
                "url": "https://github.com/example/project", "category": "engineering",
                "summary": "项目解决的问题。", "why": "具体的使用价值。", "audience": "开发者",
                "limitations": ["尚未实际运行验证。"], "try_it": ["先阅读官方文档。"],
                "license_spdx": None, "stats": {"stars_total": 10, "observed_at": "2026-10-22T01:17:00Z"},
                "sources": [{"id": "meta", "url": "https://github.com/example/project", "excerpt": "Public metadata"},
                            {"id": "readme", "url": "https://github.com/example/project/blob/abc/README.md", "excerpt": "Public README"}],
                "claims": [{"text": "解决一个具体问题。", "evidence_ids": ["readme"]}]}]}


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("contract", Path(__file__).parents[1] / "radar_contract.py")
        if not Path(spec.origin).exists():
            raise AssertionError("public contract is not implemented")
        cls.c = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.c)

    def test_valid_issue(self):
        self.c.validate_issue(sample())

    def test_rejects_unknown_private_fields(self):
        d = sample(); d["personal_notes"] = "do not export"
        with self.assertRaises(ValueError): self.c.validate_issue(d)

    def test_rejects_executable_content(self):
        for value in ["<script>alert(1)</script>", "javascript:alert(1)", "sk-" + "X" * 32]:
            d = sample(); d["summary"] = value
            with self.assertRaises(ValueError): self.c.validate_issue(d)

    def test_rejects_broken_evidence_and_duplicates(self):
        d = sample(); d["projects"][0]["claims"][0]["evidence_ids"] = ["missing"]
        with self.assertRaises(ValueError): self.c.validate_issue(d)
        d = sample(); d["projects"].append(copy.deepcopy(d["projects"][0]))
        with self.assertRaises(ValueError): self.c.validate_issue(d)

    def test_rejects_non_github_source_and_false_types(self):
        d = sample(); d["projects"][0]["sources"][0]["url"] = "https://127.0.0.1/a"
        with self.assertRaises(ValueError): self.c.validate_issue(d)
        d = sample(); d["projects"][0]["stats"]["stars_total"] = True
        with self.assertRaises(ValueError): self.c.validate_issue(d)

    def test_export_path_and_manifest_tamper(self):
        with self.assertRaises(ValueError): self.c.validate_path("content/issues/../../file.json")
        self.assertEqual(self.c.validate_path("content/issues/weekly-2026-10-22.json"), "content/issues/weekly-2026-10-22.json")
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); path=root/'content/issues/weekly-2026-10-22.json'; path.parent.mkdir(parents=True)
            path.write_bytes(self.c.canonical(sample()))
            m=root/'content/manifests'/path.name; m.parent.mkdir(parents=True)
            m.write_bytes(self.c.canonical({'schema_version':1,'issue_id':path.stem,'files':{path.relative_to(root).as_posix():self.c.digest(path.read_bytes())}}))
            self.assertEqual(len(self.c.validate_tree(root)),1)
            d=sample(); d['title']='被修改的标题'; path.write_bytes(self.c.canonical(d))
            with self.assertRaises(ValueError): self.c.validate_tree(root)


if __name__ == "__main__": unittest.main()
