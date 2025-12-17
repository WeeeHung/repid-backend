import argparse
import json
import os
import sys
from typing import Optional

import requests

# token: eyJhbGciOiJFUzI1NiIsImtpZCI6IjI4MGFjYTBlLWI4NzctNDg0OS05NTdhLWMwODg2ZjQ4ZTNlOSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3VvaWZybHd3cnpncWxkdnpsY3RuLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI2MmJlOGM5Mi00YzI5LTRhYmYtYTM1Ny0wMjc3YzlkZjIzZGQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzY1ODgyODkxLCJpYXQiOjE3NjU4NzkyOTEsImVtYWlsIjoid2VlaHVuZ0B1Lm51cy5lZHUiLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsIjoid2VlaHVuZ0B1Lm51cy5lZHUiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiI2MmJlOGM5Mi00YzI5LTRhYmYtYTM1Ny0wMjc3YzlkZjIzZGQifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc2NTg2NDQ4MH1dLCJzZXNzaW9uX2lkIjoiNDlkMDBhZjYtYjM3Zi00ZDVhLTkxMjctMmE2ZWIxYmNiZDQ5IiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.vApYyI-7UCSs5mcJCp2_0Smsbq0Eb5L_cYyED81K3KJwaBZ3Gz7ITUSiMYeL2bxyeDf0Fl9PwW6itcqO7n8V8w


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    return value if value is not None else default


def pretty_log_response(label: str, resp: requests.Response) -> None:
    """Print detailed information about an HTTP response for inspection."""
    print(f"\n--- {label} ---")
    print(f"URL:     {resp.request.method} {resp.url}")
    print(f"Status:  {resp.status_code}")

    if resp.request.headers:
        print("Request headers:")
        for k, v in resp.request.headers.items():
            print(f"  {k}: {v}")

    if resp.request.body:
        print("Request body:")
        try:
            body_json = json.loads(resp.request.body)
            print(json.dumps(body_json, indent=2, sort_keys=True))
        except Exception:
            print(resp.request.body)

    print("Response headers:")
    for k, v in resp.headers.items():
        print(f"  {k}: {v}")

    try:
        data = resp.json()
        print("Response JSON:")
        print(json.dumps(data, indent=2, sort_keys=True))
    except Exception:
        print("Non-JSON response body:")
        print(resp.text)


def main() -> None:
    """
    Simple manual tester for core workout-related API endpoints.

    Endpoints covered:
      - GET  /api/v1/workouts/{workout_id}
      - POST /api/v1/workout/generate-audio

    Usage (preferred, avoids exporting env vars permanently):
      BASE_URL=http://localhost:8000 \\
      WORKOUT_ID=<uuid> \\
      AUTH_TOKEN=<supabase_jwt> \\
      python test_core_endpoints.py

    Or via CLI args (overrides env vars):
      python test_core_endpoints.py \\
        --workout-id <uuid> \\
        --auth-token <supabase_jwt> \\
        --base-url http://localhost:8000

    Environment variables:
      - BASE_URL   (optional, default: http://localhost:8000)
      - WORKOUT_ID (required)
      - AUTH_TOKEN (optional, but required for /workout/generate-audio)
    """
    parser = argparse.ArgumentParser(description="Test core workout-related API endpoints.")
    parser.add_argument("--base-url", dest="base_url", help="API base URL (default: http://localhost:8000)")
    parser.add_argument("--workout-id", dest="workout_id", help="Workout package UUID to test with")
    parser.add_argument("--auth-token", dest="auth_token", help="Supabase JWT access token")
    args = parser.parse_args()

    # CLI args override env vars; env vars provide defaults.
    base_url = args.base_url or get_env("BASE_URL", "http://localhost:8000")
    workout_id = args.workout_id or get_env("WORKOUT_ID")
    auth_token = args.auth_token or get_env("AUTH_TOKEN")

    if not workout_id:
        print("ERROR: Please provide WORKOUT_ID env var (e.g. a workout package UUID).")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # 1) GET /api/v1/workouts/{workout_id}
    # -------------------------------------------------------------------------
    get_url = f"{base_url}/api/v1/workouts/{workout_id}"
    print(f"\n=== GET {get_url} ===")

    try:
        get_resp = requests.get(get_url)
    except Exception as exc:
        print(f"Request failed: {exc}")
        sys.exit(1)

    pretty_log_response("GET /api/v1/workouts/{workout_id}", get_resp)

    # -------------------------------------------------------------------------
    # 2) POST /api/v1/workout/generate-audio
    # -------------------------------------------------------------------------
    # post_url = f"{base_url}/api/v1/workout/generate-audio"
    # print(f"\n=== POST {post_url} ===")

    # headers = {"Content-Type": "application/json"}
    # if auth_token:
    #     headers["Authorization"] = f"Bearer {auth_token}"
    # else:
    #     print("WARNING: AUTH_TOKEN not set – generate-audio will likely fail due to missing authentication.")

    # payload = {"workout_package_id": workout_id}

    # try:
    #     post_resp = requests.post(post_url, json=payload, headers=headers)
    # except Exception as exc:
    #     print(f"Request failed: {exc}")
    #     sys.exit(1)

    # pretty_log_response("POST /api/v1/workout/generate-audio", post_resp)


if __name__ == "__main__":
    main()


