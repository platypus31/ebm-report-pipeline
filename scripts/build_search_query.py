#!/usr/bin/env python3
"""
從 PICO YAML 自動建構 PubMed 搜尋策略。

用法：
    python3 scripts/build_search_query.py --project <name>
    python3 scripts/build_search_query.py --pico pico.yaml --type therapeutic
    python3 scripts/build_search_query.py --project <name> --years 5 --lang en
    python3 scripts/build_search_query.py --project <name> --url
    python3 scripts/build_search_query.py --project <name> --expand
    python3 scripts/build_search_query.py --department 腎臟內科

讀取 pico.yaml，組合 MeSH terms 為 PubMed Boolean 搜尋式，
並依問題類型加上 publication type filter。
"""

import argparse
import re
import sys
import urllib.parse
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# ── Fallback chain: 每個問題類型按證據等級排列搜尋篩選器 ──
# tier 0 = 最高證據等級（優先搜尋）
# tier 1 = 次高（tier 0 結果不足時放寬）
# tier 2 = 第三層（再放寬）
# 使用時：先用 tier 0 搜尋，結果 < 閾值 → 合併 tier 0+1，仍不足 → 合併全部
PUB_FILTER_CHAIN: dict[str, list[str]] = {
    # 治療型：SR/MA of RCTs → RCT → Cohort → Case-control / Case series
    "therapeutic": [
        '(Meta-Analysis[pt] OR Systematic Review[pt] OR Randomized Controlled Trial[pt])',
        '(Controlled Clinical Trial[pt] OR Cohort Studies[MeSH])',
        '(Case-Control Studies[MeSH] OR Observational Study[pt])',
    ],
    # 預防型：同治療型
    "preventive": [
        '(Meta-Analysis[pt] OR Systematic Review[pt] OR Randomized Controlled Trial[pt])',
        '(Controlled Clinical Trial[pt] OR Cohort Studies[MeSH])',
        '(Case-Control Studies[MeSH] OR Observational Study[pt])',
    ],
    # 診斷型：Prospective blind + gold standard → Cross-sectional / Retrospective → Case-control
    "diagnostic": [
        (
            '(Systematic Review[pt] OR Meta-Analysis[pt]'
            ' OR ((Sensitivity and Specificity[MeSH]) AND (Prospective Studies[MeSH]'
            ' OR Cross-Sectional Studies[MeSH]) AND (Reference Standards[MeSH])))'
        ),
        '((Sensitivity and Specificity[MeSH]) OR (Cross-Sectional Studies[MeSH]))',
        '(Case-Control Studies[MeSH] OR Observational Study[pt])',
    ],
    # 預後型：Cohort → Case-control → Case series
    "prognostic": [
        '(Systematic Review[pt] OR Meta-Analysis[pt] OR Cohort Studies[MeSH] OR Prognosis[MeSH])',
        '(Case-Control Studies[MeSH])',
        '(Observational Study[pt] OR Case Reports[pt])',
    ],
    # 病因傷害型：Cohort → Case-control → Case series
    "etiology_harm": [
        '(Systematic Review[pt] OR Meta-Analysis[pt] OR Cohort Studies[MeSH])',
        '(Case-Control Studies[MeSH] OR Risk Factors[MeSH])',
        '(Observational Study[pt] OR Case Reports[pt])',
    ],
}

# 向後相容：PUB_FILTERS = 各類型 tier 0（最嚴格）
PUB_FILTERS = {k: v[0] for k, v in PUB_FILTER_CHAIN.items()}

LANG_FILTERS = {
    "en": "English[lang]",
    "zh": "(Chinese[lang] OR English[lang])",
}


def _expand_mesh_term(term: str) -> str:
    """Expand a single MeSH term to include title/abstract search for better recall.

    Input:  '"Kidney Diseases"[MeSH]'
    Output: '("Kidney Diseases"[MeSH] OR "Kidney Diseases"[tiab])'

    Input:  'Kidney Diseases[MeSH]'
    Output: '("Kidney Diseases"[MeSH] OR "Kidney Diseases"[tiab])'

    Terms without [MeSH] qualifier are returned as-is.
    """
    # Match: optional quotes, term name, [MeSH] qualifier
    m = re.match(r'^"?([^"[\]]+)"?\[MeSH\]$', term.strip())
    if not m:
        return term
    name = m.group(1).strip()
    return f'("{name}"[MeSH] OR "{name}"[tiab])'


def _expand_terms(terms: list[str], expand: bool) -> list[str]:
    """Optionally expand a list of MeSH terms with tiab synonyms."""
    if not expand:
        return terms
    return [_expand_mesh_term(t) for t in terms]


def parse_departments(filepath: Path | None = None) -> dict[str, dict]:
    """Parse data/departments.md into a lookup dict.

    Returns dict keyed by abbreviation, Chinese name, and English name,
    all pointing to the same record:
        {"abbr": "NEPH", "zh": "腎臟內科", "en": "Nephrology",
         "mesh_terms": ['"Kidney Diseases"[MeSH]', '"Renal Dialysis"[MeSH]']}
    """
    if filepath is None:
        filepath = Path(__file__).resolve().parent.parent / "data" / "departments.md"
    if not filepath.exists():
        return {}

    departments: dict[str, dict] = {}
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|") or line.startswith("| #") or line.startswith("|---"):
                continue
            cols = [c.strip() for c in line.split("|")]
            # cols: ['', '#', '縮寫', '科別', 'English', 'MeSH Terms', '']
            cols = [c for c in cols if c]
            if len(cols) < 5:
                continue
            try:
                int(cols[0])  # skip non-data rows
            except ValueError:
                continue
            abbr = cols[1]
            zh = cols[2]
            en = cols[3]
            mesh_raw = cols[4]
            # Parse MeSH terms from the table cell
            mesh_terms = _split_mesh_terms(mesh_raw)
            record = {"abbr": abbr, "zh": zh, "en": en, "mesh_terms": mesh_terms}
            # Register under multiple keys for flexible lookup
            for key in [abbr, abbr.lower(), zh, en, en.lower()]:
                departments[key] = record
    return departments


def lookup_department_mesh(dept_key: str, filepath: Path | None = None) -> list[str]:
    """Look up MeSH terms for a department by abbreviation, Chinese, or English name."""
    departments = parse_departments(filepath)
    record = departments.get(dept_key) or departments.get(dept_key.lower())
    if record:
        return record["mesh_terms"]
    return []


def _split_mesh_terms(mesh_str: str) -> list[str]:
    """Split a mesh string that may contain comma-separated terms.

    Input:  '"GFR"[MeSH], "Kidney Failure"[MeSH]'
    Output: ['"GFR"[MeSH]', '"Kidney Failure"[MeSH]']

    Also handles single terms and AND-connected terms.
    """
    if not mesh_str:
        return []

    # If already has AND/OR operators, return as-is (user structured it themselves)
    if " AND " in mesh_str or " OR " in mesh_str:
        return [mesh_str]

    # Split by comma, but not within quotes
    terms = []
    for part in re.split(r",\s*(?=[\"'])", mesh_str):
        part = part.strip()
        if part:
            terms.append(part)

    # If no quoted comma-split worked, try simpler comma split
    if len(terms) <= 1 and "," in mesh_str:
        terms = [t.strip() for t in mesh_str.split(",") if t.strip()]

    return terms if terms else [mesh_str]


def _join_or(terms: list[str]) -> str:
    """Join multiple terms with OR."""
    if len(terms) == 1:
        return terms[0]
    return " OR ".join(terms)


def parse_yaml_simple(filepath: Path) -> dict:
    """Simple YAML-like parser for pico.yaml (no external deps)."""
    data = {}
    current_section = None
    current_key = None

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue

            if not line.startswith(" ") and ":" in stripped:
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if val:
                    data[key] = val
                else:
                    current_section = key
                    if key not in data:
                        data[key] = {}
                continue

            if line.startswith("  ") and not line.startswith("    ") and ":" in stripped:
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if current_section and isinstance(data.get(current_section), dict):
                    if val:
                        data[current_section][key] = val
                    else:
                        data[current_section][key] = {}
                        current_key = key
                continue

            if line.startswith("    ") and ":" in stripped:
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if current_section and current_key:
                    sect = data.get(current_section, {})
                    if isinstance(sect.get(current_key), dict):
                        sect[current_key][key] = val

    return data


def _extract_mesh(
    elem_data: dict, include_secondary: bool = False, expand: bool = False
) -> str:
    """Extract MeSH terms from a PICO element, handling nested primary/secondary."""
    if not isinstance(elem_data, dict):
        return str(elem_data) if elem_data else ""

    mesh = elem_data.get("mesh", "")
    if mesh:
        terms = _split_mesh_terms(mesh)
        terms = _expand_terms(terms, expand)
        return _join_or(terms)

    # Handle nested primary/secondary (for outcomes)
    all_terms = []
    primary = elem_data.get("primary", {})
    if isinstance(primary, dict) and primary.get("mesh"):
        all_terms.extend(_split_mesh_terms(primary["mesh"]))

    if include_secondary:
        secondary = elem_data.get("secondary", {})
        if isinstance(secondary, dict) and secondary.get("mesh"):
            all_terms.extend(_split_mesh_terms(secondary["mesh"]))

    all_terms = _expand_terms(all_terms, expand)
    return _join_or(all_terms) if all_terms else ""


def _resolve_pub_filter(q_type: str, tier: int) -> str:
    """Resolve publication type filter for a given question type and tier.

    tier=0: strictest (highest evidence only)
    tier=1: merge tier 0 + tier 1
    tier=2: merge tier 0 + 1 + 2 (broadest)
    """
    chain = PUB_FILTER_CHAIN.get(q_type, [])
    if not chain:
        return ""
    # Clamp tier to available range
    max_tier = min(tier, len(chain) - 1)
    if max_tier == 0:
        return chain[0]
    # Merge tiers: combine all filters up to requested tier with OR
    merged = " OR ".join(chain[: max_tier + 1])
    return f"({merged})"


def build_query(
    pico_data: dict,
    q_type: str = "",
    years: int = 0,
    lang: str = "",
    include_secondary: bool = True,
    expand: bool = False,
    dept_mesh: list[str] | None = None,
    tier: int = 0,
) -> str:
    """Build PubMed query from PICO data.

    Args:
        pico_data: Parsed PICO YAML data.
        q_type: Question type override (therapeutic/diagnostic/...).
        years: Limit to last N years (0 = no limit).
        lang: Language filter (en/zh/"" = no filter).
        include_secondary: Include secondary outcomes in search.
        expand: Expand MeSH terms with title/abstract synonyms.
        dept_mesh: Department MeSH terms to scope the search.
        tier: Evidence tier (0=strictest, 1=relaxed, 2=broadest).
    """
    pico = pico_data.get("pico", {})
    parts = []

    # Add department scope if provided (from --department or pico.yaml)
    if not dept_mesh:
        dept_data = pico_data.get("department", {})
        if isinstance(dept_data, dict):
            raw = dept_data.get("mesh_terms", [])
            if isinstance(raw, list) and raw:
                dept_mesh = [
                    f'"{t}"[MeSH]' if "[MeSH]" not in t else t
                    for t in raw
                ]
    if dept_mesh:
        expanded = _expand_terms(dept_mesh, expand)
        parts.append(f"({_join_or(expanded)})")

    for element in ["p", "i", "c"]:
        elem_data = pico.get(element, {})
        mesh = _extract_mesh(elem_data, expand=expand)
        if mesh:
            parts.append(f"({mesh})")

    # Outcomes: include both primary and optionally secondary
    o_data = pico.get("o", {})
    o_mesh = _extract_mesh(o_data, include_secondary=include_secondary, expand=expand)
    if o_mesh:
        parts.append(f"({o_mesh})")

    if not parts:
        return ""

    query = "\nAND ".join(parts)

    # Add publication type filter (tier-based fallback)
    classification = pico_data.get("classification", {})
    if not q_type:
        q_type = classification.get("type", "")

    pub_filter = _resolve_pub_filter(q_type, tier)
    if pub_filter:
        query += f"\nAND {pub_filter}"

    # Add date filter
    if years > 0:
        query += f'\nAND ("{years} years"[dp])'

    # Add language filter
    lang_filter = LANG_FILTERS.get(lang, "")
    if lang_filter:
        query += f"\nAND {lang_filter}"

    return query


def build_query_chain(
    pico_data: dict, **kwargs
) -> list[dict[str, str]]:
    """Build a list of queries from strictest to broadest evidence tier.

    Returns list of dicts: [{"tier": 0, "label": "...", "query": "..."}]
    Each successive tier is more relaxed. The caller should try tier 0 first,
    and only move to higher tiers if results are insufficient.
    """
    q_type = kwargs.get("q_type", "")
    if not q_type:
        classification = pico_data.get("classification", {})
        if isinstance(classification, dict):
            q_type = classification.get("type", "")

    chain = PUB_FILTER_CHAIN.get(q_type, [])
    num_tiers = max(len(chain), 1)

    tier_labels = {
        "therapeutic": ["SR/MA + RCT", "Controlled Trial + Cohort", "Case-Control + Observational"],
        "preventive": ["SR/MA + RCT", "Controlled Trial + Cohort", "Case-Control + Observational"],
        "diagnostic": [
            "SR/MA + Prospective Blind + Gold Standard",
            "Cross-Sectional + Sensitivity/Specificity",
            "Case-Control + Observational",
        ],
        "prognostic": ["SR/MA + Cohort", "Case-Control", "Observational + Case Reports"],
        "etiology_harm": ["SR/MA + Cohort", "Case-Control + Risk Factors", "Observational + Case Reports"],
    }
    labels = tier_labels.get(q_type, ["Tier 0", "Tier 1", "Tier 2"])

    results = []
    for t in range(num_tiers):
        query = build_query(pico_data, **{**kwargs, "tier": t})
        if query:
            label = labels[t] if t < len(labels) else f"Tier {t}"
            results.append({"tier": t, "label": label, "query": query})
    return results


def build_eutils_url(query: str, retmax: int = 100) -> str:
    """Build a PubMed E-utilities esearch URL from a query string."""
    encoded = urllib.parse.quote(query.replace("\n", " "), safe="[]()\"'")
    return (
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?db=pubmed&retmode=json&retmax={retmax}&sort=date&term={encoded}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="從 PICO YAML 建構 PubMed 搜尋策略",
        epilog=(
            "範例：\n"
            "  python3 scripts/build_search_query.py --project sglt2i-ckd\n"
            "  python3 scripts/build_search_query.py --project sglt2i-ckd --years 5 --lang en\n"
            "  python3 scripts/build_search_query.py --project sglt2i-ckd --expand\n"
            "  python3 scripts/build_search_query.py --project sglt2i-ckd --url --retmax 50\n"
            "  python3 scripts/build_search_query.py --project sglt2i-ckd --chain\n"
            "  python3 scripts/build_search_query.py --project sglt2i-ckd --tier 1\n"
            "  python3 scripts/build_search_query.py --department 腎臟內科\n"
            "  python3 scripts/build_search_query.py --department NEPH --expand --years 3\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--project", help="專案名稱")
    parser.add_argument("--pico", help="pico.yaml 檔案路徑")
    parser.add_argument("--type", default="", help="問題類型 (therapeutic/diagnostic/...)")
    parser.add_argument("--years", type=int, default=0, help="限制最近 N 年的文獻（0=不限）")
    parser.add_argument("--lang", default="", choices=["", "en", "zh"], help="語言篩選 (en/zh)")
    parser.add_argument("--no-secondary", action="store_true", help="不包含次要結局")
    parser.add_argument("--expand", action="store_true", help="展開 MeSH 同義詞（加入 [tiab] 搜尋）")
    parser.add_argument("--department", default="", help="科別篩選（縮寫/中文/英文，如 NEPH、腎臟內科、Nephrology）")
    parser.add_argument("--tier", type=int, default=0, choices=[0, 1, 2],
                        help="證據等級層（0=最嚴格, 1=放寬, 2=最寬鬆）")
    parser.add_argument("--chain", action="store_true",
                        help="顯示完整 fallback chain（所有層級的搜尋式）")
    parser.add_argument("--url", action="store_true", help="同時輸出 E-utilities API URL")
    parser.add_argument("--retmax", type=int, default=100, help="E-utilities 最大回傳筆數（預設 100）")
    parser.add_argument("--output", help="輸出檔案路徑")

    args = parser.parse_args()
    base_dir = Path(__file__).resolve().parent.parent

    # Resolve department MeSH terms from --department flag
    dept_mesh: list[str] = []
    if args.department:
        dept_mesh = lookup_department_mesh(args.department)
        if not dept_mesh:
            print(f"警告：找不到科別 '{args.department}' 的 MeSH terms。", file=sys.stderr)
            print("可用科別：使用 --department 搭配縮寫（NEPH）、中文（腎臟內科）或英文（Nephrology）。", file=sys.stderr)

    # ── Load PICO data ──
    if args.project:
        pico_path = base_dir / "projects" / args.project / "01_ask" / "pico.yaml"
    elif args.pico:
        pico_path = Path(args.pico)
    elif args.department and dept_mesh:
        pico_path = None
    else:
        parser.print_help()
        sys.exit(1)

    if pico_path is not None:
        if not pico_path.exists():
            print(f"錯誤：找不到 PICO 檔案 '{pico_path}'。", file=sys.stderr)
            sys.exit(1)
        try:
            if yaml:
                with open(pico_path, encoding="utf-8") as f:
                    pico_data = yaml.safe_load(f)
            else:
                pico_data = parse_yaml_simple(pico_path)
        except Exception as e:
            print(f"錯誤：無法讀取 PICO 檔案 '{pico_path}'。{e}", file=sys.stderr)
            sys.exit(1)
        if not isinstance(pico_data, dict):
            print("錯誤：PICO 檔案格式不正確（預期為 YAML 物件）。", file=sys.stderr)
            sys.exit(1)
    else:
        pico_data = {}

    # ── Shared build kwargs ──
    build_kwargs = dict(
        q_type=args.type,
        years=args.years,
        lang=args.lang,
        include_secondary=not args.no_secondary,
        expand=args.expand,
        dept_mesh=dept_mesh,
    )

    # ── Chain mode: show all tiers ──
    if args.chain:
        chain = build_query_chain(pico_data, **build_kwargs)
        if not chain:
            print("警告：PICO 中沒有任何 MeSH terms，無法建構搜尋式。", file=sys.stderr)
            sys.exit(1)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            content = "# PubMed 搜尋策略 — Fallback Chain\n\n"
            for item in chain:
                content += f"## Tier {item['tier']}: {item['label']}\n\n```\n{item['query']}\n```\n\n"
                if args.url:
                    url = build_eutils_url(item["query"], args.retmax)
                    content += f"URL: `{url}`\n\n"
            output_path.write_text(content, encoding="utf-8")
            print(f"搜尋策略已產生：{output_path}")
        else:
            for item in chain:
                tier_num = item["tier"]
                label = item["label"]
                print(f"═══ Tier {tier_num}: {label} ═══\n")
                print(item["query"])
                if args.url:
                    url = build_eutils_url(item["query"], args.retmax)
                    print(f"\nURL: {url}")
                print()
        sys.exit(0)

    # ── Single tier mode ──
    query = build_query(pico_data, **build_kwargs, tier=args.tier)

    if not query:
        print("警告：PICO 中沒有任何 MeSH terms，無法建構搜尋式。", file=sys.stderr)
        sys.exit(1)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        content = f"# PubMed 搜尋策略\n\n```\n{query}\n```\n"
        if args.url:
            url = build_eutils_url(query, args.retmax)
            content += f"\n## E-utilities API URL\n\n```\n{url}\n```\n"
        output_path.write_text(content, encoding="utf-8")
        print(f"搜尋策略已產生：{output_path}")
    else:
        print("═══ PubMed 搜尋策略 ═══\n")
        print(query)
        if args.url:
            url = build_eutils_url(query, args.retmax)
            print("\n═══ E-utilities API URL ═══\n")
            print(url)
        print()


if __name__ == "__main__":
    main()
