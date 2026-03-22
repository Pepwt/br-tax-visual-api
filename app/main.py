from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.models.schemas import ScenarioRequest
from app.services.cfop_service import CFOPService
from app.services.tax_service import TaxService
from app.services.diagram_service import DiagramService
from uuid import uuid4

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

cfop_service = CFOPService()
tax_service = TaxService()
diagram_service = DiagramService()


@app.get("/")
def home():
    return {"msg": "BR Tax API rodando"}


@app.post("/simular")
def simular(payload: ScenarioRequest):
    cfop = cfop_service.sugerir_cfop(
        payload.operacao,
        payload.finalidade,
        payload.origem,
        payload.destino
    )

    resultado = tax_service.calcular(payload, cfop)

    filename = f"{uuid4().hex}.png"
    diagram_service.gerar(payload, resultado, filename)

    return {
        "resultado": resultado,
        "diagram": f"https://br-tax-visual-api.onrender.com/outputs/{filename}"
    }