Quickstart
==========

Install
-------

.. code-block:: bash

   pip install scifig

One-liner plot
--------------

.. code-block:: python

   import scifig
   fig = scifig.plot("data.csv", chart="volcano", style="nature", output="fig.svg")

Multi-panel builder
-------------------

.. code-block:: python

   (
       scifig.Figure(style="cell")
       .add_panel(chart="volcano", data=de_df, position=(0, 0))
       .add_panel(chart="km", data=survival_df, position=(0, 1))
       .compose(recipe="story_board_2x2")
       .render(output="figure.pdf")
   )

Multi-group statistics
----------------------

.. code-block:: python

   from scifig.stats import kruskal_wallis, one_way_anova, tukey_hsd, fdr_bh, recommend_test

   rec = recommend_test(df, "group", "value")
   if rec["test"] == "one_way_anova":
       result = one_way_anova(group_a, group_b, group_c)
       posthoc = tukey_hsd(df, "group", "value")
   else:
       result = kruskal_wallis(group_a, group_b, group_c)

   fdr = fdr_bh([0.001, 0.04, 0.03, 0.20], alpha=0.05)

Layout recipes
--------------

.. code-block:: python

   from scifig.compose import build_grid, list_recipes, pick_recipe

   recipe = pick_recipe(panel_count=4, use_case="multipanel_grid")
   fig, axes = build_grid(recipe["id"])

Finalizer
---------

.. code-block:: python

   from scifig.polish import enforce
   report = enforce(fig)   # collapse axes legends into a framed bottom-center figure legend
   fig.savefig("output.svg")
