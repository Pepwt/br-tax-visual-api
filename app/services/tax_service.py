from app.utils.helpers import eh_interestadual


class TaxService:
    def calcular(self, payload, cfop_info):
        interestadual = eh_interestadual(payload.origem, payload.destino)

        difal = (
            payload.operacao.lower() == "venda"
            and interestadual
            and payload.destinatario_final
            and not payload.contribuinte
        )

        return {
            "cfop": cfop_info["cfop"],
            "descricao": cfop_info.get("descricao"),
            "concat_code": cfop_info.get("concat_code"),
            "difal": difal,
            "interestadual": interestadual
        }