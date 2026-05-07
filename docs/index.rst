SciFig Documentation
====================

**SciFig** is a publication-quality scientific figure generation toolkit:
121 chart types, 6 journal style profiles, hybrid fluent + builder Python
API, multi-panel composition, statistical guardrails, and SVG/PDF/PNG
export with reproducibility metadata.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   quickstart
   api/index
   changelog


Quick example
-------------

.. code-block:: python

   import scifig

   fig = scifig.plot("data.csv", chart="volcano", style="nature")
   fig.savefig("volcano.svg")

Builder mode for multi-panel composition::

   (
       scifig.Figure(style="cell")
       .add_panel(chart="volcano", data=de_df, position=(0, 0))
       .add_panel(chart="box_strip", data=group_df, position=(0, 1))
       .compose(recipe="story_board_2x2")
       .render(output="figure.pdf")
   )


Modules
-------

.. autosummary::
   :toctree: api

   scifig
   scifig.api
   scifig.compose
   scifig.figure
   scifig.ingest
   scifig.polish
   scifig.registry
   scifig.stats
   scifig.styles
