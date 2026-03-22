from pathlib import Path
from uuid import uuid4
from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class DiagramService:
    def __init__(self, output_dir: str | None = None):
        self.output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.colors = {
            "bg": "#F5F7FA",
            "header": "#79AEE3",
            "header_border": "#5C95D1",
            "lane_fill": "#EEF3F8",
            "lane_label_fill": "#DFE8F2",
            "lane_border": "#C8D3E0",
            "box_origin": "#DCEBFA",
            "box_fusion": "#DDECD6",
            "box_tax": "#F7E1C8",
            "box_fiscal": "#F7D1A6",
            "box_output": "#DDD7EF",
            "box_difal": "#F6E08A",
            "decision": "#1E63D6",
            "decision_text": "#FFFFFF",
            "start_end": "#69AEEF",
            "line": "#394B5A",
            "text": "#1F2937",
            "white": "#FFFFFF",
        }

    def _get_font(self, size: int = 18, bold: bool = False):
        try:
            if bold:
                return ImageFont.truetype("arialbd.ttf", size)
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()

    def _wrap_text(self, draw, text, font, max_width):
        words = text.split()
        lines = []
        current = ""

        for word in words:
            candidate = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines

    def _draw_box(self, draw, x1, y1, x2, y2, text, fill, radius=18, font_size=18, bold=False):
        draw.rounded_rectangle(
            (x1, y1, x2, y2),
            radius=radius,
            fill=fill,
            outline=self.colors["line"],
            width=2
        )

        font = self._get_font(font_size, bold=bold)
        max_width = (x2 - x1) - 24
        lines = self._wrap_text(draw, text, font, max_width)

        line_height = font_size + 6
        total_height = len(lines) * line_height
        y_text = y1 + ((y2 - y1) - total_height) / 2

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            x_text = x1 + ((x2 - x1) - tw) / 2
            draw.text((x_text, y_text), line, fill=self.colors["text"], font=font)
            y_text += line_height

    def _draw_diamond(self, draw, cx, cy, w, h, text):
        points = [
            (cx, cy - h // 2),
            (cx + w // 2, cy),
            (cx, cy + h // 2),
            (cx - w // 2, cy),
        ]
        draw.polygon(points, fill=self.colors["decision"], outline=self.colors["line"])

        font = self._get_font(16, bold=True)
        lines = self._wrap_text(draw, text, font, w - 28)

        line_height = 20
        total_height = len(lines) * line_height
        y_text = cy - total_height / 2

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            draw.text((cx - tw / 2, y_text), line, fill=self.colors["decision_text"], font=font)
            y_text += line_height

    def _draw_circle(self, draw, cx, cy, radius, text):
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            fill=self.colors["start_end"],
            outline=self.colors["line"],
            width=2
        )
        font = self._get_font(16, bold=True)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((cx - tw / 2, cy - th / 2), text, fill=self.colors["white"], font=font)

    def _draw_arrow(self, draw, x1, y1, x2, y2, label=None):
        draw.line((x1, y1, x2, y2), fill=self.colors["line"], width=3)

        if y2 > y1:
            arrow = [(x2, y2), (x2 - 8, y2 - 12), (x2 + 8, y2 - 12)]
        elif x2 > x1:
            arrow = [(x2, y2), (x2 - 12, y2 - 8), (x2 - 12, y2 + 8)]
        elif x2 < x1:
            arrow = [(x2, y2), (x2 + 12, y2 - 8), (x2 + 12, y2 + 8)]
        else:
            arrow = [(x2, y2), (x2 - 8, y2 + 12), (x2 + 8, y2 + 12)]

        draw.polygon(arrow, fill=self.colors["line"])

        if label:
            font = self._get_font(14, bold=True)
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            draw.text((mx + 8, my - 18), label, fill=self.colors["text"], font=font)

    def _draw_lane(self, draw, x1, y1, x2, y2, title):
        draw.rectangle((x1, y1, x2, y2), fill=self.colors["lane_fill"], outline=self.colors["lane_border"], width=2)
        draw.rectangle((x1, y1, x1 + 180, y2), fill=self.colors["lane_label_fill"], outline=self.colors["lane_border"], width=2)

        font = self._get_font(20, bold=True)
        lines = title.split("\n")
        line_height = 26
        total_height = len(lines) * line_height
        y_text = ((y1 + y2) / 2) - total_height / 2

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            draw.text((x1 + 90 - tw / 2, y_text), line, fill=self.colors["text"], font=font)
            y_text += line_height

    def _sanitize(self, value):
        if value is None:
            return ""
        return str(value).replace("$", "").strip()

    def gerar(self, payload, resultado, filename=None):
        if filename is None:
            filename = f"diagram_{uuid4().hex}.png"

        image_path = self.output_dir / filename

        operacao = self._sanitize(payload.operacao).upper()
        origem = self._sanitize(payload.origem).upper()
        destino = self._sanitize(payload.destino).upper()
        finalidade = self._sanitize(payload.finalidade).capitalize()
        cfop = self._sanitize(resultado.get("cfop", "N/A"))
        descricao = self._sanitize(resultado.get("descricao", "Sem descrição"))
        interestadual = bool(resultado.get("interestadual", False))
        difal = bool(resultado.get("difal", False))

        width, height = 1800, 1280
        img = Image.new("RGB", (width, height), self.colors["bg"])
        draw = ImageDraw.Draw(img)

        # Header
        draw.rounded_rectangle(
            (20, 20, 1780, 140),
            radius=22,
            fill=self.colors["header"],
            outline=self.colors["header_border"],
            width=2
        )

        title_font = self._get_font(34, bold=True)
        sub_font = self._get_font(18)

        draw.text((60, 40), "BR Tax Enterprise Process Flow", fill=self.colors["text"], font=title_font)
        subtitle = f"Operação: {operacao} | Origem: {origem} → Destino: {destino} | Finalidade: {finalidade} | CFOP Sugerido: {cfop}"
        draw.text((60, 95), subtitle, fill=self.colors["text"], font=sub_font)

        # Lanes
        self._draw_lane(draw, 20, 180, 1780, 380, "Origem da\nTransação")
        self._draw_lane(draw, 20, 390, 1780, 590, "Oracle\nFusion")
        self._draw_lane(draw, 20, 600, 1780, 800, "Tax Engine /\nLACLS")
        self._draw_lane(draw, 20, 810, 1780, 1010, "Fiscal\nDetermination")
        self._draw_lane(draw, 20, 1020, 1780, 1230, "Output /\nAccounting")

        # Origem
        self._draw_circle(draw, 300, 280, 42, "Início")
        self._draw_box(
            draw, 410, 235, 760, 325,
            "Criar Transação\n(Invoice / Purchase Order / Shipment)",
            self.colors["box_origin"]
        )
        self._draw_arrow(draw, 342, 280, 410, 280)

        # Fusion
        self._draw_box(
            draw, 410, 445, 760, 535,
            "Submeter Transação\nno Oracle Fusion",
            self.colors["box_fusion"]
        )
        self._draw_arrow(draw, 585, 325, 585, 445)

        self._draw_box(
            draw, 900, 445, 1240, 535,
            "Executar BR Tax Engine\n(Simulação Fiscal)",
            self.colors["box_fusion"]
        )
        self._draw_arrow(draw, 760, 490, 900, 490)

        # Tax / LACLS
        self._draw_box(
            draw, 410, 655, 760, 745,
            "Avaliar Regime Fiscal\ne Jurisdição",
            self.colors["box_tax"]
        )
        self._draw_arrow(draw, 1070, 535, 1070, 620)
        draw.line((1070, 620, 585, 620), fill=self.colors["line"], width=3)
        self._draw_arrow(draw, 585, 620, 585, 655)

        self._draw_diamond(draw, 1020, 700, 210, 120, "Operação\nInterestadual?")
        self._draw_arrow(draw, 760, 700, 915, 700)

        self._draw_box(
            draw, 1240, 650, 1560, 740,
            f"{'Aplicar Regras Interestaduais' if interestadual else 'Fluxo Interno'}\n{origem} → {destino}",
            self.colors["box_tax"]
        )
        self._draw_arrow(draw, 1125, 700, 1240, 700, label="Sim" if interestadual else "Não")

        # Fiscal determination
        self._draw_diamond(draw, 470, 910, 210, 120, "Destinatário é\nContribuinte?")
        self._draw_arrow(draw, 1400, 740, 1400, 855)
        draw.line((1400, 855, 470, 855), fill=self.colors["line"], width=3)
        self._draw_arrow(draw, 470, 855, 470, 850)

        self._draw_box(
            draw, 670, 865, 980, 955,
            f"Finalidade:\n{finalidade}",
            self.colors["box_fiscal"]
        )
        self._draw_arrow(draw, 575, 910, 670, 910, label="Sim" if bool(payload.contribuinte) else "Não")

        self._draw_box(
            draw, 1060, 865, 1370, 955,
            f"Determinar CFOP\n{cfop}",
            self.colors["box_fiscal"]
        )
        self._draw_arrow(draw, 980, 910, 1060, 910)

        self._draw_box(
            draw, 1450, 865, 1710, 955,
            "Aplica DIFAL" if difal else "Não Aplica DIFAL",
            self.colors["box_difal"]
        )
        self._draw_arrow(draw, 1370, 910, 1450, 910)

        # Output
        self._draw_box(
            draw, 320, 1070, 820, 1185,
            f"Gerar Documento Fiscal (NF-e) via FDG\n{descricao}",
            self.colors["box_output"],
            font_size=16
        )
        self._draw_arrow(draw, 1215, 955, 1215, 1025)
        draw.line((1215, 1025, 570, 1025), fill=self.colors["line"], width=3)
        self._draw_arrow(draw, 570, 1025, 570, 1070)

        self._draw_box(
            draw, 920, 1070, 1260, 1185,
            "Post Accounting\n(Escrituração Contábil)",
            self.colors["box_output"]
        )
        self._draw_arrow(draw, 820, 1127, 920, 1127)

        self._draw_circle(draw, 1420, 1127, 42, "Fim")
        self._draw_arrow(draw, 1260, 1127, 1378, 1127)

        img.save(image_path)
        return str(image_path)