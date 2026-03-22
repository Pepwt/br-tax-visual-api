def normalizar_texto(valor: str) -> str:
    return valor.strip().lower()


def eh_interestadual(origem: str, destino: str) -> bool:
    return normalizar_texto(origem) != normalizar_texto(destino)


def validar_api_key(api_key: str, header_key: str):
    if api_key != header_key:
        raise Exception("API Key inválida")