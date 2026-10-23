"""Listagem/cancelamento do F17, sem catálogo de pessoas nem alteração de autorização."""

import time

import streamlit as st

from api_client import ApiError, cancelar_delegacao, minhas_delegacoes
from delegacoes_modelo import pode_cancelar, vinculada

CACHE = "dg_cache"
_CAMPOS = ("id", "titular_user_id", "substituto_user_id", "data_inicio", "data_fim", "escopo", "motivo", "cancelada_em")


def invalidar() -> None:
    st.session_state.pop(CACHE, None)


def carregar(token: str, usuario_id, atualizar: bool = False) -> dict:
    if usuario_id is None:
        raise ApiError("Não foi possível identificar sua conta. Entre novamente.", 403)
    sessao = (token, usuario_id)
    if st.session_state.get("dg_sessao") != sessao:
        for chave in list(st.session_state):
            if str(chave).startswith("dg_"):
                st.session_state.pop(chave, None)
        st.session_state["dg_sessao"] = sessao
    if atualizar:
        invalidar()
    cache = st.session_state.get(CACHE)
    if cache and time.time() - cache["em"] < 20:
        return cache["dados"]
    resposta = minhas_delegacoes(token)
    if not isinstance(resposta, dict) or not isinstance(resposta.get("delegacoes"), list):
        raise ApiError("Não foi possível carregar as delegações. Tente novamente.", 0)
    delegacoes, incompletas = [], False
    for d in resposta["delegacoes"]:
        if not isinstance(d, dict) or type(d.get("id")) is not int or d["id"] <= 0 or not vinculada(d, usuario_id):
            incompletas = True
            continue
        registro = {campo: d.get(campo) for campo in _CAMPOS}
        for campo in ("data_inicio", "data_fim", "escopo", "motivo"):
            if registro[campo] is not None and not isinstance(registro[campo], str):
                registro[campo] = None
                incompletas = True
        delegacoes.append(registro)
    dados = {"delegacoes": delegacoes, "incompletas": incompletas}
    st.session_state[CACHE] = {"em": time.time(), "dados": dados}
    return dados


def cancelar(token: str, usuario_id, delegacao_id: int) -> None:
    # A lista atual confirma vínculo e estado; o POST decide a autorização final, inclusive corridas.
    dados = carregar(token, usuario_id, atualizar=True)
    alvo = next((d for d in dados["delegacoes"] if d["id"] == delegacao_id), None)
    if alvo is None or not pode_cancelar(alvo, usuario_id):
        raise ApiError("Esta delegação não está disponível para cancelamento pela sua conta.", 403)
    try:
        resposta = cancelar_delegacao(token, delegacao_id)
        confirmada = resposta.get("delegacao") if isinstance(resposta, dict) else None
        if not isinstance(confirmada, dict) or resposta.get("sucesso") is not True or confirmada.get("id") != delegacao_id or confirmada.get("cancelada_em") is None:
            raise ApiError("Não foi possível confirmar o cancelamento. Atualize a lista antes de tentar novamente.", 0)
    finally:
        invalidar()
