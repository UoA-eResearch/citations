# Plausibility (G3), added after the independent review

The study predates the G3 gate. This places its estimates against the nearest published magnitudes.

- **The nearest prior estimate.** Azoulay et al. (2015, RESTAT) find that a retraction cuts citations to
  *topically related* papers by about 5–10%. Those papers share the retracted paper's subject matter, as found by
  PubMed's related-articles algorithm; this study's exposed works merely cited the retracted paper.
- **The preregistered estimate is implausible as an effect.** +0.068 log points is a 7% *gain* for citing a paper
  that is later retracted: as large as Azoulay et al.'s penalty, in the opposite direction. No mechanism would reward
  innocent citers by that much, which is why it was examined before being believed. The examination (deviations D1
  and D2) shows it is a matching artefact.
- **Design B's null is plausible.** Its interval, −1.5% to +2.1%, lies below Azoulay et al.'s 5–10%. A penalty for a
  topical neighbour of the retracted paper, but not for a mere citer, is the expected ordering: most citations are
  perfunctory, so citing a paper does not tie a work's credibility to it.
- **The sample.** The analysed works are those that could be matched, which are not the most-cited citers
  (`results/tables/selection.json`). A penalty confined to prominent citers would not be visible here.
