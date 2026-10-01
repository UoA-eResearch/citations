# Per-file aggregation of mediawiki_history TSV (2026-08 snapshot, 78 columns; plan.md sec 2-3).
# Output rows: wiki, date, group, n, n_temp, rev24, rev48
#   group LO  = logged-out (col 20 is_anonymous or col 21 is_temporary)
#   group REG = permanent account (col 22) with no bot flag (col 16 empty)
#   group ACCT = self-created permanent accounts (user-create events; cols 52, 57)
# Revision filter: revision-create events (cols 3-4), date >= 2024-01-01 (col 5), content namespace (col 35),
# not deleted with their page (col 71), not a cross-wiki import (col 23, event_user_is_cross_wiki; deviations.md D5).
# Revert: identity-reverted (col 73) within 24 h / 48 h (col 75, seconds).
BEGIN { FS = "\t"; OFS = "\t" }
NF == 78 && $3 == "revision" && $4 == "create" && $5 >= "2024-01-01" && $35 == "true" && $71 != "true" {
  d = substr($5, 1, 10)
  if ($23 == "true") next                       # cross-wiki imported revisions ("ar>User"; col 23), not logged-out edits
  if ($20 == "true" || $21 == "true") g = "LO"
  else if ($22 == "true" && $16 == "") g = "REG"
  else next
  k = $1 SUBSEP d SUBSEP g
  n[k]++
  if ($21 == "true") t[k]++
  if ($73 == "true" && $75 != "") {
    if ($75 + 0 <= 86400) r24[k]++
    if ($75 + 0 <= 172800) r48[k]++
  }
  next
}
NF == 78 && $3 == "user" && $4 == "create" && $5 >= "2024-01-01" && $52 == "true" && $57 == "true" {
  k = $1 SUBSEP substr($5, 1, 10) SUBSEP "ACCT"
  n[k]++
}
END {
  for (k in n) {
    split(k, a, SUBSEP)
    print a[1], a[2], a[3], n[k], t[k] + 0, r24[k] + 0, r48[k] + 0
  }
}
