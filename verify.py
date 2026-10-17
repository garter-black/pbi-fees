#!/usr/bin/env python3
"""pbi-fees - prove this repo reproduces the live site.

    python verify.py

Materialises every tracked blob out of git into a clean checkout, runs build.py
there, fetches the live brand hostname three times (one cache-busted), removes
Cloudflare's Web Analytics beacon, and byte-compares.

Exit 0 = the committed source regenerates the live document.
"""
import hashlib, os, re, shutil, subprocess, ssl, sys, tempfile, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
LIVE = "https://fees.black.industries/"
PAGES = "https://pbi-fees.pages.dev/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
BEACON = re.compile(rb'<script type="module" src="https://static\.cloudflareinsights\.com[^"]*"[^>]*>\s*</script>', re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40, context=ssl.create_default_context()) as r:
        return r.read()


def clean_checkout(tmp):
    """Write every git-tracked blob to disk. Proves the rebuild runs on COMMITTED
    bytes, not on anything uncommitted in the working tree."""
    files = subprocess.check_output(["git", "-C", ROOT, "ls-files"], text=True).split()
    for f in files:
        blob = subprocess.check_output(["git", "-C", ROOT, "show", "HEAD:" + f])
        dest = os.path.join(tmp, f.replace("/", os.sep))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as h:
            h.write(blob)
    return files


def main():
    tmp = tempfile.mkdtemp(prefix="pbi-fees-verify-")
    try:
        files = clean_checkout(tmp)
        r = subprocess.run([sys.executable, os.path.join(tmp, "build.py"), "--verify"],
                           capture_output=True, text=True)
        sys.stdout.write(r.stdout)
        if r.returncode != 0:
            print("build.py FAILED:", r.stderr[:400]); return 2
        built = open(os.path.join(tmp, "dist", "index.html"), "rb").read()
        print("tracked blobs materialised from git: %d  %s" % (len(files), files))

        origin_live = fetch(PAGES)
        print("Pages origin  %6d B  sha %s" % (len(origin_live), hashlib.sha256(origin_live).hexdigest()))
        src = open(os.path.join(tmp, "src", "index.html"), "rb").read()
        print("src/index.html matches live Pages origin: %s" % (src == origin_live))

        ok = True
        for i, cb in enumerate((False, False, True), 1):
            live = fetch(LIVE + ("?cb=estate-sot" if cb else ""))
            stripped = BEACON.sub(b"", live)
            same = stripped == built
            ok = ok and same
            print("brand fetch %d%s  %6d B  beacon-stripped %6d B  %s"
                  % (i, " (cache-busted)" if cb else "", len(live), len(stripped),
                     "MATCH" if same else "DIFFER"))
            if not same:
                n = min(len(stripped), len(built))
                k = next((j for j in range(n) if stripped[j] != built[j]), n)
                print("   first diff @%d" % k)
                print("   live   %r" % stripped[max(0, k - 70):k + 70])
                print("   built  %r" % built[max(0, k - 70):k + 70])
        print("\nbuilt sha %s" % hashlib.sha256(built).hexdigest())
        print("VERIFY %s" % ("PASS - committed source regenerates the live document"
                             if ok else "FAIL"))
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
