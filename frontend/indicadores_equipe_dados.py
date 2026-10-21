"""Fontes autorizadas do F18, com projeção mínima, cache por sessão e falhas isoladas."""

import time
from datetime import date

import streamlit as st

from api_client import ApiError, banco_horas_colaborador, folha_mes, folha_pessoas, organograma
from indicadores_equipe_modelo import id_valido, meses, motivo_cobertura, numero, recorte_banco, recorte_folha


def invalidar() -> None:
    st.session_state.pop("ie_cache", None)


def _mes(resposta: dict) -> dict:
    campos = {"registros": ("id", "colaborador_id", "data", "horas_extras"),
              "ausencias": ("id", "colaborador_id", "tipo", "data_inicio", "data_fim", "status")}
    return {chave: [{c: r.get(c) for c in nomes} if isinstance(r, dict) else None for r in resposta[chave]]
            if isinstance(resposta.get(chave), list) else None for chave, nomes in campos.items()}


def carregar(token: str, usuario: dict, hoje: date) -> dict:
    if not id_valido(usuario.get("id")):
        raise ApiError("Não foi possível identificar sua conta. Entre novamente.", 403)
    sessao = (token, usuario["id"], usuario.get("colaborador_id"))
    if st.session_state.get("ie_sessao") != sessao:
        for chave in list(st.session_state):
            if str(chave).startswith("ie_"):
                st.session_state.pop(chave, None)
        st.session_state["ie_sessao"] = sessao
    cache = st.session_state.setdefault("ie_cache", {})
    dados = {"folha": None, "banco": None, "meses": {}, "saldos": {}, "erros": {}}

    def consultar(chave, buscar, projetar):
        item = cache.get(chave)
        if item and time.time() - item["em"] < 60:
            return item["dados"]
        try:
            resposta = buscar()
            if not isinstance(resposta, dict):
                raise ValueError("Resposta inválida")
            valor = projetar(resposta)
        except ApiError as erro:
            if erro.status_code == 401:
                raise
            dados["erros"][chave] = erro.status_code
            return None
        except (ValueError, TypeError, KeyError):
            dados["erros"][chave] = 0
            return None
        cache[chave] = {"em": time.time(), "dados": valor}
        return valor

    dados["folha"] = consultar("folha", lambda: folha_pessoas(token), recorte_folha)
    colaborador_id = usuario.get("colaborador_id")
    if not id_valido(colaborador_id):
        colaborador_id = (dados["folha"] or {}).get("gestor_id")
    elif (dados["folha"] or {}).get("gestor_id") not in (None, colaborador_id):
        colaborador_id = None  # Fichas divergentes: não assumir qual delas gerencia o departamento.
    dados["banco"] = consultar(f"estrutura-{colaborador_id}", lambda: organograma(token), lambda r: recorte_banco(r, colaborador_id))
    ids_folha = dados["folha"]["ids"] if dados["folha"] is not None else None
    if not motivo_cobertura(ids_folha):
        for ano, mes in meses(hoje):
            dados["meses"][(ano, mes)] = consultar(f"mes-{ano}-{mes}", lambda a=ano, m=mes: folha_mes(token, a, m), _mes)
    ids_banco = dados["banco"]["ids"] if dados["banco"] is not None else None
    if not motivo_cobertura(ids_banco):
        def saldo_valido(resposta):
            valor = numero(resposta.get("saldo_horas"))
            if valor is None:
                raise ValueError("Saldo não disponível")
            return valor
        for pid in ids_banco:
            dados["saldos"][pid] = consultar(f"banco-{pid}", lambda pid=pid: banco_horas_colaborador(token, pid), saldo_valido)
    return dados
