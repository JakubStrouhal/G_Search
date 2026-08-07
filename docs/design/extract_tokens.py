#!/usr/bin/env python3
"""Extract Groupon's design tokens from the live www.groupon.com homepage.

Groupon ships Tailwind v4 with its token layer inlined in a <style> block on the
server-rendered homepage. Colour tokens are authored in CSS `oklch()`, which is
not directly usable in a Vue/Tailwind prototype, so this script converts each one
to an sRGB hex value.

Only declarations inside `:root` / `html` rules are read. That matters: the page
also carries a `[data-templateId="livingsocial"]` block that re-points
`--color-primary` at blue. Groupon's own primary is green; the blue is the
LivingSocial skin. A naive "last declaration wins" scrape gets this backwards.

  python3 docs/design/extract_tokens.py            # fetch live, write outputs
  python3 docs/design/extract_tokens.py page.html  # parse a saved copy instead

Writes, next to this file:
  outputs/tokens.json   every custom property, raw + resolved + hex
  outputs/tokens.css    :root block, hex only, ready to paste into the prototype

Re-run this before quoting any colour. Numbers in prose drift; scripts do not.
Note: hex values are sRGB conversions of D50 `lab()` sources, so they are exact
to within rounding, not byte-identical to whatever Groupon's designers typed.
"""

import json
import math
import pathlib
import re
import sys
import urllib.request

URL = "https://www.groupon.com/"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0 Safari/537.36"
)
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "outputs"

# ---------------------------------------------------------------- colour maths

EPS = 216 / 24389
KAPPA = 24389 / 27
# CSS Color 4: lab() is D50-referred.
D50 = (0.3457 / 0.3585, 1.0, (1 - 0.3457 - 0.3585) / 0.3585)
# Bradford-adapted D50 -> D65, then XYZ D65 -> linear sRGB (CSS Color 4 matrices).
D50_TO_D65 = (
    (0.9554734527042182, -0.023098536874261423, 0.0632593086610217),
    (-0.028369706963208136, 1.0099954580058226, 0.021041398966943008),
    (0.012314001688319899, -0.020507696433477912, 1.3303659366080753),
)
XYZ_TO_RGB = (
    (3.2409699419045226, -1.537383177570094, -0.4986107602930034),
    (-0.9692436362808796, 1.8759675015077202, 0.04155505740717559),
    (0.05563007969699366, -0.20397695888897652, 1.0569715142428786),
)


def _mul(m, v):
    return tuple(sum(row[i] * v[i] for i in range(3)) for row in m)


def _gamma(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def lab_to_hex(L, a, b):
    fy = (L + 16) / 116
    fx = fy + a / 500
    fz = fy - b / 200
    f = lambda t, cmp: t**3 if t**3 > EPS else (116 * t - 16) / KAPPA  # noqa: E731
    xyz = (f(fx, 0) * D50[0], f(fy, 1) * D50[1], f(fz, 2) * D50[2])
    lin = _mul(XYZ_TO_RGB, _mul(D50_TO_D65, xyz))
    return "#" + "".join(f"{round(_gamma(c) * 255):02x}" for c in lin)


OKLAB_TO_LMS = (
    (1.0, 0.3963377774, 0.2158037573),
    (1.0, -0.1055613458, -0.0638541728),
    (1.0, -0.0894841775, -1.2914855480),
)
LMS_TO_RGB = (
    (4.0767416621, -3.3077115913, 0.2309699292),
    (-1.2684380046, 2.6097574011, -0.3413193965),
    (-0.0041960863, -0.7034186147, 1.7076147010),
)


def oklch_to_hex(L, C, H):
    lab = (L, C * math.cos(math.radians(H)), C * math.sin(math.radians(H)))
    lms = tuple(v**3 for v in _mul(OKLAB_TO_LMS, lab))
    return "#" + "".join(f"{round(_gamma(c) * 255):02x}" for c in _mul(LMS_TO_RGB, lms))


NUM = r"[\d.+-]+"
LAB_RE = re.compile(rf"lab\(\s*({NUM})%?\s+({NUM})\s+({NUM})\s*(?:/\s*([\d.%]+)\s*)?\)")
OKLCH_RE = re.compile(
    rf"oklch\(\s*({NUM})(%?)\s+({NUM})\s+({NUM})(?:deg)?\s*(?:/\s*([\d.%]+)\s*)?\)"
)
HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}")


def _alpha(a):
    if a is None:
        return None
    return round(float(a[:-1]) / 100 if a.endswith("%") else float(a), 3)


def to_hex(value):
    """Return (hex, alpha) for a colour value, or (None, None) if it is not one."""
    v = value.strip()
    if (m := OKLCH_RE.fullmatch(v)) is not None:
        L, pct, C, H, a = m.groups()
        L = float(L) / 100 if pct else float(L)
        return oklch_to_hex(L, float(C), float(H)), _alpha(a)
    if (m := LAB_RE.fullmatch(v)) is not None:
        L, A, B, a = m.groups()
        return lab_to_hex(float(L), float(A), float(B)), _alpha(a)
    if HEX_RE.fullmatch(v):
        v = v.lower()
        if len(v) == 4:  # #abc -> #aabbcc
            v = "#" + "".join(c * 2 for c in v[1:])
        if len(v) == 9:  # #rrggbbaa
            return v[:7], round(int(v[7:], 16) / 255, 3)
        return v, None
    return None, None


# ---------------------------------------------------------------- css scraping

VAR_RE = re.compile(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;}]+)")
REF_RE = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)\s*(?:,[^)]*)?\)")


def load_html(argv):
    if len(argv) > 1:
        return pathlib.Path(argv[1]).read_text(encoding="utf-8", errors="replace")
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


RULE_RE = re.compile(r"([^{}@]+)\{([^{}]*)\}")
UNSCOPED = {":root", ":host", "html", "*", ":after", ":before", "::backdrop"}


def _is_unscoped(selector):
    parts = [p.strip() for p in selector.split(",") if p.strip()]
    return bool(parts) and all(p in UNSCOPED for p in parts)


def collect(html):
    """Read custom properties from unscoped :root / html rules only.

    Later declarations win among those, matching the cascade. Theme-scoped blocks
    such as [data-templateId="livingsocial"] are skipped by construction — see the
    module docstring for why that is the whole point.
    """
    raw, skipped = {}, {}
    for block in re.findall(r"<style[^>]*>(.*?)</style>", html, re.S):
        for selector, body in RULE_RE.findall(block):
            selector = selector.rsplit("}", 1)[-1].strip()  # drop any preceding rule tail
            if "--" not in body:
                continue
            target = raw if _is_unscoped(selector) else skipped
            for name, value in VAR_RE.findall(body):
                if name.startswith("--tw-"):  # Tailwind internals, not design tokens
                    continue
                target[name] = value.strip()
    return raw, skipped


def resolve(name, raw, seen=None):
    seen = seen or set()
    if name in seen or name not in raw:
        return raw.get(name, "")
    seen.add(name)
    value = raw[name]
    for _ in range(8):  # guard against reference cycles
        m = REF_RE.search(value)
        if m is None:
            break
        repl = resolve(m.group(1), raw, seen)
        if not repl or REF_RE.search(repl):
            break
        value = value[: m.start()] + repl + value[m.end() :]
    return value.strip()


def main():
    html = load_html(sys.argv)
    raw, skipped = collect(html)
    if "--color-green-600" not in raw:
        sys.exit("token block not found — the homepage markup changed")

    tokens = {}
    for name in sorted(raw):
        resolved = resolve(name, raw)
        hexval, alpha = to_hex(resolved)
        entry = {"raw": raw[name]}
        if resolved != raw[name]:
            entry["resolved"] = resolved
        if hexval:
            entry["hex"] = hexval
            if alpha is not None:
                entry["alpha"] = alpha
        tokens[name] = entry

    OUT.mkdir(exist_ok=True)
    (OUT / "tokens.json").write_text(json.dumps(tokens, indent=1) + "\n")

    lines = [
        "/* Groupon design tokens — generated by docs/design/extract_tokens.py.",
        "   Source: :root/:host rules in the inline <style> on https://www.groupon.com/",
        "   (Tailwind v4). oklch()/lab() sources converted to sRGB hex; theme-scoped",
        "   overrides such as [data-templateId=livingsocial] excluded. Do not hand-edit. */",
        ":root {",
    ]
    for name, e in tokens.items():
        if "hex" in e:
            v = e["hex"]
            if e.get("alpha") is not None:
                r, g, b = (int(v[i : i + 2], 16) for i in (1, 3, 5))
                v = f"rgba({r}, {g}, {b}, {e['alpha']})"
        else:
            v = e.get("resolved", e["raw"])
        lines.append(f"  {name}: {v};")
    lines.append("}")
    (OUT / "tokens.css").write_text("\n".join(lines) + "\n")

    colours = sum(1 for e in tokens.values() if "hex" in e)
    print(f"{len(tokens)} tokens ({colours} colours) -> {OUT}/tokens.json, tokens.css")
    for k in ("--color-primary", "--color-green-600", "--color-blue-500",
              "--color-neutral-900", "--text-color-extra-price"):
        if k in tokens:
            print(f"  {k}: {tokens[k].get('hex', tokens[k]['raw'])}")
    if skipped:
        print(f"  ({len(skipped)} theme-scoped declarations ignored, "
              f"e.g. --color-primary: {skipped.get('--color-primary', 'n/a')})")


if __name__ == "__main__":
    main()
