#!/usr/bin/env python3
"""pbi-fees - build the edge output from source.

    python build.py            src/index.html -> dist/index.html
    python build.py --verify   build, then print the SHA-256 and byte count

Source of truth for the page: src/index.html (byte-identical to the live Pages
project). The dist/ output is what a custom-domain request receives after the
pbi-edge Worker has run. dist/ is a build artifact and is git-ignored.

This lane is read-only against Cloudflare: it never deploys and never changes DNS.
"""
import hashlib, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "index.html")
DIST = os.path.join(ROOT, "dist")
OUT = os.path.join(DIST, "index.html")

# Verbatim from edge/pbi-edge-transform.mjs, which is verbatim from worker.js.
PLAYER_TAG = '<script src="/_pbi/player.js" defer></script>'
LAYOUT = ("<style>elevenlabs-convai{right:16px!important;bottom:24px!important}"
          "@media(max-width:640px){elevenlabs-convai{right:10px!important;bottom:76px!important}}</style>")
NETWORK_DEFAULT = ("agent_7601kv76b5cgfq9thvb5mxsdqsw0", "#c9c5bb", "#0a0a0a")


def convai_tag(a):
    aid, c1, c2 = a
    return ("<style>elevenlabs-convai{position:fixed;right:16px;bottom:24px;z-index:2147482000}"
            "@media(max-width:640px){elevenlabs-convai{bottom:76px;right:10px}}</style>"
            '<elevenlabs-convai agent-id="' + aid +
            '" avatar-orb-color-1="' + c1 + '" avatar-orb-color-2="' + c2 +
            '"></elevenlabs-convai>'
            '<script src="https://unpkg.com/@elevenlabs/convai-widget-embed" async type="text/javascript"></script>')


def transform(html):
    out = html
    if "/_pbi/player.js" not in out:
        out = re.sub(r"</head\s*>", PLAYER_TAG + "</head>", out, count=1, flags=re.I)
    out = re.sub(r"</body\s*>", LAYOUT + convai_tag(NETWORK_DEFAULT) + "\n</body>", out, count=1, flags=re.I)
    return out


def main():
    origin = open(SRC, "rb").read().decode("utf-8")
    built = transform(origin).encode("utf-8")
    os.makedirs(DIST, exist_ok=True)
    # newline="" so Windows does not convert LF to CRLF in the output bytes.
    with open(OUT, "wb") as f:
        f.write(built)
    digest = hashlib.sha256(built).hexdigest()
    if "--verify" in sys.argv:
        print("origin %d B  sha %s" % (len(origin.encode("utf-8")),
                                       hashlib.sha256(origin.encode("utf-8")).hexdigest()))
        print("built  %d B  sha %s" % (len(built), digest))
        return 0
    print("wrote %s  %d B  sha %s" % (OUT, len(built), digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
