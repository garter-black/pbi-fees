# pbi-fees

Source of truth for `fees.black.industries` and `pbi-fees.pages.dev`.

| Layer | Where it lives | Notes |
|---|---|---|
| Code + design | this repo, `src/index.html` | byte-identical to the live Pages project |
| Edge transform | `edge/pbi-edge-transform.mjs` | the `pbi-edge` Worker, constants verbatim |
| Build | `build.py` | `src/index.html` -> `dist/index.html` |
| Deploy | Cloudflare Pages project `pbi-fees` | behind a `pbi-edge` Worker route |
| Media | none | the page references no local asset and no media file |

## Verify

```
python verify.py
```

`verify.py` materialises every tracked blob out of git into a clean checkout, runs
`build.py` there, then fetches the live hostname three times (one cache-busted) and
byte-compares after removing Cloudflare's Web Analytics beacon. Exit 0 means the
committed source regenerates the live document.

## What this repo is not

It does not deploy. The `estate-sot` lane is read-only against Cloudflare: no
deployment, no DNS change, no Worker edit from here.
