#!/usr/bin/env python3
"""
從 PICO YAML 自動建構 PubMed 搜尋策略。

用法：
    python3 scripts/build_search_query.py --project <name>
    python3 scripts/build_search_query.py --pico pico.yaml --type therapeutic

讀取 pico.yaml，組合 MeSH terms 為 PubMed Boolean 搜尋式，
並依問題類型加上 publication type filter。
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# Publication type filters by question type
PUB_FILTERS = {
    "therapeutic": 'AND (Randomized Controlled Trial[pt] OR Meta-Analysis[pt] OR Systematic Review[pt])',
    "preventive": 'AND (Randomized Controlled Trial[pt] OR Meta-Analysis[pt] OR Systematic Review[pt])',
    "diagnostic": 'AND ((Sensitivity and Specificity[MeSH]) OR (Cross-Sectional Studies[MeSH]) OR Systematic Review[pt])',
    "prognostic": 'AND (Cohort Studies[MeSH] OR Prognosis[MeSH] OR Systematic Review[pt])',
    "etiology_harm": 'AND (Cohort Studies[MeSH] OR Case-Control Studies[MeSH] OR Risk Factors[MeSH] OR Systematic Review[pt])',
}


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


def build_query(pico_data: dict, q_type: str = "") -> str:
    """Build PubMed query from PICO data."""
    pico = pico_data.get("pico", {})
    parts = []

    for element in ["p", "i", "c", "o"]:
        elem_data = pico.get(element, {})
        if isinstance(elem_data, dict):
            mesh = elem_data.get("mesh", "")
            # Handle nested primary/secondary for outcomes
            if not mesh:
                primary = elem_data.get("primary", {})
                if isinstance(primary, dict):
                    mesh = primary.get("mesh", "")
        else:
            mesh = str(elem_data)

        if mesh:
            parts.append(f"({mesh})")

    query = "\nAND ".join(parts)

    # Add publication type filter
    classification = pico_data.get("classification", {})
    if not q_type:
        q_type = classification.get("type", "")

    pub_filter = PUB_FILTERS.get(q_type, "")
    if pub_filter:
        query += f"\n{pub_filter}"

    return query


def main():
    parser = argparse.ArgumentParser(
        description="從 PICO YAML 建構 PubMed 搜尋策略",
    )
    parser.add_argument("--project", help="專案名稱")
    parser.add_argument("--pico", help="pico.yaml 檔案路徑")
    parser.add_argument("--type", default="", help="問題類型 (therapeutic/diagnostic/...)")
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

    query = build_query(pico_data, args.type)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(f"# PubMed 搜尋策略\n\n```\n{query}\n```\n", encoding="utf-8")
        print(f"搜尋策略已產生：{output_path}")
    else:
        print("═══ PubMed 搜尋策略 ═══\n")
        print(query)
        print()


if __name__ == "__main__":
    main()
