#!/usr/bin/env python3
"""Local literature workflow for search, fetch, summarize, organize, matrices, and reports.

Uses public metadata APIs and only downloads open/legal PDF URLs discovered from those APIs.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, re, sys, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"; RESULTS = DATA / "search_results.jsonl"; PAPERS = ROOT / "papers"; INDUSTRY = ROOT / "industry"; PROJECTS = ROOT / "projects"
UA = "Research Evidence Vault Workflow (open scholarly metadata; mailto:replace-with-your-email@example.com)"


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def http(url: str, accept: str = "application/json", timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def norm(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def slug(s: str, n=60) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", s)[:n].strip("_")
    return s or "untitled"

def authors_short(authors: list[str]) -> str:
    return slug((authors[0].split()[-1] if authors else "Unknown"), 24)

def key(p: dict[str, Any]) -> str:
    if p.get("doi"): return "doi:" + p["doi"].lower()
    if p.get("arxiv_id"): return "arxiv:" + p["arxiv_id"].lower()
    if p.get("pmid"): return "pmid:" + str(p["pmid"])
    return "title:" + hashlib.sha1(norm(p.get("title")).lower().encode()).hexdigest()

def paper_dir(p):
    return PAPERS / f"{p.get('year') or 'YYYY'}_{authors_short(p.get('authors', []))}_{slug(p.get('title',''), 42)}"

def yaml_scalar(v):
    if v is None: return ""
    if isinstance(v, (int, float)): return str(v)
    return json.dumps(str(v), ensure_ascii=False)

def yaml_dump(d):
    lines=[]
    for k,v in d.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for x in v: lines.append(f"  - {yaml_scalar(x)}")
        else: lines.append(f"{k}: {yaml_scalar(v)}")
    return "\n".join(lines)+"\n"

def load_results():
    if not RESULTS.exists(): return []
    return [json.loads(l) for l in RESULTS.read_text(encoding="utf-8").splitlines() if l.strip()]

def append_results(items, query):
    DATA.mkdir(exist_ok=True)
    old={key(x) for x in load_results()}
    new=[]
    with RESULTS.open("a", encoding="utf-8") as f:
        for p in items:
            p["retrieved_at"] = now_utc(); p["query"] = query
            if key(p) not in old:
                f.write(json.dumps(p, ensure_ascii=False)+"\n"); old.add(key(p)); new.append(p)
    with (ROOT/"queries/search_log.md").open("a", encoding="utf-8") as f:
        f.write(f"\n## {now_utc()}\n\n- Query: `{query}`\n- New records: {len(new)}\n- Sources: {', '.join(sorted(set(i.get('source','unknown') for i in new)))}\n")
    return new

def search_arxiv(q, limit):
    url="https://export.arxiv.org/api/query?"+urllib.parse.urlencode({"search_query":"all:"+q,"start":0,"max_results":limit})
    root=ET.fromstring(http(url, "application/atom+xml")); ns={"a":"http://www.w3.org/2005/Atom"}
    out=[]
    for e in root.findall("a:entry", ns):
        links={l.attrib.get("title", l.attrib.get("type","")): l.attrib.get("href") for l in e.findall("a:link", ns)}
        eid=e.findtext("a:id", "", ns); arxiv_id=eid.rsplit("/",1)[-1]
        out.append({"title":norm(e.findtext("a:title", "", ns)),"authors":[norm(a.findtext("a:name","",ns)) for a in e.findall("a:author",ns)],"year":(e.findtext("a:published","",ns)[:4] or None),"venue":"arXiv","doi":"","url":eid,"abstract":norm(e.findtext("a:summary","",ns)),"citation_count":None,"source":"arxiv","keywords":[],"arxiv_id":arxiv_id,"pdf_url":links.get("application/pdf") or f"https://arxiv.org/pdf/{arxiv_id}.pdf"})
    return out

def search_json_api(source, url, mapper):
    try: return [mapper(x) for x in json.loads(http(url).decode()).get("results", [])]
    except Exception as e: print(f"warning: {source} failed: {e}", file=sys.stderr); return []

def search_openalex(q, limit):
    url="https://api.openalex.org/works?"+urllib.parse.urlencode({"search":q,"per-page":limit})
    def m(x):
        doi=(x.get("doi") or "").replace("https://doi.org/","")
        oa=x.get("open_access") or {}; loc=x.get("primary_location") or {}
        return {"title":norm(x.get("title")),"authors":[a.get("author",{}).get("display_name","") for a in x.get("authorships",[])],"year":x.get("publication_year"),"venue":norm((loc.get("source") or {}).get("display_name")),"doi":doi,"url":x.get("id"),"abstract":"","citation_count":x.get("cited_by_count"),"source":"openalex","keywords":[c.get("display_name") for c in x.get("concepts",[])[:8]],"pdf_url":oa.get("oa_url") if oa.get("is_oa") else ""}
    return search_json_api("openalex", url, m)

def search_crossref(q, limit):
    url="https://api.crossref.org/works?"+urllib.parse.urlencode({"query":q,"rows":limit})
    try: items=json.loads(http(url).decode()).get("message",{}).get("items",[])
    except Exception as e: print(f"warning: crossref failed: {e}", file=sys.stderr); return []
    out=[]
    for x in items:
        out.append({"title":norm((x.get("title") or [""])[0]),"authors":[norm(" ".join([a.get("given",""),a.get("family","")])) for a in x.get("author",[])],"year":(((x.get("published-print") or x.get("published-online") or {}).get("date-parts") or [[None]])[0][0]),"venue":norm((x.get("container-title") or [""])[0]),"doi":x.get("DOI",""),"url":x.get("URL",""),"abstract":re.sub("<[^>]+>","",x.get("abstract","") or ""),"citation_count":x.get("is-referenced-by-count"),"source":"crossref","keywords":x.get("subject",[])[:8],"pdf_url":""})
    return out

def search_semantic(q, limit):
    url="https://api.semanticscholar.org/graph/v1/paper/search?"+urllib.parse.urlencode({"query":q,"limit":limit,"fields":"title,authors,year,venue,abstract,citationCount,externalIds,openAccessPdf,url"})
    try: data=json.loads(http(url).decode()).get("data",[])
    except Exception as e: print(f"warning: semantic_scholar failed: {e}", file=sys.stderr); return []
    return [{"title":norm(x.get("title")),"authors":[a.get("name","") for a in x.get("authors",[])],"year":x.get("year"),"venue":x.get("venue",""),"doi":(x.get("externalIds") or {}).get("DOI",""),"url":x.get("url",""),"abstract":norm(x.get("abstract")),"citation_count":x.get("citationCount"),"source":"semantic_scholar","keywords":[],"pdf_url":((x.get("openAccessPdf") or {}).get("url") or "")} for x in data]

def search_pubmed(q, limit):
    base="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    try:
        ids=json.loads(http(base+"esearch.fcgi?"+urllib.parse.urlencode({"db":"pubmed","term":q,"retmode":"json","retmax":limit})).decode())["esearchresult"]["idlist"]
        if not ids: return []
        root=ET.fromstring(http(base+"efetch.fcgi?"+urllib.parse.urlencode({"db":"pubmed","id":",".join(ids),"retmode":"xml"}), "application/xml"))
    except Exception as e: print(f"warning: pubmed failed: {e}", file=sys.stderr); return []
    out=[]
    for art in root.findall(".//PubmedArticle"):
        pmid=art.findtext(".//PMID"); title=norm("".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else "")
        abstract=norm(" ".join("".join(a.itertext()) for a in art.findall(".//AbstractText")))
        authors=[norm((a.findtext("ForeName") or "")+" "+(a.findtext("LastName") or "")) for a in art.findall(".//Author")]
        doi=""; 
        for aid in art.findall(".//ArticleId"):
            if aid.attrib.get("IdType")=="doi": doi=aid.text or ""
        out.append({"title":title,"authors":[a for a in authors if a],"year":art.findtext(".//PubDate/Year"),"venue":art.findtext(".//Journal/Title") or "","doi":doi,"url":f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/","abstract":abstract,"citation_count":None,"source":"pubmed","keywords":[k.text for k in art.findall(".//Keyword") if k.text],"pmid":pmid,"pdf_url":""})
    return out


def search_biorxiv_medrxiv(q, limit):
    # bioRxiv/medRxiv expose date-window APIs rather than full text search.
    # Fetch a recent legal metadata window and keep records matching query terms.
    terms=[t.lower() for t in re.findall(r"[A-Za-z0-9]+", q) if len(t)>2]
    out=[]; today=dt.date.today(); start=today-dt.timedelta(days=365)
    for server in ("biorxiv", "medrxiv"):
        url=f"https://api.biorxiv.org/details/{server}/{start.isoformat()}/{today.isoformat()}/0"
        try: data=json.loads(http(url).decode()).get("collection", [])
        except Exception as e: print(f"warning: {server} failed: {e}", file=sys.stderr); continue
        for x in data:
            hay=(x.get("title","")+" "+x.get("abstract","")).lower()
            if terms and not any(t in hay for t in terms): continue
            out.append({"title":norm(x.get("title")),"authors":[norm(a) for a in (x.get("authors") or "").split(";") if norm(a)],"year":(x.get("date") or "")[:4],"venue":server,"doi":x.get("doi", ""),"url":x.get("doi_url") or ("https://doi.org/"+x.get("doi","") if x.get("doi") else ""),"abstract":norm(x.get("abstract")),"citation_count":None,"source":server,"keywords":[],"pdf_url":x.get("rel_abs") or ""})
            if len(out) >= limit: return out
    return out

def cmd_search(args):
    items=[]
    for fn in (search_arxiv, search_semantic, search_openalex, search_crossref, search_pubmed, search_biorxiv_medrxiv):
        try: items += fn(args.query, args.limit); time.sleep(0.2)
        except Exception as e: print(f"warning: {fn.__name__} failed: {e}", file=sys.stderr)
    new=append_results(items, args.query); print(f"saved {len(new)} new / {len(items)} total candidate records to {RESULTS}")
    if getattr(args, "include_industry", False):
        scope = parse_industry_scope(getattr(args, "industry_scope", "all"))
        seed = Path(getattr(args, "industry_seed", ROOT / "seeds" / "industry_anc_benchmark_seed.json"))
        records = [r for r in load_industry_seed(seed) if r.get("record_type") in scope]
        write_industry_outputs(records, query=args.query, scope=scope, output_dir=resolve_industry_output_dir(getattr(args, "project_dir", None)), topic_label=getattr(args, "topic_label", "业界"))


def cmd_ingest(args):
    src = Path(args.file)
    if not src.exists():
        raise SystemExit(f"seed file not found: {src}")
    text = src.read_text(encoding="utf-8")
    if src.suffix.lower() == ".jsonl":
        items = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        loaded = json.loads(text)
        items = loaded.get("records", loaded) if isinstance(loaded, dict) else loaded
    new = append_results(items, getattr(args, "query", "manual-ingest"))
    print(f"ingested {len(new)} new / {len(items)} supplied records from {src}")

def cmd_fetch(args):
    PAPERS.mkdir(exist_ok=True); count=0
    for p in load_results():
        d=paper_dir(p); d.mkdir(parents=True, exist_ok=True)
        meta={k:p.get(k, "") for k in ["title","authors","year","venue","doi","url","source","abstract","citation_count","keywords","arxiv_id","pmid","pdf_url","retrieved_at","query"]}
        (d/"metadata.yaml").write_text(yaml_dump(meta), encoding="utf-8")
        if p.get("abstract") and not (d/"fulltext.txt").exists(): (d/"fulltext.txt").write_text("ABSTRACT ONLY\n\n"+p["abstract"], encoding="utf-8")
        pdf=p.get("pdf_url") or ""
        if pdf and pdf.lower().startswith("http") and ("pdf" in pdf.lower() or "arxiv.org" in pdf):
            try:
                b=http(pdf, "application/pdf", 45)
                if b[:4]==b"%PDF": (d/"paper.pdf").write_bytes(b)
            except Exception as e: print(f"warning: pdf download skipped for {p.get('title')}: {e}", file=sys.stderr)
        count+=1
    print(f"fetched/normalized {count} paper directories")

def paper_md(p, basis):
    now=now_utc(); title=p.get('title','')
    fm={"type":"paper","title":title,"authors":p.get("authors",[]),"year":p.get("year"),"venue":p.get("venue",""),"doi":p.get("doi",""),"url":p.get("url",""),"source":p.get("source",""),"tags":["literature"],"topics":p.get("keywords",[])[:5],"methods":[],"population":"","measures":[],"main_findings":[],"limitations":[],"timestamp":now,"summary_basis":basis}
    cite=f"来源：{title} ({p.get('year') or 'n.d.'})。"
    abs_txt=p.get("abstract") or ""
    return "---\n"+yaml_dump(fm)+"---\n\n# "+title+f"\n\n## 一句话总结\n\n{('基于摘要总结：' if basis=='abstract' else '基于可用全文/元数据总结：')}{abs_txt[:240]} {cite}\n\n## 研究问题\n\n- 待精读确认。{cite}\n\n## 理论背景\n\n- 待从全文或人工阅读中补充；当前记录不做推断。{cite}\n\n## 方法\n\n* 样本：待确认。\n* 设计：待确认。\n* 变量：待确认。\n* 测量：待确认。\n* 分析方法：待确认。\n\n## 核心发现\n\n- {('摘要显示：' + abs_txt[:500]) if abs_txt else '未获得摘要；需人工补充。'} {cite}\n\n## 证据强度\n\n* 样本量：待确认。\n* 研究设计：待确认。\n* 统计方法：待确认。\n* 可重复性：待确认。\n* 局限：当前自动笔记可能仅基于摘要，不能替代全文精读。\n\n## 与我的研究的关系\n\n- 待根据具体研究问题人工标注。{cite}\n\n## 可引用句子/观点\n\n- 不自动生成逐字引用；请从合法全文核对后添加。\n\n## 后续追踪\n\n* 相关论文：\n* 需要精读：是\n* 需要复核：方法、样本、结论边界\n"

def cmd_summarize(args):
    for p in load_results():
        d=paper_dir(p); d.mkdir(parents=True, exist_ok=True)
        basis="fulltext" if (d/"paper.pdf").exists() else "abstract"
        md=paper_md(p,basis)
        (d/"paper.md").write_text(md, encoding="utf-8"); (d/"summary.md").write_text(md, encoding="utf-8")
        (d/"critique.md").write_text(f"# Critique\n\n- 论文：{p.get('title')} ({p.get('year')})\n- 自动状态：需人工复核研究设计、样本、统计与局限；不从摘要外推。\n", encoding="utf-8")
        (d/"quotes.md").write_text("# Quotes\n\n> 仅添加已从合法来源核对的短引用。\n", encoding="utf-8")
    print("summaries generated")

def table(rows, cols):
    return "|"+"|".join(cols)+"|\n|"+"|".join(["---"]*len(cols))+"|\n"+"\n".join("|"+"|".join(str(r.get(c,'')) for c in cols)+"|" for r in rows)+"\n"

def cmd_organize(args):
    ps=load_results(); (ROOT/"literature").mkdir(exist_ok=True); (ROOT/"okf/index.md").write_text("---\ntype: okf_index\n---\n\n# OKF Index\n\n- [[../literature/index|Literature Index]]\n", encoding="utf-8")
    rows=[{"title":p.get("title"),"year":p.get("year"),"source":p.get("source"),"doi":p.get("doi"),"note":str(paper_dir(p).relative_to(ROOT)/"paper.md")} for p in ps]
    (ROOT/"literature/index.md").write_text("# Literature Index\n\n"+table(rows,["year","title","source","doi","note"]), encoding="utf-8")
    topics={}
    for p in ps:
        for kw in p.get("keywords") or ["untagged"]: topics.setdefault(kw,[]).append(p.get("title"))
    (ROOT/"literature/by_topic.md").write_text("# By Topic\n\n"+"\n".join(f"## {k}\n"+"\n".join(f"- {t}" for t in v) for k,v in topics.items()), encoding="utf-8")
    for name in ["by_method.md","by_theory.md","citation_graph.md"]: (ROOT/"literature"/name).write_text(f"# {name[:-3].replace('_',' ').title()}\n\n待人工/agent 精读后补充。\n", encoding="utf-8")
    print("organized literature indexes")

def cmd_matrix(args):
    ps=load_results(); rows=[{"paper":p.get("title"),"year":p.get("year"),"evidence_supported":"abstract/metadata only; verify before citing","method":"待确认","finding":(p.get("abstract") or "")[:180],"gap":"需全文精读确认"} for p in ps]
    (ROOT/"literature/evidence_matrix.md").write_text("# Evidence Matrix\n\n"+table(rows,["paper","year","evidence_supported","finding"]), encoding="utf-8")
    (ROOT/"literature/method_matrix.md").write_text("# Method Matrix\n\n"+table(rows,["paper","year","method"]), encoding="utf-8")
    (ROOT/"literature/gap_matrix.md").write_text("# Gap Matrix\n\n"+table(rows,["paper","year","gap"]), encoding="utf-8")
    (ROOT/"literature/core_findings.md").write_text("# Core Findings\n\n"+table(rows,["paper","year","finding"]), encoding="utf-8")
    (ROOT/"literature/controversies.md").write_text("# Controversies\n\n自动流程不推断争议；请基于多篇全文证据补充。\n", encoding="utf-8")
    print("matrices generated")

def cmd_report(args):
    ps=load_results(); cites="\n".join(f"- {p.get('title')} ({p.get('year')}). DOI: {p.get('doi') or 'unknown'}. URL: {p.get('url') or 'unknown'}." for p in ps)
    body=f"# Literature Review\n\n## 研究背景\n\n本报告由本地工具链根据 {len(ps)} 条检索记录生成。未获得全文的条目只可视为摘要级证据。\n\n## 核心问题\n\n- 需要结合 `queries/research_question.md` 进一步明确。\n\n## 主流理论\n\n- 自动流程不从摘要推断理论谱系；见 `literature/by_theory.md`。\n\n## 代表性研究\n\n{cites}\n\n## 方法比较\n\n见 `literature/method_matrix.md`。\n\n## 结论一致性\n\n### 证据支持\n\n- 仅列入各论文摘要或全文中明确出现的信息；见 `literature/evidence_matrix.md`。\n\n### 推测\n\n- 当前自动报告不生成未由论文支持的推测。\n\n## 分歧\n\n见 `literature/controversies.md`；需人工复核。\n\n## 未解决问题\n\n见 `literature/gap_matrix.md`。\n\n## 未来研究方向\n\n- 对标 gap matrix 进行精读后补充。\n\n## 可引用文献列表\n\n{cites}\n"
    (ROOT/"reports/literature_review.md").write_text(body, encoding="utf-8"); (ROOT/"reports/executive_summary.md").write_text("# Executive Summary\n\n自动生成：请先精读并复核关键证据后使用。\n", encoding="utf-8")
    print("report generated")


INDUSTRY_SCOPES = {"patent", "product", "solution"}
INDUSTRY_SCOPE_ALIASES = {"patents": "patent", "products": "product", "solutions": "solution", "patent": "patent", "product": "product", "solution": "solution"}
INDUSTRY_EVIDENCE_LEVELS = {"official", "measurement", "review-derived", "inferred"}

def infer_industry_evidence(record: dict[str, Any]) -> tuple[str, str]:
    record_type = record.get("record_type", "")
    source_url = (record.get("source_url") or "").lower()
    organization = record.get("organization", "unknown organization")
    if record_type == "patent" or "patents.google.com" in source_url:
        return "official", "public patent publication or patent-family search page"
    if "rtings.com" in source_url:
        return "measurement", "third-party headphone noise-isolation measurement/review source"
    if any(host in source_url for host in ["support.apple.com", "apple.com", "sony.com", "bose.com", "samsung.com"]):
        return "official", f"official {organization} public product/support material"
    if any(host in source_url for host in ["soundguys.com", "tomsguide.com", "audioxpress.com"]):
        return "review-derived", "third-party review or industry-news article"
    return "inferred", "seeded industry pointer without a recognized official or measurement source"

def normalize_industry_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    evidence_level = normalized.get("evidence_level")
    evidence_basis = normalized.get("evidence_basis")
    if evidence_level and evidence_level not in INDUSTRY_EVIDENCE_LEVELS:
        raise SystemExit(f"industry record has invalid evidence_level: {evidence_level}")
    if not evidence_level or not evidence_basis:
        inferred_level, inferred_basis = infer_industry_evidence(normalized)
        normalized.setdefault("evidence_level", inferred_level)
        normalized.setdefault("evidence_basis", inferred_basis)
    return normalized

def parse_industry_scope(value: str) -> set[str]:
    value = (value or "all").strip().lower()
    if value == "all":
        return set(INDUSTRY_SCOPES)
    raw_scope = {part.strip() for part in value.split(",") if part.strip()}
    unknown = raw_scope - set(INDUSTRY_SCOPE_ALIASES)
    if unknown:
        raise SystemExit(f"unknown industry scope: {', '.join(sorted(unknown))}; choose all, patents, products, solutions")
    scope = {INDUSTRY_SCOPE_ALIASES[p] for p in raw_scope}
    return scope

def load_industry_seed(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"industry seed not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("records", data) if isinstance(data, dict) else data
    if not isinstance(records, list):
        raise SystemExit("industry seed must be a JSON list or object with records")
    normalized_records = []
    for rec in records:
        if rec.get("record_type") not in INDUSTRY_SCOPES:
            raise SystemExit(f"industry record has invalid record_type: {rec.get('record_type')}")
        normalized_records.append(normalize_industry_record(rec))
    return normalized_records

def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")

def md_table(rows, cols):
    return table([{c: r.get(c, "") for c in cols} for r in rows], cols)

def evidence_legend() -> str:
    return """## 证据等级说明

- `official`: 厂商官方资料、公开支持页、产品页，或公开专利/专利族入口。
- `measurement`: 第三方测试机构或评测库提供的测量/测试页面，适合作为曲线基准入口。
- `review-derived`: 第三方评测、行业新闻或媒体转述，适合做线索但需要复核。
- `inferred`: 从已知产品定位、公开线索或 seed 备注推断，必须人工确认后再用于结论。

"""

def evidence_summary(records: list[dict[str, Any]]) -> str:
    counts = {level: 0 for level in sorted(INDUSTRY_EVIDENCE_LEVELS)}
    for rec in records:
        counts[rec.get("evidence_level", "inferred")] = counts.get(rec.get("evidence_level", "inferred"), 0) + 1
    rows = [{"evidence_level": level, "count": count} for level, count in counts.items() if count]
    if not rows:
        return ""
    return "## 当前证据等级分布\n\n" + md_table(rows, ["evidence_level", "count"]) + "\n"

def resolve_industry_output_dir(project_dir: str | None = None) -> Path:
    return Path(project_dir) / "industry" if project_dir else INDUSTRY

def write_industry_outputs(records: list[dict[str, Any]], query: str, scope: set[str], output_dir: Path | None = None, topic_label: str = "业界") -> None:
    output_dir = output_dir or INDUSTRY
    output_dir.mkdir(parents=True, exist_ok=True)
    normalized_records = [normalize_industry_record(rec) for rec in records]
    for rec in normalized_records:
        rec.setdefault("retrieved_at", now_utc())
        rec.setdefault("query", query)
    write_jsonl(output_dir / "industry_records.jsonl", normalized_records)
    patents = [r for r in normalized_records if r.get("record_type") == "patent"]
    products = [r for r in normalized_records if r.get("record_type") == "product"]
    solutions = [r for r in normalized_records if r.get("record_type") == "solution"]
    (output_dir / "patent_report.md").write_text(render_patent_report(patents, query, topic_label), encoding="utf-8")
    (output_dir / "solution_product_report.md").write_text(render_solution_product_report(solutions, products, query, topic_label), encoding="utf-8")
    (output_dir / "integrated_literature_industry_report.md").write_text(render_integrated_report(normalized_records, query, scope, topic_label), encoding="utf-8")
    print(f"industry outputs written to {output_dir}: {len(patents)} patents, {len(solutions)} solutions, {len(products)} products")

def render_patent_report(patents: list[dict[str, Any]], query: str, topic_label: str = "业界") -> str:
    rows = [{"year": p.get("year", ""), "organization": p.get("organization", ""), "identifier": p.get("identifier", ""), "title": p.get("title", ""), "themes": ", ".join(p.get("themes", [])), "evidence_level": p.get("evidence_level", ""), "evidence_basis": p.get("evidence_basis", ""), "source_url": p.get("source_url", "")} for p in patents]
    return "---\ntype: industry_patent_report\nstatus: knowledge_base_note\n---\n\n# " + topic_label + "专利知识库报告\n\n" + f"Query: `{query}`\n\n" + "本报告只整理公开专利/专利族检索入口和主题，不做侵权判断、法律意见或工程规避设计。\n\n" + evidence_legend() + evidence_summary(patents) + md_table(rows, ["year", "organization", "identifier", "title", "themes", "evidence_level", "evidence_basis", "source_url"])

def render_solution_product_report(solutions: list[dict[str, Any]], products: list[dict[str, Any]], query: str, topic_label: str = "业界") -> str:
    srows = [{"year": s.get("year", ""), "organization": s.get("organization", ""), "title": s.get("title", ""), "themes": ", ".join(s.get("themes", [])), "knowledge_note": s.get("knowledge_note", ""), "evidence_level": s.get("evidence_level", ""), "evidence_basis": s.get("evidence_basis", ""), "source_url": s.get("source_url", "")} for s in solutions]
    prows = [{"organization": p.get("organization", ""), "title": p.get("title", ""), "product_form": p.get("product_form", ""), "curve_design": p.get("curve_design", ""), "evidence_level": p.get("evidence_level", ""), "evidence_basis": p.get("evidence_basis", ""), "source_url": p.get("source_url", "")} for p in products]
    return "---\ntype: industry_solution_product_report\nstatus: knowledge_base_note\n---\n\n# " + topic_label + "方案与产品知识库报告\n\n" + f"Query: `{query}`\n\n" + evidence_legend() + evidence_summary(solutions + products) + "## 成熟方案/公开技术叙述\n\n" + md_table(srows, ["year", "organization", "title", "themes", "knowledge_note", "evidence_level", "evidence_basis", "source_url"]) + "\n## 产品与应用/产品设计线索（定性）\n\n" + "这些记录是产品/应用级设计线索，不替代第三方测量曲线、厂商私有算法或工程实现细节。\n\n" + md_table(prows, ["organization", "title", "product_form", "curve_design", "evidence_level", "evidence_basis", "source_url"])

def render_integrated_report(records: list[dict[str, Any]], query: str, scope: set[str], topic_label: str = "业界") -> str:
    products = [r for r in records if r.get("record_type") == "product"]
    patents = [r for r in records if r.get("record_type") == "patent"]
    solutions = [r for r in records if r.get("record_type") == "solution"]
    return f"""---
type: integrated_literature_industry_report
status: knowledge_base_note
---

# 文献与{topic_label}信息整合报告

Query: `{query}`  
Industry scope: `{', '.join(sorted(scope))}`

## 定位

这是知识库整合入口，用来把学术文献 vault 与业界公开信息（专利、方案、上市产品/应用）并排整理。它只做知识库并列索引，不提供实验执行方案、设备参数建议或法律意见。

## 当前业界记录规模

- Patents / patent-family entries: {len(patents)}
- Mature solution entries: {len(solutions)}
- Product curve-design entries: {len(products)}

{evidence_legend()}{evidence_summary(records)}

## 与文献库的连接方式

- 将文献主题、方法、评价指标与专利主题、成熟方案、上市产品/应用记录并排索引。
- 用 `themes`、`knowledge_note`、`evidence_level` 和 `source_url` 建立跨来源连接。
- 对需要数值曲线、参数、法规或法律判断的内容，只保留来源入口和复核提示。

## 知识库维护建议

- 专利记录只作为技术主题和检索入口，不从摘要推断权利要求覆盖范围。
- 每条 industry JSONL 记录必须保留 `evidence_level` 与 `evidence_basis`；前者用于排序可信度，后者说明为什么这样分级。
- 产品/应用设计线索只保留定性描述；如需数值曲线、参数或性能结论，应链接测量来源并单独记录方法版本。
- 上市产品信息变化快，建议每次更新时保留 retrieved_at 和 source_url。
"""

def cmd_industry(args):
    scope = parse_industry_scope(args.industry_scope)
    records = [r for r in load_industry_seed(Path(args.file)) if r.get("record_type") in scope]
    write_industry_outputs(records, query=args.query, scope=scope, output_dir=resolve_industry_output_dir(getattr(args, "project_dir", None)), topic_label=getattr(args, "topic_label", "业界"))

def cmd_update(args):
    cmd_search(args); cmd_fetch(args); cmd_summarize(args); cmd_organize(args); cmd_matrix(args); cmd_report(args)

def add_industry_options(p):
    p.add_argument("--include-industry", action="store_true", help="Also organize industry patents, mature solutions, and product/application evidence records.")
    p.add_argument("--industry-scope", default="all", help="Industry scope: all, patents, products, solutions, or comma-separated values.")
    p.add_argument("--industry-seed", default=str(ROOT / "seeds" / "industry_anc_benchmark_seed.json"), help="JSON seed for industry benchmark records.")
    p.add_argument("--project-dir", default="", help="Optional project directory. Industry outputs are written to <project-dir>/industry.")
    p.add_argument("--topic-label", default="业界", help="Topic label used in generated industry report titles.")

def build_parser():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd", required=True)
    for c in ["search","update"]:
        p=sub.add_parser(c); p.add_argument("--query", required=True); p.add_argument("--limit", type=int, default=10); add_industry_options(p); p.set_defaults(func=cmd_search if c=="search" else cmd_update)
    p=sub.add_parser("ingest"); p.add_argument("--file", required=True); p.add_argument("--query", default="manual-ingest"); p.set_defaults(func=cmd_ingest)
    p=sub.add_parser("industry"); p.add_argument("--file", default=str(ROOT / "seeds" / "industry_anc_benchmark_seed.json")); p.add_argument("--query", default="industry-anc-benchmark"); p.add_argument("--industry-scope", default="all"); p.add_argument("--project-dir", default=""); p.add_argument("--topic-label", default="业界"); p.set_defaults(func=cmd_industry)
    for c,fn in [("fetch",cmd_fetch),("summarize",cmd_summarize),("organize",cmd_organize),("matrix",cmd_matrix),("report",cmd_report)]:
        p=sub.add_parser(c); p.add_argument("--all", action="store_true"); p.set_defaults(func=fn)
    return ap

def main():
    args=build_parser().parse_args(); args.func(args)
if __name__ == "__main__": main()
