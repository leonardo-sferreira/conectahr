"""Cache do ciclo anual, compartilhado com Trajetória e RH; não é fonte de dados do F16."""

import time

import streamlit as st

_VALIDADE_CACHE_S = 20


def garantir_sessao(token: str) -> tuple:
    """Descarta dados e campos anteriores antes de montar widgets de outra sessão."""
    identidade = (token, (st.session_state.get("usuario") or {}).get("id"))
    if st.session_state.get("metas_sessao") != identidade:
        for chave in list(st.session_state):
            if str(chave).startswith(("cm_", "mf_", "mp_")) or chave in ("me_ciclo", "me_busca"):
                st.session_state.pop(chave, None)
        st.session_state["metas_sessao"] = identidade
    return identidade


def consultar(token: str, chave: str, buscar):
    """Guarda somente respostas bem-sucedidas por 20 s, para o mesmo usuário e token."""
    identidade = garantir_sessao(token)
    item = st.session_state.get(chave)
    if item and item.get("sessao") == identidade and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = buscar()
    st.session_state[chave] = {"em": time.time(), "sessao": identidade, "dados": dados}
    return dados


def invalidar_formulario(formulario_id: int) -> None:
    """Após feedback, reler o formulário e as listagens anuais, inclusive a própria."""
    for chave in list(st.session_state):
        if chave in (f"mf_{formulario_id}", "cm_cache") or str(chave).startswith("mf_lista_"):
            st.session_state.pop(chave, None)
