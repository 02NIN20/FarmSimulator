# map_system.py

from __future__ import annotations
from typing import List, Tuple
from pyray import *

# Importa las siluetas (listas de puntos) de zonas 2-4
# Pueden venir como tuplas (x, y), listas [x, y], Vector2 u objetos con .x/.y
try:
    from zones_geometry import (
        zone2_alaska_polygon,
        zone3_ppr_polygon,
        zone4_michigan_polygon,
    )
except Exception:
    # Fallback por si se abre el archivo de forma independiente
    def zone2_alaska_polygon(): return []
    def zone3_ppr_polygon():    return []
    def zone4_michigan_polygon(): return []


class MapSystem:
    def __init__(self, total_scenes: int = 4) -> None:
        self.total_scenes = max(1, total_scenes)
        self.is_open = False

        self.scene_names: List[str] = [
            "Escenario 1 – Agricultura local",
            "Escenario 2 – Alaska (Valle Matanuska-Susitna)",
            "Escenario 3 – Dakota del Norte (Woodworth – Prairie Pothole Region)",
            "Escenario 4 – Michigan (Suttons Bay – Leelanau Peninsula)",
        ][: self.total_scenes]

        # Layout cacheado: (rect, idx)
        self._cards: List[Tuple[Rectangle, int]] = []

        # Paleta base por escena (tarjetas)
        self.colors = [
            Color(70, 130, 180, 255),   # 1 azul
            Color(210, 140, 70, 255),   # 2 naranja
            Color(80, 160, 120, 255),   # 3 verde
            Color(160, 100, 170, 255),  # 4 violeta
        ]

        # Colores de silueta por bioma
        self.sil_fill = [
            None,                                 # 1 sin silueta
            Color(120, 160, 145, 255),            # 2 Alaska
            Color(165, 185, 100, 255),            # 3 PPR
            Color(100, 165, 125, 255),            # 4 Michigan
        ]
        self.sil_outline = [
            None,
            Color(30, 60, 55, 220),
            Color(60, 70, 25, 220),
            Color(35, 70, 45, 220),
        ]

    # =================== API pública ===================

    def toggle(self) -> None:
        self.is_open = not self.is_open

    def draw(self, screen_w: int, screen_h: int, active_scene_index: int) -> None:
        if not self.is_open:
            return

        # Fondo general
        draw_rectangle(0, 0, screen_w, screen_h, Color(24, 22, 20, 230))

        # Título superior autoajustado
        title = "MAPA DEL MUNDO"
        max_title_w = int(screen_w * 0.8)
        fs = 42
        while fs > 18 and measure_text(title, fs) > max_title_w:
            fs -= 1
        draw_text(title, (screen_w - measure_text(title, fs)) // 2, int(screen_h * 0.06), fs, Color(245, 245, 245, 255))

        # Layout 2x2
        self._compute_layout(screen_w, screen_h)

        # Tarjetas
        mouse = get_mouse_position()
        for rect, idx in self._cards:
            hovered = check_collision_point_rec(mouse, rect)
            selected = (idx == active_scene_index)
            base_col = self.colors[idx % len(self.colors)]
            name = self.scene_names[idx] if idx < len(self.scene_names) else f"Escenario {idx + 1}"

            self._draw_card(rect, base_col, name, idx + 1, idx, selected, hovered)

        # Pie
        foot = "Haz clic en una zona para viajar  |  [M] cerrar"
        fs2 = 18
        draw_text(foot, (screen_w - measure_text(foot, fs2)) // 2, int(screen_h * 0.90), fs2, Color(230, 230, 230, 220))

    def handle_click(self, screen_w: int, screen_h: int) -> int:
        """Devuelve el índice de escena al hacer click; si no hay click válido, -1."""
        if not self.is_open:
            return -1
        if not self._cards:
            self._compute_layout(screen_w, screen_h)

        mouse = get_mouse_position()
        if is_mouse_button_pressed(MOUSE_LEFT_BUTTON):
            for rect, idx in self._cards:
                if check_collision_point_rec(mouse, rect):
                    return idx
        return -1

    # =================== Layout ===================

    def _compute_layout(self, screen_w: int, screen_h: int) -> None:
        self._cards.clear()

        # Área central para grid 2x2 (dejando márgenes cómodos)
        grid_w = int(screen_w * 0.70)
        grid_h = int(screen_h * 0.64)
        grid_x = (screen_w - grid_w) // 2
        grid_y = int(screen_h * 0.20)

        cols, rows = 2, 2
        gap = int(min(grid_w, grid_h) * 0.06)
        card_w = (grid_w - gap * (cols - 1)) // cols
        card_h = (grid_h - gap * (rows - 1)) // rows

        # NOTA: el título ahora va DENTRO de la tarjeta en una banda inferior,
        # por lo que no se superpone a la fila de abajo.

        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= self.total_scenes:
                    break
                x = grid_x + c * (card_w + gap)
                y = grid_y + r * (card_h + gap)
                self._cards.append((Rectangle(x, y, card_w, card_h), idx))
                idx += 1

    # =================== Dibujo de tarjeta ===================

    def _draw_card(
        self,
        rect: Rectangle,
        base_col: Color,
        title: str,
        index_number: int,
        scene_idx: int,
        selected: bool,
        hovered: bool,
    ) -> None:
        x, y, w, h = int(rect.x), int(rect.y), int(rect.width), int(rect.height)

        # Sombra
        draw_rectangle(x + 4, y + 4, w, h, Color(0, 0, 0, 70))

        # Fondo + borde redondeado
        fill = self._tint(base_col, 1.06) if hovered else base_col
        try:
            draw_rectangle_rounded(Rectangle(x, y, w, h), 0.12, 8, fill)
            # 🔹 Quita el borde solo del escenario 2
            if index_number != 2:
                draw_rectangle_rounded_lines(Rectangle(x, y, w, h), 0.12, 8, 2, Color(30, 30, 30, 200))
        except Exception:
            draw_rectangle(x, y, w, h, fill)
            if index_number != 2:
                draw_rectangle_lines(x, y, w, h, Color(30, 30, 30, 200))


        # Borde de selección
        if selected:
            draw_rectangle_lines(x - 2, y - 2, w + 4, h + 4, Color(255, 220, 120, 255))

        # Padding interno
        pad = int(min(w, h) * 0.08)
        content = Rectangle(x + pad, y + pad, w - 2 * pad, h - 2 * pad)

        # Banda inferior para título (dentro de la tarjeta)
        title_h = int(max(28, h * 0.22))
        title_rect = Rectangle(content.x, content.y + content.height - title_h, content.width, title_h)
        shape_area = Rectangle(content.x, content.y, content.width, content.height - title_h - int(pad * 0.25))

        # Silueta (escenas 2–4) o rectángulo (escena 1)
        try:
            self.scene_images = [None] * self.total_scenes
            self.scene_images[1] = load_texture("Assets/plantilla_mundo_1.png")
        except Exception:
            self.scene_images = [None] * self.total_scenes

        # Badge con número (esquina sup. izq.)
        self._draw_badge_number(x + 12, y + 10, index_number)

        # Título centrado en la banda inferior
        self._draw_title_in_band(title_rect, title)

    # ======== Siluetas / Texto / Utilidades ========

    def _get_scene_polygon_points(self, scene_idx: int) -> List[Vector2]:
        """Convierte cualquier formato de puntos (tupla/list/Vector2/obj) en Vector2."""
        if scene_idx == 1:
            raw = zone2_alaska_polygon()
        elif scene_idx == 2:
            raw = zone3_ppr_polygon()
        elif scene_idx == 3:
            raw = zone4_michigan_polygon()
        else:
            return []

        pts: List[Vector2] = []
        for v in raw or []:
            try:
                # Vector2 u objeto con .x/.y
                x = float(v.x) if hasattr(v, "x") else float(v[0])
                y = float(v.y) if hasattr(v, "y") else float(v[1])
                pts.append(Vector2(x, y))
            except Exception:
                # Si algo raro, ignora ese vértice
                continue
        return pts

    def _draw_shape_silhouette(self, area: Rectangle, polygon_pts: List[Vector2], fill: Color, outline: Color) -> None:
        if not polygon_pts or len(polygon_pts) < 3:
            return

        # Bounds del polígono
        min_x = min(p.x for p in polygon_pts)
        max_x = max(p.x for p in polygon_pts)
        min_y = min(p.y for p in polygon_pts)
        max_y = max(p.y for p in polygon_pts)
        bw = max(1e-5, max_x - min_x)
        bh = max(1e-5, max_y - min_y)

        # Padding interno y escala
        pad = min(area.width, area.height) * 0.06
        avail_w = area.width - 2 * pad
        avail_h = area.height - 2 * pad
        scale = min(avail_w / bw, avail_h / bh)

        # Offset para centrar
        offset_x = area.x + (area.width - bw * scale) * 0.5 - min_x * scale
        offset_y = area.y + (area.height - bh * scale) * 0.5 - min_y * scale

        # Transformar a coords de pantalla
        pts: List[Vector2] = [Vector2(offset_x + p.x * scale, offset_y + p.y * scale) for p in polygon_pts]

        # Centroide
        cx = sum(pt.x for pt in pts) / len(pts)
        cy = sum(pt.y for pt in pts) / len(pts)
        c = Vector2(cx, cy)

        # Relleno con triangulación fan
        for i in range(1, len(pts) - 1):
            draw_triangle(c, pts[i], pts[i + 1], fill)

        # Contorno
        thickness = max(1.5, min(area.width, area.height) * 0.010)
        for i in range(len(pts)):
            a = pts[i]
            b = pts[(i + 1) % len(pts)]
            draw_line_ex(a, b, thickness, outline)

        # Sombreado sutil
        draw_circle(int(cx), int(cy), max(4.0, min(area.width, area.height) * 0.02), Color(0, 0, 0, 30))

    def _draw_badge_number(self, x: int, y: int, number: int) -> None:
        text = str(number)
        fs = 22
        w = max(28, measure_text(text, fs) + 12)
        h = 26
        try:
            draw_rectangle_rounded(Rectangle(x, y, w, h), 0.35, 8, Color(0, 0, 0, 110))
            draw_rectangle_rounded_lines(Rectangle(x, y, w, h), 0.35, 8, 2, Color(255, 255, 255, 40))
        except Exception:
            draw_rectangle(x, y, w, h, Color(0, 0, 0, 110))
            draw_rectangle_lines(x, y, w, h, Color(255, 255, 255, 40))
        draw_text(text, x + (w - measure_text(text, fs)) // 2, y + (h - fs) // 2, fs, Color(255, 255, 255, 240))

    def _draw_title_in_band(self, band: Rectangle, title: str) -> None:
        """Dibuja el título dentro de una banda inferior de la tarjeta (2 líneas máx)."""
        # Fondo banda
        draw_rectangle(int(band.x), int(band.y), int(band.width), int(band.height), Color(0, 0, 0, 100))

        max_w = int(band.width * 0.94)
        base_fs = max(14, int(band.height * 0.34))
        fs = base_fs
        while fs > 12 and self._lines_needed(title, fs, max_w) > 2:
            fs -= 1
        lines = self._wrap_text(title, fs, max_w, max_lines=2)

        total_h = len(lines) * (fs + 2)
        y0 = int(band.y + (band.height - total_h) // 2)
        for i, line in enumerate(lines):
            tw = measure_text(line, fs)
            draw_text(line, int(band.x + (band.width - tw) // 2), y0 + i * (fs + 2), fs, Color(245, 245, 245, 240))

    # =========== Utilidades de texto y color ===========

    def _wrap_text(self, text: str, fs: int, max_w: int, max_lines: int = 2) -> List[str]:
        words = text.split()
        lines: List[str] = []
        cur = ""
        for w in words:
            test = w if not cur else cur + " " + w
            if measure_text(test, fs) <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
                if len(lines) >= max_lines - 1:
                    break
        if cur and len(lines) < max_lines:
            lines.append(cur)
        # Truncado con “…” si queda texto fuera
        joined = " ".join(words).strip()
        shown = " ".join(lines).strip()
        if joined != shown and len(lines) >= max_lines:
            last = lines[-1]
            ell = "…"
            while last and measure_text(last + ell, fs) > max_w:
                last = last[:-1]
            lines[-1] = last + ell
        return lines

    def _lines_needed(self, text: str, fs: int, max_w: int) -> int:
        return len(self._wrap_text(text, fs, max_w, max_lines=999))

    def _tint(self, c: Color, factor: float) -> Color:
        r = int(max(0, min(255, c.r * factor)))
        g = int(max(0, min(255, c.g * factor)))
        b = int(max(0, min(255, c.b * factor)))
        return Color(r, g, b, c.a)
