"""AI-agent attribution for one commit (plan section 2). Fixed before any repository was cloned.

classify(author_name, author_email, committer_name, committer_email, message) -> (agent or None, rule or None)
is_bot(author_name, author_email) -> True for non-AI automation (dependabot, renovate, ...) and any "[bot]" author
"""
import re

COAUTHOR = re.compile(r"^\s*co-authored-by:\s*(?P<who>.+?)\s*$", re.I | re.M)
# (agent, pattern on the "Name <email>" text of a co-author trailer)
TRAILER = [
    ("claude", re.compile(r"\bclaude\b|noreply@anthropic\.com", re.I)),
    ("copilot", re.compile(r"^copilot\b|\+copilot@users\.noreply\.github\.com|copilot-swe-agent", re.I)),
    ("cursor", re.compile(r"cursor agent|cursoragent@cursor\.com", re.I)),
    ("aider", re.compile(r"^aider\b", re.I)),
    ("devin", re.compile(r"^devin\b|devin-ai-integration", re.I)),
    ("jules", re.compile(r"^jules\b|google-labs-jules", re.I)),
    ("openhands", re.compile(r"\bopenhands\b|openhands@all-hands\.dev", re.I)),
    ("amp", re.compile(r"^amp\b.*<|amp@ampcode\.com", re.I)),
    ("codex", re.compile(r"\bcodex\b|chatgpt-codex-connector", re.I)),
    ("gemini", re.compile(r"\bgemini\b.*<[^>]*(google\.com|gemini)", re.I)),
    ("junie", re.compile(r"\bjunie\b", re.I)),
]
GENERATED = re.compile(r"generated with \[?(claude code|cursor|aider|devin|jules|openhands|amp|codex|gemini cli|copilot)\]?", re.I)
GEN_AGENT = {"claude code": "claude", "cursor": "cursor", "aider": "aider", "devin": "devin", "jules": "jules",
             "openhands": "openhands", "amp": "amp", "codex": "codex", "gemini cli": "gemini", "copilot": "copilot"}
# (agent, pattern on "name <email>" of author or committer)
IDENTITY = [
    ("copilot", re.compile(r"copilot-swe-agent|\+copilot@users\.noreply\.github\.com|^copilot <", re.I)),
    ("devin", re.compile(r"devin-ai-integration", re.I)),
    ("claude", re.compile(r"^claude\[bot\]|claude\[bot\]@users\.noreply", re.I)),
    ("jules", re.compile(r"google-labs-jules", re.I)),
    ("codex", re.compile(r"chatgpt-codex-connector", re.I)),
    ("openhands", re.compile(r"openhands-agent|openhands@all-hands\.dev", re.I)),
    ("cursor", re.compile(r"^cursor\[bot\]|cursoragent@cursor\.com|^cursor agent <", re.I)),
    ("aider", re.compile(r"\(aider\) <", re.I)),
]
BOTS = re.compile(r"dependabot|renovate|github-actions|pre-commit-ci|greenkeeper|snyk-bot|mergify|semantic-release-bot|"
                  r"allcontributors|imgbot|pyup-bot|whitesource|deepsource|codecov|release-please|changeset-bot|"
                  r"web-flow|\[bot\]", re.I)
AI_BOTS = re.compile(r"copilot-swe-agent|devin-ai-integration|claude\[bot\]|google-labs-jules|chatgpt-codex-connector|"
                     r"openhands-agent|cursor\[bot\]", re.I)


def classify(an, ae, cn, ce, msg):
    for who in COAUTHOR.findall(msg or ""):
        for agent, pat in TRAILER:
            if pat.search(who):
                return agent, "trailer"
    m = GENERATED.search(msg or "")
    if m:
        return GEN_AGENT[m.group(1).lower()], "generated"
    for ident in (f"{an} <{ae}>", f"{cn} <{ce}>"):
        for agent, pat in IDENTITY:
            if pat.search(ident):
                return agent, "identity"
    return None, None


def is_bot(an, ae):
    ident = f"{an} <{ae}>"
    return bool(BOTS.search(ident)) and not AI_BOTS.search(ident)


if __name__ == "__main__":
    cases = [
        (("Jane", "j@x.org", "Jane", "j@x.org", "fix: thing\n\nCo-Authored-By: Claude <noreply@anthropic.com>"), "claude"),
        (("Jane", "j@x.org", "Jane", "j@x.org", "x\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)"), "claude"),
        (("Copilot", "198982749+Copilot@users.noreply.github.com", "GitHub", "noreply@github.com", "Add tests\n\nCo-authored-by: jane <j@x.org>"), "copilot"),
        (("Jane", "j@x.org", "Jane", "j@x.org", "Apply suggestion\n\nCo-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>"), "copilot"),
        (("Jane (aider)", "j@x.org", "Jane", "j@x.org", "feat: y"), "aider"),
        (("devin-ai-integration[bot]", "158243242+devin-ai-integration[bot]@users.noreply.github.com", "x", "y", "z"), "devin"),
        (("Jane", "j@x.org", "Jane", "j@x.org", "Co-authored-by: Cursor Agent <cursoragent@cursor.com>"), "cursor"),
        (("Jane", "j@x.org", "Jane", "j@x.org", "Co-authored-by: Amp <amp@ampcode.com>"), "amp"),
        (("Claude Monet", "claude@monet.fr", "Claude Monet", "claude@monet.fr", "fix typo"), None),       # a person named Claude, no trailer
        (("dependabot[bot]", "49699333+dependabot[bot]@users.noreply.github.com", "GitHub", "noreply@github.com", "Bump x"), None),
        (("Jane", "j@x.org", "Jane", "j@x.org", "Co-authored-by: Bob Ampersand <bob@b.com>"), None),
        (("Jane", "j@x.org", "Jane", "j@x.org", "Co-authored-by: Ampel <ampel@b.com>"), None),
    ]
    for args, want in cases:
        got = classify(*args)[0]
        assert got == want, (args, got, want)
    assert is_bot("dependabot[bot]", "x") and not is_bot("Copilot", "198982749+Copilot@users.noreply.github.com")
    assert not is_bot("devin-ai-integration[bot]", "x")
    print("attribution tests pass:", len(cases))
