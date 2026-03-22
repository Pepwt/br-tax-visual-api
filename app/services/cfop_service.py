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

        df = df[["CFOP", "CONCAT_CODE", "CLASS_NAME", "TRX_TYPE"]].copy()

        df["CFOP"] = df["CFOP"].astype(str).str.strip()
        df["CONCAT_CODE"] = df["CONCAT_CODE"].astype(str).str.strip()
        df["CLASS_NAME"] = df["CLASS_NAME"].astype(str).str.strip()
        df["TRX_TYPE"] = df["TRX_TYPE"].astype(str).str.upper().str.strip()

        # remove linhas inválidas
        df = df[df["CFOP"] != ""].copy()
        df = df[df["TRX_TYPE"].isin(["PURCHASE", "SALES"])].copy()

        return df

    def _normalizar(self, valor: str) -> str:
        return str(valor).strip().lower()

    def _eh_exterior(self, origem: str, destino: str) -> bool:
        origem_n = self._normalizar(origem)
        destino_n = self._normalizar(destino)

        palavras_exterior = {
            "exterior",
            "outside",
            "outside brazil",
            "fora do brasil",
            "importacao",
            "importação",
            "exportacao",
            "exportação",
        }

        return origem_n in palavras_exterior or destino_n in palavras_exterior

    def _determinar_prefixo(self, operacao: str, origem: str, destino: str) -> str:
        operacao_n = self._normalizar(operacao)

        if self._eh_exterior(origem, destino):
            return "3" if operacao_n == "compra" else "7"

        interestadual = str(origem).strip().upper() != str(destino).strip().upper()

        if operacao_n == "compra":
            return "2" if interestadual else "1"

        return "6" if interestadual else "5"

    def _palavras_por_finalidade(self, finalidade: str) -> list[str]:
        finalidade_n = self._normalizar(finalidade)

        mapa = {
            "revenda": [
                "comercialização",
                "comercializacao",
                "revenda",
                "comercial"
            ],
            "consumo": [
                "uso ou consumo",
                "uso",
                "consumo",
                "energia elétrica",
                "energia eletrica",
                "material para uso",
                "material de consumo"
            ],
            "ativo": [
                "ativo imobilizado",
                "imobilizado",
                "bem para o ativo"
            ],
            "industrializacao": [
                "industrialização",
                "industrializacao",
                "produção",
                "producao",
                "insumo",
                "matéria-prima",
                "materia-prima",
                "processo produtivo"
            ],
            "industrialização": [
                "industrialização",
                "industrializacao",
                "produção",
                "producao",
                "insumo",
                "matéria-prima",
                "materia-prima",
                "processo produtivo"
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

    def buscar_por_operacao(self, operacao: str):
        df = self.carregar_excel()
        trx = "PURCHASE" if self._normalizar(operacao) == "compra" else "SALES"
        return df[df["TRX_TYPE"] == trx].copy()

    def _fallback_cfop(self, operacao: str, prefixo: str, finalidade: str):
        operacao_n = self._normalizar(operacao)
        finalidade_n = self._normalizar(finalidade)

        fallbacks = {
            ("compra", "1", "consumo"): ("1556", "Compra de material para uso ou consumo"),
            ("compra", "1", "revenda"): ("1102", "Compra para comercialização"),
            ("compra", "1", "ativo"): ("1551", "Compra de bem para o ativo imobilizado"),
            ("compra", "1", "industrializacao"): ("1101", "Compra para industrialização"),

            ("compra", "2", "consumo"): ("2556", "Compra de material para uso ou consumo"),
            ("compra", "2", "revenda"): ("2102", "Compra para comercialização"),
            ("compra", "2", "ativo"): ("2551", "Compra de bem para o ativo imobilizado"),
            ("compra", "2", "industrializacao"): ("2101", "Compra para industrialização"),

            ("compra", "3", "consumo"): ("3556", "Compra de material para uso ou consumo do exterior"),
            ("compra", "3", "revenda"): ("3102", "Compra para comercialização do exterior"),
            ("compra", "3", "ativo"): ("3551", "Compra de bem para o ativo imobilizado do exterior"),
            ("compra", "3", "industrializacao"): ("3101", "Compra para industrialização do exterior"),

            ("venda", "5", "consumo"): ("5101", "Venda de produção do estabelecimento"),
            ("venda", "5", "revenda"): ("5102", "Venda de mercadoria adquirida ou recebida de terceiros"),
            ("venda", "5", "ativo"): ("5551", "Venda de bem do ativo imobilizado"),
            ("venda", "5", "industrializacao"): ("5101", "Venda de produção do estabelecimento"),

            ("venda", "6", "consumo"): ("6101", "Venda de produção do estabelecimento"),
            ("venda", "6", "revenda"): ("6102", "Venda de mercadoria adquirida ou recebida de terceiros"),
            ("venda", "6", "ativo"): ("6551", "Venda de bem do ativo imobilizado"),
            ("venda", "6", "industrializacao"): ("6101", "Venda de produção do estabelecimento"),

            ("venda", "7", "consumo"): ("7101", "Venda de produção do estabelecimento para o exterior"),
            ("venda", "7", "revenda"): ("7102", "Venda de mercadoria adquirida ou recebida de terceiros para o exterior"),
            ("venda", "7", "ativo"): ("7551", "Venda de bem do ativo imobilizado para o exterior"),
            ("venda", "7", "industrializacao"): ("7101", "Venda de produção do estabelecimento para o exterior"),
        }

        chave = (operacao_n, prefixo, finalidade_n)

        if chave in fallbacks:
            cfop, descricao = fallbacks[chave]
            return {
                "cfop": cfop,
                "descricao": descricao,
                "concat_code": ""
            }

        # fallback genérico por grupo
        fallback_generico = {
            ("compra", "1"): ("1102", "Entrada intraestadual"),
            ("compra", "2"): ("2102", "Entrada interestadual"),
            ("compra", "3"): ("3102", "Entrada do exterior"),
            ("venda", "5"): ("5101", "Saída intraestadual"),
            ("venda", "6"): ("6101", "Saída interestadual"),
            ("venda", "7"): ("7101", "Saída para o exterior"),
        }

        chave_generica = (operacao_n, prefixo)

        if chave_generica in fallback_generico:
            cfop, descricao = fallback_generico[chave_generica]
            return {
                "cfop": cfop,
                "descricao": descricao,
                "concat_code": ""
            }

        return {
            "cfop": "N/A",
            "descricao": f"Nenhum CFOP encontrado para o grupo {prefixo}.xxx",
            "concat_code": ""
        }

    def sugerir_cfop(self, operacao, finalidade, origem, destino):
        operacao_n = self._normalizar(operacao)
        finalidade_n = self._normalizar(finalidade)

        df = self.buscar_por_operacao(operacao)
        prefixo = self._determinar_prefixo(operacao, origem, destino)

        print("=== DEBUG CFOP ===")
        print("operacao:", operacao)
        print("origem:", origem)
        print("destino:", destino)
        print("finalidade:", finalidade)
        print("prefixo esperado:", prefixo)
        print("total linhas por operacao:", len(df))

        candidatos = df[df["CFOP"].str.startswith(prefixo)].copy()
        print("qtd candidatos prefixo:", len(candidatos))

        palavras = self._palavras_por_finalidade(finalidade_n)

        if self._eh_exterior(origem, destino):
            palavras = list(set(
                palavras + ["exterior", "importação", "importacao", "exportação", "exportacao"]
            ))

        print("palavras finalidade:", palavras)

        if not candidatos.empty and palavras:
            candidatos["SCORE"] = candidatos["CLASS_NAME"].apply(
                lambda x: self._score_linha(x, palavras)
            )

            melhores = candidatos[candidatos["SCORE"] > 0].copy()
            print("qtd melhores com score > 0:", len(melhores))

            if not melhores.empty:
                candidatos = melhores.sort_values(
                    by=["SCORE", "CFOP"],
                    ascending=[False, True]
                ).copy()
            else:
                candidatos = candidatos.sort_values(by="CFOP").copy()
        elif not candidatos.empty:
            candidatos = candidatos.sort_values(by="CFOP").copy()

        if candidatos.empty:
            print("Nenhum candidato no Excel. Usando fallback.")
            return self._fallback_cfop(operacao_n, prefixo, finalidade_n)

        print("top 10 candidatos:")
        print(
            candidatos[["CFOP", "CLASS_NAME", "TRX_TYPE"]]
            .head(10)
            .to_dict(orient="records")
        )

        row = candidatos.iloc[0]
        print("escolhido:", row["CFOP"], row["CLASS_NAME"])

        return {
            "cfop": row["CFOP"],
            "descricao": row["CLASS_NAME"],
            "concat_code": row["CONCAT_CODE"]
        }