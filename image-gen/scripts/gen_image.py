#!/usr/bin/env python3
"""image-gen skill script: generate an image with the OpenAI Images API.

Usage:
    python gen_image.py --prompt "水墨風中秋月夜" --out output.png --size 1024x1024

The API key is read from the OPENAI_API_KEY environment variable.
Never hardcode the key in this file.
"""
from __future__ import annotations

import argparse
import base64
import os
import sys
import urllib.request
from pathlib import Path


def fail(msg: str) -> None:
    print(f"[image-gen] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    # Windows console safety: avoid gbk/codec errors on CJK output.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="Generate an image with OpenAI")
    ap.add_argument("--prompt", required=True, help="image prompt")
    ap.add_argument("--out", default="output.png", help="output file path (default: output.png)")
    ap.add_argument("--size", default="1024x1024",
                    help="1024x1024 | 1536x1024 | 1024x1536 | auto")
    ap.add_argument("--model", default="gpt-image-1",
                    help="model id (default: gpt-image-1)")
    ap.add_argument("--quality", default=None, choices=["low", "medium", "high", "auto"],
                    help="quality (gpt-image-1 only)")
    ap.add_argument("--ref", nargs="+", default=None, metavar="IMG",
                    help="reference image path(s); switches to images.edit (style/consistency)")
    ap.add_argument("--transparent", action="store_true",
                    help="request transparent background (gpt-image-1 only)")
    args = ap.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        fail("OPENAI_API_KEY is not set. Set it in your own terminal with: "
             "[Environment]::SetEnvironmentVariable(\"OPENAI_API_KEY\",\"sk-...\",\"User\") "
             "then restart OpenCode.")

    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        fail("Python package 'openai' is missing. Install it with: pip install openai")

    out = Path(args.out).expanduser()
    if out.suffix == "":
        out = out.with_suffix(".png")
    out.parent.mkdir(parents=True, exist_ok=True)

    client = OpenAI(api_key=api_key)

    kwargs: dict = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "n": 1,
    }
    if args.quality:
        kwargs["quality"] = args.quality
    if args.transparent:
        # gpt-image-1 only; ignored/errored on older models.
        kwargs["background"] = "transparent"

    ref_handles = []
    if args.ref:
        # images.edit: pass reference image(s) for style/subject consistency.
        files = []
        for ref in args.ref:
            rp = Path(ref).expanduser()
            if not rp.is_file():
                fail(f"reference image not found: {rp}")
            fh = rp.open("rb")
            ref_handles.append(fh)
            files.append(fh)
        kwargs["image"] = files if len(files) > 1 else files[0]

    print(f"[image-gen] generating: model={args.model} size={args.size} ref={bool(args.ref)} -> {out}")
    try:
        if args.ref:
            result = client.images.edit(**kwargs)
        else:
            result = client.images.generate(**kwargs)
    except Exception as exc:  # noqa: BLE001 - surface the API error verbatim
        fail(f"OpenAI API request failed: {exc}")
    finally:
        for fh in ref_handles:
            fh.close()

    item = result.data[0]
    if getattr(item, "b64_json", None):
        out.write_bytes(base64.b64decode(item.b64_json))
    elif getattr(item, "url", None):
        with urllib.request.urlopen(item.url) as resp:
            out.write_bytes(resp.read())
    else:
        fail("unexpected API response: neither b64_json nor url")

    print(f"[image-gen] OK: {out.resolve()}")


if __name__ == "__main__":
    main()
