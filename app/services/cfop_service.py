from pathlib import Path
import pandas as pd


class CFOPService:
    def __init__(self, file_path: str | None = None):
        # raiz do projeto: .../br-tax-visual-api
        project_root = Path(__file__).resolve().parents[2]

        if file_path:
            self.file_path = Path(file_path)
        else:
            self.file_path = project_root / "cfop.xlsx"

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

        return df

    def buscar_por_operacao(self, operacao: str):
        df = self.carregar_excel()
        trx = "PURCHASE" if operacao.lower() == "compra" else "SALES"
        return df[df["TRX_TYPE"] == trx].copy()

    def sugerir_cfop(self, operacao, finalidade, origem, destino):
        df = self.buscar_por_operacao(operacao)

        interestadual = origem.strip().upper() != destino.strip().upper()

        if operacao.lower() == "compra":
            prefixo = "2" if interestadual else "1"
        else:
            prefixo = "6" if interestadual else "5"

        df = df[df["CFOP"].str.startswith(prefixo)].copy()

        finalidade = finalidade.lower().strip()

        if finalidade == "revenda":
            palavras = ["comercialização", "comercializacao"]
        elif finalidade == "consumo":
            palavras = ["consumo", "uso"]
        elif finalidade == "ativo":
            palavras = ["ativo imobilizado"]
        elif finalidade == "industrializacao":
            palavras = ["industrialização", "industrializacao", "produção", "producao"]
        else:
            palavras = []

        if palavras:
            filtrado = df[df["CLASS_NAME"].str.lower().apply(
                lambda x: any(p in x for p in palavras)
            )]
            if not filtrado.empty:
                df = filtrado

        if not df.empty:
            row = df.iloc[0]
            return {
                "cfop": row["CFOP"],
                "descricao": row["CLASS_NAME"],
                "concat_code": row["CONCAT_CODE"]
            }

        return {
            "cfop": "N/A",
            "descricao": "Nenhum CFOP encontrado",
            "concat_code": ""
        }