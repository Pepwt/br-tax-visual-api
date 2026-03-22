from pydantic import BaseModel, Field
from typing import Optional


class ScenarioRequest(BaseModel):
    operacao: str = Field(..., description="compra ou venda")
    origem: str = Field(..., description="UF de origem, ex: SP")
    destino: str = Field(..., description="UF de destino, ex: RJ")
    finalidade: str = Field(..., description="consumo, revenda, industrializacao, ativo")
    contribuinte: bool | str = Field(..., description='true/false ou "true"/"false"')
    destinatario_final: bool | str = Field(..., description='true/false ou "true"/"false"')
    observacao: Optional[str] = Field(default=None)

    model_config = {
        "extra": "ignore"
    }