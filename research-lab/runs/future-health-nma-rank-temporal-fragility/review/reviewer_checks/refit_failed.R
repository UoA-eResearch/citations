# (a) Re-run every fit that failed with 'arguments must have same length' or 'Network consists of ... sub-networks'
#     using a working largest-component rule (components from netconnection's distance matrix), as plan section 4 says.
# (b) Refit 501220 and 501274 (full, T10) with the corrected direction of benefit.
suppressMessages({library(netmeta); library(jsonlite); library(parallel)})
settings.meta(warn.deprecated = FALSE)
RUN <- "/mnt/citations/research-lab/runs/future-health-nma-rank-temporal-fragility"
jobs <- fromJSON(file.path(RUN, "data/jobs.json"), simplifyVector = FALSE); names(jobs) <- sapply(jobs, function(j) j$record)
failed <- list(); con <- file(file.path(RUN, "data/fits.jsonl"), "r")
while (length(l <- readLines(con, n = 1)) > 0) { r <- fromJSON(l, simplifyVector = FALSE)
  for (f in r$fits) if (!is.null(f$error) && (grepl("same length", f$error) || grepl("sub-networks", f$error))) failed[[length(failed) + 1]] <- list(record = r$record, name = f$name) }
close(con)
cat("failed fits to redo:", length(failed), "\n")
largest_component <- function(P) {
  nc <- netconnection(P$treat1, P$treat2, P$studlab)
  if (nc$n.subnets <= 1) return(P)
  dd <- nc$D.matrix; trts <- rownames(dd); comp <- setNames(integer(length(trts)), trts); k <- 0
  for (tr in trts) if (comp[tr] == 0) { k <- k + 1; comp[trts[is.finite(dd[tr, ])]] <- k }
  memb <- comp[as.character(P$treat1)]
  ns <- tapply(P$studlab, memb, function(x) length(unique(x)))
  P[memb == as.integer(names(ns)[which.max(ns)]), ]
}
pairs_of <- function(Ds, kind, sm) {
  if (kind == "long_binary") pairwise(treat = t, event = r, n = n, studlab = study, data = Ds, sm = sm, allstudies = TRUE)
  else if (kind == "long_continuous") pairwise(treat = t, mean = y, sd = sd, n = n, studlab = study, data = Ds, sm = sm)
  else if (kind == "long_rate") pairwise(treat = t, event = r, time = time, studlab = study, data = Ds, sm = sm)
  else data.frame(TE = Ds$TE, seTE = Ds$seTE, treat1 = Ds$t1, treat2 = Ds$t2, studlab = Ds$study)
}
fit <- function(rec, name, small_override = NULL, detail = FALSE) {
  j <- jobs[[rec]]; D <- read.csv(j$path, stringsAsFactors = FALSE); D$study <- as.character(D$study)
  if ("t" %in% names(D)) D$t <- as.character(D$t)
  if ("t1" %in% names(D)) { D$t1 <- as.character(D$t1); D$t2 <- as.character(D$t2) }
  f <- j$fits[[which(sapply(j$fits, function(x) x$name) == name)]]
  Ds <- D[D$study %in% unlist(f$studies), ]
  P <- pairs_of(Ds, j$kind, j$measure); P <- P[is.finite(P$TE) & is.finite(P$seTE) & P$seTE > 0, ]
  P <- largest_component(P)
  small <- if (is.null(small_override)) j$small_values else small_override
  sv <- if (small == "good") "desirable" else "undesirable"
  tol <- if (j$kind == "long_continuous") 0.2 else 0.001
  fitnet <- function(P) netmeta(TE, seTE, treat1, treat2, studlab, data = P, sm = j$measure, method.tau = "DL", small.values = sv, tol.multiarm = tol, warn = FALSE, details.chkmultiarm = FALSE)
  net <- tryCatch(fitnet(P), error = function(e) e); split <- FALSE
  if (inherits(net, "error") && j$kind == "iv") { P$studlab <- paste(P$studlab, seq_len(nrow(P)), sep = "_"); net <- fitnet(P); split <- TRUE }
  if (inherits(net, "error")) return(list(record = rec, name = name, error = conditionMessage(net)))
  ps <- netrank(net, method = "P-score")$ranking.random
  out <- list(record = rec, name = name, trts = names(ps), pscore = unname(ps), top = names(ps)[which.max(ps)], n_studies = net$k, n_trts = net$n, split = split, small = small)
  if (detail) { set.seed(as.integer(rec) %% 100000 + 1); rk <- rankogram(net, nsim = 10000, random = TRUE, common = FALSE)
    out$pbest <- unname(rk$ranking.matrix.random[names(ps), 1]); out$TE <- unname(net$TE.random); out$seTE <- unname(net$seTE.random) }
  out
}
res <- mclapply(failed, function(x) tryCatch(fit(x$record, x$name, detail = x$name %in% c("T10", "S1", "S2", "S3")), error = function(e) list(record = x$record, name = x$name, error = conditionMessage(e))), mc.cores = 8)
writeLines(sapply(res, function(r) toJSON(r, auto_unbox = TRUE, digits = NA, null = "null")), file.path(RUN, "review/reviewer_checks/cache/refit_failed.jsonl"))
cat("redone; still failing:", sum(sapply(res, function(r) !is.null(r$error))), "\n")
# (b) corrected directions
res2 <- list()
for (rec in c("501220", "501274")) for (nm in c("full", "T10")) res2[[length(res2) + 1]] <- fit(rec, nm, small_override = "bad", detail = TRUE)
writeLines(sapply(res2, function(r) toJSON(r, auto_unbox = TRUE, digits = NA, null = "null")), file.path(RUN, "review/reviewer_checks/cache/refit_corrected_direction.jsonl"))
for (r in res2) cat(r$record, r$name, "top:", r$top, " pbest(top):", round(r$pbest[which.max(r$pscore)], 3), "\n")
