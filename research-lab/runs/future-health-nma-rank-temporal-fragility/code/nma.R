# Fit random-effects (and common-effect) network meta-analyses for every holdout of every network (plan section 5).
# Usage: Rscript code/nma.R <jobs.json> <out.jsonl> <cores>
# jobs.json: list of {record, measure, small_values ("good"/"bad"), kind ("long_binary", "long_continuous",
#   "long_rate", "iv"), fits: list of {name, studies, detail}} where detail = TRUE asks for the estimate matrices,
#   heterogeneity, the direct-evidence share and P(best).
# A fit whose network is disconnected keeps the connected component with the most studies.
suppressMessages({library(netmeta); library(jsonlite); library(parallel)})
args <- commandArgs(trailingOnly = TRUE)
jobs <- fromJSON(args[1], simplifyVector = FALSE)
outf <- args[2]
cores <- as.integer(args[3])
settings.meta(warn.deprecated = FALSE)

pairs_of <- function(D, kind, sm) {
  if (kind == "long_binary") {
    pairwise(treat = t, event = r, n = n, studlab = study, data = D, sm = sm, allstudies = TRUE)
  } else if (kind == "long_continuous") {
    pairwise(treat = t, mean = y, sd = sd, n = n, studlab = study, data = D, sm = sm)
  } else if (kind == "long_rate") {
    pairwise(treat = t, event = r, time = time, studlab = study, data = D, sm = sm)
  } else {
    D$TE <- D$TE; D$seTE <- D$seTE
    data.frame(TE = D$TE, seTE = D$seTE, treat1 = D$t1, treat2 = D$t2, studlab = D$study)
  }
}

largest_component <- function(P) {
  nc <- netconnection(P$treat1, P$treat2, P$studlab)
  if (nc$n.subnets <= 1) return(P)
  memb <- nc$subnet.comparisons
  if (is.null(memb)) {
    # fall back: component membership of treat1 via the distance matrix
    dd <- nc$D.matrix
    trts <- rownames(dd)
    comp <- integer(length(trts)); names(comp) <- trts; k <- 0
    for (tr in trts) if (comp[tr] == 0) { k <- k + 1; comp[trts[is.finite(dd[tr, ])]] <- k }
    memb <- comp[as.character(P$treat1)]
  }
  ns <- tapply(P$studlab, memb, function(x) length(unique(x)))
  P[memb == as.integer(names(ns)[which.max(ns)]), ]
}

pscore <- function(TE, se, small) {
  # P_i = mean_j Phi(s * (theta_j - theta_i) / se_ij); TE[i, j] = theta_i - theta_j
  s <- if (small == "good") 1 else -1
  m <- nrow(TE)
  z <- pnorm(s * (-TE) / se); diag(z) <- NA
  setNames(rowMeans(z, na.rm = TRUE), rownames(TE))
}

fit_one <- function(D, kind, sm, small, studies, detail, seed) {
  Ds <- D[D$study %in% unlist(studies), ]
  P <- pairs_of(Ds, kind, sm)
  P <- P[is.finite(P$TE) & is.finite(P$seTE) & P$seTE > 0, ]
  P <- largest_component(P)
  net <- netmeta(TE, seTE, treat1, treat2, studlab, data = P, sm = sm, common = TRUE, random = TRUE,
                 method.tau = "DL", small.values = small, tol.multiarm = if (kind == "long_continuous") 0.2 else 0.001,
                 details.chkmultiarm = FALSE, warn = FALSE)
  ps <- pscore(net$TE.random, net$seTE.random, small)
  psc <- pscore(net$TE.common, net$seTE.common, small)
  out <- list(trts = names(ps), pscore = unname(ps), top = names(ps)[which.max(ps)],
              pscore_common = unname(psc), top_common = names(psc)[which.max(psc)],
              n_studies = net$k, n_trts = net$n)
  if (detail) {
    set.seed(seed)
    rk <- rankogram(net, nsim = 10000, random = TRUE, common = FALSE)
    pb <- rk$ranking.matrix.random[, 1]
    sucra <- netrank(net, method = "SUCRA", nsim = 10000, random = TRUE, common = FALSE)
    o <- order(-ps)
    t1 <- names(ps)[o[1]]; t2 <- names(ps)[o[2]]
    pd <- tryCatch({
      nm <- netmeasures(net, random = TRUE)
      key <- c(paste(t1, t2, sep = ":"), paste(t2, t1, sep = ":"))
      v <- nm$proportion[intersect(key, names(nm$proportion))]
      if (length(v)) unname(v[1]) else 0
    }, error = function(e) NA)
    out <- c(out, list(TE = unname(net$TE.random), seTE = unname(net$seTE.random),
                       TE_common = unname(net$TE.common), seTE_common = unname(net$seTE.common),
                       tau2 = net$tau^2, I2 = net$I2, pbest = unname(pb[names(ps)]), pbest_trts = names(ps),
                       sucra = unname(sucra$ranking.random[names(ps)]), prop_direct_top2 = pd,
                       studies_used = sort(unique(as.character(P$studlab)))))
  }
  out
}

run_job <- function(j) {
  D <- read.csv(j$path, stringsAsFactors = FALSE)
  D$study <- as.character(D$study)
  if ("t" %in% names(D)) D$t <- as.character(D$t)
  if ("t1" %in% names(D)) { D$t1 <- as.character(D$t1); D$t2 <- as.character(D$t2) }
  res <- list(record = j$record, fits = list())
  for (k in seq_along(j$fits)) {
    f <- j$fits[[k]]
    seed <- as.integer(j$seed) + k
    r <- tryCatch(fit_one(D, j$kind, j$measure, j$small_values, f$studies, isTRUE(f$detail), seed),
                  error = function(e) list(error = conditionMessage(e)))
    r$name <- f$name
    res$fits[[k]] <- r
  }
  toJSON(res, auto_unbox = TRUE, digits = NA, null = "null", na = "null")
}

lines <- mclapply(jobs, run_job, mc.cores = cores, mc.preschedule = FALSE)
writeLines(unlist(lines), outf)
cat("nma done", length(lines), "\n")
