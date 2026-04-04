#!/usr/bin/env python3
"""
從 PICO YAML 自動建構 PubMed 搜尋策略。

用法：
    python3 scripts/build_search_query.py --project <name>
    python3 scripts/build_search_query.py --pico pico.yaml --type therapeutic
    python3 scripts/build_search_query.py --project <name> --years 5 --lang en
    python3 scripts/build_search_query.py --project <name> --url

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

# Publication type filters by question type
PUB_FILTERS = {
    "therapeutic": '(Randomized Controlled Trial[pt] OR Meta-Analysis[pt] OR Systematic Review[pt])',
    "preventive": '(Randomized Controlled Trial[pt] OR Meta-Analysis[pt] OR Systematic Review[pt])',
    "diagnostic": '((Sensitivity and Specificity[MeSH]) OR (Cross-Sectional Studies[MeSH]) OR Systematic Review[pt])',
    "prognostic": '(Cohort Studies[MeSH] OR Prognosis[MeSH] OR Systematic Review[pt])',
    "etiology_harm": '(Cohort Studies[MeSH] OR Case-Control Studies[MeSH] OR Risk Factors[MeSH] OR Systematic Review[pt])',
}

LANG_FILTERS = {
    "en": "English[lang]",
    "zh": "(Chinese[lang] OR English[lang])",
}


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


def _extract_mesh(elem_data: dict, include_secondary: bool = False) -> str:
    """Extract MeSH terms from a PICO element, handling nested primary/secondary."""
    if not isinstance(elem_data, dict):
        return str(elem_data) if elem_data else ""

    mesh = elem_data.get("mesh", "")
    if mesh:
        terms = _split_mesh_terms(mesh)
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

    return _join_or(all_terms) if all_terms else ""


def build_query(
    pico_data: dict,
    q_type: str = "",
    years: int = 0,
    lang: str = "",
    include_secondary: bool = True,
) -> str:
    """Build PubMed query from PICO data.

    Args:
        pico_data: Parsed PICO YAML data.
        q_type: Question type override (therapeutic/diagnostic/...).
        years: Limit to last N years (0 = no limit).
        lang: Language filter (en/zh/"" = no filter).
        include_secondary: Include secondary outcomes in search.
    """
    pico = pico_data.get("pico", {})
    parts = []

    for element in ["p", "i", "c"]:
        elem_data = pico.get(element, {})
        mesh = _extract_mesh(elem_data)
        if mesh:
            parts.append(f"({mesh})")

    # Outcomes: include both primary and optionally secondary
    o_data = pico.get("o", {})
    o_mesh = _extract_mesh(o_data, include_secondary=include_secondary)
    if o_mesh:
        parts.append(f"({o_mesh})")

    if not parts:
        return ""

    query = "\nAND ".join(parts)

    # Add publication type filter
    classification = pico_data.get("classification", {})
    if not q_type:
        q_type = classification.get("type", "")

    pub_filter = PUB_FILTERS.get(q_type, "")
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
            "  python3 scripts/build_search_query.py --project sglt2i-ckd --url --retmax 50\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--project", help="專案名稱")
    parser.add_argument("--pico", help="pico.yaml 檔案路徑")
    parser.add_argument("--type", default="", help="問題類型 (therapeutic/diagnostic/...)")
    parser.add_argument("--years", type=int, default=0, help="限制最近 N 年的文獻（0=不限）")
    parser.add_argument("--lang", default="", choices=["", "en", "zh"], help="語言篩選 (en/zh)")
    parser.add_argument("--no-secondary", action="store_true", help="不包含次要結局")
    parser.add_argument("--url", action="store_true", help="同時輸出 E-utilities API URL")
    parser.add_argument("--retmax", type=int, default=100, help="E-utilities 最大回傳筆數（預設 100）")
    parser.add_argument("--output", help="輸出檔案路徑")

    args = parser.parse_args()
    base_dir = Path(__file__).resolve().parent.parent

    if args.project:
        pico_path = base_dir / "projects" / args.project / "01_ask" / "pico.yaml"
    elif args.pico:
        pico_path = Path(args.pico)
    else:
        parser.print_help()
        sys.exit(1)

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

    query = build_query(
        pico_data,
        q_type=args.type,
        years=args.years,
        lang=args.lang,
        include_secondary=not args.no_secondary,
    )

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
