"""
Página "Integrações e e-mails" do grupo Admin (Figma 249:7847; change integracoes-e-emails). Admin (e RH, que o
backend também aceita).

Indicadores (na fila, falharam e enviados nas últimas 24 h, contas bloqueadas por senha), "Processar fila agora" e as
abas:
- Fila de e-mails: os 50 mais recentes, com filtro de situação; tipo, assunto, destinatário mascarado (o e-mail inteiro
  não sai do backend), criado em, tentativas, situação e o último erro.
- Tarefas manuais: rotina diária, desligamentos com data efetiva vencida e documentos vencidos, com o botão de cada
  uma (o plano do Xano não roda tarefas agendadas).
- Modelos: o modelo dos e-mails fica no Brevo; aqui só o aviso e o link.
Endpoints: `email_outbox` GET, `email_outbox/processar`, `status_operacional`, `rotinas/processar_diarias` e
`documentos/processar_vencimentos`.
"""

import html
import time

import streamlit as st

from api_client import ApiError, fila_emails, processar_fila_emails, processar_rotina_diaria, processar_vencimentos, status_operacional
from integracoes_modelo import (ABAS, BREVO_PAINEL, SITUACOES, indicadores, linhas_fila, resumo_processamento, resumo_rotina, tarefas)
from theme import alerta, render_hero, render_indicadores, render_topbar

_VALIDADE_CACHE_S = 20


def _guardado(chave: str, buscar):
    item = st.session_state.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = buscar()
    st.session_state[chave] = {"em": time.time(), "dados": dados}
    return dados


def _concluir(aviso: str) -> None:
    for chave in [k for k in st.session_state if str(k).startswith("int_cache")]:
        st.session_state.pop(chave, None)
    st.session_state.aviso_toast = aviso
    st.rerun()


def _executar(acao, resumo) -> None:
    try:
        with st.spinner("Processando..."):
            r = acao(st.session_state.token)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    _concluir(resumo(r))


def _aba_fila(token: str, status: str | None) -> None:
    emails = _guardado(f"int_cache_fila_{status or 'todos'}", lambda: fila_emails(token, status)).get("emails") or []
    pesos = [2.4, 2, 1.2, 1, 1.1]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["E-mail", "Destinatário", "Criado em", "Tentativas", "Situação"]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        linhas = linhas_fila(emails)
        if not linhas:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhum e-mail nesta situação.</p>')
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_lin_{i}" + ("_alerta" if l["destaque"] else "")):
                col = st.columns(pesos, vertical_alignment="center")
                erro = f'<p class="d">Erro: {html.escape(l["erro"])}</p>' if l["erro"] else ""
                col[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["tipo"])}</p><p class="d">{html.escape(l["chave"])}</p>{erro}</div>')
                col[1].html(f'<p class="crh-doc-prazo">{html.escape(l["destinatario"])}</p>')
                col[2].html(f'<p class="crh-doc-prazo">{html.escape(l["criado"])}</p>')
                col[3].html(f'<p class="crh-doc-prazo">{html.escape(l["tentativas"])}</p>')
                selo, tom = l["situacao"]
                col[4].html(f'<span class="crh-selo {tom}">{html.escape(selo)}</span>', width="content")
    st.html('<p class="crh-meta">Os 50 mais recentes. O código de acesso do login e o "esqueci minha senha" saem na hora e não passam por esta fila. '
            'O destinatário aparece mascarado; o assunto e o texto ficam só no backend.</p>')


def _aba_tarefas(status_op: dict) -> None:
    acoes = {"rotina": (processar_rotina_diaria, resumo_rotina),
             "documentos": (processar_vencimentos, lambda r: f"Documentos processados: {r.get('total_vencidos') or 0} vencidos, {r.get('total_alertas') or 0} alertas.")}
    with st.container(key="cfg_card_int_tarefas"):
        st.html('<p class="crh-cfg-titulo">Tarefas manuais pendentes</p>'
                '<p class="crh-meta">O plano do Xano não roda tarefas agendadas: rode estas uma vez por dia. Rodar de novo não repete nada.</p>')
        for t in tarefas(status_op):
            with st.container(horizontal=True, vertical_alignment="center", key=f"int_tarefa_{t['chave']}"):
                st.html(f'<div class="crh-pc-item"><p class="t">{html.escape(t["titulo"])}</p><p class="d">{html.escape(t["detalhe"])}</p>'
                        f'<span class="crh-selo {"amb" if t["quantidade"] else "ok"}">{t["quantidade"] or "Em dia"}</span></div>')
                if t["acao"] and st.button(t["acao"], key=f"int_rodar_{t['chave']}"):
                    _executar(*acoes[t["chave"]])
                if t["chave"] == "desligamentos" and t["quantidade"] and st.button("Abrir Desligamentos", key="int_ir_deslig", type="tertiary"):
                    st.session_state.ir_desligamentos = True
                    st.rerun()


def _aba_modelos() -> None:
    with st.container(key="cfg_card_int_modelos"):
        st.html('<p class="crh-cfg-titulo">Modelos de e-mail</p>'
                '<p class="crh-alerta-inline">Editar modelos ainda não tem endpoint no backend.</p>'
                '<p class="crh-meta">Todos os avisos usam o mesmo modelo do Brevo ("conectarh_outbox_generico"): o sistema preenche o nome, o '
                'título e a mensagem. Para mudar a aparência, edite o modelo no painel do Brevo.</p>')
        st.link_button("Abrir os modelos no Brevo", BREVO_PAINEL)


def pagina_integracoes() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Integrações e e-mails", "Saúde do envio de e-mails (Brevo) e tarefas que precisam de ação manual")
    if str(usuario.get("perfil", "")).upper() not in ("ADMIN", "RH"):
        alerta(st.empty(), "erro", "Esta tela é só do Admin.")
        return
    try:
        with st.spinner("Carregando..."):
            contagens = _guardado("int_cache_fila_todos", lambda: fila_emails(token)).get("contagens") or {}
            status_op = _guardado("int_cache_status", lambda: status_operacional(token))
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    render_indicadores(indicadores(contagens, status_op))
    with st.container(horizontal=True, vertical_alignment="center"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Aba", ABAS, default=ABAS[0], required=True, key="int_aba", label_visibility="collapsed")
        st.space("stretch")
        status = None
        if aba == ABAS[0]:
            status = st.selectbox("Situação", [None] + list(SITUACOES), format_func=lambda s: "Situação: Todas" if s is None else f"Situação: {SITUACOES[s][0]}",
                                  key="int_status", label_visibility="collapsed", width=200)
        if st.button("Processar fila agora", type="primary", key="int_processar", disabled=not (contagens.get("na_fila") or 0),
                     help=None if contagens.get("na_fila") else "Nenhum e-mail pendente."):
            _executar(processar_fila_emails, resumo_processamento)
    try:
        if aba == ABAS[0]:
            _aba_fila(token, status)
        elif aba == ABAS[1]:
            _aba_tarefas(status_op)
        else:
            _aba_modelos()
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
