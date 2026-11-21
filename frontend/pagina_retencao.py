"""
Página "Retenção e anonimização" do grupo RH (Figma 290:902 e os modais 290:1187 e 290:1213; tarefa 64 da change
concluir-frontend-streamlit). Só RH e Admin.

Duas abas: "Documentos com retenção vencida" (só consulta: nada é alterado nem eliminado por esta lista) e "Desligados
com prazo cumprido", com a situação de cada pessoa e a ação. "Anonimizar" abre o modal com o aviso de que não há volta
e pede a justificativa (mínimo de 5 caracteres). Quem ainda não pode ser anonimizado abre "Não dá para anonimizar" com o
motivo. Os anonimizados mostram "Ver registro". Endpoints: `retencao` GET e `colaboradores/{id}/anonimizar` POST.

Diferença do Figma: "Ver registro" mostra a data e onde a operação está registrada (auditoria, ação
`anonimizar_colaborador`), sem abrir a auditoria, que é do Admin.
"""

import html
import time

import streamlit as st

from api_client import ApiError, anonimizar_colaborador, retencao
from campos import campo
from retencao_modelo import linhas_desligados, linhas_documentos, motivo_recusa, validar_justificativa
from theme import alerta, render_hero, render_topbar

_VALIDADE_CACHE_S = 20
ABAS = {"documentos": "Documentos com retenção vencida", "desligados": "Desligados com prazo cumprido"}


def _carregar(token: str) -> dict:
    item = st.session_state.get("ret_cache")
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = retencao(token)
    st.session_state.ret_cache = {"em": time.time(), "dados": dados}
    return dados


def _fechar() -> None:
    st.session_state.pop("ret_modal", None)


def _resumo(pares: list[tuple[str, str]]) -> str:
    return '<div class="crh-lgpd-resumo">' + "".join(f"<div><span>{html.escape(r)}</span><b>{html.escape(v)}</b></div>" for r, v in pares) + "</div>"


@st.dialog("Anonimizar colaborador", width="small", on_dismiss=_fechar)
def _modal_anonimizar(linha: dict) -> None:
    st.html(_resumo([("Pessoa", linha["nome"]), ("Desligamento", linha["desligamento"]), ("Prazo de guarda cumprido em", linha["guarda_ate"])])
            + '<p class="crh-alerta-inline">Nome, CPF, contato, endereço, data de nascimento e dados bancários serão trocados por '
            "marcadores. Isto não pode ser desfeito.</p>")
    justificativa = campo(st, "Justificativa (mínimo de 5 caracteres)", "texto", "ret_justificativa", area=True, max_chars=500, height=80,
                          placeholder="Prazo de guarda cumprido e sem processo em aberto.")
    slot = st.empty()
    with st.container(horizontal=True):
        if st.button("Voltar", key="ret_voltar"):
            _fechar()
            st.rerun()
        with st.container(key="ret_perigo", width="content"):
            clicou = st.button("Anonimizar", type="primary", key="ret_ok")
    if clicou:
        if erro := validar_justificativa(justificativa):
            alerta(slot, "erro", erro)
            return
        try:
            anonimizar_colaborador(st.session_state.token, linha["id"], justificativa.strip())
        except ApiError as erro_api:
            alerta(slot, "erro", erro_api.message)
            return
        for chave in ("ret_modal", "ret_cache", "ret_justificativa"):
            st.session_state.pop(chave, None)
        st.session_state.aviso_toast = "Colaborador anonimizado. A operação ficou na auditoria."
        st.rerun()


@st.dialog("Não dá para anonimizar", width="small", on_dismiss=_fechar)
def _modal_recusa(linha: dict) -> None:
    st.html(_resumo([("Pessoa", linha["nome"]), ("Desligamento", linha["desligamento"])])
            + f'<div class="crh-incluso"><p class="n" style="margin:0">{html.escape(motivo_recusa(linha))}</p></div>')
    with st.container(horizontal=True):
        if st.button("Fechar", key="ret_fechar"):
            _fechar()
            st.rerun()
        if linha["chave"] == "vigente" and st.button("Ver documentos retidos", type="primary", key="ret_ver_docs"):
            _fechar()
            st.session_state.ret_ir_documentos = True  # aplicado antes de desenhar as abas
            st.rerun()


@st.dialog("Registro da anonimização", width="small", on_dismiss=_fechar)
def _modal_registro(linha: dict) -> None:
    st.html(_resumo([("Pessoa", linha["nome"]), ("Desligamento", linha["desligamento"]), ("Situação", linha["situacao"][0])])
            + '<p class="crh-meta">A operação está na auditoria (ação "anonimizar_colaborador"), com quem fez e a justificativa, '
            "sem os valores pessoais anteriores.</p>")
    if st.button("Fechar", key="ret_fechar_reg"):
        _fechar()
        st.rerun()


def _cabecalho(titulo: str, texto: str) -> None:
    st.html(f'<div style="padding:16px 18px 12px"><p class="crh-cfg-titulo">{html.escape(titulo)}</p><p class="crh-cfg-nota">{html.escape(texto)}</p></div>')


def _tabela_documentos(linhas: list[dict]) -> None:
    pesos = [2.4, 1.8, 1.4, 1.2, 1.8]
    with st.container(key="rh_tabela"):
        _cabecalho("Documentos com retenção vencida", "Só consulta: nenhum documento é alterado ou eliminado por esta lista.")
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Documento", "Pessoa", "Tipo", "Retenção até", "Situação"]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhum documento com prazo de guarda vencido.</p>')
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_lin_doc_{i}"):
                col = st.columns(pesos, vertical_alignment="center")
                col[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["documento"])}</p></div>')
                col[1].html(f'<p class="crh-doc-prazo">{html.escape(l["pessoa"])}</p>')
                col[2].html(f'<p class="crh-doc-prazo">{html.escape(l["tipo"])}</p>')
                col[3].html(f'<p class="crh-doc-prazo">{html.escape(l["retencao_ate"])}</p>')
                selo, tom = l["situacao"]
                col[4].html(f'<span class="crh-selo {tom}">{html.escape(selo)}</span>', width="content")


def _tabela_desligados(linhas: list[dict]) -> None:
    pesos = [2.2, 1.3, 1.3, 2.0, 1.3]
    with st.container(key="rh_tabela_comp"):
        _cabecalho("Desligados com prazo de guarda cumprido",
                   "A anonimização troca os dados pessoais por marcadores. O histórico agregado e a auditoria ficam sem os valores pessoais.")
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Pessoa", "Desligamento", "Guarda até", "Situação", "Ação"]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhum colaborador desligado.</p>')
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_lin_des_{i}"):
                col = st.columns(pesos, vertical_alignment="center")
                col[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["nome"])}</p></div>')
                col[1].html(f'<p class="crh-doc-prazo">{html.escape(l["desligamento"])}</p>')
                col[2].html(f'<p class="crh-doc-prazo">{html.escape(l["guarda_ate"])}</p>')
                selo, tom = l["situacao"]
                col[3].html(f'<span class="crh-selo {tom}">{html.escape(selo)}</span>', width="content")
                with col[4]:
                    rotulo = "Ver registro" if l["chave"] == "anonimizado" else "Anonimizar"
                    if st.button(rotulo, key=f"ret_acao_{l['id']}"):
                        st.session_state.ret_modal = l["id"]
                        st.rerun()


def pagina_retencao() -> None:
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Retenção e anonimização", "Documentos com prazo de guarda vencido e desligados prontos para anonimizar. Nada é apagado automaticamente.")
    if str(usuario.get("perfil", "")).upper() not in ("RH", "ADMIN"):
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return
    try:
        with st.spinner("Carregando..."):
            dados = _carregar(st.session_state.token)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    docs, desligados = linhas_documentos(dados), linhas_desligados(dados)
    contagem = {"documentos": len(docs), "desligados": len(desligados)}
    if st.session_state.pop("ret_ir_documentos", False):
        st.session_state.ret_aba = "documentos"
    with st.container(key="cfg_abas", width="content"):
        aba = st.segmented_control("Aba", list(ABAS), format_func=lambda a: f"{ABAS[a]} ({contagem[a]})", default="documentos", required=True,
                                   key="ret_aba", label_visibility="collapsed")
    if aba == "documentos":
        _tabela_documentos(docs)
    else:
        _tabela_desligados(desligados)
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">Prazos de guarda por tipo de documento: a confirmar com o jurídico. '
            "A anonimização exige justificativa e é registrada na auditoria.</p></div>")

    alvo = st.session_state.get("ret_modal")
    linha = next((l for l in desligados if l["id"] == alvo), None) if alvo else None
    if alvo and not linha:
        _fechar()
    elif linha:
        {"pronto": _modal_anonimizar, "anonimizado": _modal_registro}.get(linha["chave"], _modal_recusa)(linha)
