# Can open repeat LiDAR see kauri dieback? Not at trees graded from the track in 2014–15, and only faintly at trees graded in 2021

*Ground survey: Auckland Council's ObsKauri public layer. Trees graded along Waitākere tracks in 2014–15 (9,069
non-symptomatic, 320 with possible or severe dieback symptoms, after merging duplicate points) were compared with the
change in LiDAR canopy height within 15 m of each tree. The change runs between the LINZ Auckland North 2016–18 survey
and the Auckland 2024 survey. The test is prognostic, as the plan states: the labels predate the first LiDAR epoch.*

**Verdict: H1 Refuted; H2 Inconclusive.**

- **H1 (LiDAR crown change separates trees graded symptomatic, AUC at least 0.70): Refuted.**
  - The spatially blocked AUC of the change model is **0.51** (95% block bootstrap 0.44–0.56).
  - Every variant stays at or below chance: severe trees only (0.45), a 10 m or 20 m circle (0.47), no slip mask
    (0.50).
- **H2 (change adds at least 0.05 AUC to elevation, slope, canopy height and distance to track): Inconclusive.** The
  gain is +0.048 (−0.021 to +0.092), on a static model that is itself near chance (0.54).
- **With time-aligned labels (2021 survey, secondary), there is a faint signal.**
  - The change model scores AUC 0.55 (0.51–0.59), and it adds 0.021 (0.002–0.041) to the static model.
  - Canopy P95 rose 2.2 m around non-symptomatic trees, 2.0 m around trees with possible symptoms, and 1.6 m around
    severely affected trees.
- **The surveys differ by more than the trees do.** Canopy height rose by 1.25 m on average even at random forest
  points away from any survey record. This is growth plus any systematic difference between the two LiDAR surveys,
  and it is larger than any difference between symptom groups.

## In plain terms

Kauri dieback kills Aotearoa's giant kauri, and finding sick trees on foot is slow and can spread the disease. We
asked whether free laser scans of Auckland, flown in 2016–18 and again in 2024, can show which kauri are dying, by
measuring how much each tree's crown thinned or dropped between the two scans.

We used the council's ground survey of 2014–15, when people walked the Waitākere tracks grading every kauri they
could see. The trees graded as sick then did not lose more crown over the following years than the trees graded
healthy. The scans could not tell them apart at all. Trees graded in 2021, closer in time to the second scan, showed
a faint difference: sick trees' canopies grew a little less. That is far too weak to use as a map of sick trees.

Part of the reason is the scans themselves. The forest canopy measured more than a metre taller in 2024 almost
everywhere, which is partly real growth and partly a difference between the two surveys. Part is the trees: those
graded in 2014–15 stand along tracks, under mixed canopy, where a 15 m circle catches neighbouring trees as much as
the kauri. Open LiDAR at this resolution does not give a cheap early-warning map of kauri dieback, at least not
without crown-level data.

## What was asked

The lead (`auckland-nz-kauri-dieback-multitemporal-lidar`, Auckland signature area) asked whether open repeat LiDAR
can see kauri dieback, using ObsKauri field surveys as the answer key. The critic's note reframed it as a prognostic
test, because the 2014–15 labels predate the first LiDAR epoch, and added the 2021 survey as a time-aligned check. No
dieback study using repeat LiDAR or ObsKauri was found.

The plan (`plan.md`) was committed before any LiDAR was read. The feature and model code was committed before any
feature was computed.

## How it was done

- **Labels.** ObsKauri, downloaded in full on 2026-10-23 (52,867 records).
  - Primary set: the Waitakere Track Survey 2014-2015. Positive is status 3 (possible) or 4 (severe); negative is
    status 1.
  - Records within 2 m with the same status were merged: 12,512 status-1 records became 9,069 trees, and 336
    symptomatic records became 320.
  - 30 trees were dropped because under half of their circle had valid LiDAR.
- **Canopy height.** DSM minus DEM at 1 m for each epoch: Auckland North 2016–2018, and Auckland 2024 Parts 1 and 2.
  The mosaics cover the survey extent.
- **Features within 15 m of each tree:**
  - change in P95 and P50 canopy height, and in the share of cover above 15 m;
  - cells whose ground height changed by more than 1 m (slips) masked;
  - static features: elevation, slope, 2016–18 P95, and distance to the nearest OSM path, footway or track.
- **Models.** Logistic regression on standardised features. Out-of-fold predictions came from 5-fold cross-validation
  over 500 m blocks, with 5 repeated splits averaged. AUC intervals come from a bootstrap over blocks (2,000
  resamples), and the H2 gain is paired.

## Results

### H1 and H2 (`results/figures/F1_auc.png`)

![AUC by model and label set](results/figures/F1_auc.png)

| labels | symptomatic / trees | change AUC | static AUC | static + change | gain |
|---|---|---|---|---|---|
| 2014–15 (primary) | 320 / 9,359 | 0.51 (0.44–0.56) | 0.54 (0.48–0.62) | 0.59 (0.52–0.65) | +0.048 (−0.021 to +0.092) |
| 2014–15, severe only | 86 / 9,125 | 0.45 (0.37–0.54) | 0.47 | 0.51 | +0.042 (−0.049 to +0.097) |
| 2014–15, 10 m circle | 317 / 9,349 | 0.47 (0.41–0.52) | 0.57 | 0.61 | +0.040 (−0.026 to +0.076) |
| 2014–15, 20 m circle | 320 / 9,362 | 0.47 (0.41–0.53) | 0.53 | 0.58 | +0.046 (−0.018 to +0.089) |
| 2014–15, no slip mask | 320 / 9,389 | 0.50 (0.44–0.55) | 0.55 | 0.59 | +0.044 (−0.021 to +0.083) |
| 2021 (time-aligned) | 633 / 1,801 | 0.55 (0.51–0.59) | 0.59 | 0.61 | +0.021 (+0.002 to +0.041) |

### Canopy change by status (`results/figures/F2_change_by_status.png`)

![Change by status](results/figures/F2_change_by_status.png)

- **2014–15.** Mean P95 change was:
  - +1.58 m (1.46–1.69) around non-symptomatic trees;
  - +1.40 m (1.16–1.69) around possible;
  - +1.35 m (1.05–1.70) around severe.

  The intervals overlap.
- **2021.** Mean P95 change was:
  - +2.16 m (2.08–2.24) around non-symptomatic trees;
  - +1.97 m (1.86–2.07) around possible;
  - +1.56 m (1.29–1.83) around severe.
- **Random forest points:** +1.25 m (1.04–1.45). Between-survey differences (season, point density, processing) are
  not separable from growth here.
- **Setting.** The 2014–15 trees stand a median 5 m from a track, under canopy whose P95 is about 15 m. The 2021 trees
  stand a median 130–180 m from a track, under canopy of about 23 m.

## What this does and does not show

- **No prognostic signal from track-side ground grades.**
  - Trees graded symptomatic in 2014–15 did not lose more crown between 2016–18 and 2024. Neither the change features
    nor the static ones separate them, so a cheap LiDAR screen calibrated on these labels would not work.
  - Possible reasons:
    - GPS error under canopy;
    - track-side mixed canopy inside a 15 m circle;
    - a lag of 1–4 years between grading and the first scan;
    - severe trees that had already lost their crowns before 2016–18.
- **A faint, time-aligned signal.** With 2021 grades, severe and possible trees grew 0.2–0.6 m less than healthy ones
  (AUC 0.55). That is evidence that LiDAR registers dieback in aggregate, not that it can map it.
- **Not shown:**
  - that LiDAR cannot see dieback with crown segmentation, full point clouds or structural metrics (gap fraction,
    return intensity);
  - anything about Hunua, where the 2017 survey found almost no symptomatic trees.
- **Care.** Kauri are taonga, and the Waitākere Ranges are under a rāhui placed by Te Kawerau ā Maki. This study entered
  no forest and used only open data. It publishes features by record identifier only, with no coordinates. Methods
  like this belong with the kaitiaki and the council's kauri programme.

## Process and deviations

- **Preregistration:** `plan.md`.
- **Deviations:** none (`deviations.md`). Overpass needed retries, with no change to the method.
- **Independent review:** queued (Fable), per the lab's pacing rule.

## Reproducing it

1. `code/fetch_obskauri.py`.
2. `code/features.py mosaics`, then `code/features.py trees` (→ `results/tables/trees.csv`, with no coordinates).
3. `code/model.py` (→ `results/tables/primary.json`).
4. `code/figures.py`.
