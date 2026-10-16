"""Post-hoc, descriptive checks written after the preregistered results were seen (deviations D6). None changes a
verdict.

The preregistered results: elements are mentioned almost always (H1, H2 Refuted), and an element changes the agent
framing's stated verdict in 85% of cases (H3 Refuted). The pilot adjudication notes suggested the substance lies in
what models SAY about an element, not whether they mention it. Three lexical/structured checks:

  V1  agent verdicts by condition and model: the share of commercial_use_allowed = no, and of
      permission_or_contact_required = yes, against NONE; matched pairs TK NC vs CC BY-NC (commercial use) and
      TK CB vs the contact clause (contact)
  V2  "not binding": among researcher and direct responses that mention the element, the share describing it as not
      a legal requirement ("not legally binding", "no legal weight", "not a legal restriction", "does not impose
      legal restrictions", "not a legal requirement", "courtesy")
  V3  invented licence terms: in NONE responses (the record carries only CC BY), the share that attach a
      NonCommercial, NoDerivatives or ShareAlike condition to it, by model
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import score as S  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
NOTBIND = re.compile(r"not\s+(a\s+)?legal(ly)?\s+(binding|restriction|requirement|obligation)|no\s+legal\s+(weight|force|effect)|"
                     r"does\s+not\s+impose\s+(any\s+)?legal|not\s+legally\s+(binding|enforceable)|not\s+a\s+legal\s+barrier|"
                     r"\bcourtesy\b|not\s+(a\s+)?(binding|enforceable)", re.I)
INVENT = {"noncommercial": re.compile(r"non[- ]?commercial\s*(\(nc\))?\s*[:\-–]|\*\*non[- ]?commercial|you\s+may\s+not\s+use\s+the\s+"
                                      r"(material|dataset|data|work)\s+for\s+commercial", re.I),
          "noderivatives": re.compile(r"no\s*-?\s*derivatives?|\bnoderivatives\b", re.I),
          "sharealike": re.compile(r"share\s*-?\s*alike", re.I)}


def main():
    d = A.score_frame(A.load("main"))
    out = {}
    a = d[d.framing == "agent"].copy()
    a["fields"] = [S.agent_fields(t) for t in a.text]
    a = a[a.fields.notna()]
    a["commercial_no"] = [f[0] == "no" for f in a.fields]
    a["contact_yes"] = [f[1] == "yes" for f in a.fields]
    v1 = a.groupby(["condition", "model"])[["commercial_no", "contact_yes"]].mean().round(3)
    out["V1_agent_verdicts"] = {f"{c}|{m}": r.to_dict() for (c, m), r in v1.iterrows()}
    out["V1_by_condition"] = a.groupby("condition")[["commercial_no", "contact_yes"]].mean().round(3).to_dict()
    out["V1_matched"] = {
        "commercial_no: LC_NC vs CV_NC vs NONE": [float(a[a.condition == c].commercial_no.mean()) for c in ("LC_NC", "CV_NC", "NONE")],
        "contact_yes: LC_CB vs CV_CONTACT vs NONE": [float(a[a.condition == c].contact_yes.mean()) for c in ("LC_CB", "CV_CONTACT", "NONE")],
        "contact_yes: LC_CO vs CV_DUA": [float(a[a.condition == c].contact_yes.mean()) for c in ("LC_CO", "CV_DUA")]}
    t = d[(d.framing != "agent") & (d.condition != "NONE") & (d.mention == 1)].copy()
    t["notbinding"] = [bool(NOTBIND.search(S.strip_echo(x))) for x in t.text]
    out["V2_not_binding_by_condition"] = t.groupby("condition").notbinding.mean().round(3).to_dict()
    out["V2_not_binding_by_condition_model"] = {f"{c}|{m}": float(v) for (c, m), v in
                                               t.groupby(["condition", "model"]).notbinding.mean().round(3).items()}
    n = d[(d.condition == "NONE") & (d.framing != "agent")].copy()
    for k, rx in INVENT.items():
        n[k] = [bool(rx.search(S.strip_echo(x))) for x in n.text]
    n["any_invented"] = n[list(INVENT)].any(axis=1)
    out["V3_invented_terms_in_NONE_by_model"] = n.groupby("model")[list(INVENT) + ["any_invented"]].mean().round(3).to_dict()
    json.dump(out, open(TAB / "supplementary.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float)[:5000])


if __name__ == "__main__":
    sys.exit(main())
