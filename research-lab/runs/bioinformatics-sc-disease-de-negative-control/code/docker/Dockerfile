FROM bioconductor/bioconductor_docker:RELEASE_3_22
RUN Rscript -e 'BiocManager::install(c("edgeR", "limma"), ask = FALSE, update = FALSE)' && \
    Rscript -e 'library(edgeR); cat("edgeR", as.character(packageVersion("edgeR")), "limma", as.character(packageVersion("limma")), "\n")'
