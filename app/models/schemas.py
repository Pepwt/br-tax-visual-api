from pydantic import BaseModel
from typing import Optional, Dict, Any


class ScenarioRequest(BaseModel):
    operacao: str
    origem: str
    destino: str
    finalidade: str
    contribuinte: bool | str
    destinatario_final: bool | str
    observacao: Optional[str] = None


class DiagramResponse(BaseModel):
    status: str
    image_url: str
    resultado: Dict[str, Any]


class PdfRequest(BaseModel):
    titulo: str
    pergunta: str
    resposta: str
    image_url: Optional[str] = None


class PdfResponse(BaseModel):
    status: str
    pdf_url: str