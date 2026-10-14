#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50,<2"]
# ///
"""Export one editable draw.io page through the real editor, then rasterize its SVG.

Requires network access and an existing Chromium/Chrome browser. No browser install,
cloud publication, or source diagram modification is performed.
"""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path
from urllib.parse import unquote_to_bytes
from xml.etree import ElementTree as ET

from playwright.sync_api import Error as BrowserError, sync_playwright

SHELL = '''<html><body style="margin:0">
<iframe id="editor" style="width:100vw;height:100vh;border:0"></iframe>
<script>
window.events = [];
addEventListener('message', event => {
  if (event.origin !== 'https://embed.diagrams.net' ||
      event.source !== document.querySelector('iframe').contentWindow) return;
  try { window.events.push(JSON.parse(event.data)); }
  catch (error) { window.protocolError = String(error); }
});
document.querySelector('iframe').src =
  'https://embed.diagrams.net/?embed=1&proto=json&spin=1&libraries=1';
window.send = data => document.querySelector('iframe').contentWindow.postMessage(
  JSON.stringify(data), 'https://embed.diagrams.net');
</script></body></html>'''


def export(source: Path, prefix: Path, executable: str | None) -> tuple[Path, Path]:
    """Load one page in draw.io; preserve the input and export native editor output."""
    xml = source.read_text(encoding="utf-8")
    document = ET.fromstring(xml)
    if document.tag != "mxfile" or len(document.findall("diagram")) != 1:
        raise ValueError("Expected an mxfile containing exactly one diagram page")
    svg_path, png_path = Path(f"{prefix}.svg"), Path(f"{prefix}.png")
    if source.resolve() in {svg_path.resolve(), png_path.resolve()}:
        raise ValueError("Output must not overwrite the editable source")
    prefix.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as runtime:
        browser = runtime.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page(viewport={"width": 1500, "height": 1350})
            page.set_content(SHELL)
            page.wait_for_function("window.events.some(e => e.event === 'init')", timeout=60000)
            page.evaluate("xml => {window.events = []; window.send({action:'load', xml});}", xml)
            page.wait_for_function("window.events.some(e => e.event === 'load')", timeout=60000)
            page.evaluate("window.send({action:'export', format:'svg', spinKey:'export'})")
            page.wait_for_function("window.events.some(e => e.event === 'export')", timeout=60000)
            result = page.evaluate("window.events.find(e => e.event === 'export')")
            data = result.get("data", "")
            if not data.startswith("data:image/svg+xml") or "," not in data:
                raise ValueError("draw.io did not return an SVG export")
            header, payload = data.split(",", 1)
            svg = base64.b64decode(payload, validate=True) if ";base64" in header else unquote_to_bytes(payload)
            if ET.fromstring(svg).tag.split("}")[-1] != "svg":
                raise ValueError("Export content is not an SVG document")
            svg_path.write_bytes(svg)
            preview = browser.new_page(viewport={"width": 1500, "height": 1350})
            preview.set_content(svg.decode("utf-8"))
            preview.locator("svg").first.screenshot(path=str(png_path))
        finally:
            browser.close()
    return svg_path, png_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output-prefix", type=Path, help="Output path without extension")
    parser.add_argument("--browser-executable", help="Existing Chrome/Chromium executable")
    args = parser.parse_args()
    prefix = args.output_prefix or args.source.with_suffix("")
    try:
        paths = export(args.source, prefix, args.browser_executable)
    except (OSError, ValueError, ET.ParseError, BrowserError) as error:
        print(f"Preview export failed: {error}", file=sys.stderr)
        return 1
    for path in paths:
        print(f"Exported {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
