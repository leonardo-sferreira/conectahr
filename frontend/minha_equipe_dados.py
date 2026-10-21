"""Consultas de Minha equipe: cache curto por sessão e falhas complementares isoladas."""

import time
from datetime import date

import streamlit as st

from api_client import ApiError, calendario, central_de_tarefas, correcoes_ponto, folha_mes, folha_pessoas, organograma
from api_client import ferias_equipe
from minha_equipe_modelo import colaborador_do_gestor, liderados, meses_da_semana, periodo_ferias

CACHE = "minha_equipe_cache"
_VALIDADE_CACHE_S = 20


def _consultar(token: str, chave: str, buscar) -> dict:
    cache = st.session_state.get(CACHE)
    if not cache or cache["dono"] != token:
        cache = {"dono": token, "itens": {}}
        st.session_state[CACHE] = cache
        st.session_state.pop("me_liderado", None)
        st.session_state.pop("me_busca", None)
        st.session_state.pop("me_situacao", None)
    item = cache["itens"].get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = buscar()
    cache["itens"][chave] = {"em": time.time(), "dados": dados}
    return dados


def carregar(token: str, hoje: date) -> dict:
    """A lista principal precisa carregar; demais fontes devolvem None e o código do erro.

    Não guarda falhas como listas vazias. Um 401 interrompe as consultas: o app encerra a sessão.
    Não consulta dados complementares se a conta não tem ficha ou subordinados diretos.
    """
    pessoas = _consultar(token, "pessoas", lambda: folha_pessoas(token)).get("pessoas") or []
    dados = {"gestor_id": colaborador_do_gestor(pessoas), "pessoas": liderados(pessoas),
             "gestor": next((p for p in pessoas if p.get("e_voce")), {}), "ferias": None,
             "organograma": None, "calendario": None, "central": None, "correcoes": None,
             "meses": {}, "erros": {}}
    if not dados["pessoas"]:
        return dados
    fontes = (("organograma", organograma), ("calendario", calendario),
              ("central", central_de_tarefas), ("correcoes", correcoes_ponto),
              (f"ferias-{hoje.isoformat()}", lambda token: ferias_equipe(token, *periodo_ferias(hoje))))
    for chave, buscar in fontes:
        destino = "ferias" if chave.startswith("ferias-") else chave
        try:
            dados[destino] = _consultar(token, chave, lambda buscar=buscar: buscar(token))
        except ApiError as erro:
            if erro.status_code == 401:
                raise
            dados["erros"][destino] = erro.status_code
    for ano, mes in meses_da_semana(hoje):
        chave = f"mes-{ano}-{mes}"
        try:
            dados["meses"][(ano, mes)] = _consultar(token, chave, lambda ano=ano, mes=mes: folha_mes(token, ano, mes))
        except ApiError as erro:
            if erro.status_code == 401:
                raise
            dados["meses"][(ano, mes)] = None
            dados["erros"][chave] = erro.status_code
    return dados
