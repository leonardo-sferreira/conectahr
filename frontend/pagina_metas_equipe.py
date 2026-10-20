"""
Página "Metas da equipe" (change ciclo-de-metas, D4 e D5), no grupo Equipe do menu: para o Gestor e para quem é
superior direto de alguém. Lista o ciclo de metas da equipe (quem enviou cada etapa) e abre o formulário de cada
pessoa, com as respostas e a caixa de feedback de cada etapa enviada, onde o superior direto ou o gestor do
departamento registra o feedback. O modal do formulário também serve à tela do RH ("Ciclos de avaliação").

Endpoints: `meu_ciclo_metas` (os ciclos), `formularios_meta`, `formularios_meta/{id}` e `formularios_meta/{id}/feedback`.
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import ApiError, feedback_meta, formulario_meta, formularios_meta
from ciclo_metas_modelo import enviadas_do, linhas_pessoas, perguntas_do_formulario, situacao_ciclo, validar_feedback
from formulario_metas_ui import etapa_leitura, tabela_pessoas, trilha_etapas
from pagina_metas_ciclo import carregar as carregar_meus_ciclos
from theme import alerta, render_hero, render_topbar

_VALIDADE_CACHE_S = 20


def _guardado(chave: str, buscar):
    """Resposta da API guardada por 20 s em `chave`; o erro sobe."""
    item = st.session_state.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = buscar()
    st.session_state[chave] = {"em": time.time(), "dados": dados}
    return dados


def pessoas_do_ciclo(token: str, ciclo_id: int) -> dict:
    return _guardado(f"mf_lista_{ciclo_id}", lambda: formularios_meta(token, ciclo_id))


def fechar_formulario() -> None:
    st.session_state.pop("mf_aberto", None)


@st.dialog("Formulário de metas", width="large", on_dismiss=fechar_formulario)
def modal_formulario(formulario_id: int) -> None:
    """As três etapas com as respostas e o feedback; quem pode, registra feedback em cada etapa enviada."""
    token = st.session_state.token
    try:
        dados = _guardado(f"mf_{formulario_id}", lambda: formulario_meta(token, formulario_id))
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
                    st.session_state.pop(f"mf_{formulario_id}", None)
                    st.session_state.pop(f"mf_{formulario_id}_fb{n}", None)
                    st.toast(f"Feedback da etapa {n} registrado. A pessoa foi avisada.")
                    st.rerun()


def pagina_metas_equipe() -> None:
    token = st.session_state.token
    render_topbar(st.session_state.usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Metas da equipe", "Acompanhe o ciclo de metas da sua equipe e deixe o seu feedback em cada etapa")
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
