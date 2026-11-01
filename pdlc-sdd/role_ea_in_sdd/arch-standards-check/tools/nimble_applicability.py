#!/usr/bin/env python3
"""
Проверяет применимость каждого требования стандарта к proposal через Nimble.

Usage:
    python3 tools/nimble_applicability.py \
        --proposal tests/fixtures/proposal-wallet-fl.md \
        --standard standards/reliability/v2.0.yaml \
        [--output /tmp/report.json] \
        [--url http://localhost:11434/v1/systemone] \
        [--model nimble] \
        [--timeout 120] \
        [--trust 0.80] [--gray 0.55] [--margin-min 0.30] \
        [--raw]

Exit codes:
    0 — ok
    1 — HTTP / connection error
    2 — input error
    3 — timeout
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install pyyaml", file=sys.stderr)
    sys.exit(2)


# ---------------- Чтение входных файлов ----------------

def load_standard(path: Path) -> dict:
    """Читает YAML-файл стандарта и возвращает словарь."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_proposal(path: Path) -> str:
    """Читает markdown-файл proposal и возвращает строку."""
    return path.read_text(encoding="utf-8")


# ---------------- Сборка prompt для Nimble ----------------

def build_state(proposal: str, req: dict) -> str:
    """
    Собирает текст, который уйдёт в поле "state" запроса Nimble.
    Это то, что модель будет анализировать.
    """
    return (
        f"PROPOSAL:\n{proposal}\n\n"
        f"---\n"
        f"ТРЕБОВАНИЕ: {req['code']}\n"
        f"{req['description']}\n\n"
        f"УСЛОВИЕ ПРИМЕНИМОСТИ:\n{req['applicability'].strip()}\n"
    )


# ---------------- HTTP-вызов Nimble ----------------

def call_nimble(state: str, url: str, model: str, timeout: float) -> dict:
    """
    Отправляет POST-запрос к Nimble и возвращает разобранный JSON.
    Если что-то пошло не так — выбрасывает исключение, которое
    ловит main() и превращает в нужный exit code.
    """
    payload = {
        "model": model,
        "state": state,
        "questions": {
            "applicability": {
                "type": "choice",
                "instructions": "Применимо ли это требование к описанному proposal?",
                "criteria": {
                    "applicable": "Все условия применимости выполнены",
                    "not_applicable": "Хотя бы одно условие явно не выполнено",
                    "unclear": "Недостаточно информации для решения",
                },
            }
        },
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------------- Разбор ответа Nimble ----------------

def _first_str(d: dict, *keys):
    """Возвращает первое непустое строковое значение из словаря по списку ключей."""
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v:
            return v
    return None


def _first_num(d: dict, *keys):
    """Возвращает первое числовое значение из словаря по списку ключей."""
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                pass
    return None


def normalize(raw: dict) -> tuple[str, float, dict, dict]:
    """
    Достаёт из ответа Nimble 4 вещи:
      - choice        — какой вариант выбран ('applicable' / 'not_applicable' / 'unclear')
      - confidence    — уверенность модели (0..1)
      - probabilities — распределение по всем вариантам (словарь)
      - usage         — сколько токенов потрачено

    Модель может вернуть разные структуры — поэтому мы перебираем
    несколько возможных мест, где лежит ответ.
    """
    if not isinstance(raw, dict):
        return "unclear", 0.0, {}, {}

    usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else {}

    # Собираем список словарей-кандидатов, где может лежать choice.
    candidates: list[dict] = []

    def push(d):
        if isinstance(d, dict):
            candidates.append(d)

    push(raw)
    for key in ("questions", "answers", "results", "data"):
        if isinstance(raw.get(key), dict):
            push(raw[key])
            for sub in ("applicability", "label", "answer", "choice"):
                if isinstance(raw[key].get(sub), dict):
                    push(raw[key][sub])
    for sub in ("applicability", "label", "answer"):
        if isinstance(raw.get(sub), dict):
            push(raw[sub])

    # Проходим по кандидатам и ищем первого, у которого есть choice.
    for c in candidates:
        choice = _first_str(
            c, "choice", "label", "value", "selected",
            "answer", "verdict", "result",
        )
        conf = _first_num(
            c, "confidence", "probability", "score",
            "prob", "p", "conf",
        )
        if choice:
            probs = c.get("probabilities") if isinstance(c.get("probabilities"), dict) else {}
            return choice, (conf if conf is not None else 0.0), probs, usage

    return "unclear", 0.0, {}, usage


# ---------------- Логика принятия решения ----------------

def decision_from(
    choice: str,
    conf: float,
    probs: dict,
    trust: float,
    gray: float,
    margin_min: float,
) -> tuple[str, float, bool]:
    """
    Возвращает (verdict, margin, gray_zone).

    Логика:
      1. Если Nimble сам сказал 'unclear' — оставляем unclear.
      2. Считаем margin = top1 - top2 (насколько модель различает варианты).
      3. Если confidence >= trust ИЛИ margin >= margin_min — принимаем choice.
      4. Иначе — unclear (модель колеблется).

    Пример:
      conf=0.43, probs={app:0.43, not:0.30, un:0.27} → margin=0.13 → unclear
      conf=0.22, probs={not:0.75, app:0.15, un:0.10} → margin=0.60 → not_applicable
    """
    if choice == "unclear":
        return "unclear", 0.0, False

    # Считаем margin
    if len(probs) >= 2:
        vals = sorted(probs.values(), reverse=True)
        margin = vals[0] - vals[1]
    elif len(probs) == 1:
        margin = list(probs.values())[0]
    else:
        margin = 0.0

    gray_zone = gray <= conf < trust

    if conf >= trust or margin >= margin_min:
        return choice, margin, gray_zone
    return "unclear", margin, gray_zone


# ---------------- Точка входа ----------------

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--proposal", required=True,
                   help="Путь к markdown-файлу proposal")
    p.add_argument("--standard", required=True,
                   help="Путь к YAML-файлу стандарта")
    p.add_argument("--output", default=None,
                   help="Куда сохранить JSON-отчёт (если не указано — печатает в stdout)")
    p.add_argument("--url", default="http://localhost:11434/v1/systemone",
                   help="URL REST API Nimble")
    p.add_argument("--model", default="nimble",
                   help="Имя модели")
    p.add_argument("--timeout", type=float, default=120.0,
                   help="Таймаут одного запроса в секундах")
    p.add_argument("--trust", type=float, default=0.80,
                   help="Порог confidence, выше которого принимаем решение")
    p.add_argument("--gray", type=float, default=0.55,
                   help="Нижняя граница серой зоны (для отчёта)")
    p.add_argument("--margin-min", type=float, default=0.20,
                   help="Минимальный отрыв top1-top2 для принятия решения при низком confidence")
    p.add_argument("--raw", action="store_true",
                   help="Напечатать сырой ответ Nimble для первого требования и выйти")
    args = p.parse_args()

    # Проверка входных файлов
    proposal_path = Path(args.proposal)
    standard_path = Path(args.standard)
    if not proposal_path.exists():
        print(f"proposal not found: {proposal_path}", file=sys.stderr)
        return 2
    if not standard_path.exists():
        print(f"standard not found: {standard_path}", file=sys.stderr)
        return 2

    # Загрузка данных
    std = load_standard(standard_path)
    proposal = load_proposal(proposal_path)
    sid = std["standard"]["id"]
    sver = std["standard"]["version"]

    # Шапка отчёта
    print(f"Standard: {sid} v{sver}")
    print(f"Proposal: {proposal_path}  ({len(proposal)} chars)")
    print(f"Thresholds: trust={args.trust} gray={args.gray} margin_min={args.margin_min}")
    print("-" * 80)

    # Основной цикл
    results: list[dict] = []
    for req in std["requirements"]:
        state = build_state(proposal, req)

        # --- HTTP-вызов ---
        try:
            raw = call_nimble(state, args.url, args.model, args.timeout)
        except urllib.error.HTTPError as e:
            print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
            return 1
        except urllib.error.URLError as e:
            print(f"Connection error: {e.reason}", file=sys.stderr)
            return 1
        except TimeoutError:
            print(f"Timeout after {args.timeout}s", file=sys.stderr)
            return 3

        # --- Отладочный режим: печатаем первый сырой ответ и выходим ---
        if args.raw and not results:
            print(json.dumps(raw, ensure_ascii=False, indent=2))
            return 0

        # --- Разбор и решение ---
        choice, conf, probs, usage = normalize(raw)
        verdict, margin, gray_zone = decision_from(
            choice, conf, probs, args.trust, args.gray, args.margin_min,
        )

        results.append({
            "standard": sid,
            "standard_version": sver,
            "code": req["code"],
            "raw_choice": choice,
            "raw_confidence": conf,
            "raw_probabilities": probs,
            "margin": margin,
            "usage": usage,
            "verdict": verdict,
            "gray_zone": gray_zone,
        })

        # --- Красивый вывод в консоль ---
        mark = {"applicable": "✓", "not_applicable": "·"}.get(verdict, "?")
        extra = "  [gray]" if gray_zone else ""
        prob_str = ",".join(f"{k[:3]}={v:.2f}" for k, v in probs.items())
        print(
            f"  {mark} {req['code']:22s} {choice:15s} "
            f"conf={conf:.2f} margin={margin:.2f} → {verdict}{extra}  [{prob_str}]"
        )

    # --- Агрегируем решение по стандарту ---
    verdicts = [r["verdict"] for r in results]
    if "applicable" in verdicts:
        decision = "architect_required"
    elif "unclear" in verdicts:
        decision = "escalate"
    else:
        decision = "architect_not_required"

    # --- Считаем токены ---
    total_input = sum(r.get("usage", {}).get("input_tokens", 0) for r in results)
    total_output = sum(r.get("usage", {}).get("output_tokens", 0) for r in results)

    report = {
        "proposal": str(proposal_path),
        "standard": {
            "id": sid,
            "version": sver,
            "title": std["standard"].get("title"),
        },
        "thresholds": {
            "trust": args.trust,
            "gray": args.gray,
            "margin_min": args.margin_min,
        },
        "decision": decision,
        "summary": {
            "applicable": sum(1 for r in results if r["verdict"] == "applicable"),
            "not_applicable": sum(1 for r in results if r["verdict"] == "not_applicable"),
            "unclear": sum(1 for r in results if r["verdict"] == "unclear"),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
        },
        "requirements": results,
    }

    # --- Итоги в консоль ---
    print("-" * 80)
    print(f"Decision: {decision}")
    print(f"  applicable:     {report['summary']['applicable']}")
    print(f"  not_applicable: {report['summary']['not_applicable']}")
    print(f"  unclear:        {report['summary']['unclear']}")
    print(f"  input_tokens:   {total_input}")
    print(f"  output_tokens:  {total_output}")

    # --- Сохранение JSON ---
    if args.output:
        Path(args.output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Report: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())