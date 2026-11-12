# Slim FSL image for the software axis (D1): only the first-level tools FEAT's stats stage uses.
# feat_model builds the design from an .fsf (FSL's double-gamma HRF, temporal derivative, design high-pass),
# film_gls estimates it (with or without FILM prewhitening), fslmaths/susan smooth and filter the data.
# FSL is free for non-commercial academic use (https://fsl.fmrib.ox.ac.uk/fsl/docs/license.html).
FROM mambaorg/micromamba:1.5.10
RUN micromamba install -y -n base \
      -c https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/public/ -c conda-forge \
      fsl-feat5=2201.9 fsl-film=2111.2 fsl-avwutils=2209.8 fsl-susan=2111.0 \
 && micromamba clean -a -y
ENV FSLDIR=/opt/conda FSLOUTPUTTYPE=NIFTI_GZ PATH=/opt/conda/bin:$PATH
