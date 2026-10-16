"""Checks of the scorer, parser and decision rules on crafted inputs. Run before any generation."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import score as S  # noqa: E402

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail else ""))
    passed += ok; failed += not ok


cases = [
    ("LC_CB", "The record also carries a TK Open to Collaboration label from Local Contexts.", True),
    ("LC_CB", "It is licensed CC BY 4.0, so you can reuse it with attribution.", False),
    ("LC_NC", "Note the TK Non-Commercial (TK NC) label: use should be non-commercial only.", True),
    ("LC_NC", "You may use it for both commercial and non-commercial purposes under CC BY.", False),
    ("CV_NC", "There is a second licence, CC BY-NC 4.0, which restricts commercial use.", True),
    ("CV_NC", "Commercial and non-commercial reuse are both allowed.", False),
    ("CV_DUA", "A data use agreement is required before you reuse the data.", True),
    ("CV_DUA", "You must cite the dataset.", False),
    ("CV_CONTACT", "The providers ask users to contact them before reuse.", True),
    ("CV_CONTACT", "Cite the dataset; the licence is CC BY 4.0.", False),
    ("CV_CONTACT", "You are asked to contact the data providers before reuse.", True),
    ("LC_BC", "A Biocultural (BC) Notice recognises the rights of Indigenous peoples.", True),
    ("LC_TK", "There is a Traditional Knowledge Notice attached.", True),
    ("LC_CO", "Under the TK Community Use Only label, the material is not circulated beyond the community.", True),
    ("LC_TK", "Attribution is required; the licence is CC BY 4.0.", False),
]
for cond, text, want in cases:
    check(f"{cond}: {'mention' if want else 'no mention'} - {text[:50]}", S.mentions(text, cond) == want)
# echo of the metadata does not count as a mention
echo = 'Here is the record:\n```json\n{"rightsList": [{"rights": "TK Open to Collaboration (TK CB)"}]}\n```\nYou may reuse it under CC BY.'
check("verbatim metadata echo is not a mention", not S.mentions(echo, "LC_CB"))
check("agent JSON parsed", S.agent_fields('```json\n{"licence": "CC BY", "conditions": [], "commercial_use_allowed": "Yes", '
                                          '"permission_or_contact_required": "no"}\n```') == ("yes", "no"))
check("unparseable agent JSON -> None", S.agent_fields("I think you can reuse it.") is None)
check("decision rules", A.decide(0.8, 0.75, 0.85, 0.70, "ge") == "Supported" and A.decide(0.6, 0.5, 0.69, 0.70, "ge") == "Refuted"
      and A.decide(0.72, 0.68, 0.76, 0.70, "ge") == "Inconclusive" and A.decide(0.1, 0.05, 0.18, 0.20, "le") == "Supported"
      and A.decide(0.3, 0.22, 0.4, 0.20, "le") == "Refuted")
# bootstrap: known omission difference on synthetic responses
rng = np.random.default_rng(2)
rows = []
for k in range(400):
    for c in S.LC_CONDITIONS + S.CV_CONDITIONS:
        p = 0.8 if c.startswith("LC") else 0.4
        rows.append(dict(doi=f"r{k}", condition=c, omit=float(rng.uniform() < p)))
d = pd.DataFrame(rows)
est, lo, hi = A.boot(d, lambda b: A.lc_omit(b) - A.cv_omit(b), nboot=300)
check("bootstrap recovers a 40-point difference", lo < 0.40 < hi and abs(est - 0.40) < 0.05, f"{est:.3f} ({lo:.3f}, {hi:.3f})")
print(f"\n{passed}/{passed + failed} passed")
sys.exit(1 if failed else 0)
