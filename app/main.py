from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.models.schemas import ScenarioRequest
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


def to_bool(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in ["true", "1", "sim", "yes"]


@app.get("/")
def home():
    return {"msg": "BR Tax API rodando"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/simular")
def simular(payload: ScenarioRequest):
    try:
        # Normaliza booleans vindos do Agent Studio
        payload.contribuinte = to_bool(payload.contribuinte)
        payload.destinatario_final = to_bool(payload.destinatario_final)

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
            "diagram": f"https://br-tax-visual-api.onrender.com/outputs/{filename}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))