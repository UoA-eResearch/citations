# Check: (1) netmeta accepts small.values "good"/"bad" and what it maps to; (2) pscore() equals netrank P-score;
# (3) TE.random[i,j] = theta_i - theta_j convention; (4) rankogram P(best) direction
suppressMessages({library(netmeta); library(jsonlite)})
settings.meta(warn.deprecated = FALSE)
RUN <- "/mnt/citations/research-lab/runs/future-health-nma-rank-temporal-fragility"
pscore <- function(TE, se, small) { s <- if (small == "good") 1 else -1; z <- pnorm(s * (-TE) / se); diag(z) <- NA; setNames(rowMeans(z, na.rm = TRUE), rownames(TE)) }
D <- read.csv(file.path(RUN, "data/std/473269.csv")); D$study <- as.character(D$study); D$t <- as.character(D$t)
P <- pairwise(treat = t, event = r, n = n, studlab = study, data = D, sm = "RR", allstudies = TRUE)
for (sv in c("good", "bad", "desirable", "undesirable")) {
  net <- netmeta(TE, seTE, treat1, treat2, studlab, data = P, sm = "RR", method.tau = "DL", small.values = sv, warn = FALSE)
  cat("\n--- small.values passed:", sv, " stored:", net$small.values, "\n")
  nr <- netrank(net, method = "P-score")
  cat("netrank P-score:", round(nr$ranking.random[net$trts], 4), "\n")
  cat("pscore() :", round(pscore(net$TE.random, net$seTE.random, if (sv %in% c("good","desirable")) "good" else "bad")[net$trts], 4), "\n")
  set.seed(1); rk <- rankogram(net, nsim = 10000, random = TRUE, common = FALSE)
  cat("rankogram P(rank1):", round(rk$ranking.matrix.random[net$trts, 1], 3), "\n")
}
# TE convention: compare a direct pairwise estimate with the TE.random matrix
cat("\nTE.random['1','2'] =", net$TE.random["1","2"], " ; direct studies 1 vs 2 in P:\n")
print(P[(P$treat1 == "1" & P$treat2 == "2") | (P$treat1 == "2" & P$treat2 == "1"), c("studlab","treat1","treat2","TE")])
# Treatment 1 is timolol? read trt json
cat("trt names:", readLines(file.path(RUN, "data/std/473269.trt.json")), "\n")
# study Martin (id 4): t=1 r=11/30, t=2 r=16/30 -> log RR(1 vs 2) = log((11/30)/(16/30)) = ", log(11/16)
cat("log RR of t1 vs t2 in Martin:", log(11/16), "\n")
