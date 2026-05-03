"""Gallery expansion — 7 new figures using SciFig skill design system.

Generates 6 new hero figures + 1 new multi-panel using raw datasets,
following Nature journal style (rcParams kernel from specs/journal-profiles.md)
and colorblind-safe Wong/Okabe-Ito palette.
"""
import sys, os, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patheffects as pe
warnings.filterwarnings('ignore')

# ── Paths ──
BASE = r'D:\SciFig'
GALLERY = os.path.join(BASE, 'docs', 'gallery')
RAW = os.path.join(BASE, '.workflow', '.scratchpad', 'test-data', 'raw')

# ── Nature-style rcParams (from specs/journal-profiles.md) ──
def apply_nature():
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'font.size': 6,
        'axes.linewidth': 0.6,
        'axes.labelsize': 7,
        'axes.titlesize': 7.5,
        'axes.titleweight': 'bold',
        'xtick.labelsize': 5.5,
        'ytick.labelsize': 5.5,
        'xtick.major.width': 0.6,
        'ytick.major.width': 0.6,
        'xtick.direction': 'out',
        'ytick.direction': 'out',
        'xtick.major.size': 3,
        'ytick.major.size': 3,
        'legend.fontsize': 5.5,
        'legend.frameon': False,
        'figure.dpi': 200,
        'savefig.dpi': 200,
        'lines.linewidth': 1.0,
        'lines.markersize': 3,
        'axes.grid': False,
        'axes.spines.top': False,
        'axes.spines.right': False,
    })

# ── Palettes ──
WONG = ['#56B4E9', '#E69F00', '#009E73', '#D55E00', '#CC79A7',
        '#0072B2', '#F0E442', '#000000']
NATURE_CMAP = LinearSegmentedColormap.from_list(
    'nature_heat', ['#4393C3', '#F7F7F7', '#D6604D'])

DPI = 200
FW = 7.2  # 183mm hero width in inches

def save(fig, name):
    p = os.path.join(GALLERY, name)
    fig.savefig(p, dpi=DPI, bbox_inches='tight', facecolor='white', edgecolor='none')
    w, h = fig.get_size_inches()
    print(f'  {name}: {int(w*DPI)}x{int(h*DPI)}px')
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════
# 1. Iris Radar Hero
# ═══════════════════════════════════════════════════════════════
def gen_iris_radar():
    df = pd.read_csv(os.path.join(RAW, 'uci_iris.csv'),
                     names=['sepal_l', 'sepal_w', 'petal_l', 'petal_w', 'species'])
    means = df.groupby('species').mean()
    normed = (means - means.min()) / (means.max() - means.min())

    features = ['Sepal L', 'Sepal W', 'Petal L', 'Petal W']
    n = len(features)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles_closed = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(FW * 0.6, FW * 0.6),
                           subplot_kw=dict(polar=True))
    for i, (sp, row) in enumerate(normed.iterrows()):
        vals = row.tolist() + [row.iloc[0]]
        short = sp.replace('Iris-', '')
        ax.plot(angles_closed, vals, 'o-', color=WONG[i], lw=1.2, ms=4, label=short)
        ax.fill(angles_closed, vals, alpha=0.10, color=WONG[i])

    ax.set_xticks(angles)
    ax.set_xticklabels(features, fontsize=6.5)
    ax.set_yticklabels([])
    ax.set_ylim(0, 1.08)
    ax.spines['polar'].set_linewidth(0.4)
    ax.grid(True, lw=0.3, alpha=0.4)
    ax.legend(loc='upper right', bbox_to_anchor=(1.18, 1.12), fontsize=6)
    fig.tight_layout()
    save(fig, 'iris_radar_hero.png')
    print('  [1/7] Iris radar done')


# ═══════════════════════════════════════════════════════════════
# 2. Covid States Heatmap Hero
# ═══════════════════════════════════════════════════════════════
def gen_covid_heatmap():
    df = pd.read_csv(os.path.join(RAW, 'nyt_covid_states.csv'))
    df['date'] = pd.to_datetime(df['date'])
    # Top 15 states by total cases
    top = df.groupby('state')['cases'].max().nlargest(15).index
    sub = df[df['state'].isin(top)]
    # Monthly aggregation
    sub = sub.set_index('date').groupby([pd.Grouper(freq='MS'), 'state'])['cases'].max().reset_index()
    piv = sub.pivot(index='state', columns='date', values='cases').fillna(0)
    piv = piv.loc[piv.sum(axis=1).sort_values(ascending=False).index]
    # Log scale for readability
    mat = np.log10(piv.values + 1)

    fig, ax = plt.subplots(figsize=(FW, FW * 0.55))
    im = ax.imshow(mat, aspect='auto', cmap=NATURE_CMAP, interpolation='nearest')
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels(piv.index, fontsize=5)
    ax.set_xticks(range(0, len(piv.columns), 3))
    ax.set_xticklabels([d.strftime('%b\n%Y') for d in piv.columns[::3]], fontsize=5)
    ax.set_xlabel('')
    ax.set_title('Cumulative COVID-19 Cases by State (log₁₀)', fontsize=7, pad=6)
    cb = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
    cb.ax.tick_params(labelsize=5)
    cb.set_label('log₁₀(cases + 1)', fontsize=5.5)
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.spines['top'].set_linewidth(0.4)
    ax.spines['right'].set_linewidth(0.4)
    fig.tight_layout()
    save(fig, 'covid_states_heatmap_hero.png')
    print('  [2/7] Covid heatmap done')


# ═══════════════════════════════════════════════════════════════
# 3. GTEX Raincloud Hero
# ═══════════════════════════════════════════════════════════════
def gen_gtex_raincloud():
    df = pd.read_csv(os.path.join(RAW, 'gtex_samples.tsv'), sep='\t', low_memory=False)
    # Use SMRIN (RIN score) grouped by tissue (SMTS)
    metric = 'SMRIN'
    tissue_col = 'SMTS'
    sub = df[[tissue_col, metric]].dropna()
    # Top 8 tissues by sample count
    top_tissues = sub[tissue_col].value_counts().head(8).index
    sub = sub[sub[tissue_col].isin(top_tissues)]
    sub[tissue_col] = pd.Categorical(sub[tissue_col], categories=top_tissues, ordered=True)
    groups = [g[metric].values for _, g in sub.groupby(tissue_col, observed=True)]
    labels = [str(g) for g in top_tissues]

    fig, ax = plt.subplots(figsize=(FW, FW * 0.6))
    positions = np.arange(len(labels))
    for i, (data, pos) in enumerate(zip(groups, positions)):
        # Violin (half)
        vp = ax.violinplot(data, [pos], showmeans=False, showextrema=False, widths=0.7)
        for body in vp['bodies']:
            body.set_facecolor(WONG[i % len(WONG)])
            body.set_alpha(0.25)
        # Box (narrow)
        q1, med, q3 = np.percentile(data, [25, 50, 75])
        ax.vlines(pos, q1, q3, lw=4, color=WONG[i % len(WONG)], alpha=0.7)
        ax.scatter(pos, med, s=12, color='white', zorder=3, edgecolors='black', linewidths=0.5)
        # Strip points (jittered)
        jitter = np.random.default_rng(42).uniform(-0.15, 0.15, len(data))
        sample_idx = np.random.default_rng(42).choice(len(data), min(60, len(data)), replace=False)
        ax.scatter(pos + jitter[sample_idx], data[sample_idx],
                   s=2, alpha=0.35, color=WONG[i % len(WONG)], zorder=2)

    ax.set_xticks(positions)
    ax.set_xticklabels(labels, fontsize=5, rotation=25, ha='right')
    ax.set_ylabel('RIN Score')
    ax.set_title('GTEx Sample Quality by Tissue', fontsize=7, pad=6)
    fig.tight_layout()
    save(fig, 'gtex_raincloud_hero.png')
    print('  [3/7] GTEX raincloud done')


# ═══════════════════════════════════════════════════════════════
# 4. Power Streamgraph Hero
# ═══════════════════════════════════════════════════════════════
def gen_power_streamgraph():
    df = pd.read_csv(os.path.join(RAW, 'uci_power.csv'), sep=';', low_memory=True)
    df.columns = [c.strip() for c in df.columns]
    df = df.replace('?', np.nan)
    for c in ['Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['Global_active_power'] = pd.to_numeric(df['Global_active_power'], errors='coerce')
    # Sample every 500 rows for performance
    df = df.iloc[::500].reset_index(drop=True)
    n = len(df)
    x = np.arange(n)
    y1 = df['Sub_metering_1'].fillna(0).values
    y2 = df['Sub_metering_2'].fillna(0).values
    y3 = df['Sub_metering_3'].fillna(0).values

    # Stack and center for streamgraph effect
    y_stack = np.vstack([y1, y2, y3])
    y_cum = np.vstack([np.zeros_like(x), np.cumsum(y_stack, axis=0)])
    y_centered = y_cum - y_cum[-1:] / 2

    fig, ax = plt.subplots(figsize=(FW, FW * 0.5))
    labels_sm = ['Kitchen', 'Laundry', 'Water Heater']
    colors = [WONG[0], WONG[1], WONG[2]]
    for i in range(3):
        ax.fill_between(x, y_centered[i], y_centered[i+1],
                        color=colors[i], alpha=0.75, label=labels_sm[i])

    ax.set_xlim(0, n)
    ax.set_ylim(y_centered.min() * 1.1, y_centered.max() * 1.1)
    ax.set_ylabel('Power (Wh)')
    ax.set_xlabel('Time (sampled)')
    ax.set_title('Household Power Consumption — Sub-metering Streamgraph', fontsize=7, pad=6)
    ax.legend(loc='upper right', fontsize=5.5)
    fig.tight_layout()
    save(fig, 'power_streamgraph_hero.png')
    print('  [4/7] Power streamgraph done')


# ═══════════════════════════════════════════════════════════════
# 5. Citibike Dotplot Hero
# ═══════════════════════════════════════════════════════════════
def gen_citibike_dotplot():
    df = pd.read_csv(os.path.join(RAW, 'citi_bike_jc_202508.csv'), low_memory=False)
    # Top 15 start stations by ride count
    top = df['start_station_name'].value_counts().head(15)
    stations = top.values[::-1]
    names = top.index[::-1].str.slice(0, 30)

    fig, ax = plt.subplots(figsize=(FW, FW * 0.55))
    y = np.arange(len(names))
    colors = [WONG[0] if i < 8 else WONG[2] for i in range(len(names))]
    ax.scatter(stations, y, s=stations * 0.6, c=colors, alpha=0.7, edgecolors='white', linewidths=0.5, zorder=3)
    ax.hlines(y, 0, stations, color='#cccccc', linewidth=0.5, zorder=1)

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=5.5)
    ax.set_xlabel('Number of Rides')
    ax.set_title('Top 15 Citi Bike Stations — Ride Count', fontsize=7, pad=6)
    ax.spines['left'].set_linewidth(0.4)
    ax.set_xlim(0, stations.max() * 1.1)
    fig.tight_layout()
    save(fig, 'citibike_dotplot_hero.png')
    print('  [5/7] Citibike dotplot done')


# ═══════════════════════════════════════════════════════════════
# 6. Exoplanet Bubble Scatter Hero
# ═══════════════════════════════════════════════════════════════
def gen_exoplanet_bubble():
    df = pd.read_csv(os.path.join(RAW, 'nasa_exoplanets.csv'), low_memory=False)
    sub = df.dropna(subset=['pl_bmasse', 'pl_rade', 'pl_eqt']).copy()
    sub = sub[(sub['pl_bmasse'] < 5000) & (sub['pl_rade'] < 20)]

    fig, ax = plt.subplots(figsize=(FW, FW * 0.65))
    sc = ax.scatter(sub['pl_rade'], sub['pl_bmasse'],
                    c=sub['pl_eqt'], cmap='RdYlBu_r',
                    s=np.clip(sub['pl_orbper'].fillna(1) * 0.3, 3, 80),
                    alpha=0.55, edgecolors='none', linewidths=0.3)

    ax.set_xlabel('Planet Radius (R⊕)')
    ax.set_ylabel('Planet Mass (M⊕)')
    ax.set_title('Exoplanet Mass–Radius Relation', fontsize=7, pad=6)
    ax.set_yscale('log')
    ax.set_xscale('log')
    cb = fig.colorbar(sc, ax=ax, shrink=0.7, pad=0.02)
    cb.set_label('Equilibrium Temp (K)', fontsize=5.5)
    cb.ax.tick_params(labelsize=5)
    fig.tight_layout()
    save(fig, 'exoplanet_bubble_hero.png')
    print('  [6/7] Exoplanet bubble done')


# ═══════════════════════════════════════════════════════════════
# 7. Iris Multi-Panel Feature Atlas
# ═══════════════════════════════════════════════════════════════
def gen_iris_atlas():
    df = pd.read_csv(os.path.join(RAW, 'uci_iris.csv'),
                     names=['sepal_l', 'sepal_w', 'petal_l', 'petal_w', 'species'])
    species = df['species'].unique()
    colors = {s: WONG[i] for i, s in enumerate(species)}

    fig = plt.figure(figsize=(FW * 1.35, FW * 0.95))
    gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.32)

    # Panel A: Scatter matrix (sepal_l vs petal_l)
    ax1 = fig.add_subplot(gs[0, 0])
    for s in species:
        sub = df[df['species'] == s]
        ax1.scatter(sub['sepal_l'], sub['petal_l'], s=8, alpha=0.6,
                    color=colors[s], label=s.replace('Iris-', ''))
    ax1.set_xlabel('Sepal Length')
    ax1.set_ylabel('Petal Length')
    ax1.set_title('A', fontsize=8, fontweight='bold', loc='left', pad=2)

    # Panel B: Box plots
    ax2 = fig.add_subplot(gs[0, 1])
    feat = 'petal_l'
    data_box = [df[df['species'] == s][feat].values for s in species]
    bp = ax2.boxplot(data_box, patch_artist=True, widths=0.5,
                     medianprops=dict(color='black', linewidth=0.8))
    for patch, s in zip(bp['boxes'], species):
        patch.set_facecolor(colors[s])
        patch.set_alpha(0.6)
    ax2.set_xticklabels([s.replace('Iris-', '') for s in species], fontsize=5.5)
    ax2.set_ylabel('Petal Length')
    ax2.set_title('B', fontsize=8, fontweight='bold', loc='left', pad=2)

    # Panel C: Parallel coordinates
    ax3 = fig.add_subplot(gs[0, 2])
    features = ['sepal_l', 'sepal_w', 'petal_l', 'petal_w']
    x_feat = np.arange(len(features))
    for s in species:
        sub = df[df['species'] == s]
        normed = (sub[features] - df[features].min()) / (df[features].max() - df[features].min())
        for _, row in normed.iterrows():
            ax3.plot(x_feat, row.values, color=colors[s], alpha=0.08, lw=0.5)
        # Mean line
        mean_normed = (sub[features].mean() - df[features].min()) / (df[features].max() - df[features].min())
        ax3.plot(x_feat, mean_normed.values, color=colors[s], lw=1.5, label=s.replace('Iris-', ''))
    ax3.set_xticks(x_feat)
    ax3.set_xticklabels(['SL', 'SW', 'PL', 'PW'], fontsize=5.5)
    ax3.set_ylabel('Normalized')
    ax3.set_title('C', fontsize=8, fontweight='bold', loc='left', pad=2)

    # Panel D: Histogram (petal_l)
    ax4 = fig.add_subplot(gs[1, 0])
    for s in species:
        sub = df[df['species'] == s]
        ax4.hist(sub['petal_l'], bins=12, alpha=0.5, color=colors[s], label=s.replace('Iris-', ''))
    ax4.set_xlabel('Petal Length')
    ax4.set_ylabel('Count')
    ax4.set_title('D', fontsize=8, fontweight='bold', loc='left', pad=2)

    # Panel E: Radar summary
    ax5 = fig.add_subplot(gs[1, 1], polar=True)
    means = df.groupby('species')[features].mean()
    normed = (means - means.min()) / (means.max() - means.min())
    n_feat = len(features)
    angles = np.linspace(0, 2 * np.pi, n_feat, endpoint=False).tolist()
    angles_closed = angles + [angles[0]]
    for s in species:
        vals = normed.loc[s].tolist() + [normed.loc[s].iloc[0]]
        ax5.plot(angles_closed, vals, 'o-', color=colors[s], lw=1, ms=3, label=s.replace('Iris-', ''))
        ax5.fill(angles_closed, vals, alpha=0.08, color=colors[s])
    ax5.set_xticks(angles)
    ax5.set_xticklabels(['SL', 'SW', 'PL', 'PW'], fontsize=5.5)
    ax5.set_yticklabels([])
    ax5.set_title('E', fontsize=8, fontweight='bold', loc='left', pad=8)
    ax5.grid(True, lw=0.3, alpha=0.4)

    # Panel F: Violin plot (petal_w)
    ax6 = fig.add_subplot(gs[1, 2])
    data_violin = [df[df['species'] == s]['petal_w'].values for s in species]
    vp = ax6.violinplot(data_violin, showmeans=False, showextrema=False)
    for i, body in enumerate(vp['bodies']):
        body.set_facecolor(list(colors.values())[i])
        body.set_alpha(0.45)
    for i, (data, s) in enumerate(zip(data_violin, species)):
        jitter = np.random.default_rng(42).uniform(-0.08, 0.08, len(data))
        ax6.scatter(np.full(len(data), i + 1) + jitter, data,
                    s=2, alpha=0.3, color=list(colors.values())[i])
    ax6.set_xticks([1, 2, 3])
    ax6.set_xticklabels([s.replace('Iris-', '') for s in species], fontsize=5.5)
    ax6.set_ylabel('Petal Width')
    ax6.set_title('F', fontsize=8, fontweight='bold', loc='left', pad=2)

    # Shared legend
    handles = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=colors[s],
                          markersize=5, label=s.replace('Iris-', '')) for s in species]
    fig.legend(handles=handles, loc='lower center', ncol=3, fontsize=6,
               bbox_to_anchor=(0.5, -0.01))
    fig.suptitle('Iris Feature Atlas', fontsize=9, fontweight='bold', y=1.01)
    fig.tight_layout(rect=[0, 0.03, 1, 0.99])
    save(fig, 'iris_feature_atlas.png')
    print('  [7/7] Iris atlas done')


# ── Main ──
if __name__ == '__main__':
    apply_nature()
    print('Generating 7 new gallery figures...')
    gen_iris_radar()
    gen_covid_heatmap()
    gen_gtex_raincloud()
    gen_power_streamgraph()
    gen_citibike_dotplot()
    gen_exoplanet_bubble()
    gen_iris_atlas()
    print('\nAll 7 figures generated successfully!')
