"""
Página "Metas da equipe": estrutura parcial do F16 para Gestor, separada do ciclo anual funcional.
O ciclo anual (change ciclo-de-metas, D4 e D5) fica no grupo Equipe do menu: para o Gestor e para quem é
superior direto de alguém. Lista o ciclo de metas da equipe (quem enviou cada etapa) e abre o formulário de cada
pessoa, com as respostas e a caixa de feedback de cada etapa enviada, onde o superior direto ou o gestor do
departamento registra o feedback. O modal do formulário também serve à tela do RH ("Ciclos de avaliação").

Endpoints: `meu_ciclo_metas` (os ciclos), `formularios_meta`, `formularios_meta/{id}` e `formularios_meta/{id}/feedback`.
"""

import html
from datetime import date

import streamlit as st

from api_client import ApiError, feedback_meta, formulario_meta, formularios_meta
from ciclo_metas_modelo import enviadas_do, linhas_pessoas, perguntas_do_formulario, situacao_ciclo, validar_feedback
from formulario_metas_ui import etapa_leitura, tabela_pessoas, trilha_etapas
from metas_equipe_dados import consultar, garantir_sessao, invalidar_formulario
from pagina_metas_ciclo import carregar as carregar_meus_ciclos
from theme import alerta, render_hero, render_titulo_cartao, render_topbar


def pessoas_do_ciclo(token: str, ciclo_id: int) -> dict:
    return consultar(token, f"mf_lista_{ciclo_id}", lambda: formularios_meta(token, ciclo_id))


def fechar_formulario() -> None:
    st.session_state.pop("mf_aberto", None)


@st.dialog("Formulário de metas", width="large", on_dismiss=fechar_formulario)
def modal_formulario(formulario_id: int) -> None:
    """As três etapas com as respostas e o feedback; quem pode, registra feedback em cada etapa enviada."""
    token = st.session_state.token
    try:
        dados = consultar(token, f"mf_{formulario_id}", lambda: formulario_meta(token, formulario_id))
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    form = dados.get("formulario") or {}
    ciclo = dict(dados.get("ciclo") or {}, etapa_aberta=None, respostas=dados.get("respostas") or [])
    hoje = date.fromisoformat(str(dados.get("hoje") or date.today())[:10])
    enviadas = enviadas_do(form)
    perguntas = perguntas_do_formulario(ciclo, [])
    st.html(f'<div class="crh-cm-cab"><div><p class="t">{html.escape(dados.get("colaborador_nome") or "—")}</p>'
            f'<p class="s">{html.escape(dados.get("departamento") or "Sem departamento")} · Ciclo {html.escape(str(ciclo.get("ano")))}</p></div></div>')
    trilha_etapas(ciclo, hoje, enviadas)
    for n in (1, 2, 3):
        etapa_leitura(ciclo, n, perguntas, enviadas, dados.get("feedbacks"), hoje)
        if dados.get("pode_dar_feedback") and enviadas.get(n):
            texto = st.text_area(f"Seu feedback na etapa {n}", max_chars=2000, height=80, key=f"mf_{formulario_id}_fb{n}",
                                 help="Fica registrado na caixa da etapa, visível para a pessoa, para você e para o RH. Não dá para editar depois.")
            slot = st.empty()
            with st.container(horizontal=True, horizontal_alignment="right"):
                if st.button(f"Registrar feedback da etapa {n}", type="primary", key=f"mf_{formulario_id}_fb{n}_ok"):
                    erro_campo = validar_feedback(texto)
                    if erro_campo:
                        alerta(slot, "erro", erro_campo)
                        return
                    try:
                        feedback_meta(token, formulario_id, n, texto.strip())
                    except ApiError as erro:
                        alerta(slot, "erro", erro.message)
                        return
                    invalidar_formulario(formulario_id)
                    st.session_state.pop(f"mf_{formulario_id}_fb{n}", None)
                    st.toast(f"Feedback da etapa {n} registrado. A pessoa foi avisada.")
                    st.rerun()


def _reunioes() -> None:
    with st.container(border=True):
        render_titulo_cartao("Próximas reuniões 1:1")
        st.html('<p class="crh-meta">O agendamento e a consulta de próximas reuniões ainda não estão disponíveis nesta versão.</p>')
        st.button("Registrar reunião 1:1", disabled=True, key="mp_reuniao",
                  help="O agendamento de reuniões ainda não está disponível.")


def _pdi() -> None:
    with st.container(border=True):
        render_titulo_cartao("PDI da equipe")
        st.html('<p class="crh-meta">A consulta dos planos de desenvolvimento da equipe ainda não está disponível nesta versão.</p>')


def _f16() -> None:
    """Estrutura do F16, sem chamar os contratos insuficientes ou inseguros desse domínio."""
    st.session_state.setdefault("mp_aba", "Metas")
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Metas, PDI e reuniões 1:1", ["Metas", "PDI", "Reuniões 1:1"],
                                       required=True, key="mp_aba", label_visibility="collapsed")
        st.space("stretch")
        st.selectbox("Pessoa", ["Todos"], disabled=True, key="mp_pessoa", width=180,
                     format_func=lambda _: "Pessoa: Todos", label_visibility="collapsed",
                     help="O filtro depende da consulta de metas e PDI da equipe, ainda indisponível.")
        st.button("Nova meta", type="primary", disabled=True, key="mp_nova",
                  help="A criação de metas para liderados ainda não está disponível.")
    if aba == "Metas":
        with st.container(border=True, key="mp_tabela"):
            for coluna, titulo in zip(st.columns([3, 2, 1.3, 1.8, 1.5]), ("Meta", "Pessoa", "Prazo", "Progresso", "Situação")):
                coluna.html(f'<p class="crh-doc-cab">{titulo}</p>')
            st.html('<p class="crh-meta">As metas da equipe ainda não estão disponíveis para consulta nesta versão.</p>')
            st.button("Check-in", type="tertiary", disabled=True, key="mp_checkin",
                      help="O check-in de metas de liderados ainda não está disponível para o Gestor.")
        esquerda, direita = st.columns(2, gap="medium")
        with esquerda:
            _reunioes()
        with direita:
            _pdi()
    elif aba == "PDI":
        _pdi()
    else:
        _reunioes()


def _ciclo_anual(token: str) -> None:
    st.html('<p class="crh-bloco-titulo">Ciclo anual de metas e feedback</p>'
            '<p class="crh-meta">Acompanhe as três etapas do ciclo anual e registre seu feedback. '
            'Este formulário é independente das metas percentuais, PDI e reuniões 1:1.</p>')
    with st.spinner("Carregando..."):
        try:
            meus = carregar_meus_ciclos(token)
        except ApiError as erro:
            alerta(st.empty(), "erro", erro.message)
            return
    ciclos = meus.get("ciclos") or []
    if not ciclos:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">O RH ainda não abriu um ciclo de metas.</p></div>')
        return
    hoje = date.fromisoformat(str(meus.get("hoje") or date.today())[:10])
    por_id = {c["id"]: c for c in ciclos}
    with st.container(horizontal=True, vertical_alignment="center"):
        ciclo_id = st.selectbox("Ciclo", list(por_id), format_func=lambda i: f"Ciclo {por_id[i].get('ano')} — {situacao_ciclo(por_id[i], hoje)[0]}",
                                key="me_ciclo", label_visibility="collapsed", width=320)
        busca = st.text_input("Busca", placeholder="⌕  Nome", key="me_busca", label_visibility="collapsed", width=240)
    try:
        lista = pessoas_do_ciclo(token, ciclo_id)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    escolhido = tabela_pessoas(linhas_pessoas(lista.get("pessoas"), lista.get("ciclo") or por_id[ciclo_id], hoje, busca=busca), "me",
                               "Ninguém da sua equipe neste ciclo.")
    if escolhido:
        st.session_state.mf_aberto = escolhido
        st.rerun()
    if st.session_state.get("mf_aberto"):
        modal_formulario(st.session_state.mf_aberto)


def pagina_metas_equipe() -> None:
    token = st.session_state.token
    garantir_sessao(token)
    render_topbar(st.session_state.usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    gestor = str(st.session_state.usuario.get("perfil") or "").strip().upper() == "GESTOR"
    if gestor:
        render_hero("Metas e PDI da equipe", "Metas, check-ins, reuniões 1:1 e plano de desenvolvimento dos liderados")
        _f16()
        st.divider()
    else:
        render_hero("Metas da equipe", "Acompanhe o ciclo de metas da sua equipe e deixe o seu feedback em cada etapa")
    _ciclo_anual(token)
