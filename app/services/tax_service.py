class TaxService:
    def str_to_bool(self, valor):
        if isinstance(valor, bool):
            return valor
        return str(valor).strip().lower() in ["true", "1", "sim", "yes"]

    def eh_exterior(self, origem, destino):
        origem_n = str(origem).strip().lower()
        destino_n = str(destino).strip().lower()

        exterior_vals = {
            "exterior", "outside", "outside brazil",
            "fora do brasil", "importacao", "importação",
            "exportacao", "exportação"
        }

        return origem_n in exterior_vals or destino_n in exterior_vals

    def calcular(self, payload, cfop_info):
        operacao = str(payload.operacao).strip().lower()
        origem = str(payload.origem).strip().upper()
        destino = str(payload.destino).strip().upper()

        destinatario_contribuinte = self.str_to_bool(payload.contribuinte)
        destinatario_final = self.str_to_bool(payload.destinatario_final)

        exterior = self.eh_exterior(origem, destino)
        interestadual = (origem != destino) and not exterior

        difal = (
            operacao == "venda"
            and interestadual
            and destinatario_final
            and not destinatario_contribuinte
        )

        explicacao = []

        if exterior:
            explicacao.append("Operação classificada como exterior.")
        elif interestadual:
            explicacao.append("Operação classificada como interestadual.")
        else:
            explicacao.append("Operação classificada como intraestadual.")

        if difal:
            explicacao.append("Há incidência potencial de DIFAL por se tratar de venda interestadual para destinatário final não contribuinte.")
        else:
            explicacao.append("Não há incidência de DIFAL pela regra simplificada do motor atual.")

        return {
            "cfop": cfop_info.get("cfop"),
            "descricao": cfop_info.get("descricao"),
            "concat_code": cfop_info.get("concat_code"),
            "difal": difal,
            "interestadual": interestadual,
            "exterior": exterior,
            "destinatario_contribuinte": destinatario_contribuinte,
            "destinatario_final": destinatario_final,
            "explicacao_fiscal": " ".join(explicacao)
        }