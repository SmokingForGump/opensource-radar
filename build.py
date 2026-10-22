"""Build the complete public magazine with Python's standard library."""
import html
import json
import shutil
from pathlib import Path
from xml.sax.saxutils import escape
from radar_contract import canonical, digest, validate_tree, SECRET

BASE = "/opensource-radar"
ORIGIN = "https://smokingforgump.github.io"
CATEGORY = {"product": "产品启发", "engineering": "工程实践", "life": "生活发现", "knowledge": "知识管理"}
e = html.escape


def layout(title, body, issue_id="", active=""):
    nav = "".join(f'<a href="{BASE}/{slug}/" {"aria-current=page" if active==slug else ""}>{label}</a>' for slug, label in [("weekly", "每周精选"), ("monthly", "Monthly 深研"), ("archive", "全部期刊"), ("method", "研究方法")])
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} · OpenSource Radar</title><meta name="description" content="有证据、有观点、有尝试路径的开源科技杂志。"><meta name="radar-issue" content="{e(issue_id)}"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'"><link rel="stylesheet" href="{BASE}/assets/style.css"><link rel="alternate" type="application/rss+xml" title="OpenSource Radar" href="{BASE}/feed.xml"></head><body><a class="skip" href="#main">跳到正文</a><header><div class="masthead"><a class="wordmark" href="{BASE}/">OpenSource<br><strong>Radar<span>·</span></strong></a><p class="strap">开源世界，值得深入的发现。<br><span>PRODUCT · ENGINEERING · EVERYDAY LIFE</span></p><a class="source" href="https://github.com/SmokingForGump/opensource-radar" rel="noopener noreferrer">阅读开源档案 ↗</a></div><nav aria-label="主导航">{nav}<a href="{BASE}/feed.xml">RSS ↗</a></nav></header><main id="main">{body}</main><footer><div class="footer-mark">OpenSource Radar</div><p>独立观察 · 公开证据 · 持续更正</p><p>AI 辅助研究。项目描述不代表实际试用或安全背书。<br>原始项目及第三方内容的权利归原作者。</p><a href="{BASE}/method/">了解我们的研究方法 →</a></footer></body></html>'''


def link_issue(d):
    edition = "每周精选" if d["edition"] == "weekly" else "Monthly 深度精选"
    return f'<article class="issue-row"><div class="issue-date">{e(d["scheduled_for"])}<span>{edition}</span></div><div><h2><a href="{BASE}/issues/{e(d["id"])}/">{e(d["title"])}</a></h2><p>{e(d["summary"])}</p></div><a class="arrow" href="{BASE}/issues/{e(d["id"])}/" aria-label="阅读{e(d["title"])}">↗</a></article>'


def empty():
    return '<section class="empty"><span class="edition">创刊准备中</span><h2>首期正在准备。<br>好项目，值得多看一层。</h2><p>我们先读文档、找证据、核实限制，再把值得你花时间的项目带到这里。</p><a class="button" href="'+BASE+'/method/">看看如何筛选 →</a></section>'


def project(p, n):
    def ul(values): return "<ul>" + "".join("<li>"+e(v)+"</li>" for v in values)+"</ul>"
    sources = "".join(f'<li id="{p["repository_id"]}-{e(s["id"])}"><a href="{e(s["url"])}" rel="noopener noreferrer">{e(s["id"])} ↗</a><blockquote>{e(s["excerpt"])}</blockquote></li>' for s in p["sources"])
    claims = "".join('<li>'+e(c["text"])+" <small>依据："+", ".join(e(x) for x in c["evidence_ids"])+"</small></li>" for c in p["claims"])
    return f'''<article class="project" id="project-{p["repository_id"]}"><div class="project-heading"><span class="index">{n:02}</span><div><span class="edition">{CATEGORY[p["category"]]}</span><h2><a href="{e(p["url"])}" rel="noopener noreferrer">{e(p["full_name"])} ↗</a></h2><p class="lead">{e(p["summary"])}</p></div></div><div class="project-body"><section><h3>为什么值得看</h3><p>{e(p["why"])}</p><h3>适合谁</h3><p>{e(p["audience"])}</p><h3>可以怎样开始</h3>{ul(p["try_it"])}<h3>限制与注意</h3>{ul(p["limitations"])}</section><aside><dl><dt>Stars · 采集时</dt><dd>{p["stats"]["stars_total"]:,}</dd><dt>许可证</dt><dd>{e(p["license_spdx"] or "尚未确认")}</dd><dt>证据时间</dt><dd>{e(p["stats"]["observed_at"][:10])}</dd></dl><p class="note">未实际运行验证。请先检查上游文档、许可证及环境要求。</p></aside></div><details><summary>展开事实与原始证据（{len(p["sources"])} 条）</summary><ul>{claims}</ul><ol class="evidence">{sources}</ol></details></article>'''


def build(root=Path(__file__).parent, out=None):
    root = Path(root); out = Path(out or root/"dist")
    issues = validate_tree(root)
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    (out/"assets").mkdir(); (out/".nojekyll").write_text("")
    css = Path(__file__).parent/"assets/style.css"
    shutil.copyfile(css, out/"assets/style.css")
    def write(path, title, body, issue_id="", active=""):
        p = out/path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(layout(title, body, issue_id, active))
    hero = '<section class="opening"><div><span class="edition">一份关于开源的独立读物</span><h1>发现项目。<br>读懂价值。</h1><p>从产品灵感到工程实践，也把目光留给日常生活。</p></div><div class="editor-note"><span class="orbit" aria-hidden="true">◎</span><h2>热度是入口，<br>证据让判断发生。</h2><p>每周四精选 · 每两周 Monthly 深研<br>原始来源、适用场景和限制，放在一起读。</p></div></section>'
    content = '<div class="section-title"><h2>最新一期</h2><a href="'+BASE+'/archive/">浏览全部期刊 →</a></div>'+link_issue(issues[0]) if issues else empty()
    write(Path("index.html"), "发现项目，读懂价值", hero+content, issues[0]["id"] if issues else "")
    for edition, title in [("weekly", "每周精选"), ("monthly", "Monthly 深度精选"), ("archive", "全部期刊")]:
        selected=[d for d in issues if edition=="archive" or d["edition"]==edition]
        intro = "持续观察、版本变化与同类比较。" if edition=="monthly" else "值得关注的开源项目，和具体的尝试方向。"
        write(Path(edition)/"index.html", title, f'<section class="page-heading"><h1>{title}</h1><p>{intro}</p></section>'+(''.join(link_issue(d) for d in selected) or empty()), active=edition)
    for d in issues:
        body=f'<section class="page-heading"><span class="edition">{e(d["edition"])} · {e(d["scheduled_for"])}</span><h1>{e(d["title"])}</h1><p class="lead">{e(d["summary"])}</p><p class="note">采集于 {e(d["observed_at"])} · {e(d["baseline_note"])}</p></section>'
        body += ''.join(project(p,n+1) for n,p in enumerate(d["projects"]))
        write(Path("issues")/d["id"]/"index.html", d["title"], body, d["id"])
    method='''<section class="page-heading"><h1>好判断，<br>始于可追溯的证据。</h1><p>我们如何研究、筛选和更正。</p></section><article class="prose"><h2>从榜单出发，回到项目本身</h2><p>GitHub Trending 是发现入口。我们进一步阅读项目官方文档、README、许可证和公开活动，保留原始来源与采集时间。</p><h2>把价值和限制放在同一页</h2><p>每个项目说明适用场景、尝试方向和限制。没有实际执行项目时，不把文档描述写成试用体验；没有历史基线时，不展示虚构增长趋势。</p><h2>周刊与 Monthly</h2><p>周刊侧重发现与快速尝试。Monthly 每两周观察一次月度榜单，侧重持续性、变化及替代方案。首次研究会明确标注缺少历史基线。</p><h2>AI 辅助，证据优先</h2><p>研究与独立复核均由 DeepSeek 辅助完成。引用、数据格式、内容安全与构建须通过检查才会发布。自动校验不能保证内容完全正确。</p><h2>更正与反馈</h2><p>发现事实错误时，请附上原始来源，在公开仓库提交 Issue。不要提交任何私人信息或凭证。我们保留修改历史。</p><p><a href="https://github.com/SmokingForGump/opensource-radar/issues" rel="noopener noreferrer">提交更正 →</a></p></article>'''
    write(Path("method/index.html"), "研究方法", method, active="method")
    write(Path("404.html"), "页面未找到", '<section class="page-heading"><h1>这页还没有信号。</h1><p>页面可能已移动。</p><a href="'+BASE+'/">返回首页 →</a></section>')
    rss=''.join(f'<item><title>{escape(d["title"])}</title><link>{ORIGIN}{BASE}/issues/{d["id"]}/</link><guid>{ORIGIN}{BASE}/issues/{d["id"]}/</guid><description>{escape(d["summary"])}</description></item>' for d in issues)
    (out/"feed.xml").write_text('<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel><title>OpenSource Radar</title><link>'+ORIGIN+BASE+'/</link><description>有证据的开源精选</description>'+rss+'</channel></rss>')
    urls=["", "weekly/", "monthly/", "archive/", "method/"]+["issues/"+d["id"]+"/" for d in issues]
    (out/"sitemap.xml").write_text('<?xml version="1.0" encoding="utf-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+ORIGIN+BASE+'/'+u+'</loc></url>' for u in urls)+'</urlset>')
    total=0
    for p in out.rglob('*'):
        if not p.is_file(): continue
        total+=p.stat().st_size
        if SECRET.search(p.read_text()): raise ValueError("Sensitive content in final site")
    if total>100_000_000: raise ValueError("Site exceeds size budget")
    print(f"Built {len(issues)} issues; {total} bytes")

if __name__ == "__main__": build()
