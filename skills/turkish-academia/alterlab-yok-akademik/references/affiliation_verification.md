# Affiliation verification — why YÖKSİS, and how to disambiguate

## Why YÖK Akademik is the authoritative TR affiliation source

YÖK Akademik is backed by **YÖKSİS** (the national Higher-Education Information
System). When a Turkish academic moves, changes title, or is appointed, the official
record flows through YÖKSİS — so the portal reflects the **current, official** kurum
(institution), fakülte/bölüm, and unvan (title).

For Turkish institutions this is **more reliable than ORCID or bibliographic-index
affiliation strings** (Crossref, Semantic Scholar), which:

- lag (authors update ORCID rarely; indexes copy affiliation from paper metadata
  that can be months/years stale),
- fragment one institution into many spellings (Turkish/English names, abbreviations,
  diacritic variants), and
- often show a *past* affiliation from an old paper rather than the person's current post.

So: for **"where does this person officially work right now?"** → YÖK Akademik. For
**"what has this person published, with which DOIs and co-authors?"** → the keyless
bibliography route below. The two are complementary: YÖK Akademik for the affiliation
ground truth, these sources for the bibliography.

1. **ORCID iD on the profile** (the header shows an ORCID badge when the person linked
   one): read the public ORCID record, `https://pub.orcid.org/v3.0/<ORCID>/works` with
   `Accept: application/json`, and Crossref's works for that iD,
   `https://api.crossref.org/works?filter=orcid:<ORCID>` (DOIs, venues,
   `is-referenced-by-count`). Both are keyless and need no contact address. Both list
   only what the person or the publishers deposited, so treat them as incomplete.
2. **No ORCID iD**: search by name and institution with `alterlab-research-lookup`, or
   Crossref's `query.author=<name>&query.affiliation=<institution>`, and confirm each
   work is this person's. Common Turkish surnames collide, and the affiliation query
   matches only deposited affiliation strings.
3. **Turkish-language journals** often carry no DOI or ORCID link: check them in TR Dizin
   (`alterlab-trdizin`) and DergiPark (`alterlab-dergipark`).

No keyless source gives a complete, deduplicated publication list for a person; say so
when you report one.

## When you actually need this

- **Authorship bylines** — confirming the affiliation line for a Turkish co-author
  before submission.
- **Recommendation letters** — verifying the candidate's (or referee's) current title
  and institution. (This skill only supplies the verified affiliation that goes into the
  letter; it does not draft the letter itself.)
- **Grant teams / editorial boards** — confirming a named person's post and unvan.

## Disambiguation checklist (do this every time)

1. **Search** the normalized name (see `turkish_names.md`).
2. If **>1 candidate**, present a table — *name · unvan · university · faculty/dept* —
   and ask which one, or confirm the institution the user expected.
3. **Watch for common-name collisions**: Yılmaz, Demir, Kaya, Şahin, Çelik return
   many people. A bare name match is *not* a confirmation.
4. **Cross-check the unvan against the claim**: if the user calls someone "Professor"
   but YÖKSİS shows *Dr. Öğr. Üyesi*, surface the discrepancy rather than smoothing it.
5. **Report with provenance**: "Per YÖK Akademik (YÖKSİS), as of <date>: <Unvan>,
   <Bölüm>, <Fakülte>, <Üniversite>." People move — the date matters.
6. **If the portal failed** (302/500, markup change, no match), say so and fall back to
   WebFetch on the search page. **Never** fabricate an affiliation, title, or authorId.

## What this skill does NOT decide

It does not judge research quality, compute **doçentlik** points
(`alterlab-docentlik-eligibility`) or **akademik teşvik** scores
(`alterlab-akademik-tesvik`), and it does not fetch thesis full text
(`alterlab-yok-tez`). It establishes *identity and current affiliation*, full stop.
