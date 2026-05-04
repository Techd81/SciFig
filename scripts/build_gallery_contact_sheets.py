from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
GALLERY_DIR = ROOT / "docs" / "gallery"

SINGLE_PANEL_IMAGES = [
    ("iris_radar_hero.png", "Iris Radar"),
    ("covid_national_burden_hero.png", "COVID Burden"),
    ("covid_states_heatmap_hero.png", "COVID Heatmap"),
    ("gtex_quality_hero.png", "GTEx QC"),
    ("power_load_hero.png", "Power Load"),
    ("power_streamgraph_hero.png", "Power Stream"),
    ("citibike_mobility_spine.png", "Citi Bike"),
    ("citibike_dotplot_hero.png", "Citi Dotplot"),
    ("exoplanet_mass_radius_hero.png", "Exoplanets"),
    ("exoplanet_bubble_hero.png", "Exoplanet Bubble"),
    ("wine_class_hero.png", "Wine Classes"),
]

MULTI_PANEL_IMAGES = [
    ("iris_feature_atlas.png", "Iris Atlas"),
    ("covid_state_storyboard.png", "COVID Storyboard"),
    ("covid_parallel_heatmaps.png", "COVID Heatmaps"),
    ("covid_wave_atlas.png", "COVID Wave Atlas"),
    ("covid_marginal_coupling.png", "COVID Coupling"),
    ("gtex_qc_atlas.png", "GTEx Atlas"),
    ("power_load_atlas.png", "Power Atlas"),
    ("citibike_mobility_atlas.png", "Citi Bike Atlas"),
    ("exoplanet_physical_atlas.png", "Exoplanet Physical"),
    ("exoplanet_discovery_bias.png", "Discovery Bias"),
    ("exoplanet_candidate_quality.png", "Candidate Quality"),
    ("wine_feature_atlas.png", "Wine Atlas"),
]


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _fit_image(path: Path, size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail(size, Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", size, "white")
        x = (size[0] - image.width) // 2
        y = (size[1] - image.height) // 2
        canvas.paste(image, (x, y))
        return canvas


def build_contact_sheet(items: list[tuple[str, str]], output_name: str, title: str, columns: int) -> None:
    thumb_size = (420, 280)
    padding = 30
    gap = 24
    label_h = 34
    title_h = 66
    rows = (len(items) + columns - 1) // columns
    width = padding * 2 + columns * thumb_size[0] + (columns - 1) * gap
    height = title_h + padding + rows * (thumb_size[1] + label_h) + (rows - 1) * gap
    sheet = Image.new("RGB", (width, height), "#F7F7F5")
    draw = ImageDraw.Draw(sheet)
    title_font = _font(30, bold=True)
    label_font = _font(17)
    draw.text((width / 2, 32), title, fill="#222222", font=title_font, anchor="mm")

    for index, (filename, label) in enumerate(items):
        source = GALLERY_DIR / filename
        if not source.exists():
            raise FileNotFoundError(source)
        row, col = divmod(index, columns)
        x = padding + col * (thumb_size[0] + gap)
        y = title_h + row * (thumb_size[1] + label_h + gap)
        tile = _fit_image(source, thumb_size)
        sheet.paste(tile, (x, y))
        draw.rectangle((x, y, x + thumb_size[0], y + thumb_size[1]), outline="#D0D0CC", width=1)
        draw.text((x + thumb_size[0] / 2, y + thumb_size[1] + 20), label, fill="#333333", font=label_font, anchor="mm")

    sheet.save(GALLERY_DIR / output_name, quality=95)


def main() -> None:
    build_contact_sheet(SINGLE_PANEL_IMAGES, "singlepanel_gallery.png", "Single-Panel Gallery", columns=3)
    build_contact_sheet(MULTI_PANEL_IMAGES, "multipanel_gallery.png", "Multi-Panel Gallery", columns=3)


if __name__ == "__main__":
    main()
