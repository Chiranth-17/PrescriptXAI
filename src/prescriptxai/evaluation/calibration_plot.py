"""Small dependency-light HTML and PNG reliability plots for measured calibration results."""

from __future__ import annotations

from html import escape
from pathlib import Path

from PIL import Image, ImageDraw


def _points(diagnostics: dict[str, object]) -> list[tuple[float, float]]:
    """Extract mean predicted and observed positive rates from populated bins."""
    curve = diagnostics.get("reliability_curve", [])
    if not isinstance(curve, list):
        return []
    output: list[tuple[float, float]] = []
    for item in curve:
        if isinstance(item, dict):
            output.append((float(item["mean_probability"]), float(item["fraction_positive"])))
    return output


def write_calibration_plots(
    output_stem: Path,
    before: dict[str, object],
    after: dict[str, object],
    title: str,
) -> tuple[Path, Path]:
    """Write the supplied reliability measurements to a self-contained HTML and PNG pair."""
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    html_path = output_stem.with_suffix(".html")
    png_path = output_stem.with_suffix(".png")
    width, height, margin = 900, 700, 90
    plot_size = min(width - 2 * margin, height - 2 * margin)

    def to_svg_xy(point: tuple[float, float]) -> tuple[float, float]:
        return margin + point[0] * plot_size, height - margin - point[1] * plot_size

    before_points = _points(before)
    after_points = _points(after)
    svg_lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
        ),
        '<rect width="100%" height="100%" fill="white"/>',
        (
            f'<text x="{width / 2:g}" y="36" text-anchor="middle" '
            f'font-family="sans-serif" font-size="22">{escape(title)}</text>'
        ),
        (
            f'<line x1="{margin}" y1="{height - margin}" '
            f'x2="{margin + plot_size}" y2="{height - margin}" stroke="#333"/>'
        ),
        (
            f'<line x1="{margin}" y1="{height - margin}" '
            f'x2="{margin}" y2="{height - margin - plot_size}" stroke="#333"/>'
        ),
        (
            f'<line x1="{margin}" y1="{height - margin - plot_size}" '
            f'x2="{margin + plot_size}" y2="{height - margin}" '
            'stroke="#888" stroke-dasharray="7 5"/>'
        ),
        (
            f'<text x="{margin + plot_size / 2:g}" y="{height - 20}" text-anchor="middle" '
            'font-family="sans-serif" font-size="15">Mean predicted probability</text>'
        ),
        (
            f'<text x="22" y="{height / 2:g}" text-anchor="middle" '
            f'transform="rotate(-90 22 {height / 2:g})" font-family="sans-serif" '
            'font-size="15">Observed fraction positive</text>'
        ),
    ]
    for points, color, label, y in (
        (before_points, "#d95f02", "Before calibration", 60),
        (after_points, "#1b9e77", "After calibration", 82),
    ):
        if len(points) > 1:
            coords = " ".join(f"{x:g},{y_value:g}" for x, y_value in map(to_svg_xy, points))
            svg_lines.append(
                f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="3"/>'
            )
        for point in points:
            x, y_value = to_svg_xy(point)
            svg_lines.append(f'<circle cx="{x:g}" cy="{y_value:g}" r="5" fill="{color}"/>')
        svg_lines.append(
            f'<text x="{width - margin - 165}" y="{y}" '
            f'font-family="sans-serif" font-size="14" fill="{color}">{label}</text>'
        )
    svg_lines.append("</svg>")
    svg = "\n".join(svg_lines)
    html_path.write_text(
        '<!doctype html><html><head><meta charset="utf-8"><title>'
        + escape(title)
        + "</title></head><body>"
        + svg
        + "</body></html>\n",
        encoding="utf-8",
    )

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((width / 2, 28), title, fill="#111", anchor="mt")
    left, top, right, bottom = margin, margin, margin + plot_size, margin + plot_size
    draw.line((left, bottom, right, bottom), fill="#333", width=2)
    draw.line((left, bottom, left, top), fill="#333", width=2)
    draw.line((left, bottom, right, top), fill="#888", width=2)
    draw.text((width / 2, height - 35), "Mean predicted probability", fill="#222", anchor="mm")
    draw.text((25, height / 2), "Observed fraction positive", fill="#222", anchor="mm")
    for points, color, label, legend_y in (
        (before_points, "#d95f02", "Before calibration", 60),
        (after_points, "#1b9e77", "After calibration", 82),
    ):
        coordinates = [
            (left + x * plot_size, bottom - y_value * plot_size) for x, y_value in points
        ]
        if len(coordinates) > 1:
            draw.line(coordinates, fill=color, width=4)
        for x, y_value in coordinates:
            draw.ellipse((x - 5, y_value - 5, x + 5, y_value + 5), fill=color)
        draw.text((right - 175, legend_y), label, fill=color)
    image.save(png_path, format="PNG")
    return png_path, html_path
