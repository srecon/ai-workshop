#!/usr/bin/env python3
"""
Гоняет все стандарты из каталога standards/ на одном proposal
и агрегирует единый вердикт "нужен ли архитектор".

Перед вызовом Nimble для каждого стандарта делается быстрый локальный
precheck по ключевым словам (precheck_keywords в YAML). Если ни одного
ключевого слова в proposal нет — стандарт скипается без вызова Nimble.

Usage:
    python3 tools/architect_involvement.py \
        --proposal tests/fixtures/proposal-monitoring.md \
        --standards-dir standards/ \
        --output /tmp/architect-involvement.json \
        [--url http://localhost:11434/v1/systemone] \
        [--model nimble] \
        [--timeout 120] \
        [--trust 0.80] [--gray 0.55] [--margin-min 0.20] \
        [--no-precheck]

Exit codes:
    0 — ok
    1 — HTTP / connection error
    2 — input error
    3 — timeout
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
import urllib.error
from pathlib import Path

# Импортируем функции из соседнего файла nimble_applicability.py
from nimble_applicability import (
    load_standard,
    load_proposal,
    build_state,
    call_nimble,
    normalize,
    decision_from,
)


# ---------------- Поиск стандартов ----------------

def find_standards(standards_dir: Path) -> list[Path]:
    """
    Рекурсивно ищет все *.yaml файлы внутри standards_dir.
    Возвращает отсортированный список путей.
    """
    return sorted(standards_dir.rglob("*.yaml"))


# ---------------- Precheck по ключевым словам ----------------

def precheck(proposal: str, std: dict) -> tuple[bool, list[str]]:
    """
    Быстрая локальная проверка: есть ли в proposal ключевые слова стандарта.

    Возвращает (matched, hits):
      matched = True,  если хотя бы одно ключевое слово найдено
      hits    = список найденных слов (для отчёта)
    """
    keywords = std.get("precheck_keywords") or []
    if not keywords:
        return True, []  # если ключей не задано — не скипаем

    text_lower = proposal.lower()
    hits = [kw for kw in keywords if kw.lower() in text_lower]
    return bool(hits), hits


# ---------------- Обработка одного стандарта ----------------

def check_standard(
    proposal: str,
    std: dict,
    url: str,
    model: str,
    timeout: float,
    trust: float,
    gray: float,
    margin_min: float,
) -> dict:
    """
    Прогоняет все требования одного стандарта.
    Возвращает словарь:
      {
        "id": "...", "version": "...", "title": "...",
        "decision": "architect_required" | "architect_not_required" | "escalate",
        "summary": {...},
        "requirements": [...]
      }
    """
    sid = std["standard"]["id"]
    sver = std["standard"]["version"]
    requirements = []

    for req in std["requirements"]:
        state = build_state(proposal, req)
        raw = call_nimble(state, url, model, timeout)
        choice, conf, probs, usage = normalize(raw)
        verdict, margin, gray_zone = decision_from(
            choice, conf, probs, trust, gray, margin_min
        )

        requirements.append({
            "code": req["code"],
            "raw_choice": choice,
            "raw_confidence": conf,
            "raw_probabilities": probs,
            "margin": margin,
            "usage": usage,
            "verdict": verdict,
            "gray_zone": gray_zone,
        })

    # Локальный decision по стандарту
    verdicts = [r["verdict"] for r in requirements]
    if "applicable" in verdicts:
        decision = "architect_required"
    elif "unclear" in verdicts:
        decision = "escalate"
    else:
        decision = "architect_not_required"

    # Суммарные токены по стандарту
    total_input = sum(r["usage"].get("input_tokens", 0) for r in requirements)
    total_output = sum(r["usage"].get("output_tokens", 0) for r in requirements)

    return {
        "id": sid,
        "version": sver,
        "title": std["standard"].get("title"),
        "decision": decision,
        "summary": {
            "applicable": sum(1 for r in requirements if r["verdict"] == "applicable"),
            "not_applicable": sum(1 for r in requirements if r["verdict"] == "not_applicable"),
            "unclear": sum(1 for r in requirements if r["verdict"] == "unclear"),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
        },
        "requirements": requirements,
    }


# ---------------- Красивый вывод одной строки ----------------

def print_standard_line(idx: int, total: int, result: dict) -> None:
    """
    Печатает одну строку вида:
      [1/7] !! monitoring     v2.1   → architect_required   (app=14 not= 3 unc= 0)
    """
    s = result["summary"]
    mark = {
        "architect_required": "!!",
        "escalate": "??",
        "architect_not_required": "..",
    }.get(result["decision"], "?")
    print(
        f"  [{idx}/{total}] {mark} {result['id']:14s} "
        f"v{result['version']:6s} → {result['decision']:24s} "
        f"(app={s['applicable']:2d} not={s['not_applicable']:2d} unc={s['unclear']:2d})"
    )


# ---------------- Точка входа ----------------

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--proposal", required=True,
                   help="Путь к markdown-файлу proposal")
    p.add_argument("--standards-dir", default="standards/",
                   help="Каталог со стандартами (рекурсивно ищет *.yaml)")
    p.add_argument("--output", default=None,
                   help="Куда сохранить сводный JSON-отчёт")
    p.add_argument("--url", default="http://localhost:11434/v1/systemone")
    p.add_argument("--model", default="nimble")
    p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--trust", type=float, default=0.80)
    p.add_argument("--gray", type=float, default=0.55)
    p.add_argument("--margin-min", type=float, default=0.20)
    p.add_argument("--no-precheck", action="store_true",
                   help="Отключить precheck по ключевым словам (гонять все стандарты)")
    args = p.parse_args()

    proposal_path = Path(args.proposal)
    standards_dir = Path(args.standards_dir)

    if not proposal_path.exists():
        print(f"proposal not found: {proposal_path}", file=sys.stderr)
        return 2
    if not standards_dir.exists():
        print(f"standards dir not found: {standards_dir}", file=sys.stderr)
        return 2

    # Загружаем все стандарты
    standard_files = find_standards(standards_dir)
    if not standard_files:
        print(f"no *.yaml files found under {standards_dir}", file=sys.stderr)
        return 2

    proposal = load_proposal(proposal_path)

    print(f"Proposal:    {proposal_path} ({len(proposal)} chars)")
    print(f"Standards:   {standards_dir} → {len(standard_files)} файлов")
    print(f"Thresholds:  trust={args.trust} gray={args.gray} margin_min={args.margin_min}")
    print(f"Precheck:    {'OFF (--no-precheck)' if args.no_precheck else 'ON'}")
    print("=" * 80)

    # Прогоняем каждый стандарт
    standard_results: list[dict] = []
    skipped_by_precheck: list[dict] = []

    for i, sf in enumerate(standard_files, start=1):
        std = load_standard(sf)
        sid = std["standard"]["id"]
        sver = std["standard"]["version"]

        # --- precheck ---
        if not args.no_precheck:
            passed, hits = precheck(proposal, std)
            if not passed:
                skipped_by_precheck.append({
                    "id": sid,
                    "version": sver,
                    "reason": "no precheck keywords found",
                })
                print(
                    f"  [{i}/{len(standard_files)}] -- {sid:14s} "
                    f"v{sver:6s} → skipped (no keywords)"
                )
                continue
        else:
            hits = []

        # --- основная проверка через Nimble ---
        try:
            result = check_standard(
                proposal, std, args.url, args.model, args.timeout,
                args.trust, args.gray, args.margin_min,
            )
        except urllib.error.HTTPError as e:
            print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
            return 1
        except urllib.error.URLError as e:
            print(f"Connection error: {e.reason}", file=sys.stderr)
            return 1
        except TimeoutError:
            print(f"Timeout after {args.timeout}s", file=sys.stderr)
            return 3

        result["precheck_hits"] = hits
        standard_results.append(result)
        print_standard_line(i, len(standard_files), result)

    # --- Агрегация глобального решения ---
    decisions = [r["decision"] for r in standard_results]
    if "architect_required" in decisions:
        global_decision = "architect_required"
    elif "escalate" in decisions:
        global_decision = "escalate"
    else:
        global_decision = "architect_not_required"

    # --- Сводка по всем стандартам ---
    total_applicable = sum(r["summary"]["applicable"] for r in standard_results)
    total_not_applicable = sum(r["summary"]["not_applicable"] for r in standard_results)
    total_unclear = sum(r["summary"]["unclear"] for r in standard_results)
    total_input = sum(r["summary"]["total_input_tokens"] for r in standard_results)
    total_output = sum(r["summary"]["total_output_tokens"] for r in standard_results)

    triggered = [
        {
            "id": r["id"],
            "version": r["version"],
            "applicable_count": r["summary"]["applicable"],
            "unclear_count": r["summary"]["unclear"],
            "decision": r["decision"],
        }
        for r in standard_results
        if r["summary"]["applicable"] > 0 or r["summary"]["unclear"] > 0
    ]

    skipped_full = [
        {"id": r["id"], "version": r["version"],
         "reason": "no applicable or unclear requirements"}
        for r in standard_results
        if r["summary"]["applicable"] == 0 and r["summary"]["unclear"] == 0
    ]

    # --- Формируем итоговый отчёт ---
    report = {
        "proposal": str(proposal_path),
        "decided_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "decision": global_decision,
        "thresholds": {
            "trust": args.trust,
            "gray": args.gray,
            "margin_min": args.margin_min,
        },
        "precheck_enabled": not args.no_precheck,
        "summary": {
            "standards_total": len(standard_files),
            "standards_checked": len(standard_results),
            "standards_skipped_by_precheck": len(skipped_by_precheck),
            "standards_triggered": len(triggered),
            "total_requirements": total_applicable + total_not_applicable + total_unclear,
            "applicable": total_applicable,
            "not_applicable": total_not_applicable,
            "unclear": total_unclear,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
        },
        "triggered_standards": triggered,
        "skipped_standards": skipped_full,
        "skipped_by_precheck": skipped_by_precheck,
        "standards": standard_results,
    }

    # --- Итоги в консоль ---
    print("=" * 80)
    print(f"GLOBAL DECISION: {global_decision}")
    print(f"  standards total:     {len(standard_files)}")
    print(f"  standards checked:   {len(standard_results)}")
    print(f"  skipped by precheck: {len(skipped_by_precheck)}")
    print(f"  standards triggered: {len(triggered)}")
    print(f"  applicable:          {total_applicable}")
    print(f"  not_applicable:      {total_not_applicable}")
    print(f"  unclear:             {total_unclear}")
    print(f"  input_tokens:        {total_input}")
    print(f"  output_tokens:       {total_output}")

    if args.output:
        Path(args.output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nReport: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())