#!/usr/bin/env python3
"""
5A 品質門檻驗證器。

在每個 5A 階段完成時自動檢核產出品質，不只是檔案存在，還檢查內容。

用法：
    python3 scripts/quality_gate.py --project <name> --step ask
    python3 scripts/quality_gate.py --project <name> --step acquire
    python3 scripts/quality_gate.py --project <name> --step appraise
    python3 scripts/quality_gate.py --project <name> --step apply
    python3 scripts/quality_gate.py --project <name> --step audit
    python3 scripts/quality_gate.py --project <name>  # 驗證到目前最新完成的步驟
"""

import argparse
import csv
import sys
from pathlib import Path

from scripts.utils import file_has_content as _file_has_content
from scripts.utils import get_project_path, read_yaml


class GateResult:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def check(self, condition: bool, msg: str, is_warning: bool = False):
        if condition:
            self.checks.append(("✓", msg))
            self.passed += 1
        elif is_warning:
            self.checks.append(("⚠", msg))
            self.warnings += 1
        else:
            self.checks.append(("✗", msg))
            self.failed += 1

    @property
    def ok(self):
        return self.failed == 0

    def display(self, step_name: str):
        status = "通過" if self.ok else f"未通過（{self.failed} 項失敗）"
        if self.warnings:
            status += f"（{self.warnings} 項警告）"
        print(f"\n【{step_name}】品質門檻：{status}")
        for icon, msg in self.checks:
            print(f"  {icon} {msg}")


def file_has_content(filepath: Path, min_bytes: int = 20) -> bool:
    """Check file exists and has meaningful content."""
    return _file_has_content(filepath, min_bytes)


def gate_ask(project: Path) -> GateResult:
    """ASK phase quality gate."""
    r = GateResult()
    ask_dir = project / "01_ask"

    # pico.yaml exists and has PICO content
    pico_path = ask_dir / "pico.yaml"
    r.check(file_has_content(pico_path), "pico.yaml 存在且有內容")

    if pico_path.exists():
        pico = read_yaml(pico_path)

        # Check PICO fields are not empty
        pico_section = pico.get("pico", {})
        if isinstance(pico_section, dict):
            for element in ["p", "i", "c"]:
                elem = pico_section.get(element, {})
                if isinstance(elem, dict):
                    has_mesh = bool(elem.get("mesh", ""))
                    has_zh = bool(elem.get("zh", ""))
                    r.check(has_mesh, f"PICO {element.upper()} 的 MeSH 欄位已填寫")
                    r.check(has_zh, f"PICO {element.upper()} 的中文描述已填寫")
                else:
                    r.check(False, f"PICO {element.upper()} 格式不正確")

            # Outcome can be nested
            o = pico_section.get("o", {})
            if isinstance(o, dict):
                primary = o.get("primary", o)
                if isinstance(primary, dict):
                    r.check(bool(primary.get("zh", "") or primary.get("mesh", "")),
                            "PICO O (Primary Outcome) 已填寫")
                else:
                    r.check(bool(o.get("zh", "") or o.get("mesh", "")),
                            "PICO O (Outcome) 已填寫")

        # Topic not empty
        r.check(bool(pico.get("topic", "")), "主題 (topic) 已填寫")

        # Classification
        classification = pico.get("classification", {})
        if isinstance(classification, dict):
            r.check(bool(classification.get("type", "")), "問題分類 (classification.type) 已填寫")
        else:
            r.check(False, "問題分類未填寫", is_warning=True)

    # Clinical scenario
    r.check(file_has_content(ask_dir / "clinical_scenario.md"),
            "clinical_scenario.md 臨床情境已撰寫")

    # Classification file
    r.check(file_has_content(ask_dir / "classification.md"),
            "classification.md 問題分類已撰寫")

    # Introduction (optional)
    r.check(file_has_content(ask_dir / "introduction.md"),
            "introduction.md 背景資訊已撰寫（選擇性）", is_warning=True)

    return r


def gate_acquire(project: Path) -> GateResult:
    """ACQUIRE phase quality gate."""
    r = GateResult()
    acq_dir = project / "02_acquire"

    r.check(file_has_content(acq_dir / "search_strategy.md"),
            "search_strategy.md 搜尋策略已記錄")

    r.check(file_has_content(acq_dir / "selected_articles.md"),
            "selected_articles.md 選定文獻已記錄")

    # Candidates CSV: check has data rows
    csv_path = acq_dir / "candidates.csv"
    if csv_path.exists():
        try:
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            r.check(len(rows) >= 1, f"candidates.csv 有 {len(rows)} 篇候選文獻")
            selected = [row for row in rows if row.get("selected", "").lower() in ("是", "yes", "true", "1")]
            r.check(len(selected) >= 1,
                    f"至少選定 {len(selected)} 篇文獻",
                    is_warning=(len(selected) == 0))
        except (UnicodeDecodeError, csv.Error):
            r.check(False, "candidates.csv 格式錯誤或編碼不正確")
        except OSError as e:
            r.check(False, f"candidates.csv 無法讀取：{e}")
    else:
        r.check(False, "candidates.csv 候選文獻列表不存在", is_warning=True)

    # PRISMA flow (optional but recommended)
    r.check(file_has_content(acq_dir / "prisma_flow.md"),
            "prisma_flow.md PRISMA 流程圖已產生（建議）", is_warning=True)

    return r


def gate_appraise(project: Path) -> GateResult:
    """APPRAISE phase quality gate."""
    r = GateResult()
    app_dir = project / "03_appraise"

    r.check(file_has_content(app_dir / "tool_selection.md"),
            "tool_selection.md 評讀工具選擇已記錄")

    r.check(file_has_content(app_dir / "results_summary.md"),
            "results_summary.md 研究結果已摘要")

    # Appraisal CSV: check content quality
    csv_path = app_dir / "appraisal.csv"
    if csv_path.exists():
        try:
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            total = len(rows)
            answered = sum(1 for row in rows if row.get("answer", "").strip())
            cant_tell = sum(1 for row in rows
                          if row.get("answer", "").strip().lower() == "can't tell")

            r.check(total > 0, f"appraisal.csv 有 {total} 題評讀")
            r.check(answered == total,
                    f"所有 {total} 題都有 answer（已答 {answered}/{total}）")

            if cant_tell > 2:
                r.check(False,
                        f"Can't tell 有 {cant_tell} 題（> 2 題），報告品質可能不足",
                        is_warning=True)
            else:
                r.check(True, f"Can't tell 僅 {cant_tell} 題（≤ 2 題）")

            # Check evidence column
            with_evidence = sum(1 for row in rows if row.get("evidence", "").strip())
            r.check(with_evidence >= total * 0.7,
                    f"有 {with_evidence}/{total} 題附有文獻原文佐證",
                    is_warning=(with_evidence < total * 0.7))

        except (UnicodeDecodeError, csv.Error):
            r.check(False, "appraisal.csv 格式錯誤或編碼不正確")
        except OSError as e:
            r.check(False, f"appraisal.csv 無法讀取：{e}")
    else:
        r.check(False, "appraisal.csv 評讀結果不存在")

    # COI check
    r.check(file_has_content(app_dir / "coi_check.md"),
            "coi_check.md 利益衝突檢核已完成")

    # GRADE (optional)
    r.check(file_has_content(app_dir / "grade.md"),
            "grade.md GRADE 評定已完成（選擇性）", is_warning=True)

    return r


def gate_apply(project: Path) -> GateResult:
    """APPLY phase quality gate."""
    r = GateResult()
    apply_dir = project / "04_apply"

    r.check(file_has_content(apply_dir / "evidence_level.md"),
            "evidence_level.md 證據等級已標示")

    r.check(file_has_content(apply_dir / "clinical_reply.md"),
            "clinical_reply.md 臨床回覆已撰寫")

    r.check(file_has_content(apply_dir / "local_considerations.md"),
            "local_considerations.md 在地化考量已撰寫（建議）", is_warning=True)

    return r


def gate_audit(project: Path) -> GateResult:
    """AUDIT phase quality gate."""
    r = GateResult()
    audit_dir = project / "05_audit"

    sa_path = audit_dir / "self_assessment.md"
    r.check(file_has_content(sa_path), "self_assessment.md 自我評估已完成")

    # Check that all 5 dimensions are covered
    if sa_path.exists():
        content = sa_path.read_text(encoding="utf-8")
        dimensions = ["提出臨床問題", "搜尋最佳證據", "搜尋技巧", "應用到臨床", "改變醫療行為"]
        found = sum(1 for d in dimensions if d in content)
        r.check(found >= 4,
                f"自我評估涵蓋 {found}/5 個面向",
                is_warning=(found < 4))

    return r


GATES = {
    "ask": ("ASK（問題）", gate_ask),
    "acquire": ("ACQUIRE（檢索）", gate_acquire),
    "appraise": ("APPRAISE（評讀）", gate_appraise),
    "apply": ("APPLY（應用）", gate_apply),
    "audit": ("AUDIT（評估）", gate_audit),
}

STEP_ORDER = ["ask", "acquire", "appraise", "apply", "audit"]


def detect_current_step(project: Path) -> str:
    """Detect the latest completed step."""
    for step in reversed(STEP_ORDER):
        _, gate_fn = GATES[step]
        result = gate_fn(project)
        if result.ok:
            return step
    return "ask"


def main():
    parser = argparse.ArgumentParser(
        description="5A 品質門檻驗證器",
        epilog=(
            "範例：\n"
            "  python3 scripts/quality_gate.py --project sglt2i-ckd --step ask\n"
            "  python3 scripts/quality_gate.py --project sglt2i-ckd  # 自動偵測\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--project", required=True, help="專案名稱")
    parser.add_argument("--step", choices=STEP_ORDER, help="要驗證的步驟（預設：自動偵測）")

    args = parser.parse_args()
    project = get_project_path(args.project)

    if not project.exists():
        print(f"錯誤：找不到專案 '{args.project}'。", file=sys.stderr)
        sys.exit(1)

    print(f"═══ 品質門檻驗證：{args.project} ═══")

    if args.step:
        steps = [args.step]
    else:
        # Run all steps up to current
        current = detect_current_step(project)
        idx = STEP_ORDER.index(current)
        steps = STEP_ORDER[:idx + 1]

    all_ok = True
    total_passed = 0
    total_failed = 0
    total_warnings = 0

    for step in steps:
        name, gate_fn = GATES[step]
        result = gate_fn(project)
        result.display(name)
        total_passed += result.passed
        total_failed += result.failed
        total_warnings += result.warnings
        if not result.ok:
            all_ok = False

    print("\n═══ 總結 ═══")
    print(f"通過：{total_passed} | 失敗：{total_failed} | 警告：{total_warnings}")

    if all_ok:
        if args.step:
            next_idx = STEP_ORDER.index(args.step) + 1
            if next_idx < len(STEP_ORDER):
                print(f"\n品質門檻通過，可以進入 {STEP_ORDER[next_idx].upper()} 階段。")
            else:
                print("\n所有 5A 階段品質門檻通過，可以產生簡報！")
        sys.exit(0)
    else:
        print("\n品質門檻未通過，請修正上述失敗項目後再繼續。")
        sys.exit(1)


if __name__ == "__main__":
    main()
