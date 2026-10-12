"""Plan section 4: the models and the SAE pairs that are compared.

Pair types:
  within   the same model, two different SAE seeds (s, t), s < t                         16 models x 3
  full     two different full seeds (0-9: both initialisation and data order differ)     45 model pairs
  init     only the parameter initialisation differs: weight-seed k vs seed 0,
           and weight-seed j vs weight-seed k                                             6 model pairs
  data     only the data order differs: data-seed k vs seed 0, data-seed j vs data-seed k  6 model pairs
  both_dc  a weight-seed vs a data-seed variant (both differ)                              9 model pairs
For model pairs, the two SAEs never share an SAE seed: (A_s, B_{(s+1) mod 3}) for s = 0, 1, 2. Identical SAE
initialisations in two models whose residual bases happen to be aligned (models with the same initialisation) could
otherwise inflate matching."""
import itertools

FULL = ["p160m"] + [f"p160m-seed{i}" for i in range(1, 10)]
WEIGHT = [f"p160m-weight-seed{i}" for i in range(1, 4)]
DATA = [f"p160m-data-seed{i}" for i in range(1, 4)]
MODELS = FULL + WEIGHT + DATA
SEEDS = [0, 1, 2]


def design():
    pairs = []

    def add(kind, a, b):
        if a == b:
            for s, t in itertools.combinations(SEEDS, 2):
                pairs.append(dict(kind=kind, a=a, sa=s, b=b, sb=t))
        else:
            for s in SEEDS:
                pairs.append(dict(kind=kind, a=a, sa=s, b=b, sb=SEEDS[(s + 1) % 3]))

    for m in MODELS:
        add("within", m, m)
    for a, b in itertools.combinations(FULL, 2):
        add("full", a, b)
    for k in WEIGHT:
        add("init", "p160m", k)
    for a, b in itertools.combinations(WEIGHT, 2):
        add("init", a, b)
    for k in DATA:
        add("data", "p160m", k)
    for a, b in itertools.combinations(DATA, 2):
        add("data", a, b)
    for a in WEIGHT:
        for b in DATA:
            add("both_dc", a, b)
    for i, p in enumerate(pairs):
        p["id"] = i
    return pairs


if __name__ == "__main__":
    from collections import Counter
    d = design()
    print(len(d), Counter(p["kind"] for p in d))
