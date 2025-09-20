#!/usr/bin/env python3
"""
S3 presign smoke test: requests a presigned upload URL from the API and prints
ready-to-run curl commands to complete the upload. Does not require jq.

Usage:
    python scripts/s3_presign_smoke.py --base-url https://api.mapmystandards.ai \
            --token <JWT> --filename hello.txt --content-type text/plain --size 12

Optional:
    --folder <prefix>     Organize under a subfolder (default: smoke)
    --write-file          Writes a small sample file with the given filename
    --auto-upload         Perform the S3 form POST automatically (uses curl)
    --save-key PATH       Save the returned file_key to PATH for later use

Note: This script does not perform the actual S3 upload to avoid extra deps.
      It prints the exact curl command you can copy/paste to complete it.
"""

import argparse
import json
import os
import sys
import textwrap
from urllib import request as urlreq
import subprocess


def http_post_json(url: str, payload: dict, headers: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urlreq.Request(url, data=data, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    req.add_header("Content-Type", "application/json")
    try:
        with urlreq.urlopen(req, timeout=20) as resp:
            body = resp.read()
            status = resp.getcode()
            try:
                js = json.loads(body.decode("utf-8"))
            except Exception:
                js = {"raw": body.decode("utf-8", errors="ignore")}
            return status, js
    except urlreq.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        try:
            js = json.loads(body)
        except Exception:
            js = {"error": body}
        return e.code, js


def main():
    ap = argparse.ArgumentParser(description="S3 presign smoke test")
    ap.add_argument("--base-url", required=True, help="API base URL e.g. https://api.mapmystandards.ai")
    ap.add_argument("--token", required=True, help="Bearer JWT token")
    ap.add_argument("--filename", required=True)
    ap.add_argument("--content-type", required=True)
    ap.add_argument("--size", type=int, required=True)
    ap.add_argument("--folder", default="smoke")
    ap.add_argument("--write-file", action="store_true")
    ap.add_argument("--auto-upload", action="store_true")
    ap.add_argument("--save-key")
    args = ap.parse_args()

    if args.write_file:
        with open(args.filename, "wb") as f:
            f.write(b"hello from smoke test\n")
        print(f"Wrote sample file: {args.filename}")

    presign_url = args.base_url.rstrip("/") + "/api/upload/presign"
    payload = {
        "filename": args.filename,
        "content_type": args.content_type,
        "size": args.size,
    }

    status, js = http_post_json(
        presign_url,
        payload,
        headers={"Authorization": f"Bearer {args.token}"},
    )
    if status != 200:
        print(f"Presign failed: HTTP {status}\n{json.dumps(js, indent=2)}")
        sys.exit(1)

    # Expected keys from our API contract
    upload_url = js.get("upload_url") or js.get("url")
    fields = js.get("upload_fields") or js.get("fields") or {}
    file_key = js.get("file_key") or js.get("key")

    print("\n✅ Presign OK")
    print(json.dumps({k: js.get(k) for k in ["file_key", "expires_in"] if k in js}, indent=2))

    if fields:
        # S3 form POST style
        print("\nS3 Upload (form POST) — copy/paste:")
        parts = ["curl -s -X POST "]
        parts.append(f"{upload_url!r} ")
        for k, v in fields.items():
            # Escape single quotes in values
            vstr = str(v).replace("'", "'\"'\"'")
            parts.append(f"-F '{k}={vstr}' ")
        parts.append(f"-F 'file=@{args.filename};type={args.content_type}'")
        curl_cmd = "".join(parts)
        print(curl_cmd)

        if args.auto_upload:
            # Build argv form to avoid shell quoting issues
            argv = ["curl", "-s", "-X", "POST", upload_url]
            for k, v in fields.items():
                argv += ["-F", f"{k}={v}"]
            argv += ["-F", f"file=@{args.filename};type={args.content_type}"]
            print("\nRunning S3 upload via curl...", flush=True)
            result = subprocess.run(argv, capture_output=True, text=True)
            if result.returncode != 0:
                print("S3 upload failed:", result.stderr or result.stdout)
                sys.exit(2)
            # S3 typically returns 204 or 201 with no body for form POST
            print("S3 upload complete (HTTP 2xx).")
    else:
        # PUT style
        print("\nS3 Upload (PUT) — copy/paste:")
        print(
            f"curl -s -X PUT '{upload_url}' -H 'Content-Type: {args.content_type}' --data-binary '@{args.filename}'"
        )

    # Optionally print a download hint if your API exposes it later
    if file_key:
        print("\nFILE_KEY=", file_key)
        if args.save_key:
            try:
                with open(args.save_key, "w") as f:
                    f.write(file_key)
                print(f"Saved file key to: {args.save_key}")
            except Exception as e:
                print(f"Warning: couldn't save file key: {e}")


if __name__ == "__main__":
    main()
