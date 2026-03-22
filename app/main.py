from fastapi import FastAPI
from app.models.schemas import ScenarioRequest
from app.services.cfop_service import CFOPService
from app.services.tax_service import TaxService
from app.services.diagram_service import DiagramService
from uuid import uuid4
from fastapi.staticfiles import StaticFiles


app = FastAPI()

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

cfop_service = CFOPService()
tax_service = TaxService()
diagram_service = DiagramService()


@app.get("/")
def home():
    return {"msg": "BR Tax API rodando "}


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
        "diagram": f"http://127.0.0.1:8000/outputs/{filename}"
    }