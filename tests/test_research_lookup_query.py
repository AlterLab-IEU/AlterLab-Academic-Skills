"""alterlab-research-lookup's keyless scholarly backend: query handling, dedup, ranking, dates.

Covers the repairs to scripts/scholarly_backend.py:

  B1  Unicode-preserving tokenization (Turkish, accented names, Greek, CJK, Devanagari, mixed).
  B2  Explicit search syntax (--terms or quotes / AND / OR / NOT / parentheses / leading '-') is
      parsed into an expression tree and translated per index; an index that cannot express it
      is skipped or labelled approximate in ``query_translation``; malformed syntax is an error
      (--terms) or a disclosed plain-word fallback (natural-language query).
  B3  Dedup by DOI, then arXiv id / PMID / PMCID, then full Unicode title + year (+-1) + first
      author; never on an empty key; provenance kept in ``merged_from``.
  B4  Default order is relevance; "cited" orders by ONE declared index's count; a graded
      relevance fixture (agent-labelled, awaiting human review) is scored with nDCG@k.
  B5  --since / --until reach every index and are re-checked on the returned dates; "recent"
      is never turned into a date filter, and a year in the topic is never a filter.

No test touches the network: every request goes to an in-memory router.
"""

from __future__ import annotations

import importlib
import json
import math
import re
import sys
import unicodedata
import urllib.parse
from pathlib import Path
from xml.sax.saxutils import escape

import pytest

SKILL = (Path(__file__).resolve().parent.parent / "skills" / "research-tools"
         / "alterlab-research-lookup")
SCRIPTS = SKILL / "scripts"
FIXTURE = SKILL / "evals" / "fixtures" / "relevance_fixture.json"
sys.path.insert(0, str(SCRIPTS))
sb = importlib.import_module("scholarly_backend")
rl = importlib.import_module("research_lookup")


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    monkeypatch.setattr(sb, "_S2_PAUSED_UNTIL", 0.0)
    monkeypatch.setattr(sb.time, "sleep", lambda s: None)

    def no_network(*a, **k):
        pytest.fail("test attempted network access")

    monkeypatch.setattr(sb.urllib.request, "urlopen", no_network)


# --------------------------------------------------------------------------------------------
# A fake transport that answers each index from neutral record dicts
# --------------------------------------------------------------------------------------------

def _crossref_item(r):
    item = {"title": [r["title"]], "is-referenced-by-count": r.get("cites", {}).get("crossref", 0),
            "author": [{"family": a.split(",")[0], "given": a.split(",")[-1].strip()}
                       for a in r.get("authors", [])],
            "container-title": [r.get("venue", "")], "URL": r.get("url", "u")}
    if r.get("doi"):
        item["DOI"] = r["doi"]
    if r.get("date"):
        item["issued"] = {"date-parts": [[int(p) for p in r["date"].split("-")]]}
    elif r.get("year"):
        item["issued"] = {"date-parts": [[r["year"]]]}
    return item


def _epmc_item(r):
    item = {"title": r["title"], "authorList": {"author": [{"fullName": a} for a in r.get("authors", [])]},
            "citedByCount": r.get("cites", {}).get("europepmc", 0), "source": "MED",
            "id": r.get("pmid") or "PPR0", "abstractText": r.get("abstract", "")}
    if r.get("year"):
        item["pubYear"] = str(r["year"])
    for k in ("doi", "pmid", "pmcid"):
        if r.get(k):
            item[k] = r[k]
    if r.get("date"):
        item["firstPublicationDate"] = r["date"]
    return item


def _arxiv_entry(r):
    when = r.get("date") or (f"{r['year']}-01-15" if r.get("year") else "")
    doi = f"<arxiv:doi>{escape(r['journal_doi'])}</arxiv:doi>" if r.get("journal_doi") else ""
    return (f"<entry><id>http://arxiv.org/abs/{r['arxiv_id']}v1</id>"
            f"<title>{escape(r['title'])}</title>"
            + (f"<published>{when}T00:00:00Z</published>" if when else "")
            + f"<summary>{escape(r.get('abstract', 's'))}</summary>{doi}"
            + "".join(f"<author><name>{escape(a)}</name></author>" for a in r.get("authors", []))
            + "</entry>")


def _s2_item(r):
    ext = {}
    if r.get("doi"):
        ext["DOI"] = r["doi"]
    if r.get("arxiv_id"):
        ext["ArXiv"] = r["arxiv_id"]
    if r.get("pmid"):
        ext["PubMed"] = r["pmid"]
    return {"title": r["title"], "year": r.get("year"), "venue": r.get("venue", ""),
            "externalIds": ext, "citationCount": r.get("cites", {}).get("semanticscholar", 0),
            "authors": [{"name": a} for a in r.get("authors", [])], "url": "s2",
            "publicationDate": r.get("date")}


def router(crossref=(), europepmc=(), arxiv=(), semanticscholar=(), calls=None):
    """A fake ``get`` answering each index from lists of neutral record dicts."""
    calls = [] if calls is None else calls

    def get(url: str) -> bytes:
        calls.append(url)
        host = urllib.parse.urlsplit(url).hostname
        if host == "api.crossref.org":
            return json.dumps({"message": {"items": [_crossref_item(r) for r in crossref]}}).encode()
        if host == "www.ebi.ac.uk":
            return json.dumps({"resultList": {"result": [_epmc_item(r) for r in europepmc]}}).encode()
        if host == "export.arxiv.org":
            return ('<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom" '
                    'xmlns:arxiv="http://arxiv.org/schemas/atom">'
                    + "".join(_arxiv_entry(r) for r in arxiv) + "</feed>").encode()
        if host == "api.semanticscholar.org":
            return json.dumps({"data": [_s2_item(r) for r in semanticscholar]}).encode()
        pytest.fail(f"unexpected host contacted: {url}")

    return get, calls


def params(calls, host):
    """Decoded query parameters of every request sent to ``host``."""
    return [dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(u).query))
            for u in calls if urllib.parse.urlsplit(u).hostname == host]


# --------------------------------------------------------------------------------------------
# B1 Unicode-preserving tokenization
# --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("query, expected", [
    ("öz-yeterlik and öğrenme", "öz-yeterlik öğrenme"),
    ("find papers on İstanbul depremi ve ılık iklim", "İstanbul depremi ve ılık iklim"),
    ("papers by Gödel and Ångström on Lévy flights", "Gödel Ångström Lévy flights"),
    ("Μάθηση και μνήμη στην εκπαίδευση", "Μάθηση και μνήμη στην εκπαίδευση"),
    ("find papers on 学习与记忆 and retrieval practice", "学习与记忆 retrieval practice"),
    ("research on Μάθηση in the classroom with 記憶", "Μάθηση classroom 記憶"),
    ("शिक्षा में स्मृति", "शिक्षा में स्मृति"),
    ("COVID-19 and C++ compilers", "COVID-19 C++ compilers"),
])
def test_search_terms_keep_every_script(query, expected):
    assert sb.search_terms(query) == expected


def test_search_terms_compose_decomposed_accents_without_dropping_them():
    decomposed = unicodedata.normalize("NFD", "Gödel incompleteness")
    assert sb.search_terms(decomposed) == "Gödel incompleteness"


def test_unicode_words_reach_the_index_unchanged():
    get, calls = router()
    sb.search("öz-yeterlik and öğrenme", limit=3, sources=["crossref", "europepmc"], get=get)
    assert params(calls, "api.crossref.org")[0]["query.bibliographic"] == "öz-yeterlik öğrenme"
    epmc = params(calls, "www.ebi.ac.uk")[0]["query"]
    assert "öğrenme" in epmc and '"öz-yeterlik"' in epmc


# --------------------------------------------------------------------------------------------
# B2 explicit search syntax
# --------------------------------------------------------------------------------------------

def _translations(terms=None, query="find papers"):
    get, calls = router()
    res = sb.search(query, limit=3, terms=terms, get=get)
    return res, calls


def test_or_is_kept_as_or_in_arxiv_and_europepmc():
    res, calls = _translations(terms='"testing effect" OR "retrieval practice"')
    assert params(calls, "export.arxiv.org")[0]["search_query"] == \
        'all:"testing effect" OR all:"retrieval practice"'
    assert params(calls, "www.ebi.ac.uk")[0]["query"] == \
        'TITLE_ABS:("testing effect" OR "retrieval practice")'
    qt = res["query_translation"]
    assert qt["arxiv"]["mode"] == "exact" and qt["europepmc"]["mode"] == "exact"
    assert qt["crossref"]["mode"] == "approximate" and qt["semanticscholar"]["mode"] == "approximate"
    assert params(calls, "api.crossref.org")[0]["query.bibliographic"] == \
        "testing effect retrieval practice"
    assert "OR" in qt["crossref"]["note"]


def test_or_in_a_plain_query_is_detected_without_terms():
    res, calls = _translations(query="cancer OR diabetes")
    assert params(calls, "export.arxiv.org")[0]["search_query"] == "all:cancer OR all:diabetes"
    assert res["syntax"] == "query-syntax"
    assert sb.search_terms("cancer OR diabetes") == "cancer diabetes"  # word cleanup only


def test_or_binds_tighter_than_implicit_and():
    _, calls = _translations(query="effects of exercise on depression OR anxiety")
    assert params(calls, "export.arxiv.org")[0]["search_query"] == \
        "all:effects AND all:exercise AND (all:depression OR all:anxiety)"


def test_not_is_translated_or_the_index_is_skipped_with_a_reason():
    res, calls = _translations(terms='"retrieval practice" NOT fear')
    assert params(calls, "export.arxiv.org")[0]["search_query"] == \
        'all:"retrieval practice" ANDNOT all:fear'
    assert params(calls, "www.ebi.ac.uk")[0]["query"] == \
        'TITLE_ABS:("retrieval practice" AND NOT fear)'
    qt = res["query_translation"]
    assert qt["crossref"]["mode"] == "skipped" and qt["semanticscholar"]["mode"] == "skipped"
    assert "exclu" in qt["crossref"]["note"]
    assert not params(calls, "api.crossref.org") and not params(calls, "api.semanticscholar.org")
    assert set(res["skipped"]) == {"crossref", "semanticscholar"}
    md = sb.to_markdown(res)
    assert "skipped: crossref, semanticscholar" in md and "crossref: skipped" in md


def test_leading_minus_excludes_a_term_but_negative_numbers_stay_terms():
    _, calls = _translations(query="memory consolidation -rodent")
    assert params(calls, "export.arxiv.org")[0]["search_query"] == \
        "(all:memory AND all:consolidation) ANDNOT all:rodent"
    _, calls = _translations(query="storage at -80 C (plasma)")
    assert "ANDNOT" not in params(calls, "export.arxiv.org")[0]["search_query"]


def test_nested_parentheses_and_phrases():
    res, calls = _translations(terms='(memory OR learning) AND (sleep OR "slow wave") NOT rodent')
    assert params(calls, "export.arxiv.org")[0]["search_query"] == (
        '((all:memory OR all:learning) AND (all:sleep OR all:"slow wave")) ANDNOT all:rodent')
    assert params(calls, "www.ebi.ac.uk")[0]["query"] == (
        'TITLE_ABS:((memory OR learning) AND (sleep OR "slow wave") AND NOT rodent)')
    assert res["terms"] == '(memory OR learning) AND (sleep OR "slow wave") AND NOT rodent'


def test_approximate_only_records_are_labelled_in_markdown():
    rec = {"title": "Testing effect in schools", "doi": "10.5555/x.1", "year": 2020,
           "authors": ["Ng, A."]}
    get, _ = router(crossref=[rec])
    res = sb.search("x", terms='"testing effect" OR "retrieval practice"', get=get)
    md = sb.to_markdown(res)
    assert "crossref: approximate" in md
    assert "approximate query only" in md


@pytest.mark.parametrize("bad, why", [
    ('"testing effect OR retrieval', "unbalanced"),
    ("(memory OR learning", "parenthes"),
    ("memory OR learning)", "parenthes"),
    ("memory OR", "OR"),
    ("AND memory", "AND"),
    ("()", "empty"),
    ('""', "empty"),
    ("NOT fear", "excluded"),
    ("memory OR -fear", "excluded"),
    ("memory or learning", "OR"),
])
def test_malformed_terms_raise_a_clear_error(bad, why):
    get, calls = router()
    with pytest.raises(sb.QuerySyntaxError, match=re.compile(why, re.I)):
        sb.search("find papers", terms=bad, get=get)
    assert calls == []


def test_malformed_terms_exit_2_from_the_cli(capsys):
    assert sb.main(["find papers", "--terms", '"testing effect']) == 2
    assert "unbalanced" in capsys.readouterr().err


def test_malformed_syntax_in_a_plain_query_falls_back_to_words_and_says_so():
    get, calls = router()
    res = sb.search("effects of vitamin D (25(OH)D on bone", get=get)
    assert res["syntax"] == "natural"
    assert any("could not be parsed" in n for n in res["notes"])
    assert params(calls, "api.crossref.org")[0]["query.bibliographic"] == \
        "effects vitamin D 25 OH D bone"
    assert "could not be parsed" in sb.to_markdown(res)


def test_terms_skip_the_routing_word_filter():
    _, calls = _translations(terms="papers on memory")
    assert params(calls, "export.arxiv.org")[0]["search_query"] == \
        "all:papers AND all:on AND all:memory"


def test_every_terms_example_in_the_docs_parses():
    docs = [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md")),
            SCRIPTS / "research_lookup.py"]
    examples = [m for p in docs for m in re.findall(r"--terms '([^']+)'", p.read_text("utf-8"))]
    assert examples, "no --terms example found in the docs"
    for ex in examples:
        sb.parse_query(ex, strict=True)


def test_research_lookup_terms_follow_the_same_contract(monkeypatch):
    get, calls = router(crossref=[{"title": "Test-enhanced learning", "doi": "10.5555/t.1",
                                   "year": 2006, "authors": ["Roediger, H."]}])
    monkeypatch.setattr(sb, "_http_get", get)
    monkeypatch.delenv("PARALLEL_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    out = rl.ResearchLookup(terms='"testing effect" OR "retrieval practice"').lookup("find papers")
    assert out["success"] and out["query_translation"]["crossref"]["mode"] == "approximate"
    assert params(calls, "export.arxiv.org")[0]["search_query"] == \
        'all:"testing effect" OR all:"retrieval practice"'
    with pytest.raises(sb.QuerySyntaxError):
        rl.ResearchLookup(terms='"unbalanced').lookup("find papers")


# --------------------------------------------------------------------------------------------
# B3 dedup
# --------------------------------------------------------------------------------------------

_PREFIX = ("A longitudinal investigation of retrieval practice, spacing and interleaving "
           "in secondary-school mathematics classrooms")


def test_long_titles_sharing_a_prefix_stay_separate():
    a = {"title": _PREFIX + ": effects on algebra", "year": 2020, "authors": ["Kim, J."]}
    b = {"title": _PREFIX + ": effects on geometry", "year": 2020, "authors": ["Kim, J."]}
    get, _ = router(crossref=[a], europepmc=[b])
    res = sb.search("x", sources=["crossref", "europepmc"], get=get)
    assert len(res["records"]) == 2


def test_non_latin_titles_never_merge_on_an_empty_key():
    a = {"title": "学习与记忆", "year": 2020, "authors": ["王, 明"]}
    b = {"title": "Μάθηση", "year": 2020, "authors": ["Παππάς, Γ."]}
    get, _ = router(crossref=[a], europepmc=[b])
    res = sb.search("x", sources=["crossref", "europepmc"], get=get)
    assert sorted(r["title"] for r in res["records"]) == ["Μάθηση", "学习与记忆"]


def test_punctuation_only_titles_never_merge():
    get, _ = router(crossref=[{"title": "—", "year": 2020}], europepmc=[{"title": "?", "year": 2020}])
    res = sb.search("x", sources=["crossref", "europepmc"], get=get)
    assert len(res["records"]) == 2


def test_same_work_without_a_doi_merges_by_title_year_and_author_with_provenance():
    a = {"title": "The Critical Importance of Retrieval for Learning", "doi": "10.5555/k.1",
         "year": 2008, "authors": ["Karpicke, J."], "cites": {"crossref": 700}}
    b = {"title": "The critical importance of retrieval for learning.", "year": 2009,
         "authors": ["Karpicke JD"], "pmid": "18276894", "cites": {"europepmc": 650}}
    get, _ = router(crossref=[a], europepmc=[b])
    res = sb.search("x", sources=["crossref", "europepmc"], get=get)
    assert len(res["records"]) == 1
    rec = res["records"][0]
    assert rec["cited_by"] == {"crossref": 700, "europepmc": 650}
    assert rec["pmid"] == "18276894" and rec["doi"] == "10.5555/k.1"
    assert [m["source"] for m in rec["merged_from"]] == ["crossref", "europepmc"]
    assert rec["merged_from"][1]["matched_on"] == "title+year+author"
    assert rec["merged_from"][1]["title"] == "The critical importance of retrieval for learning."


@pytest.mark.parametrize("b_year, b_author", [(2015, "Karpicke, J."), (2008, "Smith, A.")])
def test_same_title_but_different_year_or_author_stays_separate(b_year, b_author):
    a = {"title": "Introduction", "year": 2008, "authors": ["Karpicke, J."], "doi": "10.5555/i.1"}
    b = {"title": "Introduction", "year": b_year, "authors": [b_author]}
    get, _ = router(crossref=[a], europepmc=[b])
    assert len(sb.search("x", sources=["crossref", "europepmc"], get=get)["records"]) == 2


def test_preprint_and_journal_version_with_different_dois_stay_separate():
    title = "Retrieval practice at scale"
    journal = {"title": title, "doi": "10.5555/j.1", "year": 2022, "authors": ["Author, A."],
               "cites": {"crossref": 40}}
    preprint = {"title": title, "arxiv_id": "2101.00001", "year": 2021, "authors": ["A. Author"]}
    s2 = {"title": title, "doi": "10.5555/j.1", "arxiv_id": "2101.00001", "year": 2022,
          "authors": ["A. Author"], "cites": {"semanticscholar": 55}}
    get, _ = router(crossref=[journal], arxiv=[preprint], semanticscholar=[s2])
    res = sb.search("x", get=get)
    by_doi = {r["doi"]: r for r in res["records"]}
    assert set(by_doi) == {"10.5555/j.1", "10.48550/arxiv.2101.00001"}
    assert set(by_doi["10.5555/j.1"]["found_in"]) == {"crossref", "semanticscholar"}
    assert "10.48550/arxiv.2101.00001" in by_doi["10.5555/j.1"]["related_versions"]


def test_provider_ids_merge_records_without_dois():
    a = {"title": "Retrieval and learning: a randomized trial", "pmid": "123", "year": 2010,
         "authors": ["Lee, K."]}
    b = {"title": "Retrieval & learning - a randomised trial", "pmid": "123", "year": 2010,
         "authors": ["K. Lee"]}
    get, _ = router(europepmc=[a], semanticscholar=[b])
    res = sb.search("x", sources=["europepmc", "semanticscholar"], get=get)
    assert len(res["records"]) == 1
    assert res["records"][0]["merged_from"][1]["matched_on"] == "pmid"


# --------------------------------------------------------------------------------------------
# B4 ranking
# --------------------------------------------------------------------------------------------

def test_default_order_is_relevance_everywhere(monkeypatch):
    rec = {"title": "Retrieval practice in class", "doi": "10.5555/r.1", "year": 2019,
           "authors": ["Arslan, M."]}
    off = {"title": "Exposure therapy and fear memory retrieval", "doi": "10.5555/e.1",
           "year": 2008, "authors": ["Brandt, K."], "cites": {"crossref": 5000}}
    get, _ = router(crossref=[rec, off])
    res = sb.search("retrieval practice", get=get)
    assert res["rank"] == "relevance"
    assert [r["doi"] for r in res["records"]] == ["10.5555/r.1", "10.5555/e.1"]
    assert rl.ResearchLookup().rank == "relevance"
    with pytest.raises(SystemExit):
        sb.main(["x", "--rank", "auto"])


def test_cited_orders_by_one_declared_index_not_the_max_across_indexes():
    a = {"title": "A", "doi": "10.5555/a", "year": 2010, "authors": ["X, Y."],
         "cites": {"crossref": 100, "semanticscholar": 5000}}
    b = {"title": "B", "doi": "10.5555/b", "year": 2010, "authors": ["Z, Y."],
         "cites": {"crossref": 500}}
    c = {"title": "C", "pmid": "9", "year": 2010, "authors": ["Q, R."], "cites": {"europepmc": 9000}}
    get, _ = router(crossref=[a, b], europepmc=[c], semanticscholar=[a])
    res = sb.search("x", rank="cited", get=get)
    assert [r["title"] for r in res["records"]] == ["B", "A", "C"]
    assert res["cite_index"] == "crossref"
    assert "records without a crossref count follow" in res["rank_basis"]
    assert res["records"][1]["cited_by"] == {"crossref": 100, "semanticscholar": 5000}
    res = sb.search("x", rank="cited", cite_index="europepmc", get=get)
    assert res["records"][0]["title"] == "C"
    assert "europepmc citation count" in sb.to_markdown(res)


def _load_fixture():
    return json.loads(FIXTURE.read_text("utf-8"))


def fixture_router(q):
    recs = q["records"]
    return router(**{src: [recs[i] for i in ids] for src, ids in q["order"].items()})


def _fixture_id(q, rec):
    for fid, r in q["records"].items():
        if (r.get("doi") and r["doi"] == rec["doi"]) or (
                r.get("arxiv_id") and r["arxiv_id"] in (rec.get("url") or "")) or (
                not r.get("doi") and r["title"] == rec["title"]):
            return fid
    raise AssertionError(f"record not in fixture: {rec['title']}")


def ndcg_at_k(ranked_ids, labels, k):
    def dcg(gains):
        return sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(gains[:k]))
    ideal = dcg(sorted(labels.values(), reverse=True))
    return dcg([labels.get(i, 0) for i in ranked_ids]) / ideal if ideal else 0.0


def fixture_scores(**search_kw):
    fx = _load_fixture()
    out = {}
    for q in fx["queries"]:
        get, _ = fixture_router(q)
        res = sb.search(q["query"], limit=10, get=get, **search_kw)
        ranked = [_fixture_id(q, r) for r in res["records"]]
        out[q["id"]] = (round(ndcg_at_k(ranked, q["labels"], fx["k"]), 3), ranked)
    return out


def test_relevance_fixture_is_labelled_honestly():
    fx = _load_fixture()
    assert "awaiting independent human review" in fx["_status"]
    assert "implementing agent" in fx["_status"]
    for q in fx["queries"]:
        assert set(q["labels"]) == set(q["records"])
        assert all(0 <= g <= 3 for g in q["labels"].values())


def test_ndcg_on_the_relevance_fixture(capsys):
    """Deterministic offline nDCG@k of the default and the cited orderings on the fixture."""
    default, cited = fixture_scores(), fixture_scores(rank="cited")
    with capsys.disabled():
        for qid in default:
            print(f"\n[nDCG@5] {qid}: default(relevance)={default[qid][0]} "
                  f"cited(crossref)={cited[qid][0]}  default order={default[qid][1]}")
    assert all(0.0 <= s <= 1.0 for s, _ in [*default.values(), *cited.values()])
    rp = default["retrieval-practice"][1]
    assert rp.index("R1") < rp.index("E1") and rp.index("R2") < rp.index("I1")
    assert fixture_scores() == default  # deterministic


# --------------------------------------------------------------------------------------------
# B5 dates
# --------------------------------------------------------------------------------------------

def test_since_until_reach_every_index():
    get, calls = router()
    res = sb.search("retrieval practice", since="2020", until="2021-06-30", get=get)
    assert "from-pub-date:2020-01-01" in params(calls, "api.crossref.org")[0]["filter"]
    assert "until-pub-date:2021-06-30" in params(calls, "api.crossref.org")[0]["filter"]
    assert params(calls, "www.ebi.ac.uk")[0]["query"].endswith(
        " AND FIRST_PDATE:[2020-01-01 TO 2021-06-30]")
    assert params(calls, "export.arxiv.org")[0]["search_query"].endswith(
        " AND submittedDate:[202001010000 TO 202106302359]")
    assert params(calls, "api.semanticscholar.org")[0]["year"] == "2020-2021"
    assert res["date_filter"]["since"] == "2020-01-01"


def test_out_of_range_records_are_dropped_and_unknown_dates_flagged():
    recs = [{"title": "Old work", "doi": "10.5555/o", "year": 1995, "authors": ["A, B."]},
            {"title": "In range", "doi": "10.5555/i", "date": "2021-03-01", "authors": ["C, D."]},
            {"title": "Late in until year", "doi": "10.5555/l", "date": "2021-09-01",
             "authors": ["E, F."]},
            {"title": "Undated", "doi": "10.5555/u", "authors": ["G, H."]}]
    get, _ = router(crossref=recs)
    res = sb.search("x", sources=["crossref"], since="2020", until="2021-06-30", get=get)
    titles = [r["title"] for r in res["records"]]
    assert titles == ["In range", "Undated"]
    assert res["date_filter"]["dropped_out_of_range"] == 2
    assert res["date_filter"]["kept_unknown_date"] == 1
    assert res["records"][1]["date_unknown"] is True
    md = sb.to_markdown(res)
    assert "2 record(s) outside" in md and "date unknown" in md


@pytest.mark.parametrize("since, until", [("2020-13-01", None), ("20", None), ("2022", "2020"),
                                          (None, "next year")])
def test_invalid_dates_are_rejected(since, until, capsys):
    get, calls = router()
    with pytest.raises(ValueError):
        sb.search("x", since=since, until=until, get=get)
    assert calls == []
    argv = ["x"] + (["--since", since] if since else []) + (["--until", until] if until else [])
    assert sb.main(argv) == 2


def test_recent_is_not_turned_into_a_date_filter_and_says_so():
    old = {"title": "Retrieval practice classic", "doi": "10.5555/c", "year": 1995,
           "authors": ["A, B."]}
    get, calls = router(crossref=[old])
    res = sb.search("recent work on retrieval practice", get=get)
    assert "filter" not in params(calls, "api.crossref.org")[0] or \
        "pub-date" not in params(calls, "api.crossref.org")[0]["filter"]
    assert res["date_filter"] is None and res["records"][0]["year"] == 1995
    note = " ".join(res["notes"])
    assert "not converted into a date filter" in note and "--since" in note
    assert "not converted into a date filter" in sb.to_markdown(res)


def test_a_year_in_the_topic_is_a_search_word_not_a_filter():
    get, calls = router()
    res = sb.search("COVID-19 2020 lockdown", get=get)
    cr = params(calls, "api.crossref.org")[0]
    assert cr["query.bibliographic"] == "COVID-19 2020 lockdown"
    assert "pub-date" not in cr.get("filter", "")
    assert "year" not in params(calls, "api.semanticscholar.org")[0]
    assert res["date_filter"] is None and not res["notes"]


def test_research_lookup_passes_dates_through(monkeypatch):
    get, calls = router()
    monkeypatch.setattr(sb, "_http_get", get)
    monkeypatch.delenv("PARALLEL_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    rl.ResearchLookup(since="2020", until="2021").lookup("find papers on retrieval practice")
    assert "from-pub-date:2020-01-01,until-pub-date:2021-12-31" in \
        params(calls, "api.crossref.org")[0]["filter"]


def test_scholarly_only_options_route_to_scholarly_and_refuse_a_forced_keyed_backend(monkeypatch):
    get, calls = router()
    monkeypatch.setattr(sb, "_http_get", get)
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    monkeypatch.delenv("PARALLEL_API_KEY", raising=False)
    out = rl.ResearchLookup(since="2020").lookup("find papers on retrieval practice")
    assert out["backend"] == "scholarly"
    with pytest.raises(ValueError, match="only to the scholarly backend"):
        rl.ResearchLookup(force_backend="perplexity", since="2020").lookup("find papers on x")


def test_research_lookup_cli_exposes_since_until_and_relevance_default(monkeypatch, capsys):
    get, calls = router(crossref=[{"title": "In range", "doi": "10.5555/i", "year": 2021,
                                   "authors": ["C, D."]}])
    monkeypatch.setattr(sb, "_http_get", get)
    monkeypatch.delenv("PARALLEL_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", ["research_lookup.py", "find papers on retrieval practice",
                                      "--since", "2021", "--json"])
    assert rl.main() == 0
    out = json.loads(capsys.readouterr().out)[0]
    assert out["rank"] == "relevance" and out["date_filter"]["since"] == "2021-01-01"
    assert "from-pub-date:2021-01-01" in params(calls, "api.crossref.org")[0]["filter"]

