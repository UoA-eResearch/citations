"""Unit checks of the extractor on crafted sentences (statcheck-style cases included). Run before any real text."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract as X  # noqa: E402

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail else ""))
    passed += ok; failed += not ok


def one(text):
    s = X.extract(text)
    return s[0] if s else None


cases = [
    ("The effect was significant (p = 0.03).", ("=", 0.03, True)),
    ("No difference was found (P = .21).", ("=", 0.21, False)),
    ("Strongly associated (p < 0.001).", ("<", 0.001, True)),
    ("Not significant (p > 0.05).", (">", 0.05, False)),
    ("Borderline (p = 0.05).", ("=", 0.05, None)),
    ("Trend (p < 0.1).", ("<", 0.1, None)),
    ("Genome-wide hit (p = 1.2 x 10-8).", ("=", 1.2e-8, True)),
    ("Genome-wide hit (P = 3.4 × 10−6).", ("=", 3.4e-6, True)),
    ("Association (p=2e-4).", ("=", 2e-4, True)),
    ("Lower (p ≤ 0.01).", ("<=", 0.01, True)),
    ("We obtained a p-value of 0.12 for this.", ("=", 0.12, False)),
    ("Odds were higher (p-value < 0.05).", ("<", 0.05, True)),
]
for text, (c, p, sig) in cases:
    r = one(text)
    check(f"{text[:45]}", r is not None and r["cmp"] == c and abs(r["p"] - p) < 1e-12 and r["sig"] is sig,
          str({k: r[k] for k in ("cmp", "p", "sig")}) if r else "none")
r = X.extract("Groups differed, t(28) = 2.20, p = .036, and F(2, 57) = 4.11, p < .05.")
check("two statcheck tuples, no duplicate bare p", len(r) == 2 and r[0]["test"] == "t" and r[0]["df"] == "28"
      and r[1]["test"] == "f" and r[1]["df"] == "2,57", str([(x["kind"], x["test"], x["df"], x["p"]) for x in r]))
r = X.extract("The correlation was weak, r(98) = .12, p = .23; χ2(1, N = 120) = 5.2, p = .02.")
check("r and chi-square tuples", len(r) == 2 and r[0]["test"] == "r" and r[1]["test"] == "χ2" and r[1]["df"] == "1",
      str([(x["test"], x["df"]) for x in r]))
check("non-statistics ignored", X.extract("Group P = parietal cortex; pH = 7.4; p53 levels rose.") == [],
      str(X.extract("Group P = parietal cortex; pH = 7.4; p53 levels rose.")))
check("sentence and offset kept", X.extract("First sentence. Second has p = 0.02 here.")[0]["sentence"].startswith("Second"))
print(f"\n{passed}/{passed + failed} passed")
sys.exit(1 if failed else 0)
