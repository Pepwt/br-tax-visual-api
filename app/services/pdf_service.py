from reportlab.pdfgen import canvas


class PdfService:
    def gerar(self, payload, filename):
        c = canvas.Canvas(f"outputs/{filename}")

        c.drawString(50, 800, payload.titulo)
        c.drawString(50, 750, payload.pergunta)
        c.drawString(50, 700, payload.resposta)

        c.save()