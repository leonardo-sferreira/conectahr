"""
Aba "SLA de solicitações" de Configurações (change sla-de-solicitacoes, D4 e D6; Figma "Configurações — SLA de
solicitações", Admin e RH, e "Modal/Alterar prazo (SLA)", seção 5, claro e escuro).

- Admin e RH veem a aba (o Gestor e o Colaborador não). O RH só lê; o Admin tem "Editar" em cada linha.
- O modal grava pelo `sla_config` POST (tipo ainda sem linha) ou `sla_config/{id}` PATCH; "Voltar ao padrão (72 h)"
  desativa a linha. O backend recusa o que não for do Admin (403), e a recusa aparece no modal.
- Estados: carregando (spinner), erro e permissão negada (o alerta com a mensagem do backend), sucesso (aviso).
"""

import html
import time

import streamlit as st

from api_client import ApiError, alterar_sla, criar_sla, sla_config
from sla_modelo import COMO_CONTA, MAXIMO_HORAS, NOMES, TEXTO_ABA, TEXTO_SO_ADMIN, linhas_config, validar_horas
from theme import alerta

_CACHE = "sla_cache"
_VALIDADE_S = 20


def _dados(token: str) -> dict:
    item = st.session_state.get(_CACHE)
    if item and time.time() - item["em"] < _VALIDADE_S:
        return item["dados"]
    dados = sla_config(token)
    st.session_state[_CACHE] = {"em": time.time(), "dados": dados}
    return dados


def _fechar() -> None:
    st.session_state.pop("sla_modal", None)


def _concluir(aviso: str) -> None:
    st.session_state.pop(_CACHE, None)
    _fechar()
    st.session_state.aviso_toast = aviso
    st.rerun()


@st.dialog("Alterar prazo", width="small", on_dismiss=_fechar)
def _modal(linha: dict) -> None:
    st.text_input("Tipo de solicitação", value=linha["nome"], disabled=True, key=f"sla_m_tipo_{linha['tipo']}")
    c1, c2 = st.columns(2)
    c1.text_input("Setor responsável", value=linha["setor"], disabled=True, key=f"sla_m_setor_{linha['tipo']}")
    horas = c2.number_input("Prazo em horas úteis", min_value=1, max_value=MAXIMO_HORAS, value=int(linha["horas"]), step=1,
                            key=f"sla_m_horas_{linha['tipo']}")
    st.html(f'<p class="crh-nota-neutra">{html.escape(COMO_CONTA)}</p>')
    slot = st.empty()
    token = st.session_state.token
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar ao padrão (72 h)", key=f"sla_m_padrao_{linha['tipo']}", disabled=linha["padrao"] or not linha["id"]):
            try:
                alterar_sla(token, linha["id"], linha["horas"], ativo=False)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _concluir(f"{linha['nome']}: voltou ao padrão de 72 horas úteis.")
        if st.button("Salvar prazo", type="primary", key=f"sla_m_salvar_{linha['tipo']}"):
            erro = validar_horas(linha["tipo"], horas)
            if erro:
                alerta(slot, "erro", erro)
                return
            try:
                if linha["id"]:
                    alterar_sla(token, linha["id"], horas, ativo=True)
                else:
                    criar_sla(token, linha["tipo"], horas)
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            _concluir(f"{linha['nome']}: prazo de {int(horas)} horas úteis. Vale para os pedidos abertos daqui em diante.")


def aba_sla(token: str) -> None:
    with st.container(key="cfg_card_sla"):
        try:
            with st.spinner("Carregando..."):
                dados = _dados(token)
        except ApiError as erro:
            st.html('<p class="crh-cfg-titulo">SLA de solicitações</p>')
            alerta(st.empty(), "erro", erro.message)
            return
        pode_editar = bool(dados.get("pode_editar"))
        texto = TEXTO_ABA + ("" if pode_editar else TEXTO_SO_ADMIN)
        st.html(f'<p class="crh-cfg-titulo">SLA de solicitações</p><p class="crh-cfg-texto">{html.escape(texto)}</p>')
        linhas = linhas_config(dados.get("slas") or [])
        pesos = [5, 1.4, 1.6]
        with st.container(key="cfg_sla_cab"):
            for coluna, titulo in zip(st.columns(pesos, vertical_alignment="center"), ["Tipo de solicitação", "Setor", "Prazo (SLA)"]):
                coluna.html(f'<p class="crh-doc-cab">{titulo}</p>')
        for linha in linhas:
            with st.container(key=f"cfg_av_sla_{linha['tipo']}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(linha["nome"])}</p><p class="d">{html.escape(linha["descricao"])}</p></div>')
                c[1].html(f'<p class="crh-doc-prazo">{html.escape(linha["setor"])}</p>')
                with c[2]:
                    with st.container(horizontal=True, vertical_alignment="center"):
                        st.html(f'<p class="crh-doc-prazo">{html.escape(linha["prazo"])}</p>', width="content")
                        if pode_editar and st.button("Editar", type="tertiary", key=f"sla_editar_{linha['tipo']}"):
                            st.session_state.sla_modal = linha["tipo"]
                            st.rerun()
    alvo = st.session_state.get("sla_modal")
    if alvo and pode_editar:
        linha = next((x for x in linhas if x["tipo"] == alvo), None)
        if linha:
            _modal(linha)
        else:
            _fechar()


__all__ = ["aba_sla", "NOMES"]
