#!/usr/bin/env python3
"""Test OMLX local inference using the OpenAI-compatible API."""

import os
import sys
import time

from openai import OpenAI
from openai import APIConnectionError, APIStatusError, APITimeoutError

# OMLX server configuration
BASE_URL = "http://127.0.0.1:8000/v1"
MODEL = "Qwen3.6-35B-A3B-MLX-4bit"
API_KEY = os.getenv("OMLX_API_KEY", "sk-omlx")

TIMEOUT_SECONDS = 600
MAX_TOKENS = 8192

def main():
    client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        timeout=TIMEOUT_SECONDS,
        max_retries=0,
    )

    prompt = (
        "Explain how Python async and await work. "
        "Give a short example and explain why it is useful."
    )

    print("=" * 65)
    print("OMLX Inference Test")
    print("=" * 65)
    print(f"Endpoint : {BASE_URL}")
    print(f"Model    : {MODEL}")
    print(f"Prompt   : {prompt}")
    print("-" * 65)
    print("Sending request...")

    start_time = time.perf_counter()

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful programming assistant.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
            top_p=0.8,
            max_tokens=MAX_TOKENS,
        )

        elapsed = time.perf_counter() - start_time

        answer = response.choices[0].message.content or ""

        print("\nResponse:")
        print("-" * 65)
        print(answer)
        print("-" * 65)

        print("\nPerformance:")
        print(f"Elapsed time : {elapsed:.2f} seconds")
        print(f"Finish reason: {response.choices[0].finish_reason}")

        if response.usage:
            print(f"Input tokens : {response.usage.prompt_tokens}")
            print(f"Output tokens: {response.usage.completion_tokens}")
            print(f"Total tokens : {response.usage.total_tokens}")

            output_tokens = response.usage.completion_tokens
            if elapsed > 0 and output_tokens:
                print(f"Overall output rate: {output_tokens / elapsed:.2f} tokens/sec")

        print("\nSUCCESS: Inference completed.")

    except APIConnectionError as exc:
        print(f"\nCONNECTION ERROR: Cannot connect to {BASE_URL}")
        print("Check that OMLX is running and listening on port 8000.")
        print(f"Details: {exc}")
        sys.exit(1)

    except APITimeoutError:
        print(f"\nTIMEOUT: Request exceeded {TIMEOUT_SECONDS} seconds.")
        print("Check the model's inference progress and server logs.")
        sys.exit(1)

    except APIStatusError as exc:
        print(f"\nAPI ERROR: HTTP {exc.status_code}")
        print(exc.message)
        sys.exit(1)

    except Exception as exc:
        print(f"\nUNEXPECTED ERROR: {type(exc).__name__}: {exc}")
        sys.exit(1)

    finally:
        client.close()


if __name__ == "__main__":
    main()
