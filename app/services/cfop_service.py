from pathlib import Path
import pandas as pd


class CFOPService:
    def __init__(self, file_path: str | None = None):
        project_root = Path(__file__).resolve().parents[2]
        self.file_path = Path(file_path) if file_path else project_root / "cfop.xlsx"

    def carregar_excel(self):
        if not self.file_path.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {self.file_path}\n"
                f"Coloque o arquivo cfop.xlsx na raiz do projeto."
            )

        df = pd.read_excel(self.file_path, header=1)
        df.columns = [str(c).strip().upper() for c in df.columns]

        colunas_esperadas = {"CFOP", "CONCAT_CODE", "CLASS_NAME", "TRX_TYPE"}
        faltando = colunas_esperadas - set(df.columns)
        if faltando:
            raise ValueError(
                f"O Excel não possui as colunas esperadas. Faltando: {', '.join(sorted(faltando))}"
            )

        df["CFOP"] = df["CFOP"].astype(str).str.strip()
        df["TRX_TYPE"] = df["TRX_TYPE"].astype(str).str.upper().str.strip()
        df["CLASS_NAME"] = df["CLASS_NAME"].astype(str).str.strip()
        df["CONCAT_CODE"] = df["CONCAT_CODE"].astype(str).str.strip()

        # remove linhas inválidas
        df = df[df["CFOP"] != ""].copy()

        return df

    def buscar_por_operacao(self, operacao: str):
        df = self.carregar_excel()
        trx = "PURCHASE" if operacao.lower().strip() == "compra" else "SALES"
        return df[df["TRX_TYPE"] == trx].copy()

    def _normalizar(self, valor: str) -> str:
        return str(valor).strip().lower()

    def _eh_exterior(self, origem: str, destino: str) -> bool:
        origem_n = self._normalizar(origem)
        destino_n = self._normalizar(destino)

        palavras_exterior = {
            "exterior", "outside", "outside brazil", "fora do brasil", "importacao", "importação", "exportacao", "exportação"
        }

        return origem_n in palavras_exterior or destino_n in palavras_exterior

    def _determinar_prefixo(self, operacao: str, origem: str, destino: str) -> str:
        operacao_n = self._normalizar(operacao)

        if self._eh_exterior(origem, destino):
            return "3" if operacao_n == "compra" else "7"

        interestadual = origem.strip().upper() != destino.strip().upper()

        if operacao_n == "compra":
            return "2" if interestadual else "1"
        return "6" if interestadual else "5"

    def _palavras_por_finalidade(self, finalidade: str) -> list[str]:
        finalidade_n = self._normalizar(finalidade)

        mapa = {
            "revenda": [
                "comercialização",
                "comercializacao",
                "revenda"
            ],
            "consumo": [
                "uso ou consumo",
                "uso",
                "consumo",
                "energia elétrica",
                "energia eletrica"
            ],
            "ativo": [
                "ativo imobilizado",
                "imobilizado"
            ],
            "industrializacao": [
                "industrialização",
                "industrializacao",
                "produção",
                "producao",
                "insumo"
            ],
            "industrialização": [
                "industrialização",
                "industrializacao",
                "produção",
                "producao",
                "insumo"
            ],
            "exterior": [
                "importação",
                "importacao",
                "exportação",
                "exportacao",
                "exterior"
            ]
        }

        return mapa.get(finalidade_n, [])

    def _score_linha(self, class_name: str, palavras: list[str]) -> int:
        texto = self._normalizar(class_name)
        score = 0

        for palavra in palavras:
            if palavra in texto:
                score += 1

        return score

    def sugerir_cfop(self, operacao, finalidade, origem, destino):
        df = self.buscar_por_operacao(operacao)
        prefixo = self._determinar_prefixo(operacao, origem, destino)

        candidatos = df[df["CFOP"].str.startswith(prefixo)].copy()

        if candidatos.empty:
            return {
                "cfop": "N/A",
                "descricao": f"Nenhum CFOP encontrado para o grupo {prefixo}.xxx",
                "concat_code": ""
            }

        palavras = self._palavras_por_finalidade(finalidade)

        if self._eh_exterior(origem, destino):
            palavras = list(set(palavras + ["exterior", "importação", "importacao", "exportação", "exportacao"]))

        if palavras:
            candidatos["SCORE"] = candidatos["CLASS_NAME"].apply(lambda x: self._score_linha(x, palavras))
            melhores = candidatos[candidatos["SCORE"] > 0].copy()

            if not melhores.empty:
                candidatos = melhores.sort_values(by=["SCORE", "CFOP"], ascending=[False, True]).copy()
            else:
                candidatos = candidatos.sort_values(by="CFOP").copy()
        else:
            candidatos = candidatos.sort_values(by="CFOP").copy()

        row = candidatos.iloc[0]

        return {
            "cfop": row["CFOP"],
            "descricao": row["CLASS_NAME"],
            "concat_code": row["CONCAT_CODE"]
        }