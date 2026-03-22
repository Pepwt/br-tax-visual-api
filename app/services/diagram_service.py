from pathlib import Path
from uuid import uuid4
from PIL import Image, ImageDraw, ImageFont


class DiagramService:
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.colors = {
            "bg": "#F7F9FC",
            "title": "#1F2937",
            "lane_fill": "#EAF2FB",
            "lane_line": "#D1D9E6",
            "box_origin": "#DCEBFA",
            "box_fusion": "#D9EAD3",
            "box_tax": "#FCE5CD",
            "box_fiscal": "#F9CB9C",
            "box_output": "#D9D2E9",
            "decision": "#1E63D6",
            "decision_text": "#FFFFFF",
            "start_end": "#66B2FF",
            "text": "#1F2937",
            "line": "#3A4A5A",
            "white": "#FFFFFF"
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
            test = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines

    def _draw_box(self, draw, x1, y1, x2, y2, text, fill, outline=None, radius=16, font_size=18, bold=False):
        outline = outline or self.colors["line"]
        draw.rounded_rectangle((x1, y1, x2, y2), radius=radius, fill=fill, outline=outline, width=2)

        font = self._get_font(font_size, bold=bold)
        max_width = (x2 - x1) - 26
        lines = self._wrap_text(draw, text, font, max_width)

        line_height = font_size + 6
        total_height = len(lines) * line_height
        y_text = y1 + ((y2 - y1) - total_height) / 2

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_text = x1 + ((x2 - x1) - text_width) / 2
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
        lines = self._wrap_text(draw, text, font, w - 30)
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
        draw.rectangle((x1, y1, x2, y2), fill=self.colors["bg"], outline=self.colors["lane_line"], width=2)
        draw.rectangle((x1, y1, x1 + 220, y2), fill=self.colors["lane_fill"], outline=self.colors["lane_line"], width=2)

        font = self._get_font(20, bold=True)
        bbox = draw.textbbox((0, 0), title, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((x1 + 110 - tw / 2, ((y1 + y2) / 2) - th / 2), title, fill=self.colors["text"], font=font)

    def gerar(self, payload, resultado, filename=None):
        if filename is None:
            filename = f"diagram_{uuid4().hex}.png"

        image_path = self.output_dir / filename

        width, height = 1800, 1300
        img = Image.new("RGB", (width, height), self.colors["bg"])
        draw = ImageDraw.Draw(img)

        # Header
        draw.rounded_rectangle((20, 20, 1780, 140), radius=20, fill="#8EC5FC", outline="#5B9EEA", width=2)
        title_font = self._get_font(40, bold=True)
        subtitle_font = self._get_font(18)

        draw.text((60, 45), "BR Tax Enterprise Process Flow", fill="#0F172A", font=title_font)
        subtitle = (
            f"Operação: {payload.operacao.upper()} | "
            f"{payload.origem.upper()} → {payload.destino.upper()} | "
            f"Finalidade: {payload.finalidade.upper()} | "
            f"CFOP sugerido: {resultado['cfop']}"
        )
        draw.text((60, 100), subtitle, fill="#0F172A", font=subtitle_font)

        # Lanes
        lanes = {
            "origem": (20, 180, 1780, 380),
            "fusion": (20, 390, 1780, 590),
            "tax": (20, 600, 1780, 800),
            "fiscal": (20, 810, 1780, 1010),
            "output": (20, 1020, 1780, 1230),
        }

        self._draw_lane(draw, *lanes["origem"], "Origem da\nTransação")
        self._draw_lane(draw, *lanes["fusion"], "Oracle\nFusion")
        self._draw_lane(draw, *lanes["tax"], "Tax Engine /\nLACLS")
        self._draw_lane(draw, *lanes["fiscal"], "Fiscal\nDetermination")
        self._draw_lane(draw, *lanes["output"], "Output /\nAccounting")

        # Lane origem
        self._draw_circle(draw, 320, 280, 42, "Início")
        self._draw_box(draw, 430, 235, 730, 325, "Criar transação\n(Invoice / PO / Shipment)", self.colors["box_origin"])
        self._draw_arrow(draw, 362, 280, 430, 280)

        # Lane fusion
        self._draw_box(draw, 430, 445, 730, 535, "Submeter transação\nno Oracle Fusion", self.colors["box_fusion"])
        self._draw_arrow(draw, 580, 325, 580, 445)

        self._draw_box(draw, 860, 445, 1160, 535, "Call ZX Tax Engine", self.colors["box_fusion"])
        self._draw_arrow(draw, 730, 490, 860, 490)

        # Lane tax
        self._draw_box(draw, 430, 655, 730, 745, "Avaliar regime fiscal\ne jurisdição", self.colors["box_tax"])
        self._draw_arrow(draw, 1010, 535, 1010, 620)
        draw.line((1010, 620, 580, 620), fill=self.colors["line"], width=3)
        self._draw_arrow(draw, 580, 620, 580, 655)

        self._draw_diamond(draw, 980, 700, 190, 120, "Interestadual?")
        self._draw_arrow(draw, 730, 700, 885, 700)

        self._draw_box(draw, 1180, 645, 1480, 735, f"Fluxo {'interestadual' if resultado['interestadual'] else 'interno'}\n{payload.origem.upper()} → {payload.destino.upper()}", self.colors["box_tax"])
        self._draw_arrow(draw, 1075, 700, 1180, 700, label="Sim" if resultado["interestadual"] else "Não")

        # Lane fiscal
        self._draw_diamond(draw, 520, 910, 190, 120, "Contribuinte?")
        self._draw_arrow(draw, 1330, 735, 1330, 855)
        draw.line((1330, 855, 520, 855), fill=self.colors["line"], width=3)
        self._draw_arrow(draw, 520, 855, 520, 850)

        self._draw_box(draw, 700, 865, 980, 955, f"Finalidade\n{payload.finalidade.capitalize()}", self.colors["box_fiscal"])
        self._draw_arrow(draw, 615, 910, 700, 910, label="Sim" if payload.contribuinte else "Não")

        self._draw_box(draw, 1080, 865, 1380, 955, f"Determinar CFOP\n{resultado['cfop']}", self.colors["box_fiscal"])
        self._draw_arrow(draw, 980, 910, 1080, 910)

        difal_texto = "Aplica DIFAL" if resultado["difal"] else "Não aplica DIFAL"
        self._draw_box(draw, 1460, 865, 1720, 955, difal_texto, "#FDE68A")
        self._draw_arrow(draw, 1380, 910, 1460, 910)

        # Lane output
        descricao = resultado.get("descricao", "Sem descrição")
        self._draw_box(draw, 340, 1070, 760, 1180, f"Gerar FDG / Documento Fiscal\n{descricao}", self.colors["box_output"])
        self._draw_arrow(draw, 1210, 955, 1210, 1025)
        draw.line((1210, 1025, 550, 1025), fill=self.colors["line"], width=3)
        self._draw_arrow(draw, 550, 1025, 550, 1070)

        self._draw_box(draw, 860, 1070, 1200, 1180, "Post Accounting /\nEscrituração", self.colors["box_output"])
        self._draw_arrow(draw, 760, 1125, 860, 1125)

        self._draw_circle(draw, 1380, 1125, 42, "Fim")
        self._draw_arrow(draw, 1200, 1125, 1338, 1125)

        img.save(image_path)
        return str(image_path)