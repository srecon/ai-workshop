#!/usr/bin/env python3
"""
systemone-check.py

Usage:
    python3 systemone-check.py "Необходимо обеспечить регистрацию событий аудита..."
"""

import json
import sys
import urllib.request
import urllib.error


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: systemone-check.py <state>", file=sys.stderr)
        return 2

    state = sys.argv[1]

    payload = {
        "model": "nimble",
        "state": state,
        "questions": {
            "label": {
                "type": "choice",
                "instructions": "Какой из этих меток соответствует вопросу?",
                "criteria": {
                    "Архитектурный вопрос": None,
                    "Вопрос к разработку": None,
                    "Аналитика": None,
                },
            }
        },
    }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url="http://localhost:11434/v1/systemone",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            print(body)
    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code}: {e.reason}", file=sys.stderr)
        print(e.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
