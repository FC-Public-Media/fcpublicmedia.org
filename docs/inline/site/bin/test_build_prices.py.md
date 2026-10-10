# `site/bin/test_build_prices.py`

Moved out of the file. Unreviewed.

## 1

Above `import importlib.util`

The price generator.

Two things are being guarded, and they fail in opposite directions.

The first is drift: a price edited in site/_data/ that never reaches the broker.
That one is quiet — the page says $70, the card is charged $60, and nobody
finds out until somebody reconciles a bank statement. `--check` in CI is the
guard; the test here is that `--check` actually notices.

The second is a placeholder becoming a charge. Several figures in the data
files are the literal string "TODO" while the board decides. A generator that
coerced those to 0, or to 0 cents, or skipped the check and let `float("TODO")`
raise at some later moment, would either sell something for nothing or take
the site down. They are skipped, deliberately and loudly.

## 2

Above `HERE = pathlib.Path(__file__).resolve().parent`

`site/bin/` is inside the Jekyll source, so a path here is relative to the
site rather than to the repository. SITE is the build root; REPO is the node.

## 3

Above `for value in ("TODO", "", None, "$40", "forty", [], {}):`

The one that would cost real money. Every one of these has to come
back None rather than raising or defaulting.

## 4

Above `self.assertIsNone(build_prices.amount(True))`

bool is a subclass of int in Python, so `isinstance(True, int)` is
True and a stray `price: yes` in YAML would otherwise be one cent.

## 5

Above `self.assertIsNone(build_prices.amount(40.001))`

Rounding somebody's price silently is worse than declining to sell
it, because the difference shows up on their statement and not ours.

## 6

Above `_, skipped = build_prices.build()`

Skipping quietly is how "why is there no buy button" becomes an
afternoon. The script says what it left out and why.

## 7

Above `result = subprocess.run(`

The same command CI runs. If this fails, run
`python3 site/bin/build-prices.py` and commit the result.

## 8

Above `target = REPO / "worker" / "src" / "prices.js"`

A --check that always passed would be worse than none, because it
would be believed. Written to a real edit and put back.
