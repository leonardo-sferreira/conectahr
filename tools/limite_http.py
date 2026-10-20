"""Chamada HTTP dos scripts de teste que respeita o limite do plano do Xano (10 requisições a cada 20 segundos).

Quando o Xano responde 429, espera a janela passar e repete (até 3 vezes), em vez de contar como falha do endpoint.
"""

import time

import requests

_ESPERA_S = 21
_TENTATIVAS = 3


def pedir(metodo: str, url: str, **kwargs) -> requests.Response:
    for tentativa in range(_TENTATIVAS + 1):
        r = requests.request(metodo, url, **kwargs)
        if r.status_code != 429 or tentativa == _TENTATIVAS:
            return r
        print(f"  (limite do Xano: esperando {_ESPERA_S} s para continuar...)")
        time.sleep(_ESPERA_S)
    return r
