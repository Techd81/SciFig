# Template Mining — Per-Case Narrative & Trick Digest

Source: 94 cases.  Re-run `enrich.py` after `extract.py` to refresh.

## Narrative arc distribution

| Arc | Cases | % |
|---|---|---|
| `single_focus` | 31 | 33% |
| `multipanel_grid` | 27 | 29% |
| `marginal_joint` | 5 | 5% |
| `composite_two_lane` | 5 | 5% |
| `global_local` | 5 | 5% |
| `hero` | 5 | 5% |
| `n×n_pairwise` | 5 | 5% |
| `train_test_diagnostic` | 4 | 4% |
| `mirror_compare` | 4 | 4% |
| `inset_overlay` | 3 | 3% |

## Signature-trick frequency (regex over code)

| Trick | Cases |
|---|---|
| `alpha_layered_scatter` | 24 |
| `density_color_scatter` | 16 |
| `group_divider_axvline` | 14 |
| `raincloud_combo` | 13 |
| `metric_text_box` | 12 |
| `pvalue_stars_overlay` | 9 |
| `axes_inset_overlay` | 8 |
| `dotted_zero_axhline` | 8 |
| `colored_marker_edge` | 8 |
| `twin_axes_color_spines` | 7 |
| `error_band_fill_between` | 6 |
| `marginal_axes_grid` | 6 |
| `category_split_dashed` | 4 |
| `dual_y_bar_line` | 4 |
| `imshow_gradient_box` | 4 |
| `upper_triangle_split` | 4 |
| `perfect_fit_diagonal` | 3 |
| `polygon_polar_grid` | 3 |
| `ridgeline_offset_kde` | 2 |
| `shaded_zone_axvspan` | 2 |
| `colorbar_ticks_styled` | 2 |
| `regression_band_fillbtw` | 1 |
| `bezier_smooth_line` | 1 |
| `diverging_cell_label` | 1 |
| `polar_value_marker` | 1 |

## Per-case digest (grouped by narrative arc)


### Narrative arc: `single_focus` (31 cases)

- **1777452458** `Python 科研绘图：如何优雅地展示“模型精度+稳定性”？顶刊可视化复盘`
  - family: forest,scatter_regression,marginal_joint | grid: [2, 3] | palette: #EE6677,#4477AA | images: 4 | code blocks: 4
  - tricks: group_divider_axvline,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5NMeBQ23bkj9gs96pW7tuUHyHaBNInwZiaB35Ms8Sy52NZQZO4q8H5SbKfkG5qPlLKZb655ibFehlA%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5NMeBQ23bkj9gs96pW7tuUWPW5LWsRzQKrkVXkn4KSns1k1BvESGfGFrUzeGF3ur6d5NlibxVNN2w%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5NMeBQ23bkj9gs96pW7tuUeMw2StBgLSWa6ZAia2P1SsCJFvTWF3Lmv1zABHtYVTsibWOeibnksqqbQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777452391** `Python科研绘图：一行代码实现 R² + 95% 置信区间的高级散点图`
  - family: scatter_regression | grid: — | palette: #313695,#A50026 | images: 2 | code blocks: 4
  - tricks: metric_text_box,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5ockOmCw74h4od1vCgldic6TNuSut2VmicDO6icAqB0JaYf8osZqafDdDatmnOb6FpXBYQN8AxtqsBg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5ockOmCw74h4od1vCgldic6evzwxD1UErlENkO7ibNCkVDPaDULjEyI3Gx9Lf0kDmh5bKFJ2CXZYpw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777451587** `如何用 Python 完美复刻一张“红蓝气泡”相关性分析图`
  - family: heatmap_pairwise,heatmap | grid: — | palette: #8ECFC9,#FFFFFF,#FA7F6F,#F0F0F0 | images: 4 | code blocks: 5
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6ia19doyebg6ibOWyMqnyuPE7vFLYCZLUZRsMxysjGVySzOpiaN8GicI3ZYAG6E6diat9tnayksiacof3w%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6ia19doyebg6ibOWyMqnyuPEzBVHzGibek5A3caqXRKkfJvIePjFMlHOCsho6NkH6s7J3tP4UquzicGg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6ia19doyebg6ibOWyMqnyuPEzy23dicWT2GTNlsMxRCibFplM2pro0bYEibXB1UOibICoKNjNw8ecNBNYw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777455232** `期刊图表复现：偏最小二乘路径模型揭示变量间因果与总效应`
  - family: scatter_regression,nmds_pca,ale_pdp | grid: — | palette: — | images: 4 | code blocks: 4
  - tricks: axes_inset_overlay,metric_text_box,group_divider_axvline,category_split_dashed
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElsucHvAyMh7u9SMRdopibMR3K6iaCtqNWohux8W3nbwIM1QPJWP3UoVfHHqsU1XfNXYDpypz3IMRkt38VhNdZvg7WlcDuOzyGajhw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElstOGDnQ3czt7CqBjj8icmTSW8Pow03bubicfTVLMxjNbUp9114stf10DiavyZdAoq8bMQ9Fht7aVXSO0TBzYaEibnhicV3y7MvNcFVs%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElstgMBremuf3OgDgfDKY9J5icvLj5ZnHBI5BE23QiceLSqpo1ascrkx9TJTicHr4lf4J3CSSiaauRicEPPFDhsnEXVic9NuoX1QASGVP4%2F640%3Fwx_fmt%3Dpng
- **1777455816** `期刊图表复现：叠加二维核密度的渗透汽化膜性能预测对比图`
  - family: scatter_regression,density_scatter | grid: [1, 2] | palette: — | images: 4 | code blocks: 4
  - tricks: density_color_scatter,metric_text_box,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsunDkp7S5wW26O7FT9e5AialiclvN0wgFHbStIwzjCf0tA5mEBicFjiaw2NganuFiaKicBytaEukPAK0DI7skSr6SL04xu3MrXgJiabyw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElstePiaE50iaNZV0Pz7b3E0TYwUcGicHYEVQ8ibggV6cYstRA2qibJzvpssNHUAhTj083d774iasREX7cJaYZicwvwaPDdr3tgZeWcFpFM%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsvibdQgawQL7sc5Mw4b5eGDXVhSBbmP4YPwPxxeKyN2RINS3qZ8yFicH4suG5jCibS6669bKWjekMsgrtGkph9brA47RLssHKSMxE%2F640%3Fwx_fmt%3Dpng
- **1777454034** `期刊复现：SHAP依赖图解析环境因子对目标变量的影响方向与程度`
  - family: shap_composite,scatter_regression,ale_pdp | grid: — | palette: #808080 | images: 3 | code blocks: 4
  - tricks: group_divider_axvline,raincloud_combo
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsswwkEC4XmXyUbvXEzicMrLbLUq3X1MStGDqWGyEKDtibALLia5L5z2TA24qnhFT9lb1tnyE1Zibbz5csLzpGrzV27RTibKhenIRdIM%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElst4ictjJXMmmjiaUn5kCS6IOmY4j6xdsTBwsNwHqicPWtCLcqibnPcCXs49VckASGcicdwKuNEjJFc1Ue14Uk47yueuiaD9mNfwMR5lc%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElstic7VMNUMSZibQYjRCNcCySsP20KoCw9viaEROSQGFNK0n0IptF6V7oLvz5JU38tVdibzTpGHwTzvdvXMB074m2El25qGXiaQ0AXJM%2F640%3Fwx_fmt%3Dpng
- **1777455105** `期刊复现：SHAP蜂群图解析环境因子对目标变量的影响方向与程度`
  - family: shap_composite,scatter_regression,ale_pdp | grid: — | palette: #808080 | images: 4 | code blocks: 4
  - tricks: group_divider_axvline,raincloud_combo
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsvCZLGkU0RWVJjdXEGjSQwdFFiaJSKI25a7R6k5VrNnoOCKX0Fya3eXu6fvsrPIPr4fwgwy78cIcBSTVd2gujn4mdSdvxwDKTl8%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsvyZOr8S6vDKmOHFZbpl7iauW2BQ9JXiaNogMGaiawYXjFMXAMXIdH2Egia0QibMFNIgK0Sybk8xlIGbLqDh1FKO3wpTXXqeu9S3wwo%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElssN92caRKnIub2RcdufacPkbXibep6yyspUSicdbzaHSJL0a21J2L3icGfLtbt8j9SRujMW5T9HAjg4V7WQvCc5fD7QlnPtwFfFd4%2F640%3Fwx_fmt%3Dpng
- **1777456122** `期刊复现：利用组合式箱线折线图与气泡热力图可视化模型超参数稳定性`
  - family: heatmap,scatter_regression,box | grid: [2, 2] | palette: — | images: 4 | code blocks: 4
  - tricks: density_color_scatter,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElstp5Eqll6hCPia3Dr2OLc3N7jffXetPQVGthfLEb41l4XjnHDLnEpwhZ3rJC4VXxFA7J65DOxLWf09Kx2o0ARr8sEXCllQVgBuY%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElsuPR4GQaxdMiaaC2JcmqqGfibJ2IlI07YQVFicJPicZNhGzQnVic7ExicnrcgibWWu0CpiafvcoInPqr5h6yazczBtTmsDQ7FwsTcf8qww%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsu9w0eib3MztsqlHa7Tbiczl5ibZoSGYjfYbl5HE8HovGALultvu3ia52FtCNDCe8KE9Oq2kOan6hsyWqyzzHlvqo7VaWqiciculEgBY%2F640%3Fwx_fmt%3Dpng
- **1777453986** `期刊复现：双面板NMDS散点图通过颜色分组评估水质期群落差异`
  - family: scatter_regression,dual_axis,nmds_pca | grid: [1, 2] | palette: — | images: 4 | code blocks: 4
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsuqDEqzfZdLgOiczI67liaxSmvdzXpcTvJm0HlWNl6HhI66uStaf0EOPlRLkAicW9PZxGv5clZfmHPl5L78l35GU6R3rpZSjlianVE%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElstZZQJmdGHicmKzRdOzjWwdzmy7YWTrxCvJa3pzUg5SmBFB0q8QicGXUibNvs29iaAiauwafrvGytI2Ax49qoFemUmEoZ3ick4eicph8Q%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElstmv69SN0z42z551tUX3gh5yl95QhK5DyIpHdxegPfNKKTAoiaa7ojDeoXTMJvmc1aNk3pa4W0NwJIt5perznr4JqEicovhjODQc%2F640%3Fwx_fmt%3Dpng
- **1777455674** `期刊复现：基于H-statistic的特征交互重要性与二维等高线依赖图解析`
  - family: heatmap,scatter_regression,ale_pdp | grid: [3, 2] | palette: #4A708B | images: 4 | code blocks: 4
  - tricks: density_color_scatter,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElsteULNxIyxoIUKQwbnEnB2hmMMgAEge6roZz8suQlxSGmkC2Uhmz0mGNS19EtyQv6MmZxlHT3RlLXAHUopn28kwsUcnnFXzaOE%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElsuxRLQIDYSFicw359cbXfvwuibibRph8kPf4okIEBQjCvjXT1DAzsb8evMmV1borQbADQ9PodlEqyFRPrN9uI0Wa2l0uJaM4GQj5E%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElst78ofibAqaZQoFTvPia2rIhQjOUOYxwDKWDB9Ja9VibaufeolyEPWXnW7sw9VRoK6835cKkgPiceYDlTXsDhsx9icGrRN4EmTIs41s%2F640%3Fwx_fmt%3Dpng
- **1777454077** `期刊复现：基于RF-XGB的SHAP部分依赖图解析关键参数阈值`
  - family: shap_composite,scatter_regression,ale_pdp | grid: [1, 3] | palette: #1F77B4 | images: 4 | code blocks: 4
  - tricks: density_color_scatter,dotted_zero_axhline,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElsvdVUYiaumRVAXic7RxpAnGgzFmqxA8cbEdic3ib5WkZwleyRfrPWJ1ufl20JF5TicMHecQIowXV0xkyzabAVMZq2Pia45PUQpjDe4kg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElstkCFcNbP70shASaQcNAkAWaK9fTNibjXD0l6ib548ZltEX0Vjw7NzE3GJC8bHUBQon8mPzc0tTdOrTpYThrmsW8VkNeHV2MscIM%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsv2JPAiakrr1Xp9o9iahQnPoSSicGBeia6osc6AWghKXfFjcQKaYXcA7CqTvf9x0BtV7qXVX45maiaZTbeaApsRTicia5xaibOOzh8AfJg%2F640%3Fwx_fmt%3Dpng
- **1777451762** `期刊配图优化：Python绘制“双面板PCA得分图”，优雅展示多配方综合评价`
  - family: dual_axis,nmds_pca | grid: — | palette: — | images: 3 | code blocks: 3
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6WKYKtqmtF44YR4NlJqRic9BXw2hOyMu4ZmMZicIArS4hejHdARBzGuy2H71K2SoDIiaialLsQxmRENQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6WKYKtqmtF44YR4NlJqRic9FvweHCqYwClXQAIoicVaohcuMm2uVeGGuDXXMicahXVNFVeiaytA8XMbQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6WKYKtqmtF44YR4NlJqRic93x7SNhArWqCsgApzonhHGsv25wIoJpAXD7DicgeTXLtgnRlffpzRFiaw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777451814** `期刊配图复现 `
  - family: scatter_regression,time_series_pi,box | grid: [2, 4] | palette: — | images: 4 | code blocks: 4
  - tricks: error_band_fill_between
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4Y08AJFiaBatuzUNzEJh9zFKNF5v6MVAnfElqNL0tt6xZypvlyFn5J2oKAAYNOZnRZeBlgnR8qibibw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4Y08AJFiaBatuzUNzEJh9zFxMSsP7Mrqiam4YVD7rzoiaZlm3lEspnNUaomjBeamZU80WRtlzbPsxfA%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4Y08AJFiaBatuzUNzEJh9zFogB2cRb4HlLL3fIGQ7gmibkV3JUBUFEDCKRCY5bTOshsiaVSbOSgm7fw%2F640%3Fwx_fmt%3Dpng
- **1777452713** `期刊配图复现 `
  - family: scatter_regression | grid: — | palette: #D62728,#1F77B4 | images: 3 | code blocks: 3
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6jjBTg6FXy3l3MUX5wpWkBx1cu9N9WicBs9frsAmTYlYnyXefLgFXCGxMEKxnHEuZLNIUj2S304zg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6jjBTg6FXy3l3MUX5wpWkB9MhPLZTyqW4IB9RIJXNSDoj4dK3tZogK7RRcr3E2oMCTeiaJ5xsENQw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_jpg%2FgCE6Jqa7zN6jjBTg6FXy3l3MUX5wpWkBoV6jArQGictRL08L4DO3m7ogssbweFsboricefjJ52hr953HYzjrX8CQ%2F640%3Fwx_fmt%3Djpeg%26from%3Dappmsg
- **1777454339** `期刊配图：云雨图结合半小提琴与抖动散点展示不同城市化水平的通量差异`
  - family: scatter_regression,violin,raincloud | grid: [1, 2] | palette: — | images: 4 | code blocks: 4
  - tricks: raincloud_combo,colored_marker_edge
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsvg21mmvz3BfCCWG40ric3YiaicojX7xGoMjRDtyPsI8X6ibj5ddPty3DoXpAEajFK3N12JicQWv6Jyp2jACbCzmZ4wgIw0hBfuVY5I%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElstTZIibbMXdicIJWfPTicX6oCibeYLR9wjap8y5qdqSGicBx4cXZK7Zd8Qw7GYJsLb1zbr2R3c2pBHzjb8eH1IOUbhhCbgwfpCQkJt0%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsvntPvUGHMerbMhfXEHPo9kTKg1XYSiafL1InhkH2Hx8iag0IjpzxVcvibSunuiaWQIPJxAQU4WLpSLVFCUerYBcLHJDltF2OoQv2U%2F640%3Fwx_fmt%3Dpng
- **1777454120** `期刊配图：基于线性拟合与误差带的距离衰减散点图解析群落空间演变`
  - family: scatter_regression,density_scatter | grid: — | palette: #D62728,#1F77B4 | images: 4 | code blocks: 4
  - tricks: error_band_fill_between
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsuh4ckP4adiawcVzQhs6OJ17b6tvibjFWHE3DhAeiao91I63JHQWiaf1eP4jKDk2mdGk2CbSllIj5kliaCmhT62tZJrKIXbET4ZibdicE%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElstOHpnCMLP0IdaKWluShAJk6wqOZBdCxsC7Omz4Ob2tlfnaMzfG426pNR3mzzjfEJBjtRtKqG9ZXYVwbDlQn2tzuMVC7cvR1Vs%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElstKTsT2s6eeTpsKSJB5tc8mJKkQCrf22F3iaQCj2L24GJ4c6gN8ltqoq8o1KKDXDafmh7icBkFmic7aPNHmQBISnKNfHkJkzcIPVM%2F640%3Fwx_fmt%3Dpng
- **1777451428** `顶刊审美 `
  - family: scatter_regression,gradient_box,box | grid: — | palette: #E0E0E0,#F06292,#C2185B | images: 5 | code blocks: 4
  - tricks: imshow_gradient_box,raincloud_combo,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7MKY1tAo6dd2Yf0nqhFvKly3Hb3AicG85H3D7MSnqdzzVfKecibXdu7yJwzoS76lXLp0VA6YukNC6A%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7MKY1tAo6dd2Yf0nqhFvKlvo8cGKlicYZCEW2MaXqv5iaJZ4TajRA4ia9ozhhicxhVQotyickjicVkW7YQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7MKY1tAo6dd2Yf0nqhFvKlQEmWRdapZ6JftPtkQDzmKprYtJy9rdTvQicdzfoQ67JPPUOCbxSTJ8A%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777451193** `高级感！Python复刻Cell顶刊散点柱状图`
  - family: — | grid: — | palette: — | images: 5 | code blocks: 5
  - tricks: raincloud_combo
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4dxprliaXjUlibvibuibHZ7GibwEtSuPa8rTTceRxic2yCpCn0kvhv5S9NZibLP5bSgYQa6Pfk8717BJEEQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4dxprliaXjUlibvibuibHZ7GibwhDwAnYywKNxia2QPE5mPHK287XMrJYqxew0lTp4QuehBj3MCVsntDMg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4dxprliaXjUlibvibuibHZ7Gibw1nc16xG125Uic1BGQicMTfkJiaP2iacWNdTWe8icruKkINH4UKsH7yfuXibA%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1778681086** `期刊复现：XGBoost的双变量偏依赖(PDP)等高线可视化图（附代码）`
  - family: forest,shap_composite,scatter_regression | grid: — | palette: — | images: 15 | code blocks: 4
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_gif%2FW3juZXNhicnpPWUqaQaH0TjDicsP8iaKoAFCb5Z0A5bTU7dDuGCtY9A7MINoyvpOFHjibVj6G6VoibAFL99uqJvfxkA%2F640%3Fwx_fmt%3Dgif&n=-1; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElssMHib1iaSKiaAyM8q0ibGfHQO8npDsoMHgNm5O4A2EopKYPicI9bXAfOrjvOunBTS71WDustHro7AniaVuia2xt62bjSgTg1yloeV1Zw%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_gif%2FW3juZXNhicnpPWUqaQaH0TjDicsP8iaKoAFCb5Z0A5bTU7dDuGCtY9A7MINoyvpOFHjibVj6G6VoibAFL99uqJvfxkA%2F640%3Fwx_fmt%3Dgif&n=-1
- **1778681131** `期刊复现：基于双Y轴折线与动力学误差棒的生物降解实验效能可视化`
  - family: forest,scatter_regression,dual_axis | grid: — | palette: #F4B1B1,#A9D1F4,#D02A27,#1F77B4 | images: 16 | code blocks: 4
  - tricks: twin_axes_color_spines
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_gif%2FW3juZXNhicnpPWUqaQaH0TjDicsP8iaKoAFCb5Z0A5bTU7dDuGCtY9A7MINoyvpOFHjibVj6G6VoibAFL99uqJvfxkA%2F640%3Fwx_fmt%3Dgif&n=-1; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsvvDE3tFDwSMcWJWmcmoF5Eef1a8G1uHoRiauJDiagXfSytaNL72s9bWMG3POPibDLnsz73sZ9DkOslVldiaCsVlnYKhM37W7y1F6w%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_gif%2FW3juZXNhicnpPWUqaQaH0TjDicsP8iaKoAFCb5Z0A5bTU7dDuGCtY9A7MINoyvpOFHjibVj6G6VoibAFL99uqJvfxkA%2F640%3Fwx_fmt%3Dgif&n=-1
- **1778681006** `期刊配图：基于集成模型的3D部分依赖图(PDP)非线性交互效应可视化（附代码）`
  - family: scatter_regression,ale_pdp | grid: — | palette: — | images: 18 | code blocks: 4
  - tricks: density_color_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_gif%2FW3juZXNhicnpPWUqaQaH0TjDicsP8iaKoAFCb5Z0A5bTU7dDuGCtY9A7MINoyvpOFHjibVj6G6VoibAFL99uqJvfxkA%2F640%3Fwx_fmt%3Dgif&n=-1; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsvtH55hkd17p0iahd9Y30pZQWSEEbSwGVEm4krqNTyQAGVia4WJvo1NGdl9P758M45QD5H7CickEvvjTxvQxDppn6ia34umoe4hMEY%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_gif%2FW3juZXNhicnpPWUqaQaH0TjDicsP8iaKoAFCb5Z0A5bTU7dDuGCtY9A7MINoyvpOFHjibVj6G6VoibAFL99uqJvfxkA%2F640%3Fwx_fmt%3Dgif&n=-1
- **1778680013** `机制解释图复刻：基于Random Forest与局部依赖图(PDP)揭示特征关键阈值（附完整代码）`
  - family: forest,ale_pdp | grid: — | palette: — | images: 0 | code blocks: 0
  - tricks: —
- **1778682927** `机制解释图复刻：基于Random Forest与局部依赖图(PDP)揭示特征关键阈值（附完整代码）`
  - family: forest,shap_composite,scatter_regression | grid: [2, 3] | palette: #0033CC,#CC0000 | images: 0 | code blocks: 4
  - tricks: —
- **1778682195** `Python 实战  `
  - family: shap_composite | grid: — | palette: — | images: 0 | code blocks: 9
  - tricks: —
- **1778682290** `Python玩转时序栅格 `
  - family: shap_composite,scatter_regression,time_series_pi | grid: — | palette: — | images: 0 | code blocks: 5
  - tricks: —
- **1778682475** `python绘制分布密度线性回归拟合图`
  - family: shap_composite,scatter_regression | grid: — | palette: — | images: 0 | code blocks: 9
  - tricks: density_color_scatter,perfect_fit_diagonal,marginal_axes_grid,colorbar_ticks_styled
- **1778682795** `Python绘制箱型图与回归线，一眼看穿数据趋势！`
  - family: box | grid: — | palette: — | images: 0 | code blocks: 12
  - tricks: shaded_zone_axvspan
- **1778682066** `Python脚本批量分析栅格数据(最大值、最小值、平均值、标准差，检查是否存在缺失值)，结果直达Ex`
  - family: shap_composite | grid: — | palette: — | images: 0 | code blocks: 6
  - tricks: —
- **1778681959** `告别枯燥表格！Python绘制超吸睛的相关性气泡图`
  - family: heatmap_pairwise,heatmap | grid: — | palette: — | images: 0 | code blocks: 7
  - tricks: pvalue_stars_overlay,upper_triangle_split,colorbar_ticks_styled
- **1778682618** `精准复现顶刊插图：Python实战零售食品环境与肥胖率关联气泡图！`
  - family: heatmap_pairwise,ale_pdp | grid: — | palette: #CC66CC,#336699,#FFCC99 | images: 0 | code blocks: 8
  - tricks: metric_text_box
- **1778682387** `轻松修复遥感影像的缺失！使用历史同期数据来填补！`
  - family: shap_composite,scatter_regression | grid: — | palette: — | images: 0 | code blocks: 6
  - tricks: —

### Narrative arc: `multipanel_grid` (27 cases)

- **1777452771** `Python复现顶刊CEJ `
  - family: scatter_regression | grid: [2, 3] | palette: #00CED1,#FF0000,#1E90FF | images: 4 | code blocks: 5
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4mLj0QNzq25hfOP6SN9icp3rGpAiaKaHlKPa14B4X51CftXyib27gaRJviciaIA8yaWDiaTqRsetUepcnw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4mLj0QNzq25hfOP6SN9icp3xwohym77nmjM8icVwOf3tMeG6NlTyjfqhia2QgMfFa14BwU9W5ibedBYg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4mLj0QNzq25hfOP6SN9icp3jtWRXUib4TtvtN880L79Ze0gd6E4874kghGXYopZIXtwkvSp5YCVc6Q%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777453520** `Python科研绘图复现`
  - family: forest,scatter_regression | grid: [1, 4] | palette: #8DA0CB,#FC8D62,#66C2A5 | images: 2 | code blocks: 5
  - tricks: group_divider_axvline,ridgeline_offset_kde,category_split_dashed
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7taZq0AqdQIvXd8GggiadCibkfsgWmuZ2meKVIIaeF01U0lu4rDmp04W61tibplVTqMWZoxmaM90tUQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElssAzaaopAs5CNEjiaWlfBXmAbBMILxiaAGxF0husAwFNyAPt8Y6zPaDgBIwvR2t8sZ8TViaKcPIPd02F0ic9Yld6J2hCziczkurzrCE%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777461729** `基于PSO多目标优化与SHAP可解释分析的回归预测模型框架`
  - family: radar,shap_composite,heatmap_pairwise | grid: — | palette: — | images: 3 | code blocks: 2
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6BdprZvicy5Zhs1z5FibE9QTWY2Ib9zeibHl6POHAO5ZupfYK92HOSMzYZiaXrBXgREmicpEpoOvYbkkw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6BdprZvicy5Zhs1z5FibE9QTc9NzD0cc49PDgXQNOmAib7pS7Y8e2KeckibNvoA8vviaSpvBCSvEicDaxg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6BdprZvicy5Zhs1z5FibE9QTLxO2DuDOKDF6rvmlyWXSUoGLNDV9MFx2RTiadgk2qGSVBIyR10vB8ag%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777451702** `如何用Python绘制教科书级的双Y轴组合图`
  - family: dual_axis,ale_pdp | grid: — | palette: #CFE2F3,#9BC2E6,#F48E66 | images: 4 | code blocks: 5
  - tricks: twin_axes_color_spines,group_divider_axvline,bezier_smooth_line,dual_y_bar_line,category_split_dashed
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN64BchtGYPJWHYXv2cjb11TRQqz6JRAicSjsE1Opxaxf2kPfPUw55qhDQTmDiahkblU6uUfdC7nIUWg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN64BchtGYPJWHYXv2cjb11TiaQX6FUQ3qywabK9us3N5lbUZng7jJNrcfTypdPa8nlXLxkg6ebdAUA%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN64BchtGYPJWHYXv2cjb11TSlOlicZYmSV1KWw9G75ibc8XnPEMt6KhnxYaJtHtZVIHkL2KT8YJmY6Q%2F640%3Fwx_fmt%3Dpng
- **1777451272** `拒绝默认配色：Python 绘制多模型性能对比图的进阶实战`
  - family: forest,shap_composite,scatter_regression | grid: — | palette: #E64B35,#4DBBD5,#00A087,#3C5488 | images: 4 | code blocks: 4
  - tricks: group_divider_axvline,category_split_dashed
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7iaibC43JDrVXFlm64QhvZ1qyJPkf5Bo5oboKlZyUkUYZyU3RhA1SudDxlCrlmxca9zTyicQZLsRtiaw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7iaibC43JDrVXFlm64QhvZ1q9PgGNwaXotd6TyZPQx501ia7Mlcse9p0ia0ViaFNT4A9DVqWJqeE2gORg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7iaibC43JDrVXFlm64QhvZ1qWyWhHhclw8h8J2pxpgLwTNAP6ua4DHdlN5yibz2eCRcIicb2h9gbF1Gw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777454691** `期刊图表复现：多面板SHAP依赖图展示分子特征对自由基反应速率的非线性影响`
  - family: shap_composite,scatter_regression,ale_pdp | grid: [2, 3] | palette: #FFCCCC,#CCE5FF | images: 2 | code blocks: 4
  - tricks: shaded_zone_axvspan,dotted_zero_axhline,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsuib6zJrVshibn5XozN3HoLTrLribuJ7KicsmUctkHfV28xkCD3XHMW5UZ1IJuibEq9nxZISLjUxDVic33uEzRlVtn5N8ickBQGhSlVJk%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElssZY5dxL1hZznwwQgwnwAP2Epa2QONmDhf0r3w9XVYz1Pn57KAasxQ7mWEFOc7l65d2pmmteEpz6lTodVT98Jic0olt7HXiaXCxc%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777454475** `期刊图表复现：多面板SHAP依赖图解析特征主效应与交互作用`
  - family: shap_composite,scatter_regression,density_scatter | grid: — | palette: — | images: 4 | code blocks: 4
  - tricks: pvalue_stars_overlay,dotted_zero_axhline,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElssmBP4KrxAELhuGWe59KH6HualBz1cJIE7icfS9JMjVgf4bKYzaXoyYCod8cul8Ql8GY06cPTibD4tWwnWBsJI0YMRId2l8JyibWo%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElstC6w7Xz1jXv4dRE0KS50sEh25PicNzzpEFnxjfDpUSbLG6wicXY0xvJ15166tXtmUp6w65hrOkhiaIx9lI5ygYQMzuRRSf55dn1s%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElst68bY17WnGFIZbtrngdeF0Gh6Vvyb0vXAvAqET1aic6RVrol6xARfDV9icgFDYMRtVaPKUMIpAibzkXZI8k9GoSNf6iaqVXEt4TvY%2F640%3Fwx_fmt%3Dpng
- **1777454431** `期刊图表：双Y轴直方图与累积频率曲线展示HPC数据集多变量分布特征`
  - family: scatter_regression,dual_axis,nmds_pca | grid: [3, 3] | palette: — | images: 4 | code blocks: 4
  - tricks: twin_axes_color_spines
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElstNkhKeB8h7f6lHNibFeRSKK9iakKuPEiaQIibicFjDaFm4uuZdYhc23iboMaWZqAicEl8YsmU0icv8eetgzLnISDOP4ISa64b9xZOFfyg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElstkibout5ibbBRwVJuNuWLicWgxees2u5p2puAiaxrBibDX4vFeHqRzvInEiaryD3x14nQFPJxUWAVzHU3TAR6icWP51Ue4oHGGf0mP70%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsvFQprWcQEzOGiaoibHBDX7zRjNZs9aFWPEelsTWr88EGOOTIxk4ZSDYicmpCAd3SmyLWppsHqibIdQJCW1Hn4b7IgiaSAfia4yfO4RE%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777450693** `期刊复现：Nature Comms 双Y轴组合图`
  - family: dual_axis | grid: — | palette: #E6553A | images: 4 | code blocks: 4
  - tricks: twin_axes_color_spines,dual_y_bar_line
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2FgCE6Jqa7zN7IomorcqUAql7LXw2qQ51sNRd8SsT46MNFmqmnLp2Vn0lhOfkqicqficQSDcE8qwiaQciaibicI3pBBSpg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2FgCE6Jqa7zN7IomorcqUAql7LXw2qQ51svjbYpRTpk6vUBFBcgr9bjHnOzoXx75G1aZ3v6IYUT7ILDoia4ib14JFA%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7IomorcqUAql7LXw2qQ51sG1M7UF6Vrtgnp0VTkY9wvlqXILCydLwTEs1D1icpla51ebOIvLfOoicg%2F640%3Fwx_fmt%3Dpng
- **1777455934** `期刊复现：双Y轴分组柱状与折线组合图评估多模型预测性能`
  - family: scatter_regression,dual_axis | grid: — | palette: #4B74B2,#F08A5D,#2CA02C | images: 4 | code blocks: 4
  - tricks: twin_axes_color_spines,dual_y_bar_line
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsscYeclKGFPicKes32fE5RjUjBiapu8Lm7xxDCyPGiaXKS4vAbxSHQw9wia6SQ0CFVO87mkqAeUREslfSnXXJkVqMW3kH3d32Zpqrw%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElssEt84jDS3n9icF9t9kj2j1awIqHiaeelaCjyqvBSrEsQklmhy7ZHEiaUIodPFIurUTSdVI9l0rGdJsiaK4wsibFlqlVRLVEbfgzalw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElsssiajIhl0Cg8nN4iaRthNJGCgEVbnZ5A6OrJllR4Q3fpXsf3oiabwo0Gbxiavan26JAwbYy2lQvC1IIJ2kVhzwdcRiawvQNE52h750%2F640%3Fwx_fmt%3Dpng
- **1777456015** `期刊复现：双面板组合图展示特征重要性权重与模型性能演变`
  - family: scatter_regression,dual_axis | grid: [2, 1] | palette: #D62728,#1F77B4 | images: 3 | code blocks: 4
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElsuW6hu7QyQVUNNpTWq7MbyMSBvu0MwkNBfQWqagfme1Y7icFOUwEQG2ibKeVlCXbZGsCxf3eicJo5gk5wYynwW0cwicYWiaMIiaakkFA%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsvuAOsVa2RqcgzbhhnZGEgXgEicjvyyibMfjViaDGMVChf5cnXEzZHXh42j99iaqDiasklenTa1xIPfu99pBcQI7uLDZ3lj0VrCh4o4%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElssKicJMyWd5d8d8GOQACEHPic0sbF4gibguBJ8gP3aAp4187zibLr43Jc2QpMujCQSAjf1BztMiaxymUfDSq4uQV8aMVgK9IdNnkLCo%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777455596** `期刊复现：基于多面板组合的SHAP依赖图解析特征对模型预测的非线性影响`
  - family: shap_composite,scatter_regression,ale_pdp | grid: [3, 2] | palette: — | images: 4 | code blocks: 4
  - tricks: marginal_axes_grid,dotted_zero_axhline,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElss4JCZuXL9WyW5qXNNSIyECd91iaTbExGjJLNlkZ2FzMKrFPib64xCF5X3dzKiciat7u3UGiaRor7mfpuXiahfLODKF6hVC2Yqebk6J0%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElstfyGic3Eibd8xQ9lLojicbicp4wgjuW1qBQibMyPGqZsnmR7tlibgPtODXu2ib4xmzQnYmB5IWSFBtc9DMwTvpsJLa3X8ialMfzleFuJM%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsu1KoNI5vt7BQ89POiaacNib5gmjMaJ3ESiaFUYI5KRzDicn2q7r3Lr4iahMFNysvPS9puU6dVUlwZicMQloBFib7G0prgpJHYEVX0R6o%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777455863** `期刊复现：多面板回归预测散点图对比不同模型真实与预测偏差`
  - family: forest,scatter_regression | grid: [2, 3] | palette: — | images: 4 | code blocks: 4
  - tricks: metric_text_box,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsukWr3caRKIRjKMfUcVVbuYxbVHL4386CppQhHDVs7cj2SqsibiaicbLa2pudR5M6uiaeywTPzfrPXeF93TS18I3dUGqUMW64lDO5A%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsuiaEsXwPQ03uI0Okeotibz2Msev6ibzhPPJx9VP6SHGb8X3hw3HV3t7USrlrDMJ1tflLQZCZS4FcN8T5E0fye4EWdAibGPku32gdk%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsv1Y1oTWkPjuPo74nq0Q0b2iauicqjibkn0QJxSdyMYu5U1u4TdKm6ygNibNdhGuVzUW6hejoeD6ICdxxQhm0aCLe86Wa0h5wTB4Jw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777455897** `期刊复现：多面板回归预测散点图对比不同模型真实与预测偏差`
  - family: scatter_regression,time_series_pi | grid: [2, 1] | palette: — | images: 7 | code blocks: 4
  - tricks: dotted_zero_axhline,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsvNnU3OF3E6grwzMfoTP6kP8IMCSicReFFzvr1M8rBvHL3bYgApZ8PV0L3HllicPLadP0S3zp5nYia36sLzPgZ7Giam8qmGPBd3Stk%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsvTlCAakCj68ibbG6Lmcao7OpjBSnZYOiaTqODBXtsUSUvLXcHzbMDzialYP0g2hT45YL1GIGibWSqnJzUcb5eTV6m0mFicczcwfibOQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElssiaukFbYMoaP6NFdXQk5fdgXel39eiaLibBY0ps6cibibTw1NicFTk1KdShnzXWr9YTQ8kS13iaCWqazOr970TzqbKPr79nHic8iaG7a84%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777455635** `期刊复现：多面板箱线图对比多模型不同评估指标的误差分布`
  - family: scatter_regression,box,ale_pdp | grid: [1, 3] | palette: #4A90E2,#F5A623 | images: 4 | code blocks: 4
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElstickTfPPw1nznkfp37Y6e0LQvn1cZxbJJPDUbDrdoiaEXs7QpoUYVfWOr4huCpYIadsFczcItIuyO5BPwWCsmr14BB7AFu0rgWk%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElssl9ColKplcUotcUAuCAN7UPZY9Ojt4utKc5SBEtbqS8Qzwoxcw2V90YYcqAk04Hk0AmLlbxEadvg4ibuaIiajzRTt8UPjq7kegE%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElssDwh3CRRnqfGFfvkxzds2VohVtbufVhGcySKl5UA4BWiaO130pNoYmmWN1h9zFD20KS35JkVH4TSooKDWj0hIe7lN82uo9c3rQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777454251** `期刊复现：通过多子图布局对比城市化梯度对气体排放量的非线性影响`
  - family: scatter_regression,box,ale_pdp | grid: [1, 2] | palette: #4C72B0,#DD8452 | images: 4 | code blocks: 4
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsuDa0fibHzejYOgXaHeujWs9cM3zEUibBcSq6w7VItYmricDkYjkosSicshpf1CdblRmNXfm1YI6MOpq28xicHaibfmvaHImw0wtKiaqI%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElssGXIav7nHMvxG3m96r3sicplicyU7qVXMa5A4ZibhsCkP5U7eURjJFagjS63FMR4dW6ZFYxI38ZNW3Kd1xBsyZNEibzEa5dIPBMfs%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElstwDsgpYarQJOyb8M55RktQwic9eMHZ6mBKnXm8f83w3R0FnWqkX5aIxL82tZbS1UMFFdiblTzicaSI3FGphZw94Xib1EP9KAXd1UY%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777454562** `期刊复现：通过多面板SHAP依赖图解析特征对转化率的主效应与交互作用`
  - family: shap_composite,scatter_regression,ale_pdp | grid: [2, 2] | palette: — | images: 4 | code blocks: 4
  - tricks: dotted_zero_axhline
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElssWNDKt9Vt0Ho1WoEWmaiarrry1jJMLq6ZEvpaNXp02iag1xoKO6JcDARQ6wl8ERY07Jw0ibOKq1NEDNqQfCHHPAe00EIHECXMuB4%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsu9QoiaV1YChkdb6cMusicGdiamu2MlcKCOvktHVn4P9WH3DtI2tsuLAbC0Cr2K5KoGvSo20PfonOC8KSnIU2Z1YXUHm1nicINwmZk%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsvOVxzHKialcLliaO2RODAkpdicSlRNiaQruicPe4ygb9sJNhyqgaAH10fwgdD4bGw3CxHzKo62z4PiaTTdW2VuRyoLn4xVsSQibv8H3w%2F640%3Fwx_fmt%3Dpng
- **1777451488** `期刊配图复现 `
  - family: dual_axis | grid: [2, 6] | palette: #D3D3D3,#E67E22,#27AE60 | images: 4 | code blocks: 4
  - tricks: twin_axes_color_spines,colored_marker_edge,dual_y_bar_line
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6BdprZvicy5Zhs1z5FibE9QTCLibWtJte10xXsXOKLl5okCvOThx77Kuoia1gnUYZhuO4fdibjs9CJyibw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6BdprZvicy5Zhs1z5FibE9QTmXemkMjx1SQIHgiaKaoZXRViabic7jDLFAmYkTSRMpoJuFXvrycuBibagg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6BdprZvicy5Zhs1z5FibE9QTrwOWSgXa1ycYBK74rJwWiaiaY7UUuUrS7l20cGzCyuIVeGKNZr0ibzLGw%2F640%3Fwx_fmt%3Dpng
- **1777452639** `期刊配图复现 `
  - family: heatmap | grid: — | palette: — | images: 4 | code blocks: 4
  - tricks: diverging_cell_label
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5QZuibegERLY5Y532sRm8cdKy9xcedrT9Tl87I9TiaUXCv66VFt0jeeoaA5vm6lyiaQmvqP3fzqE91g%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5QZuibegERLY5Y532sRm8cdK0NFI2HqF7FsWXk2oV7wZvyPPGckh4MD5VOrgDdVqTCSoDVJUTwLEQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5QZuibegERLY5Y532sRm8cddPXTyibXwH9RCmLwibAjcKzRa5UR8S9Wib4VVuEiaYFQrW6Qic0J9ZTWULg%2F640%3Fwx_fmt%3Dpng
- **1777452005** `期刊配图复现 `
  - family: shap_composite,ale_pdp | grid: [2, 6] | palette: — | images: 4 | code blocks: 5
  - tricks: density_color_scatter,twin_axes_color_spines,pvalue_stars_overlay,marginal_axes_grid,raincloud_combo,colored_marker_edge
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5u4fibrbYkU3feJibBjE72b6fuzEgZVBmFxBtDL81hldvRGPibo2PMJtVDnSO9E8d8p5yWdRSmcAEjw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5u4fibrbYkU3feJibBjE72b6rRXaBJpBawD5bTqgEhpK1UeWSszsNTusVmh34ct2Mmp8zX9DF3F62w%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5u4fibrbYkU3feJibBjE72b6t7bibLWpEWZeqGym2Z5OiapEgPrSJ2oNZ1BmicICZ3icyFZMUFBGYOyLibA%2F640%3Fwx_fmt%3Dpng
- **1777454521** `期刊配图：利用多面板2D-PDP揭示机器学习模型的双变量交互与控制边界`
  - family: forest,shap_composite,scatter_regression | grid: [2, 2] | palette: — | images: 4 | code blocks: 4
  - tricks: density_color_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElssDW9XHkH93edXRErd4bQn0QKKvuWlS8O2nsegicZiahGjSSuibxFeiabqxkdsNHuP5Ua57AXzQmwTmD7tAIvMYR6v2VF5oYkC8aSQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElstsvjKm9dqic5esWjPiasChAQxBDJnU2icEtvQeGFCkm8kqt1W92ZVQlLGEk0nicHlgMcd3ACpeGIctu0NC87Trkh1KF9J0bCGIvJU%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsskKcUY6S6UUIvaCN9AGavjgYAOzzdyCeofBzWP1A64NrBFEkkJ5Fdc7KsyPgtpfE04hpa6tLPFDIQtZs3uIaLoJibbiamViaeNok%2F640%3Fwx_fmt%3Dpng
- **1777455972** `期刊配图：基于NSGA-II的三维帕累托前沿散点图可视化多目标权衡解`
  - family: pareto | grid: — | palette: — | images: 4 | code blocks: 4
  - tricks: density_color_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsu2WicnexBtibHdFq1ga2Z6elKPN65lMq2ov9CbCZqYwm1jic3Q4ea5gxp9k5ia7ZASja7z9wRNr1iajKdRzqI632Il5Vqa2dFbLmYU%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElst2vIDWZtN9I6DL9MsKr4UJfrpzN5G7oMiadEL0yD7LAwBicArLmaaAnCvjQDxfBmdhfvecn0wY5dVwdzUGS00jJ2cEw4uAYkYPE%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsvUibxib65Pz3Xkks5CuUeCoROSbiaMbjf2IS27d49ZB69UlzxibnyenOwqhwficphyAhnOrQyiboj9AfgMTrWib2LFxKUdEsicJvBB7vA%2F640%3Fwx_fmt%3Dpng
- **1777454388** `期刊配图：基于极坐标系的多面板雷达图对比多维环境变量与模型表现`
  - family: radar | grid: — | palette: #1F77B4,#FF7F0E | images: 4 | code blocks: 4
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsuXGR3Coiau6acCbUuibp3weqP2E2JDd5xwiadQ2JQFITv5nVxQZ9vfyBm5oIy454BjOib7uqQ7qofXC32wOKeicfDhzHw5awwGeP3U%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElssMdO7BToslh4keIvtMto2MwtGTQ3FgiakkXvzWk6PyCp3WgcyamVCLIml3tkpzlWNFOfbiaiaOia4ia29J2PjsfcIkEV329icka0OFk%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElstdJTCh4icUXop6ab9Xf0FQdicApkzb92bk5ADjCicpSKhpqhxOR8e7XPufGic3Fsn8s6FcJukRibjPZZLvlP43afTMVuKtXEzbIPS8%2F640%3Fwx_fmt%3Dpng
- **1777453942** `期刊配图：基于组合多面板条形图对比多条件下的机器学习特征重要性`
  - family: scatter_regression | grid: [2, 2] | palette: #FFB74D,#2B0E68,#D26E17,#466B6C | images: 4 | code blocks: 4
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsufalBXkPeXibzt6pyV9VY0stl3jSRRIzicNAE1RnOqhLOxyXiahwojAibib0K764FqTeGvD5oOE4M39JtT6kjv1DPeLognI3gevq6M%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElssoOuCDG5m6yPiayAxS7SGExiaxlt0zWUiawNRD1X19iadwYQUDq9e22xzphhOzJbibjRmAcoM7broqIAfMCaGA8crP7DEJQeFR4PvU%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElsvIyyS25pjpGOVh9Sm27kzkpHbNnK8Y3jNErCvQJ4iaCWAYrEONymXN4mYxB7YXhTiaJyOicBNKQJjcwiahjEB5gUiayIyJS5F4GB6M%2F640%3Fwx_fmt%3Dpng
- **1777456052** `期刊配图：多面板预测散点与SHAP局部依赖特征解释组合图`
  - family: forest,shap_composite,scatter_regression | grid: [2, 2] | palette: — | images: 4 | code blocks: 4
  - tricks: perfect_fit_diagonal,metric_text_box,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElstxF3CY91CCIHXFBrUGf1aRr8v8ZgDZmZxeHAnZWic95U1Ecbc2KBBY2OweIIuJAZhvsScx1AJBmlWYglmWmJx8Pryh1TQAicVjE%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElssMnEDVqatI4qfv7hpjBuBy6OmsFSysf7XexVkSibqKAK7F05LAlcmHO3jNKjJMic26jgN1BC4b3RhNUj864Hwo0RBBrmZb2gmIc%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsve27b9ic2qL27Mgd7Y2BOEQFzMxvEuzS1slApQsFkvIheRedZEF1lKia97X7fnHJpSFdyhZdhcHgw12UP8EZGZ2FkDjlpkgribics%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777458801** `机器学习：集PSO多目标优化与SHAP的回归预测模型`
  - family: radar,forest,shap_composite | grid: — | palette: — | images: 4 | code blocks: 3
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsurX6eYtHOgJZBdmZkeeVlDVUQYMjzTxf0W3sbIcJ5pjbvaxUTIkYgCq48waXTqfTnBO1picMibX5dryq4dKmm5nC5XFzy7EN5K4%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElstuHuc67iaIyyTnW7vCIdFA35ibkCEBCEBibOxEy4Id9aHURQ1DjT9U2uibA2PKIVbUIkekj2ibicBiallgUE9lLQMTxmeYw4YlxuI4yg%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsu8TCDL5fAvQmaicbNrpSGpnFFXY6zDpntOiaCLXLgfZQvvF6tktEiarfgP72RliaOtbdoicRtvX8wLrNqXWZsU8iaU1t0apLBIjSiatU%2F640%3Fwx_fmt%3Dpng
- **1778681176** `期刊配图复现：基于二维核密度与相关热力图的多变量联合分布矩阵（附代码）`
  - family: heatmap_pairwise,heatmap,scatter_regression | grid: — | palette: — | images: 13 | code blocks: 4
  - tricks: metric_text_box,upper_triangle_split
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_gif%2FW3juZXNhicnpPWUqaQaH0TjDicsP8iaKoAFCb5Z0A5bTU7dDuGCtY9A7MINoyvpOFHjibVj6G6VoibAFL99uqJvfxkA%2F640%3Fwx_fmt%3Dgif&n=-1; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElssZ2nQueUKic7h4DVtXNLcQyuwv4kUCGAkribrf55hbOqU3AeYqibiboiamt597eLBeRfibCiaebbibugNuZZ1bT1flicfic5M8k5JGnMBCI%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_gif%2FW3juZXNhicnpPWUqaQaH0TjDicsP8iaKoAFCb5Z0A5bTU7dDuGCtY9A7MINoyvpOFHjibVj6G6VoibAFL99uqJvfxkA%2F640%3Fwx_fmt%3Dgif&n=-1

### Narrative arc: `marginal_joint` (5 cases)

- **1777453032** `Python绘图实战：基于GridSpec构建多面板回归预测与边缘分布组合图`
  - family: scatter_regression,marginal_joint | grid: — | palette: #D62728,#1F77B4 | images: 2 | code blocks: 3
  - tricks: metric_text_box
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4icEcSFZPKP4mJibRmEb6ceWfaicfD9E5a82RHIhZlGADmm8EO8rqMJfbFxQU3psQXl6BVvIn0Qt8kw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4icEcSFZPKP4mJibRmEb6ceWibrCvJnbZCPDrnWObficu1zzxOE95cq2nmTicRA0oo3O8XhQ0aEeeyJGA%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777452838** `复现 CEJ 顶刊神图 `
  - family: scatter_regression,marginal_joint,density_scatter | grid: — | palette: #69B3A2 | images: 5 | code blocks: 4
  - tricks: density_color_scatter,metric_text_box
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7FY2MhRPiaht8ypt4R0pZic8bT6KG4b1OYj7c8CSia5YAvFXhNicMBZpIHXibgt8j8NB2RN946Kmj8vdQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7FY2MhRPiaht8ypt4R0pZic8LBQazOmmCQpLtXfQicQ9icp9oFhibyER7I5ICflM1WQRm0hWlibokx6tzg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7FY2MhRPiaht8ypt4R0pZic8LEib8GaG1RjLrtAqJP3yqVo46JeKc97Yjr0bxHQIibBBXv5u2tPDj9CA%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777454914** `期刊复现：联合等高线热图与边缘分布图验证模型预测精度与参数寻优`
  - family: heatmap,scatter_regression,dual_axis | grid: [4, 8] | palette: — | images: 4 | code blocks: 4
  - tricks: density_color_scatter,metric_text_box
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElsvib5QtWwzLhXct94LiaOtZPkteejEB2pEaRwcZlVoHPSBHvAnMMic51l5CXIDQsKjiaSOAbqdqicUx3ICsyl5JGC07Cw4Awfngzfto%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsvo6tQYvCup4GoDjNWbIUnhVvHlMs8ZMRf4Ju94U4JiaDibE0PEqMfZUYN0Z4rKbH3nRIxRPJT1CMuLQUgmhW1l6v1sRU6p9AwOw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElsuIEjmtyWvT1ojRXqvH0RuViaWkgl99ibgU0cTJQmG401D3QngWhCLVuA9G7xYAXq6icT5vBsibk2Er3bQrM68dIOs7I4AOlLtX4f4%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777454731** `期刊复现：通过带边缘密度的联合残差图全面评估预测模型性能`
  - family: scatter_regression,marginal_joint | grid: [3, 2] | palette: #1F77B4,#FF7F0E | images: 4 | code blocks: 4
  - tricks: perfect_fit_diagonal,metric_text_box,dotted_zero_axhline,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsudziaZpqCmMM5f0TbFLHJA5Lvic1bL6Qj9PHh0WApjzAhhAUokt0A3axWXgibzYnfibCU0nR6vOYu84EkSw698kRhjlHmNZdY6458%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElssuFflgw0ZWtxeialrkwrlaASIcpoLA2eqib6XZeukR4lPIwtAIia639ZtGaIpPTvl3C4Lr7OSic6joxP0Ut7SjIrAOeibyRytOpJtw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElsvCQUCO68pwRXD7nDvrxyEkfyWP9AuGFoIkNG8XnhOgFKNjShoaWHze60CzibsP2ymJYpw9Orz6ZRooUVxT8gBJl9aQB9dy46Jw%2F640%3Fwx_fmt%3Dpng
- **1778682541** `【Python绘图！用Matplotlib+Statsmodels打造带边缘直方图的炫酷散点回归分析`
  - family: shap_composite,scatter_regression,marginal_joint | grid: — | palette: #0000FF,#FF0000,#FF8C00 | images: 0 | code blocks: 11
  - tricks: metric_text_box,error_band_fill_between

### Narrative arc: `composite_two_lane` (5 cases)

- **1777452577** `复现顶刊 `
  - family: shap_composite,dual_axis,treemap_pie | grid: [1, 4] | palette: — | images: 5 | code blocks: 4
  - tricks: density_color_scatter,axes_inset_overlay,pvalue_stars_overlay,raincloud_combo,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7FT2rKcXKwRSbg8KVoJMCRT3TW7HHuia45gdg8YfDKk5dTv4eJKFKzHB7ticibypgTBzDI4Z2wbqs2g%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5FT2rKcXKwRSbg8KVoJMCRPsN7hfNNyNqs0LhCibiaqRDV3647LebCDSGUx9DL2j9Ju3be1N8UbmHQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5FT2rKcXKwRSbg8KVoJMCRHlNtb2l36LPbx8YINsmcn1bzBrR3KbT9Y5XL7waWRR9POTuQnYOm9w%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777454599** `期刊复刻：多面板结合XGBoost特征重要性棒棒糖图与SHAP蜂群图`
  - family: shap_composite,scatter_regression,dual_axis | grid: [1, 2] | palette: — | images: 4 | code blocks: 4
  - tricks: group_divider_axvline
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2FeW0nHXaElsvdiaGiaRCiaKicLTFvYURialqG7DVRYiceU2y0bDOUjnaEibP0aTpYNOvypZBfcqqLIB6AUBSmLuERuq5Fg7nmqqmHG5omv9XgX0fYrY%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElstdRAPskfiac4ShHemx5nwGsAn3HNZia6I3IaMAmS9zwpibofXN7gibFX4XwU0hcL2OjWSg7MFbia5PzAqddUKQEBjspibRR816KWv38%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsuGd56hZV2dB59JzlSqWGaBv3OqsexZCHBYVWIsbQ7hK3gx7HBAshyIqVD6aDKWJPwCrQhLtYUqzr40miaicsibWic2QD0aibeFkTPI%2F640%3Fwx_fmt%3Dpng
- **1777456510** `期刊复现：随机森林(RF)模型驱动的EFI特征重要度条形图与SHAP圆环图可视化`
  - family: forest,shap_composite,scatter_regression | grid: — | palette: #D6EAF8,#5A9BBF | images: 3 | code blocks: 4
  - tricks: imshow_gradient_box,pvalue_stars_overlay,colored_marker_edge
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElstlyIOgqf2vNL9LpzaSAEm8CTQ2icYzjblzhOaibRhoaT6lZq2R5rib8VLt5adBPronAxXNMjGH9giaQibzfvJxd1UUUxZJQQBkMXLs%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElstpPXZQCxQg4OGXXrogFcUuM5GicE4urRX1At6W4QCsEfIaEpCOsicALCuM0PPHibx2t3VgXQQA4iaWictcGgm7ReQHUQBnGficqUp50%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsubMryzbXn4d7sSXSIAIQWIfK5Fz0Hb0gibHnLhFhHXobIicVIqkknmOnW992wrMmo39L65CTKo5Q657O5CBukMQx1f4uODhW8CU%2F640%3Fwx_fmt%3Dpng
- **1777456159** `期刊配图：基于GS-XGBoost与SHAP特征重要性的条形图与蜂群图组合可视化`
  - family: shap_composite,scatter_regression,dual_axis | grid: — | palette: #4A90E2,#E94B3C | images: 2 | code blocks: 4
  - tricks: axes_inset_overlay,pvalue_stars_overlay,raincloud_combo,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsvKxsv5DbRejLAGiboiauoyR4UGoOlhN6JwLYhHAanCChqat0Qicia6nwOVUPkghABjtYNDtwrvHOmVfsPsl5Kvxrrrj1f0Wzibb9WY%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsuRkxqS5bKleMQcSmXhSDiagruqo2iaVcphZrtpuMPEvrtn4rT8PL5KRfXPpysoId3uoCHFMKpqQr7qLtPSfagic1dAGDr5bJUGFA%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1778680326** `期刊配图：基于极坐标条形图与华夫饼图拆解机器学习特征重要性（附完整代码）`
  - family: radar,forest,shap_composite | grid: [2, 2] | palette: — | images: 17 | code blocks: 4
  - tricks: polygon_polar_grid,pvalue_stars_overlay,colored_marker_edge
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_gif%2FW3juZXNhicnpPWUqaQaH0TjDicsP8iaKoAFCb5Z0A5bTU7dDuGCtY9A7MINoyvpOFHjibVj6G6VoibAFL99uqJvfxkA%2F640%3Fwx_fmt%3Dgif&n=-1; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElstbGczOTU8PgIkGwibqKlibic1KXvQXf8bFsrZLgpFUtzOzN73bNFicNz2e9nYW4JhG4rGicKiat5A827s6sulRLwwPgiasY3aG26xPS4%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_gif%2FW3juZXNhicnpPWUqaQaH0TjDicsP8iaKoAFCb5Z0A5bTU7dDuGCtY9A7MINoyvpOFHjibVj6G6VoibAFL99uqJvfxkA%2F640%3Fwx_fmt%3Dgif&n=-1

### Narrative arc: `global_local` (5 cases)

- **1777454644** `期刊图表复现：组合SHAP摘要图与饼图解析分子特征对自由基反应预测的全局影响`
  - family: shap_composite,scatter_regression,treemap_pie | grid: [2, 3] | palette: #4C72B0 | images: 4 | code blocks: 4
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsuxhTdsQG22ePCw0ibciaVLVhZgg2NGkLeljexI9MveUU4S5HOZfS5iahz4wCuicAZ8fIibTVlWuDmiaG9LwNdgL8hM0Lt5hoUJdWGHw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsu0z2w9aNraTJibjMesGNHrPGTwKX3OIID4yh50XPO4TEwoic8b0kmX5nte1Z5uJ6qqgo8kQJUJmtuCDZCDaTtrzBpFBB4jicialfs%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElssuoogImg5aEmRGHd8ktf4Ln9m7Hpc172p49GAsia39f80FibzHCCMnuDsZAmhPNHBQbk7euTmPBgQsPG1XTGbwGCoia6O33r8EsI%2F640%3Fwx_fmt%3Dpng
- **1777454774** `期刊复现：基于SHAP复合图揭示高能分子特征对性能的全局与局部影响`
  - family: shap_composite,scatter_regression | grid: [2, 2] | palette: #4B74B2 | images: 3 | code blocks: 4
  - tricks: axes_inset_overlay,group_divider_axvline,raincloud_combo
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsvfUv0wSIdoPjshK5rZiaqWw6Oib66yicrVvVpSAtG8E7kSIsN7jicXN5WlYh9wF7T7U7Z7f6Z7f6Z7f6%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsumG5H3fXn5ib9pU0nNiaM7kYicPiaGiaQicPiaGiaQicPiaGiaQicPiaGiaQicPiaGiaQicPiaGiaQicPiaGiaQ%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsuvP6QWib9pU0nNiaM7kYicPiaGiaQicPiaGiaQicPiaGiaQicPiaGiaQicPiaGiaQicPiaGiaQicPiaGiaQ%2F640%3Fwx_fmt%3Dpng
- **1777454297** `期刊复现：子图平铺展示比表面积与孔容的全局SHAP值与关键特征排行`
  - family: shap_composite,scatter_regression | grid: [1, 3] | palette: — | images: 4 | code blocks: 4
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElstbvXhZwjdbv3PpqQRkczzn7iavqyfnhV5aE3YZB8p450BXtWpnbRMgaaP11YFdeZulXVm2WzDhffX9q8Xf8MiadNgIGjuEibqRnc%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsu3MfMysbBAkb6tqOooQ3hHFACxVEJF4XeXciagYdVydic6qfkVLW7CKiahhtw9FtXg73UYR4iaoGF6NzQw7APEVaRpznL7lHPnzn0%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsv1KxZnb04icZ2ToWq3BGzZojUPK5gTxRx9TS9LvHPEicPOyjqkZMibkiaa2st3SahtZPPw7wHicdyg82PeptSWMsc0a8F1gichLfWM8%2F640%3Fwx_fmt%3Dpng
- **1777454956** `期刊复现：组合重要性条形图与SHAP蜂群图解析特征的全局预测贡献`
  - family: shap_composite,scatter_regression,dual_axis | grid: [1, 2] | palette: — | images: 4 | code blocks: 4
  - tricks: pvalue_stars_overlay,marginal_axes_grid
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsvHvTVdiahxblBBPvPN1ueI7micOM8dbSXJNDqRsuDqXzhQL2oXZa6QrQEVvfenxdiaGrNpj1u1Qq2BtmljEJIqwQtRNSIYbDicFjc%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElstd4gWDjyWHOiaEqkrYNOKtOS7nCn0fsdEerSyEZG3oSmQIwqnkE76Pyvb0GUzFjibCdj0zQNicQK23kGibXmHszkCxRZIshV9a0ck%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fsz_mmbiz_png%2FeW0nHXaElssHiaejV2FpvFobiaYDVnRbD6iaQ5mMqMwkUbXXibznZMerRiaicIY2SPS3zXicENDrnia2O9tqVP1ydtVvuzEswJibQbsHU6MiaPsba5PLQ%2F640%3Fwx_fmt%3Dpng
- **1777452973** `期刊配图复现 `
  - family: shap_composite,scatter_regression,dual_axis | grid: [1, 3] | palette: #1F77B4 | images: 2 | code blocks: 5
  - tricks: group_divider_axvline,raincloud_combo,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7F97nib4iaYdX9DiaibeoAOM1pSk7CABF1IVXEjzQqKL3YkibKFcicXEr0MTic1ZO9QfOf0sRScYCklZUow%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7F97nib4iaYdX9DiaibeoAOM1ptkpybwn0c9IDEIsaqf0ZBw78crrIV76YvomRibRa5iclzeIvZeNwIibSQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg

### Narrative arc: `hero` (5 cases)

- **1777450933** `期刊复现：Advanced Science “驼峰”阈值回归图解剖与复刻（附Python源码）`
  - family: shap_composite,scatter_regression | grid: — | palette: #D9D9D9,#404040,#E87A6E,#E63946 | images: 4 | code blocks: 5
  - tricks: group_divider_axvline,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN61sPSjaH7SIiasF2ZWsq3noqhqKpeibTL06Avj8ubiba8ZPd1bxydmCS9rNBCgBK6NRBUG1Ow1mBxVQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN61sPSjaH7SIiasF2ZWsq3nogp3FN6rPGJC2vv6EOichiaL2Y03vnfJm2vo8xzZyibeNc2PNwklFI566A%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN61sPSjaH7SIiasF2ZWsq3nonCfNwicSWTcnvEmdaYkuaFxia3uvQeCDAR9SSYKFSdicbwicQNwibGekRqQ%2F640%3Fwx_fmt%3Dpng
- **1777451123** `期刊复现：Advanced Science 贝叶斯山脊图 + 热图组合策略（附代码）`
  - family: heatmap_pairwise,heatmap,ridgeline | grid: [1, 5] | palette: — | images: 4 | code blocks: 5
  - tricks: imshow_gradient_box,axes_inset_overlay,group_divider_axvline,error_band_fill_between,ridgeline_offset_kde
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5RIuHPICZricfy9UZm2WxlsU4ibw9Mt67JAUKdYB8CDEPwCHfSOV3XPE51H9g8kaIPXlmia8NN72E6w%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5RIuHPICZricfy9UZm2Wxls2LlVYLmrHfV6vnqoEoyOT3OSZYucjQ2P82M2I1jCFDLahxHfXPX9vg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5RIuHPICZricfy9UZm2WxlsViavLFveomhsnlzu8DBZcug2WtVZkZF0TCyKgovpvibLp8raibbkauoKQ%2F640%3Fwx_fmt%3Dpng
- **1777449664** `绝美！Nature 这张雷达图，被我用 Python 像素级扒下来了！`
  - family: radar,ale_pdp | grid: — | palette: — | images: 4 | code blocks: 5
  - tricks: polygon_polar_grid,polar_value_marker
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN427IoKcpImx1rPn7MPJuuDLXF1dVNEiaImsKbpSYViakYpgvb0Yj8YybFMglZM5NQTbCZWmxF9icokA%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN427IoKcpImx1rPn7MPJuuD2iaF76SzIds8FtDZOtyBBHnBg25UpUcPoH5grPBXegIvbytKcXyW11g%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN427IoKcpImx1rPn7MPJuuDmJnhr7u27yHkzibccbA74zFQNiaUvMc0VicdE3a5N9VugqeKEAg1eq9lg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777452180** `顶刊同款！Python绘制堆叠小提琴图`
  - family: scatter_regression,violin,box | grid: [3, 1] | palette: #F79698,#6CA6F0,#98E6B6,#FBC285 | images: 5 | code blocks: 5
  - tricks: colored_marker_edge
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2FgCE6Jqa7zN40iaVHRLrTsJ7biciciaWGP8UHwsPHZHyvJua8BNNUEhZh9OXsS3JUtH1D0YIhcibK5SQhvEniaYr6Up0A%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN40iaVHRLrTsJ7biciciaWGP8UHibiaEy2jf45PrXialKZtSVWOdkw0ZPK2aAWbHHEicZ0eW5hh12I4pW6S1w%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN40iaVHRLrTsJ7biciciaWGP8UHiaqBDBCHI1DZMsyYkicDIryzHs3Q3JZcBQ1hJVpqsPIkCuFSmCTIGz1A%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1778682717** `Python：一键生成专业级雷达图！`
  - family: radar,forest,ale_pdp | grid: — | palette: — | images: 0 | code blocks: 10
  - tricks: —

### Narrative arc: `n×n_pairwise` (5 cases)

- **1777451326** `期刊复现：Nature同款皮尔逊热力图`
  - family: heatmap_pairwise,heatmap | grid: — | palette: — | images: 4 | code blocks: 4
  - tricks: density_color_scatter,upper_triangle_split
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN78c88ZlDviaIItiaWyewAMlG0HFZlmxSY7aTYko8YaLbYic6XmPialnNHsLp7xYqMYxpa6LbZuVwkrTg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN78c88ZlDviaIItiaWyewAMlGQOWDqqiayln5CgTmX0j2Ws6VrzxXuaccibPTaFmgg27lx7UPoUgycQicw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN78c88ZlDviaIItiaWyewAMlGhApHv9bzD5rbUTtiaVYST64g9ZFqconzkt5IeKxfAOD0X4LVtyic96og%2F640%3Fwx_fmt%3Dpng
- **1777454813** `期刊复现：多变量散点图矩阵解析特征与比冲的相关性`
  - family: — | grid: [2, 3] | palette: #1F77B4 | images: 4 | code blocks: 4
  - tricks: colored_marker_edge,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsuIib4eib9pa4LZdc5stulrs2gHw1jMfNxfgNicPvMoNUA2WTgn0RUTsXoDDYuyCibmib9lbhSicEvbqO8AYa7uZUgwibB1vFM09GCJO8%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsu48zwQpHzIQPV2zJX9d5DxyGRpNarB3hJjS7fEntA7zCib7yXqD89HjHnJJ5qjqrMymiaP8r2W0mXf7VeX6RvTLKfthTJr747aI%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsuwiaIGuksRJViazQhCEMgPWCialyibpOzEXsictpWWEp7JCpCs9yuv2VsDmIoDw3ic5ZSNe7gHCzeS3CpVUIdeib3lxgpSZ8FHy1210k%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777452095** `期刊配图复现：如何用Python绘制多模型评估密度散点图矩阵`
  - family: scatter_regression,density_scatter | grid: [3, 6] | palette: #D62728,#1F77B4 | images: 4 | code blocks: 5
  - tricks: density_color_scatter,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4816daHqPll4Ps9icfJC1w2Aibibmm3d51HJxRN6Yw7p7TQcV6XQRJCc1Blicia0kzlOGZmwDLvricjtUQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2FgCE6Jqa7zN4816daHqPll4Ps9icfJC1w2wfoGRM5zSBP4HTypzlCoiarWn28KsY1EvdDzF7qa49gr65LIMNIBkrw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4816daHqPll4Ps9icfJC1w287rrxIftxWJnfRSCj1JnVlxFdFnFZ4AGIymwzPD3jWuhIJLRNtBibhQ%2F640%3Fwx_fmt%3Dpng
- **1777456565** `期刊配图：基于机器学习的Spearman相关性热力图与模型预测效果组合分析`
  - family: forest,shap_composite,heatmap_pairwise | grid: — | palette: — | images: 2 | code blocks: 4
  - tricks: axes_inset_overlay,pvalue_stars_overlay
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElss1fNaSRuZb7wX29ib2MnSBia8K3SmVhWovcMAgnv0Nsia1oQvbHzDoqqb5wJwl2TOJOrQMTeicBZWVPafHzN5lc7tJicfrq308MmA8%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsvbhGPN1jYxSWzvicPolU19ibxBFnenDBBxNoeCXMbOvtmZHmiajicrrbO4bZvJbfZUDhPDKhBmwojEW2RVBJ12aQNuDpBPUf6vDicY%2F640%3Fwx_fmt%3Dpng
- **1777453582** `期刊配图：基于高斯核密度的3x3多面板散点图评估混合水文模型模拟性能`
  - family: scatter_regression,density_scatter | grid: [3, 3] | palette: #D62728 | images: 3 | code blocks: 4
  - tricks: density_color_scatter,marginal_axes_grid
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsvKU3z0Yyca8wxdosBum7icJ3jA2alYtkTCRBXmUx0MJPEico4zretnPWsRuCObM1ic87TGapZ3Tp17I20JicibSFjIhrZ6icYy1gK7Q%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsuDxRBsv4dCHyd1Fh81DRpLxW3hlibcmeY1aLbIdDWTthzgtgx0HmtcuKV98zTMjZASnZ3QndUGYictpy0eEtJz2vV3EmnZic0Gl0%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsvKU3z0Yyca8wxdosBum7icJ3jA2alYtkTCRBXmUx0MJPEico4zretnPWsRuCObM1ic87TGapZ3Tp17I20JicibSFjIhrZ6icYy1gK7Q%2F640%3Fwx_fmt%3Dpng

### Narrative arc: `train_test_diagnostic` (4 cases)

- **1777452515** `复现 Nature `
  - family: shap_composite,scatter_regression,dual_axis | grid: [1, 2] | palette: #B0B0B0,#5FA896,#FBC15E | images: 5 | code blocks: 5
  - tricks: error_band_fill_between,alpha_layered_scatter,regression_band_fillbtw
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5nly0lmKMuwujJaKvlib74G8XYgObzM2x3xGE1fl2pHk0qt2Kiaeq9eOXL9BKH9nr1Ou5eqXmdSbpA%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5nly0lmKMuwujJaKvlib74GczQ9bkDtua1B8t6TbwOOJTtDb2UI0nzONibUNdSPLAMgevBfRgEPo4g%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN5nly0lmKMuwujJaKvlib74GUNJM3WibuqE69ibo5Z6MvAnJsLAgfkBwfPMIDjBTFknsqdpGCder8Q1w%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777454854** `期刊图表复现：基于预测区间与训练`
  - family: scatter_regression,time_series_pi | grid: — | palette: — | images: 2 | code blocks: 4
  - tricks: group_divider_axvline,error_band_fill_between,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsvLtETvxTGj1Oyar7L8132KomMD7rEU71NvhSic8x5MZsH0en0f5v0b0TCeGbjUsQrKeTNcKj07vhWnM73AoOWGsCgQX5Dct0gI%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsunE23icAZpHtg7ibzd7BhhodVQ4ITlrUuJYSxxjyBYnXBUZ4le3ibibicLiaZFC2IbFkoUTA2Md1IVsbHKEIicNo7s2DNMkPaluBVWGw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777456338** `期刊复现：基于梯度提升树(GBDT)的多面板预测误差评估图`
  - family: scatter_regression,dual_axis,box | grid: — | palette: #0072B2 | images: 3 | code blocks: 2
  - tricks: raincloud_combo
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElssM3ia22Z9ibRbI8nGeCyggOaYAD5kAGQqdpAoxn8IbNZCKqlZ6ElGl4GuJyE8CozKgRY17CCj9ztdOCIfXh2vN7pEPbLrOP7UwY%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElssuXUycib7dHib3kL8xgBIKkTMPEoLXjTeSDImIvZTBg6SFr2BrlnVn3zXPicDj7YoRfvU8QCGVVU1R3hic1bJ1yicZibB8X932Z2cn4%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsuzUm610ZAhusNNyhge5mGiaygibiaBZZrMCaeTKSWnDHibZBaea6Z05FQzva2IMIAWcibrLcjCuibWv0RAWrf3bN1myDgo52MRaHme4%2F640%3Fwx_fmt%3Dpng
- **1777456409** `期刊复现：基于随机森林(RF)的多维模型性能评估与预测残差可视化图谱`
  - family: forest,scatter_regression | grid: — | palette: #9BCBEB,#F6CFA3,#9BD28C,#FA9875 | images: 3 | code blocks: 2
  - tricks: dotted_zero_axhline
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElsvXYVQnpKRbp0bdd2rM8dSlnKVFwPdMWvPvNNy2nduc2cxichU2j6oh4tBTibH5UyFMzyrdtiaUmtN9M7iaSlrHbTuPlibV1YOicHzDo%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsuJibTXMCaj3DM9MWBo2BIWHGG0icIXsH5BG1yB4cZgXxef6q0dJ1kNfHIicc7GfscuGgbT4UbnApLMY5z5WqfdoSrDXwR4qGXR8o%2F640%3Fwx_fmt%3Dpng; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElstvKQt3lvZ2gAjvXlaCQQHDicrTruRk629Aryv7dKlIOQ9XAj1m97bQJDGFpTuBwfRrURRDD8uuvb3czMcOiaXIC5anjsCOmj518%2F640%3Fwx_fmt%3Dpng

### Narrative arc: `mirror_compare` (4 cases)

- **1777455283** `期刊复刻：通过双侧棒棒糖图解析特征重要性与ALE主效应方向`
  - family: dual_axis,lollipop,ale_pdp | grid: [1, 2] | palette: #4A6B8A,#C0504D,#4F81BD | images: 4 | code blocks: 4
  - tricks: group_divider_axvline
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsu59WV8iay6yh0KEjr3E8AGrThBvDHGNuSSdBsU9FwoN73fdYqFNnLGaO4hvNUe5t11bs7fNT1W5qUUSrbicd2fZuKLFg8HVrYAY%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsvxNuragJMyMYErcotEibc25On03FsAbnSTNIwRibLWiauH9czb1iaKVOLEWyib3vrjeZtq6qhudb8GVqRBrmUXrtOB0L6lTB0XibNUc%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsude8xjfF0mRP0YDkZupUCznFyVp0kSrtib7dmtVs4ktIDyWsqQBecgvUDBlAboUuiajTdMqNPu0iawhxkOok3DFtnrfJCBRgr9eA%2F640%3Fwx_fmt%3Dpng
- **1777452890** `期刊复现 `
  - family: radar,shap_composite,mirror_radial | grid: — | palette: #33CCFF,#FFFF99 | images: 4 | code blocks: 4
  - tricks: marginal_axes_grid
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7lib56iboibaEW9FPytz2G1PDr1QwGydyRQA3k6ldP4QXUfWyh0fKymmdCzXMEQw8ELbjWSC94t1ia0w%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7lib56iboibaEW9FPytz2G1PDUWRQBuQxPzvXiaDaqcSumJ9wk1nf6ywBX3icwRwqjdnDjOENFzSp7UhQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN7lib56iboibaEW9FPytz2G1PDdjFfwN4icNfMjj1ib6zelztPD8fM0uwBgdEw3n3lEBPQNv7JWSs7ppSA%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777455707** `期刊复现：基于上三角局部填充饼图的相关性矩阵解析合金成分与性能关系`
  - family: heatmap_pairwise,treemap_pie | grid: — | palette: — | images: 4 | code blocks: 4
  - tricks: —
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsuCn4FiaCH1K9bWOgvMhibonicD6W2tXHyA9VnlCMXOM8JTeuF93BZVOvdFbxVGXOpTxwuibGo6qkgG5N8q2jupj0tNB1dRIXvl5q8%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FeW0nHXaElstdWyl0NOx27suFbtSJwlxlkPKyUSJwKxibtmv4G8kWPUVz1ymNdzWrc8enXFp1db2rACUOg9ZIcDOdDJdlAM3XvPxsHnLk9zm8%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fsz_mmbiz_png%2FeW0nHXaElsvn8CyS8P038UOEsKNysvvOEL4oCn9lvPRqHhFevqaNb01yWuqopiciaptibr326ia5WoMosHIiarXRUuQf4YicsXQHqdQSx013RrKBI%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777452320** `进阶绘图：解决“多变量拥挤”痛点——Python 绘制带显著性星号与斜向色条的三角热图`
  - family: heatmap_pairwise,heatmap,scatter_regression | grid: — | palette: #A50026,#F46D43,#FFFFBF,#74ADD1 | images: 5 | code blocks: 5
  - tricks: upper_triangle_split
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN72h3licEkmZuMWRDxf5BpEnGfj4CfO22dDqaFA2lEqJIYzD5Hr2mPfWicbY3CodrQT8cjAHUdG6Spw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN72h3licEkmZuMWRDxf5BpEnsnTJDMwYWu5og9o2B799TxryEHA7ZyTDOV1CV38wjD5gqcPfAc5Irg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN72h3licEkmZuMWRDxf5BpEnDHoicZqu3vOOUVI4xbVaxvPMJjCFPSEmgWibb6iahkaXL1RZia4MaAzNHw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg

### Narrative arc: `inset_overlay` (3 cases)

- **1777452243** `复现顶刊 `
  - family: scatter_regression,raincloud,box | grid: — | palette: #FFA500,#008000 | images: 4 | code blocks: 4
  - tricks: density_color_scatter,axes_inset_overlay,raincloud_combo
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4RPvxUcN31TdzRnX131siafZjxwHRQEuqxrZ42fibCBmLmZkPxWfmB0YBdW5Xh3guXiaalNPMYTeC7g%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4RPvxUcN31TdzRnX131siafjxhEyh6hmDNYy8BC56MJOsAxZtSq3ORco1p3cr2VVFMsNvvIgaCDAQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4RPvxUcN31TdzRnX131siafD2faIu8702b7Wg51Kdez3cia0wUdY8PkC1QcgbLwPVVaRo9OuJuFkYg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
- **1777450514** `期刊复现：Nature Nanotechnology 经典“画中画”组合图（附 Python 完整代`
  - family: heatmap,scatter_regression | grid: — | palette: #ED9F78 | images: 4 | code blocks: 4
  - tricks: imshow_gradient_box,axes_inset_overlay,raincloud_combo,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN58ShOWAQO5Dwf9xeFHWfrfibWnxWibbXGEFcN4UiazIkhrHxJ9HGtCZoyRtfpWzicY0cosaANVnvXTibQ%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN58ShOWAQO5Dwf9xeFHWfrfEd8ykrUW3pHK9jeBh5gNdgkBSWpwDXRHPPWOJETM0ajep7uaNTfPMg%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN58ShOWAQO5Dwf9xeFHWfrfmpt1I2iboL3GrjhSEjpZfiaicOxNMjicjIP6ruiaiaqiaVCWcIKkic5JarOcew%2F640%3Fwx_fmt%3Dpng
- **1777451060** `顶刊复刻 `
  - family: radar,scatter_regression | grid: — | palette: — | images: 3 | code blocks: 3
  - tricks: polygon_polar_grid,colored_marker_edge,alpha_layered_scatter
  - image refs: https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN4816daHqPll4Ps9icfJC1w2wfoGRM5zSBP4HTypzlCoiarWn28KsY1EvdDzF7qa49gr65LIMNIBkrw%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6kHxG8qWbKrPmuibYcwZyToxcJjEEXJRTptiaOOOgj5icMPPHF0844QKYlttORavPa7QibvZbVonJh6g%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg; https://images.weserv.nl/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_png%2FgCE6Jqa7zN6kHxG8qWbKrPmuibYcwZyToz9ribXmux3TDwRuYZ46icMkIwpR4Zlpbg3tWDfEcJcZQ3dZTibdk2RW0w%2F640%3Fwx_fmt%3Dpng%26from%3Dappmsg
