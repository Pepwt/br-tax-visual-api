class TaxService:
    def str_to_bool(self, valor):
        if isinstance(valor, bool):
            return valor
        return str(valor).strip().lower() in ["true", "1", "sim", "yes"]

    def calcular(self, payload, cfop_info):
        contribuinte = self.str_to_bool(payload.contribuinte)
        destinatario_final = self.str_to_bool(payload.destinatario_final)

        interestadual = payload.origem.strip().upper() != payload.destino.strip().upper()

        difal = (
            payload.operacao.lower() == "venda"
            and interestadual
            and destinatario_final
            and not contribuinte
        )

        return {
            "cfop": cfop_info.get("cfop"),
            "descricao": cfop_info.get("descricao"),
            "concat_code": cfop_info.get("concat_code"),
            "difal": difal,
            "interestadual": interestadual
        }