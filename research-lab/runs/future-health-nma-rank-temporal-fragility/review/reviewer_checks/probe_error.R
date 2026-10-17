# Reproduce the 'arguments must have same length' error on 501229 T10 and probe netconnection
suppressMessages({library(netmeta); library(jsonlite)})
settings.meta(warn.deprecated = FALSE)
RUN <- "/mnt/citations/research-lab/runs/future-health-nma-rank-temporal-fragility"
jobs <- fromJSON(file.path(RUN, "data/jobs.json"), simplifyVector = FALSE)
cat("netmeta version:", as.character(packageVersion("netmeta")), "\n")
for (rec in c("501229", "501403")) {
  j <- jobs[[which(sapply(jobs, function(x) x$record) == rec)]]
  D <- read.csv(j$path, stringsAsFactors = FALSE); D$study <- as.character(D$study)
  if ("t" %in% names(D)) D$t <- as.character(D$t)
  if ("t1" %in% names(D)) { D$t1 <- as.character(D$t1); D$t2 <- as.character(D$t2) }
  f <- j$fits[[which(sapply(j$fits, function(x) x$name) == "T10")]]
  Ds <- D[D$study %in% unlist(f$studies), ]
  cat("\n==== ", rec, j$kind, j$measure, " studies in T10 pre-update:", length(unlist(f$studies)), " rows:", nrow(Ds), "\n")
  if (j$kind == "long_binary") P <- pairwise(treat = t, event = r, n = n, studlab = study, data = Ds, sm = j$measure, allstudies = TRUE)
  else if (j$kind == "long_continuous") P <- pairwise(treat = t, mean = y, sd = sd, n = n, studlab = study, data = Ds, sm = j$measure)
  else P <- data.frame(TE = Ds$TE, seTE = Ds$seTE, treat1 = Ds$t1, treat2 = Ds$t2, studlab = Ds$study)
  P <- P[is.finite(P$TE) & is.finite(P$seTE) & P$seTE > 0, ]
  cat("contrast rows:", nrow(P), "\n")
  nc <- netconnection(P$treat1, P$treat2, P$studlab)
  cat("n.subnets:", nc$n.subnets, "\n")
  cat("names(nc):", paste(names(nc), collapse = ", "), "\n")
  cat("length(subnet.comparisons):", length(nc$subnet.comparisons), " nrow(P):", nrow(P), "\n")
  print(head(nc$subnet.comparisons))
  memb <- nc$subnet.comparisons
  res <- tryCatch({ ns <- tapply(P$studlab, memb, function(x) length(unique(x))); print(ns); "ok" }, error = function(e) conditionMessage(e))
  cat("tapply result:", res, "\n")
  # what does the netmeta fit say directly?
  r2 <- tryCatch(netmeta(TE, seTE, treat1, treat2, studlab, data = P, sm = j$measure, method.tau = "DL", small.values = j$small_values, warn = FALSE), error = function(e) conditionMessage(e))
  if (is.character(r2)) cat("netmeta direct error:", substr(r2, 1, 120), "\n") else cat("netmeta direct fit ok, n =", r2$n, " k =", r2$k, "\n")
  # structure of subnet.comparisons vs the data
  if (!is.null(nc$D.matrix)) cat("D.matrix dim:", dim(nc$D.matrix), "\n")
}
