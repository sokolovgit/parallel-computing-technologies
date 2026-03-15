from __future__ import annotations

from .comparator import Comparator
from .network import ComparisonNetwork

_X_SCALE = 105
_X_SCALE_THIN = 35
_Y_SCALE = 60
_STAGE_GAP = 50
_WIRE_STROKE = "#d1d5db"
_WIRE_WIDTH = 2.0
_COMPARATOR_STROKE = "#1f2937"
_COMPARATOR_FILL = "#1f2937"
_COMPARATOR_WIDTH = 2.5
_DOT_RADIUS = 8.0
_LABEL_FILL = "#6b7280"
_LABEL_FONT_SIZE = 16.0
_STAGE_FONT_SIZE = 18.0
_TITLE_FONT_SIZE = 22.0
_BACKGROUND = "#fafafa"
_SCALE_OUTPUT = 2.5


def _layout(
    network: ComparisonNetwork,
) -> tuple[float, float, list[tuple[Comparator, float, float, float]]]:
    comparators = network._get_optimized_comparators()
    n = network.get_max_input() + 2
    h = n * _Y_SCALE
    w = _X_SCALE
    group: dict[Comparator, float] = {}
    result: list[tuple[Comparator, float, float, float]] = []

    for c in comparators:
        for other in group:
            if c.has_same_input(other):
                w = max(group.values(), default=w)
                w += _X_SCALE
                group = {}
                break
        cx = w
        for other, other_pos in group.items():
            if other_pos >= cx and c.overlaps(other):
                cx = other_pos + _X_SCALE_THIN
        y1 = _Y_SCALE * (c.i1 + 1)
        y2 = _Y_SCALE * (c.i2 + 1)
        result.append((c, cx, y1, y2))
        group[c] = cx

    w = max(group.values(), default=w) + _X_SCALE
    return w, h, result


def _layout_by_stages(
    stages: list[tuple[int, int, list[Comparator]]],
    n_wires: int,
) -> tuple[float, float, list[tuple[str, float, list[tuple[Comparator, float, float, float]]]]]:
    """(total_w, total_h, [(label, label_x, [(c, cx, y1, y2), ...]), ...])."""
    h = (n_wires + 1) * _Y_SCALE
    col_x = _X_SCALE
    result: list[tuple[str, float, list[tuple[Comparator, float, float, float]]]] = []

    for k, j, comps in stages:
        label = f"k={k}, j={j}"
        sorted_comps = sorted(comps, key=lambda c: (c.i1 + c.i2) / 2)
        stage_layout: list[tuple[Comparator, float, float, float]] = []
        cx = col_x
        for c in sorted_comps:
            y1 = _Y_SCALE * (c.i1 + 1)
            y2 = _Y_SCALE * (c.i2 + 1)
            stage_layout.append((c, cx, y1, y2))
            cx += _X_SCALE_THIN
        label_x = (col_x + cx - _X_SCALE_THIN) / 2 if comps else col_x
        result.append((label, label_x, stage_layout))
        col_x = cx + _STAGE_GAP

    w = col_x
    return w, h, result


def render_svg(
    network: ComparisonNetwork,
    title: str | None = None,
    stages: list[tuple[int, int, list[Comparator]]] | None = None,
) -> str:
    n_wires = network.get_max_input() + 1
    title_h = 32 if title else 0
    r = _DOT_RADIUS

    if stages:
        w, h, stage_layouts = _layout_by_stages(stages, n_wires)
        vb_w = w
        vb_h = title_h + h + (_Y_SCALE * 0.5)
        wire_y = title_h

        parts: list[str] = []
        stage_labels: list[str] = []
        for label, label_x, layout in stage_layouts:
            stage_labels.append(
                f"<text x='{label_x}' y='{wire_y + 20}' text-anchor='middle' "
                f"font-family='system-ui,sans-serif' font-size='{_STAGE_FONT_SIZE}' "
                f"fill='{_LABEL_FILL}'>{label}</text>"
            )
            for _c, cx, y1, y2 in layout:
                y1t, y2t = y1 + wire_y, y2 + wire_y
                parts.append(
                    f"M{cx - r} {y1t}a{r} {r} 0 1 1 {r * 2} 0a{r} {r} 0 1 1-{r * 2} 0z"
                    f"m{r} 0V{y2t}m-{r} 0a{r} {r} 0 1 1 {r * 2} 0a{r} {r} 0 1 1-{r * 2} 0z"
                )
    else:
        w, h, layout = _layout(network)
        vb_w = w
        vb_h = title_h + h + (_Y_SCALE * 0.5)
        wire_y = title_h
        parts = []
        for _c, cx, y1, y2 in layout:
            y1t, y2t = y1 + title_h, y2 + title_h
            parts.append(
                f"M{cx - r} {y1t}a{r} {r} 0 1 1 {r * 2} 0a{r} {r} 0 1 1-{r * 2} 0z"
                f"m{r} 0V{y2t}m-{r} 0a{r} {r} 0 1 1 {r * 2} 0a{r} {r} 0 1 1-{r * 2} 0z"
            )
        stage_labels = []

    comparators_d = "".join(parts)
    lines_d = "".join(
        f"M0 {wire_y + (i + 1) * _Y_SCALE}H{vb_w}" for i in range(n_wires)
    )
    wire_labels = "".join(
        f"<text x='4' y='{wire_y + (i + 1) * _Y_SCALE + 4}' "
        f"font-family='system-ui,sans-serif' font-size='{_LABEL_FONT_SIZE}' "
        f"fill='{_LABEL_FILL}'>{i}</text>"
        for i in range(n_wires)
    )
    title_svg = ""
    if title:
        title_svg = (
            f"<text x='{vb_w / 2}' y='{_TITLE_FONT_SIZE}' text-anchor='middle' "
            f"font-family='system-ui,sans-serif' font-size='{_TITLE_FONT_SIZE}' "
            f"fill='{_LABEL_FILL}'>{title}</text>"
        )
    stage_labels_svg = "".join(stage_labels)

    out_w = vb_w / _SCALE_OUTPUT
    out_h = vb_h / _SCALE_OUTPUT

    return (
        "<?xml version='1.0' encoding='utf-8'?>"
        "<!DOCTYPE svg>"
        f"<svg width='{out_w}' height='{out_h}' viewBox='0 0 {vb_w} {vb_h}' "
        "xmlns='http://www.w3.org/2000/svg'>"
        f"<rect width='{vb_w}' height='{vb_h}' fill='{_BACKGROUND}'/>"
        f"{title_svg}"
        f"{stage_labels_svg}"
        f"<path style='stroke:{_WIRE_STROKE};stroke-width:{_WIRE_WIDTH};fill:none' "
        f"d='{lines_d}'/>"
        f"<path style='stroke:{_COMPARATOR_STROKE};stroke-width:{_COMPARATOR_WIDTH};"
        f"fill:{_COMPARATOR_FILL}' d='{comparators_d}'/>"
        f"{wire_labels}"
        "</svg>"
    )
