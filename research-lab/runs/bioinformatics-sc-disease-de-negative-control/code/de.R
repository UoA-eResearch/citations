# DE engine (plan section 4), run in bioconductor/bioconductor_docker:RELEASE_3_22 with no network.
# For each job directory listed in the file given as the first argument:
#   counts.f32 (genes x donors, float32, column-major), meta.csv (ngenes, ndonors), donors.csv (sex),
#   draws.csv (id, kind, a, b: 0-based donor indices joined by ';'; a is the disease or pseudo-disease group)
# writes stats.csv (one row per draw: id, kind, ok, genes, pi1, n_de, mean_abs_lfc_top100, top100, sex_used, error)
# and, for kind == "full" or save == 1, t_<id>.f32 (moderated t of the kept genes) with kept_<id>.txt (0-based gene rows).
suppressPackageStartupMessages({ library(edgeR); library(limma) })
args <- commandArgs(trailingOnly = TRUE)
for (jd in readLines(args[1])) {
  if (file.exists(file.path(jd, "stats.csv"))) next
  meta <- read.csv(file.path(jd, "meta.csv"))
  con <- file(file.path(jd, "counts.f32"), "rb")
  x <- readBin(con, "numeric", n = meta$ngenes * meta$ndonors, size = 4)
  close(con)
  dim(x) <- c(meta$ngenes, meta$ndonors)
  donors <- read.csv(file.path(jd, "donors.csv"), stringsAsFactors = FALSE)
  draws <- read.csv(file.path(jd, "draws.csv"), stringsAsFactors = FALSE)
  rows <- vector("list", nrow(draws))
  for (i in seq_len(nrow(draws))) {
    a <- as.integer(strsplit(draws$a[i], ";")[[1]]) + 1L
    b <- as.integer(strsplit(draws$b[i], ";")[[1]]) + 1L
    idx <- c(a, b)
    grp <- factor(c(rep("A", length(a)), rep("B", length(b))), levels = c("B", "A"))
    sex <- factor(donors$sex[idx])
    res <- tryCatch({
      y <- DGEList(x[, idx, drop = FALSE])
      keep <- filterByExpr(y, group = grp)
      y <- y[keep, , keep.lib.sizes = FALSE]
      y <- calcNormFactors(y)
      design <- model.matrix(~ grp)
      sex_used <- FALSE
      if (nlevels(droplevels(sex)) > 1) {
        d2 <- model.matrix(~ grp + sex)
        if (qr(d2)$rank == ncol(d2)) { design <- d2; sex_used <- TRUE }
      }
      v <- voom(y, design)
      fit <- eBayes(lmFit(v, design))
      p <- fit$p.value[, 2]
      pi1 <- 1 - min(1, mean(p > 0.5) / 0.5)
      o <- order(p)[seq_len(min(100, length(p)))]
      if (draws$kind[i] == "full" || ("save" %in% names(draws) && draws$save[i] == 1)) {
        tc <- file(file.path(jd, paste0("t_", draws$id[i], ".f32")), "wb")
        writeBin(as.numeric(fit$t[, 2]), tc, size = 4)
        close(tc)
        writeLines(as.character(which(keep) - 1L), file.path(jd, paste0("kept_", draws$id[i], ".txt")))
      }
      data.frame(id = draws$id[i], kind = draws$kind[i], ok = TRUE, genes = length(p), pi1 = pi1,
                 n_de = sum(p.adjust(p, "BH") < 0.05), mean_abs_lfc_top100 = mean(abs(fit$coefficients[o, 2])),
                 top100 = paste(which(keep)[o] - 1L, collapse = ";"), sex_used = sex_used, error = "")
    }, error = function(e) data.frame(id = draws$id[i], kind = draws$kind[i], ok = FALSE, genes = NA, pi1 = NA,
                                      n_de = NA, mean_abs_lfc_top100 = NA, top100 = "", sex_used = NA,
                                      error = gsub("[\r\n,]", " ", conditionMessage(e))))
    rows[[i]] <- res
  }
  out <- do.call(rbind, rows)
  write.csv(out, file.path(jd, "stats.tmp"), row.names = FALSE)
  file.rename(file.path(jd, "stats.tmp"), file.path(jd, "stats.csv"))
}
