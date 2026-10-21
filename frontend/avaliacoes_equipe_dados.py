"""Consultas e gravações do F15. Atribuições são a fonte; organograma só enriquece a apresentação."""

import time

import streamlit as st

from api_client import (ApiError, avaliacao, ciclos_avaliacao, competencias_avaliacao, enviar_avaliacao,
                        minhas_avaliacoes, organograma, responder_avaliacao)
from avaliacoes_equipe_modelo import atribuicoes, atribuida, editavel
from trajetoria_modelo import respostas_alteradas, validar_envio

CACHE = "ae_cache"


def _consultar(token: str, usuario_id, chave: str, buscar) -> dict:
    cache = st.session_state.get(CACHE)
    if not cache or cache["sessao"] != (token, usuario_id):
        cache = {"sessao": (token, usuario_id), "itens": {}}
        st.session_state[CACHE] = cache
    item = cache["itens"].get(chave)
    if item and time.time() - item["em"] < 20:
        return item["dados"]
    resposta = buscar()
    cache["itens"][chave] = {"em": time.time(), "dados": resposta}
    return resposta


def carregar(token: str, usuario_id) -> dict:
    if usuario_id is None:
        raise ApiError("Não foi possível identificar o avaliador da sessão. Entre novamente.", 403)
    sessao = (token, usuario_id)
    if st.session_state.get("ae_sessao") != sessao:
        for chave in list(st.session_state):
            if str(chave).startswith("ae_"):
                st.session_state.pop(chave, None)
        st.session_state["ae_sessao"] = sessao
    resposta = _consultar(token, usuario_id, "avaliacoes", lambda: minhas_avaliacoes(token))
    if not isinstance(resposta.get("avaliacoes"), list):
        raise ApiError("Não foi possível carregar as avaliações. Tente novamente.", 0)
    avaliacoes = atribuicoes(resposta["avaliacoes"], usuario_id)
    dados = {"avaliacoes": avaliacoes, "ciclos": [], "organograma": {}, "erros": []}
    for chave, buscar in (("ciclos", lambda: ciclos_avaliacao(token)), ("organograma", lambda: organograma(token))):
        if chave == "organograma" and not avaliacoes:
            continue
        try:
            resposta = _consultar(token, usuario_id, chave, buscar)
            if chave == "ciclos" and not isinstance(resposta.get("ciclos"), list):
                raise ApiError("Ciclos não disponíveis.", 0)
            dados[chave] = resposta["ciclos"] if chave == "ciclos" else resposta
        except ApiError as erro:
            if erro.status_code == 401:
                raise
            dados["erros"].append(chave)
    return dados


def formulario(token: str, usuario_id, alvo: dict) -> dict:
    if not atribuida(alvo, usuario_id):
        raise ApiError("Você não tem permissão para responder esta avaliação.", 403)
    form = competencias_avaliacao(token, alvo["id"])
    if form.get("avaliacao_id") != alvo["id"] or form.get("relacao") != "gestor":
        raise ApiError("Não foi possível confirmar a avaliação atribuída.", 403)
    return form


def invalidar() -> None:
    st.session_state.pop(CACHE, None)
    # A mesma atribuição pode aparecer na Trajetória.
    st.session_state.pop("traj_cache", None)
    for chave in list(st.session_state):
        if str(chave).startswith("traj_form_"):
            st.session_state.pop(chave, None)


def gravar(token: str, usuario_id, alvo: dict, form: dict, notas: dict, comentarios: dict,
           comentario_geral: str, enviar: bool) -> None:
    if not atribuida(alvo, usuario_id) or form.get("avaliacao_id") != alvo["id"]:
        raise ApiError("Você não tem permissão para responder esta avaliação.", 403)
    if not editavel(form):
        raise ApiError("Esta avaliação já foi enviada ou cancelada.", 409)
    competencias = form.get("competencias") or []
    if enviar and (erro := validar_envio(competencias, notas)):
        raise ApiError(erro, 400)
    # Conferir de novo antes da primeira escrita: outra aba pode ter enviado/cancelado a avaliação.
    atual = avaliacao(token, alvo["id"]).get("avaliacao") or {}
    if atual.get("id") != alvo["id"] or not atribuida(atual, usuario_id):
        raise ApiError("Você não tem permissão para responder esta avaliação.", 403)
    if not editavel(atual):
        invalidar()
        raise ApiError("Esta avaliação já foi enviada ou cancelada. Atualize a página.", 409)
    try:
        for cid, nota, comentario in respostas_alteradas(competencias, form.get("respostas"), notas, comentarios):
            responder_avaliacao(token, alvo["id"], cid, nota, comentario)
            form["respostas"] = [r for r in form.get("respostas") or [] if r.get("competencia_avaliacao_id") != cid]
            form["respostas"].append({"competencia_avaliacao_id": cid, "nota": nota, "comentario": comentario})
            form["status"] = "em_andamento"
        if enviar:
            enviar_avaliacao(token, alvo["id"], comentario_geral.strip())
            form["status"] = "enviada"
    finally:
        invalidar()
