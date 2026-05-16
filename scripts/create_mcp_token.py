#!/usr/bin/env python3
"""Create an MCP token via the running Flask backend.

The token is printed to stdout exactly once. Save it somewhere safe.

Usage:
    python scripts/create_mcp_token.py [name]

Environment:
    APC_BASE_URL  default: http://127.0.0.1:8765
"""
import json
import os
import sys
import urllib.request
import urllib.error


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "mcp-cli"
    base = os.environ.get("APC_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
    body = json.dumps({"name": name}).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/api/settings/tokens",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"ERROR: cannot reach backend at {base}: {e}", file=sys.stderr)
        print("Make sure the Flask backend is running:", file=sys.stderr)
        print("  cd agent-project-console/backend && python run.py", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    print("Token created. Copy it now — it will not be shown again.")
    print()
    print(f"  name : {data.get('name')}")
    print(f"  id   : {data.get('id')}")
    print(f"  token: {data.get('token')}")
    print()
    print("Set this in your MCP config:")
    print(f"  APC_MCP_TOKEN={data.get('token')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
