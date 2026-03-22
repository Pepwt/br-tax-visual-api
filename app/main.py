from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles

from app.services.cfop_service import CFOPService
from app.services.tax_service import TaxService
from app.services.diagram_service import DiagramService


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="BR Tax API", version="1.0.0")
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

cfop_service = CFOPService()
tax_service = TaxService()
diagram_service = DiagramService()


def to_bool(valor, default=False) -> bool:
    if valor is None:
        return default
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in ["true", "1", "sim", "yes"]


class SimplePayload:
    def __init__(self, data: dict):
        self.operacao = str(data.get("operacao", "compra")).strip().lower()
        self.origem = str(data.get("origem", "SP")).strip().upper()
        self.destino = str(data.get("destino", "RJ")).strip().upper()
        self.finalidade = str(data.get("finalidade", "consumo")).strip().lower()
        self.contribuinte = to_bool(data.get("contribuinte", True), True)
        self.destinatario_final = to_bool(data.get("destinatario_final", True), True)
        self.observacao = str(data.get("observacao", "gerado automaticamente")).strip()


@app.get("/")
def home():
    return {"msg": "BR Tax API rodando"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/simular")
async def simular(request: Request):
    try:
        data = await request.json()

        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="O corpo da requisição deve ser um JSON object.")

        payload = SimplePayload(data)

        cfop_info = cfop_service.sugerir_cfop(
            payload.operacao,
            payload.finalidade,
            payload.origem,
            payload.destino
        )

        resultado = tax_service.calcular(payload, cfop_info)

        filename = f"{uuid4().hex}.png"
        diagram_service.gerar(payload, resultado, filename)

        return {
            "cfop": resultado.get("cfop"),
            "difal": resultado.get("difal"),
            "descricao": resultado.get("descricao"),
            "concat_code": resultado.get("concat_code"),
            "interestadual": resultado.get("interestadual"),
            "exterior": resultado.get("exterior"),
            "explicacao_fiscal": resultado.get("explicacao_fiscal"),
            "diagram": f"https://br-tax-visual-api.onrender.com/outputs/{filename}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))