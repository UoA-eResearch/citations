# Independent refit of 10 networks (full and T10) with netmeta: P-scores via netrank, P(best) via rankogram,
# compared with fits.jsonl. Written without reusing nma.R's functions.
suppressMessages({library(netmeta); library(jsonlite)})
settings.meta(warn.deprecated = FALSE)
RUN <- "/mnt/citations/research-lab/runs/future-health-nma-rank-temporal-fragility"
jobs <- fromJSON(file.path(RUN, "data/jobs.json"), simplifyVector = FALSE)
names(jobs) <- sapply(jobs, function(j) j$record)
fits <- list()
con <- file(file.path(RUN, "data/fits.jsonl"), "r")
while (length(l <- readLines(con, n = 1)) > 0) { r <- fromJSON(l, simplifyVector = FALSE); fits[[r$record]] <- r$fits }
close(con)
set.seed(99)
prim <- read.csv(file.path(RUN, "results/tables/network_results.csv"), colClasses = c(record = "character"))
prim <- prim[prim$included %in% c(TRUE, "True") & prim$set == "primary", ]
sample10 <- sample(prim$record, 8)
sample10 <- c(sample10, "479757", "501308")  # plus two contrast-level networks (one natural-scale, one with the D3 split)
out <- list()
for (rec in sample10) {
  j <- jobs[[rec]]; D <- read.csv(j$path, stringsAsFactors = FALSE); D$study <- as.character(D$study)
  if ("t" %in% names(D)) D$t <- as.character(D$t)
  if ("t1" %in% names(D)) { D$t1 <- as.character(D$t1); D$t2 <- as.character(D$t2) }
  sv <- if (j$small_values == "good") "desirable" else "undesirable"
  for (nm in c("full", "T10")) {
    f <- j$fits[[which(sapply(j$fits, function(x) x$name) == nm)]]
    Ds <- D[D$study %in% unlist(f$studies), ]
    if (j$kind == "long_binary") P <- pairwise(treat = t, event = r, n = n, studlab = study, data = Ds, sm = j$measure, allstudies = TRUE)
    else if (j$kind == "long_continuous") P <- pairwise(treat = t, mean = y, sd = sd, n = n, studlab = study, data = Ds, sm = j$measure)
    else if (j$kind == "long_rate") P <- pairwise(treat = t, event = r, time = time, studlab = study, data = Ds, sm = j$measure)
    else P <- data.frame(TE = Ds$TE, seTE = Ds$seTE, treat1 = Ds$t1, treat2 = Ds$t2, studlab = Ds$study)
    P <- P[is.finite(P$TE) & is.finite(P$seTE) & P$seTE > 0, ]
    tol <- if (j$kind == "long_continuous") 0.2 else 0.001
    net <- tryCatch(netmeta(TE, seTE, treat1, treat2, studlab, data = P, sm = j$measure, method.tau = "DL", small.values = sv, tol.multiarm = tol, warn = FALSE, details.chkmultiarm = FALSE), error = function(e) e)
    split <- FALSE
    if (inherits(net, "error")) { P$studlab <- paste(P$studlab, seq_len(nrow(P)), sep = "_"); net <- netmeta(TE, seTE, treat1, treat2, studlab, data = P, sm = j$measure, method.tau = "DL", small.values = sv, tol.multiarm = tol, warn = FALSE, details.chkmultiarm = FALSE); split <- TRUE }
    ps <- netrank(net, method = "P-score")$ranking.random
    set.seed(12345); rk <- rankogram(net, nsim = 10000, random = TRUE, common = FALSE); pb <- rk$ranking.matrix.random[, 1]
    ref <- fits[[rec]][[which(sapply(fits[[rec]], function(x) x$name) == nm)]]
    rps <- setNames(unlist(ref$pscore), unlist(ref$trts)); rpb <- setNames(unlist(ref$pbest), unlist(ref$pbest_trts))
    common <- intersect(names(ps), names(rps))
    out[[length(out) + 1]] <- data.frame(record = rec, fit = nm, kind = j$kind, sm = j$measure, split = split,
      n_trts_mine = net$n, n_trts_ref = ref$n_trts, k_mine = net$k, k_ref = ref$n_studies,
      same_trts = setequal(names(ps), names(rps)), max_abs_pscore_diff = max(abs(ps[common] - rps[common])),
      top_mine = names(ps)[which.max(ps)], top_ref = ref$top, pbest_top_mine = unname(pb[names(ps)[which.max(ps)]]), pbest_top_ref = unname(rpb[ref$top]),
      max_abs_pbest_diff = max(abs(pb[common] - rpb[common])), kendall_ps = cor(ps[common], rps[common], method = "kendall"), tau2_mine = net$tau^2, tau2_ref = ref$tau2)
  }
}
res <- do.call(rbind, out)
print(res, digits = 4)
write.csv(res, file.path(RUN, "review/reviewer_checks/refit_comparison.csv"), row.names = FALSE)
