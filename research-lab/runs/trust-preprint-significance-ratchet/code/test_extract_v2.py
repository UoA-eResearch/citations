import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_v2 import extract  # noqa: E402


def one(s):
    x = extract(s)
    assert len(x) == 1, x
    return x[0]


def test_mojibake_exponent():
    x = one("The rate ratio was 0.60 (95% CI 0.53 to 0.66, p=1 Ã\x97 10â\x88\x9220).")
    assert abs(x["p"] - 1e-20) < 1e-30 and x["sig"] is True


def test_mojibake_mantissa_only_exponent():
    x = one("Driver genes were enriched (P = 4.2 x 10â\x80\x93112).")
    assert x["p"] < 1e-100


def test_middle_dot():
    x = one("No difference was seen (p=0·76).")
    assert x["p"] == 0.76 and x["sig"] is False


def test_comma_decimal():
    x = one("No difference for Wondfo (p=0,33).")
    assert x["p"] == 0.33 and x["sig"] is False


def test_comma_list_untouched():
    xs = extract("Both differed (p = 0.049, p = 0.017).")
    assert [x["p"] for x in xs] == [0.049, 0.017]


def test_partial_eta_not_p():
    assert extract("The effect was small (F(1, 30) = 1.2, p = 0.28, η2p = 0.002).")[-1]["p"] == 0.28
    assert all(x["p"] != 0.002 for x in extract("small effect, ηp2 = 0.002 and ω²p = .01"))


def test_lost_exponent_undetermined():
    x = one("The best model (CI=0.82, p=1x10) was retained.")
    assert x["p"] is None and x["sig"] is None


def test_exponent_kept():
    x = one("Strong association (p = 5 x 10-6).")
    assert abs(x["p"] - 5e-6) < 1e-15


def test_rank_and_count():
    xs = extract("A differed (p = 0.01) but B did not (p = 0.40) and C did (t(20) = 3.1, p = 0.006).")
    assert [x["rank"] for x in xs] == [0, 1, 2] and all(x["n_in_sent"] == 3 for x in xs)
    assert xs[2]["kind"] == "tuple"
