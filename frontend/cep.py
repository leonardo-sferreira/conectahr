"""
Busca de endereço pelo CEP (pedido do usuário em 13/10/2026), para preencher logradouro, bairro, cidade e UF.

A API oficial dos Correios exige contrato e credenciais de empresa. Por isso a consulta usa a BrasilAPI
(`/api/cep/v2`, que consulta a base dos Correios e outras fontes) e, se ela falhar, o ViaCEP (também com a base dos
Correios). As duas são públicas e gratuitas. Só o CEP sai do sistema: nenhum nome nem outro dado da pessoa vai junto
(registrado em `docs/lgpd/operadores.md`). A chamada parte do servidor do Streamlit; a tela continua aceitando o
endereço digitado à mão quando o CEP não é encontrado ou as duas APIs estão fora do ar.
"""

import logging

import requests

_log = logging.getLogger(__name__)
_TEMPO_LIMITE_S = 6
UFS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
       "RS", "RO", "RR", "SC", "SP", "SE", "TO"]


class CepErro(Exception):
    """Mensagem para a tela: CEP inválido, não encontrado ou serviço indisponível."""


def digitos(cep: str | None) -> str:
    return "".join(c for c in str(cep or "") if c.isdigit())


def formatar(cep: str | None) -> str:
    d = digitos(cep)
    return f"{d[:5]}-{d[5:]}" if len(d) == 8 else str(cep or "")


def _da_brasilapi(cep: str) -> dict | None:
    resp = requests.get(f"https://brasilapi.com.br/api/cep/v2/{cep}", timeout=_TEMPO_LIMITE_S)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    d = resp.json()
    return {"logradouro": d.get("street") or "", "bairro": d.get("neighborhood") or "", "cidade": d.get("city") or "", "estado": (d.get("state") or "").upper()}


def _do_viacep(cep: str) -> dict | None:
    resp = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=_TEMPO_LIMITE_S)
    resp.raise_for_status()
    d = resp.json()
    if d.get("erro"):
        return None
    return {"logradouro": d.get("logradouro") or "", "bairro": d.get("bairro") or "", "cidade": d.get("localidade") or "", "estado": (d.get("uf") or "").upper()}


def consultar(cep: str | None) -> dict:
    """{'logradouro', 'bairro', 'cidade', 'estado'} do CEP. Levanta CepErro com a mensagem para a tela.
    CEP geral de cidade pequena volta sem logradouro e sem bairro: a pessoa completa."""
    d = digitos(cep)
    if len(d) != 8:
        raise CepErro("O CEP tem 8 números.")
    for fonte in (_da_brasilapi, _do_viacep):
        try:
            achado = fonte(d)
        except (requests.RequestException, ValueError) as exc:
            _log.warning("Consulta de CEP falhou em %s: %s", fonte.__name__, exc)
            continue
        if achado is None:
            raise CepErro("CEP não encontrado. Confira os números ou preencha o endereço.")
        if achado["estado"] not in UFS:
            achado["estado"] = ""
        return achado
    raise CepErro("A busca de CEP está fora do ar agora. Preencha o endereço.")
