class TaxService:

    def str_to_bool(self, valor):
        return str(valor).strip().lower() in ["true", "1", "sim", "yes"]

    def calcular(self, payload, cfop):

        contribuinte = self.str_to_bool(payload.contribuinte)
        destinatario_final = self.str_to_bool(payload.destinatario_final)

        difal = False

        if contribuinte and not destinatario_final:
            difal = True

        return {
            "cfop": cfop,
            "difal": difal,
            "descricao": "Simulação fiscal baseada no cenário informado",
            "regras_aplicadas": {
                "contribuinte": contribuinte,
                "destinatario_final": destinatario_final
            }
        }