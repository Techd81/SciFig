Changelog
=========

v0.2.0
------

- PyPI release pipeline (``.github/workflows/release.yml``) with version sync verification.
- Sphinx documentation site (``docs/``) with autodoc + napoleon + intersphinx.
- Tag-triggered CI release workflow.
- README documentation refresh covering v0.1.4 -> v0.2.0 modules.

v0.1.7
------

- 6 synthetic-but-realistic domain fixtures + 30-case parametrized integration suite.
- ``scripts/validate_release.sh`` 6-gate pre-release health check.
- Bug fixes: integer column names auto-coerced; scatter regression numerical safety.

v0.1.6
------

- ``scifig.stats``: ``kruskal_wallis`` / ``one_way_anova`` / ``tukey_hsd`` /
  ``fdr_bh`` / ``recommend_test``.
- ``scifig.compose``: layout-recipe loader + ``build_grid`` / ``pick_recipe``.
- 8 common short-name chart aliases (``bar``, ``violin``, ``heatmap``, ...).
- Fix dose_response 4PL Jacobian numerical overflow.

v0.1.5
------

- ``scifig.polish``: canonical legend-contract finalizer with ``enforce``,
  ``sanitize_columns``, ``apply_chart_polish`` public API.
- Polar-safe spine handling.
- Legend anchor checks use figure-relative coordinates.

v0.1.4
------

- 7 differentiated generator modules (distribution, time_series, matrix,
  scatter, clinical, genomics, ml) overriding generic_chart fallback.
- Gallery style audit specification document.
