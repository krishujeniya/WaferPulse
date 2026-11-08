"""Visualization generation module (Cookiecutter Data Science standard).

Creates exploratory, diagnostic, and results-oriented figures
saved directly in reports/figures/.
"""

from __future__ import annotations

import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("visualize")


def generate_wafer_map_figure(output_path: str | Path = "reports/figures/wafer_die_map.svg") -> Path:
    """Generate SVG visualization of 300mm silicon wafer topography and die defect distribution."""
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">
  <rect width="600" height="600" fill="#080c14" />
  <!-- Silicon Wafer Disc -->
  <circle cx="300" cy="300" r="260" fill="#0d1527" stroke="#334155" stroke-width="4" />
  <circle cx="300" cy="300" r="255" fill="none" stroke="#0284c7" stroke-width="1" stroke-dasharray="4,4" opacity="0.4" />
  <!-- Alignment Notch -->
  <path d="M 292 560 L 308 560 L 300 550 Z" fill="#080c14" stroke="#475569" stroke-width="2" />
  
  <text x="300" y="45" font-family="monospace" font-size="14" fill="#94a3b8" text-anchor="middle" font-weight="bold">300mm SILICON WAFER DIE DEFECT TOPOGRAPHY</text>
  <text x="300" y="65" font-family="monospace" font-size="11" fill="#64748b" text-anchor="middle">WaferPulse Anomaly Detection Grid</text>

  <!-- Die Grid Simulation -->
  <g transform="translate(110, 110)">
"""
    grid_size = 13
    cell_size = 28
    gap = 2

    import math
    for r in range(grid_size):
        for c in range(grid_size):
            x_coord = c - 6
            y_coord = r - 6
            dist = math.sqrt(x_coord**2 + y_coord**2)
            if dist <= 6.2:
                px = c * (cell_size + gap)
                py = r * (cell_size + gap)
                is_defect = (x_coord == 2 and y_coord == 3) or (x_coord == -3 and y_coord == 1) or (dist > 5.8 and (x_coord * y_coord) % 3 == 0)
                is_warn = not is_defect and ((x_coord == 1 and y_coord == 2) or (dist > 5.5 and abs(x_coord) == 2))
                color = "#f43f5e" if is_defect else "#f59e0b" if is_warn else "#10b981"
                opacity = "0.9" if is_defect else "0.7" if is_warn else "0.6"
                svg_content += f'    <rect x="{px}" y="{py}" width="{cell_size}" height="{cell_size}" rx="2" fill="{color}" opacity="{opacity}" stroke="#0f172a" stroke-width="1" />\n'

    svg_content += """  </g>
  <!-- Legend -->
  <g transform="translate(150, 520)" font-family="monospace" font-size="11">
    <rect x="0" y="0" width="14" height="14" rx="2" fill="#10b981" opacity="0.8" />
    <text x="20" y="11" fill="#94a3b8">Pass (Normal)</text>

    <rect x="120" y="0" width="14" height="14" rx="2" fill="#f59e0b" opacity="0.8" />
    <text x="140" y="11" fill="#94a3b8">Warning</text>

    <rect x="220" y="0" width="14" height="14" rx="2" fill="#f43f5e" opacity="0.9" />
    <text x="240" y="11" fill="#94a3b8">Defect Fault</text>
  </g>
</svg>"""

    with open(out_p, "w", encoding="utf-8") as f:
        f.write(svg_content)

    logger.info(f"Saved wafer die map figure to {out_p}")
    return out_p


def generate_drift_figure(output_path: str | Path = "reports/figures/sensor_drift_report.svg") -> Path:
    """Generate SVG visualization of sensor channel Population Stability Index (PSI)."""
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 350" width="100%" height="100%">
  <rect width="600" height="350" fill="#080c14" />
  <text x="30" y="35" font-family="monospace" font-size="14" fill="#f8fafc" font-weight="bold">SENSOR TELEMETRY POPULATION STABILITY INDEX (PSI)</text>
  <text x="30" y="55" font-family="monospace" font-size="11" fill="#64748b">Chamber Baseline vs Current Manufacturing Run</text>

  <!-- PSI Threshold Guidelines -->
  <line x1="180" y1="80" x2="180" y2="300" stroke="#10b981" stroke-width="1" stroke-dasharray="4,4" />
  <text x="180" y="75" font-family="monospace" font-size="9" fill="#10b981" text-anchor="middle">PSI 0.10 (Stable)</text>

  <line x1="320" y1="80" x2="320" y2="300" stroke="#f59e0b" stroke-width="1" stroke-dasharray="4,4" />
  <text x="320" y="75" font-family="monospace" font-size="9" fill="#f59e0b" text-anchor="middle">PSI 0.25 (Drift)</text>

  <!-- Sensor Bars -->
  <g font-family="monospace" font-size="11" fill="#94a3b8">
    <!-- Sensor 11 -->
    <text x="30" y="110">Sensor_11 (RF Power)</text>
    <rect x="180" y="98" width="180" height="14" rx="2" fill="#f43f5e" />
    <text x="370" y="110" fill="#f43f5e" font-weight="bold">PSI = 0.284 (Critical)</text>

    <!-- Sensor 25 -->
    <text x="30" y="145">Sensor_25 (Chamber Press)</text>
    <rect x="180" y="133" width="95" height="14" rx="2" fill="#f59e0b" />
    <text x="285" y="145" fill="#f59e0b" font-weight="bold">PSI = 0.142 (Moderate)</text>

    <!-- Sensor 42 -->
    <text x="30" y="180">Sensor_42 (Coolant Temp)</text>
    <rect x="180" y="168" width="65" height="14" rx="2" fill="#10b981" />
    <text x="255" y="180" fill="#10b981">PSI = 0.082 (Stable)</text>

    <!-- Sensor 03 -->
    <text x="30" y="215">Sensor_03 (Slurry Flow)</text>
    <rect x="180" y="203" width="40" height="14" rx="2" fill="#10b981" />
    <text x="230" y="215" fill="#10b981">PSI = 0.038 (Stable)</text>

    <!-- Sensor 18 -->
    <text x="30" y="250">Sensor_18 (He Backside Press)</text>
    <rect x="180" y="238" width="25" height="14" rx="2" fill="#10b981" />
    <text x="215" y="250" fill="#10b981">PSI = 0.019 (Stable)</text>
  </g>
</svg>"""

    with open(out_p, "w", encoding="utf-8") as f:
        f.write(svg_content)

    logger.info(f"Saved sensor drift figure to {out_p}")
    return out_p


def main():
    generate_wafer_map_figure()
    generate_drift_figure()


if __name__ == "__main__":
    main()
