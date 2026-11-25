# Scoping before the plan (2026-11-26)

Lead: `extra-open-energy-system-modeling-specification-curve-pypsa-conclusions` (value 7, cost 6). Chosen as the
next lead after the OpenNeuro multiverse was published: the Signature Research Area queue is exhausted for now
(`movement-akl-crl-full-timetable-reliability` is collecting data until Auckland Transport announces the full CRL
timetable; `frontier-photonic-inverse-design-seed-budget` was skipped on 22 October), and in the general ranking
the ten leads above or level with it were skipped earlier (README). It ties with
`extra-open-energy-system-modeling-reproducibility-rerun-audit` (7/6); this one goes first because the audit's
main mitigation, notifying authors, is something the lab does not do.

Nothing in this file involves a model run, a solved network or a result. `plan.md` comes next and must be committed
before any solve.

## Novelty (OpenAlex, 2026-11-26)

Close work found, none of it conclusion-centric:
- Frey et al. 2025, Nat. Commun. (10.1038/s41467-025-67593-9): 11,000+ scenarios for the German power system,
  varying inputs and method choices, evaluated on several criteria. A scenario-space method, not a re-test of
  published claims from other studies.
- Gøtske et al. 2024, Nat. Commun. (10.1038/s41467-024-54853-3): a sector-coupled European system designed against
  60 weather years.
- van Greevenbroek et al. 2025, Nat. Sustain. (10.1038/s41893-025-01556-2), and Grochowicz et al. 2023: near-optimal
  spaces across weather years.
- Karkossa et al. 2026, arXiv:2610.39859: which wind and solar modelling choices matter for European system
  configuration.
- Müller et al. 2026, arXiv:2606.16469: probabilistic technology tipping points.

Open so far: taking a handful of published qualitative claims of PyPSA-Eur-based studies and asking, claim by claim,
in what share of a defensible specification grid each one survives. To check before the plan: the papers citing
Frey et al. 2025 and Karkossa et al. 2026, and a full-text search for "specification curve" or "multiverse" with
PyPSA.

## Feasibility probes (metadata only)

- **Weather years without a Copernicus key:** PyPSA's data archive (`data.pypsa.org/workflows/cutout/v1.0`,
  dataset "cutout v1.0", added 2026-01-13 in `pypsa-eur/data/versions.csv`) serves pre-built
  `europe-<year>-sarah3-era5.nc` cutouts for 2009, 2010, 2012, 2013 and 2019–2024 (2011 and 2014–2018 return 404);
  about 6.6 GB each. Eight or more weather years are available without an account.
- **Download speed:** 200 MB in 12 s from data.pypsa.org (about 17 MB/s), so ten cutouts take about an hour.
- **Machine:** 28 cores, 93 GB RAM; /mnt/data has 183 GB free (the lead estimates 110 GB).
- **Still to check:** the technology-data releases (cost vintages) and which PyPSA-Eur version each can drive; HiGHS
  solve times at 37 and 60 nodes, 3-hourly, electricity only; whether each candidate claim can be expressed in the
  electricity-only model (a hydrogen-backbone claim needs the sector-coupled model, which is far heavier).
