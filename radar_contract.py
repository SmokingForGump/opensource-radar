"""Strict, dependency-free public content boundary. No model-produced code is executed."""
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit

ISSUE_KEYS = {"schema_version", "id", "edition", "scheduled_for", "observed_at", "title", "summary", "baseline_note", "projects"}
PROJECT_KEYS = {"repository_id", "full_name", "url", "category", "summary", "why", "audience", "limitations", "try_it", "license_spdx", "stats", "sources", "claims"}
SECRET = re.compile(r"(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]+|-----BEGIN .*PRIVATE KEY-----|PRIVATE_CANARY|personal_notes|api_key\s*[:=])", re.I)
UNSAFE = re.compile(r"[<>]|(?:javascript|data|file|vbscript):|\x00", re.I)
ISSUE_ID = r"(?:weekly|monthly)-\d{4}-\d{2}-\d{2}"


def exact(obj, keys):
    if type(obj) is not dict or set(obj) != set(keys):
        raise ValueError("Public object has missing or unexpected fields")


def text(value, max_length=12000):
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        raise ValueError("Invalid public text")
    if SECRET.search(value) or UNSAFE.search(value):
        raise ValueError("Sensitive or executable content rejected")


def safe_url(value):
    text(value, 2048)
    p = urlsplit(value)
    if p.scheme != "https" or p.hostname != "github.com" or p.username or p.password or p.port not in (None, 443):
        raise ValueError("Public sources must use canonical GitHub HTTPS URLs")
    return value


def timestamp(value):
    text(value, 64)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None: raise ValueError("Timestamp needs timezone")


def text_list(items):
    if type(items) is not list or not 1 <= len(items) <= 12: raise ValueError("Invalid public list")
    for value in items: text(value)


def validate_project(p):
    exact(p, PROJECT_KEYS)
    if type(p["repository_id"]) is not int or p["repository_id"] <= 0: raise ValueError("Invalid repository ID")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", p["full_name"]): raise ValueError("Invalid repository name")
    if p["url"] != "https://github.com/" + p["full_name"]: raise ValueError("Repository URL mismatch")
    if p["category"] not in {"product", "engineering", "life", "knowledge"}: raise ValueError("Invalid category")
    for k in ["summary", "why", "audience"]: text(p[k])
    for k in ["limitations", "try_it"]: text_list(p[k])
    if p["license_spdx"] is not None: text(p["license_spdx"], 128)
    exact(p["stats"], {"stars_total", "observed_at"})
    if type(p["stats"]["stars_total"]) is not int or p["stats"]["stars_total"] < 0: raise ValueError("Invalid stars")
    timestamp(p["stats"]["observed_at"])
    if type(p["sources"]) is not list or not 2 <= len(p["sources"]) <= 8: raise ValueError("At least two evidence records required")
    ids = set()
    for s in p["sources"]:
        exact(s, {"id", "url", "excerpt"}); text(s["id"], 64); safe_url(s["url"]); text(s["excerpt"], 3000)
        if s["id"] in ids: raise ValueError("Duplicate evidence ID")
        ids.add(s["id"])
    if type(p["claims"]) is not list or not 1 <= len(p["claims"]) <= 12: raise ValueError("Missing claims")
    for c in p["claims"]:
        exact(c, {"text", "evidence_ids"}); text(c["text"]); text_list(c["evidence_ids"])
        if not set(c["evidence_ids"]) <= ids: raise ValueError("Unresolved evidence")


def validate_issue(d):
    exact(d, ISSUE_KEYS)
    if type(d["schema_version"]) is not int or d["schema_version"] != 1: raise ValueError("Unsupported schema")
    if d["edition"] not in {"weekly", "monthly"}: raise ValueError("Invalid edition")
    date.fromisoformat(d["scheduled_for"])
    if d["id"] != d["edition"] + "-" + d["scheduled_for"]: raise ValueError("Issue identity mismatch")
    timestamp(d["observed_at"])
    for k in ["title", "summary", "baseline_note"]: text(d[k])
    if type(d["projects"]) is not list or not 1 <= len(d["projects"]) <= 10: raise ValueError("Invalid project count")
    ids = set()
    for p in d["projects"]:
        validate_project(p)
        if p["repository_id"] in ids: raise ValueError("Duplicate project")
        ids.add(p["repository_id"])
    if len(json.dumps(d).encode()) > 500000: raise ValueError("Issue too large")
    return d


def validate_path(path):
    if not isinstance(path, str) or not re.fullmatch(r"content/(?:issues|manifests)/" + ISSUE_ID + r"\.json", path):
        raise ValueError("Export path outside public allowlist")
    return path


def canonical(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def digest(data): return hashlib.sha256(data).hexdigest()


def validate_tree(root):
    root = Path(root)
    issues = []
    for path in sorted((root / "content").rglob("*")):
        if path.is_symlink(): raise ValueError("Public symlink rejected")
        if not path.is_file(): continue
        rel = path.relative_to(root).as_posix(); validate_path(rel)
        if path.stat().st_size > 500000: raise ValueError("Oversized file")
        d = json.loads(path.read_text())
        if "/issues/" in rel:
            validate_issue(d)
            if path.stem != d["id"]: raise ValueError("Filename mismatch")
            m = root / "content/manifests" / path.name
            if not m.exists(): raise ValueError("Missing manifest")
            manifest = json.loads(m.read_text())
            exact(manifest, {"schema_version", "issue_id", "files"})
            if manifest["schema_version"] != 1 or manifest["issue_id"] != d["id"] or manifest["files"] != {rel: digest(path.read_bytes())}:
                raise ValueError("Manifest digest mismatch")
            issues.append(d)
        else:
            if not (root / "content/issues" / path.name).exists(): raise ValueError("Orphan manifest")
    return sorted(issues, key=lambda x: x["scheduled_for"], reverse=True)
