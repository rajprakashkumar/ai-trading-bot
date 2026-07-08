#!/usr/bin/env python3
"""One-shot deploy of local project files to PythonAnywhere.

Usage:
    python deploy_pythonanywhere_app.py
    python deploy_pythonanywhere_app.py --only app.py market_watch.html

Reads credentials from pythonanywhere_deploy/credentials.json:
  {"username": "...", "api_token": "..."}
"""

from pathlib import Path
import argparse
import json
import requests
import sys


DEFAULT_FILES = [
        "app.py",
        "market_watch.html",
        "holdings_dashboard.html",
        "dashboard_live.html",
        "requirements.txt",
        "kite_config.py",
]


def load_credentials(path: Path) -> tuple[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    username = (data.get("username") or "").strip()
    token = (data.get("api_token") or "").strip()
    if not username or not token:
        raise ValueError("credentials.json must contain username and api_token")
    return username, token


def upload_file(username: str, headers: dict[str, str], local_path: Path) -> tuple[bool, str]:
    remote_name = local_path.name
    upload_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/files/path/home/{username}/mysite/{remote_name}"
    with local_path.open("rb") as f:
        resp = requests.post(upload_url, headers=headers, files={"content": f}, timeout=240)
    if resp.status_code != 200:
        return False, f"{resp.status_code}: {resp.text[:250]}"
    return True, "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy local project files to PythonAnywhere")
    parser.add_argument(
        "--only",
        nargs="+",
        default=None,
        help="Optional list of filenames to upload (workspace-relative, e.g. app.py market_watch.html)",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    cred_path = root / "pythonanywhere_deploy" / "credentials.json"

    if not cred_path.exists():
        print(f"[ERROR] Missing credentials file: {cred_path}")
        return 1

    try:
        username, token = load_credentials(cred_path)
    except Exception as exc:
        print(f"[ERROR] Could not load credentials: {exc}")
        return 1

    requested_files = args.only if args.only else DEFAULT_FILES
    existing_files: list[Path] = []
    skipped_files: list[str] = []
    for file_name in requested_files:
        p = root / file_name
        if p.exists() and p.is_file():
            existing_files.append(p)
        else:
            skipped_files.append(file_name)

    if not existing_files:
        print("[ERROR] No valid files to upload. Use --only with existing filenames.")
        return 1

    headers = {"Authorization": f"Token {token}"}
    reload_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{username}.pythonanywhere.com/reload/"

    print(f"[INFO] Uploading {len(existing_files)} file(s) to /home/{username}/mysite ...")
    if skipped_files:
        print(f"[WARN] Skipping missing file(s): {', '.join(skipped_files)}")

    for file_path in existing_files:
        print(f"[INFO] Uploading {file_path.name}...")
        ok, message = upload_file(username, headers, file_path)
        if not ok:
            print(f"[ERROR] Upload failed for {file_path.name}: {message}")
            return 1
        print(f"[OK] {file_path.name} uploaded")

    print("[INFO] Reloading web app...")
    reload_resp = requests.post(reload_url, headers=headers, timeout=60)

    if reload_resp.status_code != 200:
        print(f"[ERROR] Reload failed: {reload_resp.status_code}")
        print(reload_resp.text[:500])
        return 1

    print("[OK] Reload complete")

    # Optional quick health check.
    health_url = f"https://{username}.pythonanywhere.com/api/health"
    try:
        health_resp = requests.get(health_url, timeout=20)
        print(f"[INFO] Health check: {health_resp.status_code}")
    except Exception as exc:
        print(f"[WARN] Health check failed: {exc}")

    print(f"[DONE] Deployment successful ({len(existing_files)} file(s) uploaded)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
