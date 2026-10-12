"""
Página "Estrutura da empresa" do Admin (Figma 468:838; change ponto-rep-p-e-ferias-clt, tarefas 7.1 e 7.3). Por
enquanto só a aba "Feriados": a lista do ano (`calendario`) e "Importar feriados nacionais" (`feriados/importar`), que
traz os nacionais da BrasilAPI. Departamentos e cargos continuam no cadastro de colaboradores.

Diferenças em relação ao Figma: sem "Novo feriado", "Editar" e "Desativar" (o backend ainda não tem a edição nem a
desativação, e o cadastro não guarda o tipo); no lugar de "Novo feriado", o botão de importar.
"""

import html
from datetime import date

import streamlit as st

from api_client import ApiError, calendario, importar_feriados
from feriados_modelo import NOTA, anos_feriados, linhas_feriados, mensagem_importacao
from theme import alerta, render_hero, render_topbar

_PESOS = [0.8, 2.6, 1.3, 1.8]


def _importar(ano: int) -> None:
    try:
        resposta = importar_feriados(st.session_state.token, ano)
    except ApiError as erro:
        st.session_state.estr_erro = erro.message
        return
    st.session_state.pop("estr_feriados", None)
    st.session_state.pop("fe_feriados", None)  # o calendário de férias também lê de novo
    st.session_state.aviso_toast = mensagem_importacao(resposta)


def pagina_estrutura() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Estrutura da empresa", "Departamentos, cargos e feriados usados no ponto, nas férias e no calendário")
    if str(usuario.get("perfil", "")).upper() not in ("ADMIN", "RH"):
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return

    hoje = date.today()
    anos = anos_feriados(hoje)
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        with st.container(key="cfg_abas", width="content"):
            st.segmented_control("Aba", ["Feriados"], default="Feriados", required=True, key="estr_aba", label_visibility="collapsed")
        st.space("stretch")
        ano = st.selectbox("Ano", anos, index=anos.index(hoje.year), format_func=lambda a: f"Ano: {a}", key="estr_ano", label_visibility="collapsed", width=130)
        st.button("Importar feriados nacionais", type="primary", key="estr_importar", on_click=_importar, args=(ano,),
                  help="Traz os feriados nacionais do ano.")

    if erro_acao := st.session_state.pop("estr_erro", None):
        alerta(st.empty(), "erro", erro_acao)
    if "estr_feriados" not in st.session_state:
        with st.spinner("Carregando os feriados..."):
            try:
                st.session_state.estr_feriados = calendario(token).get("feriados") or []
            except ApiError as erro:
                alerta(st.empty(), "erro", erro.message)
                return
    linhas = linhas_feriados(st.session_state.estr_feriados, ano)

    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(_PESOS, vertical_alignment="center"), ["Data", "Nome", "Tipo", "Abrangência"]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            with st.container(key="rh_lin_vazio"):
                st.html(f'<p class="crh-meta">Nenhum feriado cadastrado em {ano}. Use "Importar feriados nacionais".</p>')
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_lin_{i}"):
                c = st.columns(_PESOS, vertical_alignment="center")
                c[0].html(f'<p class="crh-doc-prazo">{html.escape(l["data"])}</p>')
                c[1].html(f'<p class="crh-doc-prazo">{html.escape(l["nome"])}</p>')
                c[2].html(f'<span class="crh-selo {l["tom"]}">{html.escape(l["tipo"])}</span>')
                c[3].html(f'<p class="crh-doc-prazo">{html.escape(l["abrangencia"])}</p>')
    st.html(f'<div class="crh-incluso"><p class="n" style="margin:0">{html.escape(NOTA)}</p></div>')
