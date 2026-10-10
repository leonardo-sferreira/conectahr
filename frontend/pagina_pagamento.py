"""
Página "Pagamento" (tarefas 29 e 30 da change concluir-frontend-streamlit).

- Colaborador (Figma 70:46): os próprios holerites por ano e os informes de rendimentos, com "Baixar"
  (`documentos/{id}/arquivo`, que só o dono, o RH e o Admin abrem, e audita cada abertura).
- RH e Admin (Figma 236:357 e 236:594, "Pagamento — lançamentos"): abas Holerites e Informes, filtros de
  competência e departamento, quem já tem e quem falta, "Lançar" (237:363 e 237:402) e "Substituir"
  (237:441). Lançar é `documentos` (POST) com tipo holerite ou informe_rendimentos, que só RH e Admin
  podem; substituir é o mesmo POST com `documento_substituido_id`, e o anterior fica "substituído".

Diferença em relação ao Figma: o arquivo entra por link (https de um domínio aprovado), e não por upload,
porque o plano do Xano não recebe arquivo (a mesma decisão da tela Documentos).
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import ApiError, abrir_arquivo_documento, documentos_rh, enviar_documento, meus_documentos, organograma
from pagamento_modelo import (
    MESES,
    anos_recentes,
    competencias_recentes,
    do_colaborador,
    linhas_rh,
    nome_documento,
    rotulo_competencia,
    validar_lancamento,
    validar_substituicao,
)
from theme import alerta, render_hero, render_indicadores, render_topbar

_CACHE = "pagamento_cache"
_VALIDADE_CACHE_S = 20
_ABAS = {"Holerites": "holerite", "Informes de rendimentos": "informe_rendimentos"}


def _invalidar() -> None:
    st.session_state.pop(_CACHE, None)
    st.session_state.pop("documentos_cache", None)


def _fechar() -> None:
    st.session_state.pop("modal_pagamento", None)


def _abrir(documento_id: int) -> None:
    try:
        st.session_state.pg_link = abrir_arquivo_documento(st.session_state.token, documento_id).get("arquivo_url")
        st.session_state.pop("pg_erro", None)
    except ApiError as erro:
        st.session_state.pg_erro = erro.message
        st.session_state.pop("pg_link", None)
    st.rerun()


def _link_aberto() -> None:
    if link := st.session_state.get("pg_link"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html('<p class="crh-meta">Link do arquivo pronto (vale por 5 minutos). A abertura fica registrada na auditoria.</p>', width="content")
            st.link_button("Abrir arquivo", link)
    if erro := st.session_state.pop("pg_erro", None):
        alerta(st.empty(), "erro", erro)


# ---------------------------------------------------------------------------
# Colaborador
# ---------------------------------------------------------------------------
def _linhas(linhas: list[dict], prefixo: str) -> None:
    with st.container(key=f"{prefixo}_lista"):
        for i, l in enumerate(linhas):
            with st.container(horizontal=True, vertical_alignment="center", key=f"pg_lin_{prefixo}_{i}"):
                st.html(
                    f'<div class="crh-fe-item"><span class="p ok"></span><div><p class="t">{html.escape(l["titulo"])}</p>'
                    f'<p class="d">{html.escape(l["detalhe"])}</p></div></div>',
                    width="stretch",
                )
                st.html(f'<span class="crh-selo ok">{html.escape(l["badge"])}</span>', width="content")
                if st.button("Baixar", type="tertiary", key=f"pg_baixar_{l['id']}"):
                    _abrir(l["id"])


def _visao_colaborador(token: str) -> None:
    render_hero("Pagamento", "Holerites e informes de rendimentos emitidos pelo RH")
    with st.spinner("Carregando..."):
        try:
            documentos, erro = meus_documentos(token).get("documentos") or [], None
        except ApiError as falha:
            documentos, erro = [], falha
    if erro is not None:
        if erro.status_code == 404:
            st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">Sua conta não tem cadastro de colaborador, então não há holerites.</p></div>')
        else:
            alerta(st.empty(), "erro", erro.message)
        return
    st.html('<p class="crh-pg-nota">Documentos emitidos diretamente pelo RH já entram aprovados — não passam por análise.</p>')
    _link_aberto()
    dados = do_colaborador(documentos)
    if dados["anos"]:
        with st.container(key="cfg_abas"):
            ano = st.segmented_control("Ano", dados["anos"], default=dados["anos"][0], required=True, key="pg_ano", label_visibility="collapsed")
        st.html(f'<p class="crh-bloco-titulo">Holerites — {ano}</p>')
        _linhas(dados["holerites"][ano], "hol")
    else:
        st.html('<p class="crh-bloco-titulo">Holerites</p><p class="crh-meta">Nenhum holerite lançado ainda.</p>')
    st.html('<p class="crh-bloco-titulo">Informes de rendimentos</p>')
    if dados["informes"]:
        _linhas(dados["informes"], "inf")
    else:
        st.html('<p class="crh-meta">Nenhum informe de rendimentos lançado ainda.</p>')


# ---------------------------------------------------------------------------
# RH e Admin
# ---------------------------------------------------------------------------
def _carregar_rh(token: str) -> dict:
    cache = st.session_state.get(_CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = {"documentos": documentos_rh(token).get("documentos") or []}
    try:
        dados["org"] = organograma(token)
    except ApiError:
        dados["org"] = {}
    st.session_state[_CACHE] = {"em": time.time(), "dados": dados}
    return dados


@st.dialog("Lançar documento", width="small", on_dismiss=_fechar)
def _modal_lancar(tipo: str, competencia, org: dict, colaborador_id) -> None:
    rotulo = "holerite" if tipo == "holerite" else "informe de rendimentos"
    st.html(f'<p class="crh-cfg-titulo">Lançar {rotulo}</p>')
    deps = {d.get("id"): d.get("nome") for d in org.get("departamentos") or []}
    pessoas = {c.get("id"): f"{c.get('nome')} — {deps.get(c.get('departamento_id')) or '—'}" for c in org.get("colaboradores") or []}
    ids = sorted(pessoas, key=pessoas.get)
    colab = st.selectbox("Colaborador", ids, index=ids.index(colaborador_id) if colaborador_id in ids else None, format_func=pessoas.get, placeholder="Escolha a pessoa", key="pg_l_colab")
    c1, c2 = st.columns(2)
    if tipo == "holerite":
        opcoes = competencias_recentes(date.today())
        comp = c1.selectbox("Competência", opcoes, index=opcoes.index(competencia) if competencia in opcoes else 0, format_func=lambda c: rotulo_competencia(tipo, c), key="pg_l_comp")
    else:
        opcoes = anos_recentes(date.today())
        comp = c1.selectbox("Ano-calendário", opcoes, index=opcoes.index(competencia) if competencia in opcoes else 0, key="pg_l_comp")
    emissao = c2.date_input("Data de emissão", value=date.today(), max_value=date.today(), format="DD/MM/YYYY", key="pg_l_emissao")
    st.text_input("Nome do documento", value=nome_documento(tipo, comp), disabled=True, key=f"pg_l_nome_{comp}")
    link = st.text_input("Link do arquivo", placeholder="https://", max_chars=2000, key="pg_l_link", help="PDF, um arquivo por colaborador. O sistema ainda não recebe arquivos: informe o link https, guardado num endereço aprovado pela empresa.")
    st.html('<p class="crh-nota-verde">Fica disponível na hora na tela Pagamento do colaborador. Já nasce aprovado e não tem validade.</p>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="pg_l_cancelar"):
            _fechar()
            st.rerun()
        if st.button(f"Lançar {'holerite' if tipo == 'holerite' else 'informe'}", type="primary", key="pg_l_ok"):
            erro_campo = validar_lancamento(colab, emissao, link, date.today())
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                enviar_documento(st.session_state.token, {
                    "colaborador_id": colab, "tipo": tipo, "nome_documento": nome_documento(tipo, comp),
                    "data_emissao": emissao.isoformat(), "arquivo_url": link.strip(),
                })
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _invalidar()
            _fechar()
            for chave in ("pg_l_colab", "pg_l_comp", "pg_l_emissao", "pg_l_link"):
                st.session_state.pop(chave, None)
            st.session_state.aviso_toast = f"{nome_documento(tipo, comp)} lançado para {pessoas[colab].split(' — ')[0]}."
            st.rerun()


@st.dialog("Substituir documento", width="small", on_dismiss=_fechar)
def _modal_substituir(linha: dict) -> None:
    doc = linha["documento"]
    st.html(
        '<div class="crh-campos crh-campos-direita">'
        f'<p class="r">Colaborador</p><p class="v">{html.escape(linha["nome"])}</p>'
        f'<p class="r">Documento atual</p><p class="v">{html.escape(doc.get("nome_documento") or "—")}</p>'
        f'<p class="r">Lançado em</p><p class="v">{html.escape(linha["lancado_em"])}</p></div>'
    )
    link = st.text_input("Link do arquivo corrigido", placeholder="https://", max_chars=2000, key="pg_s_link")
    motivo = st.text_area("Motivo da correção", max_chars=1000, key="pg_s_motivo", height=80)
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">O arquivo anterior fica no histórico como "substituído". O colaborador passa a ver só a versão nova.</p></div>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="pg_s_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Substituir", type="primary", key="pg_s_ok"):
            erro_campo = validar_substituicao(link, motivo)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                enviar_documento(st.session_state.token, {
                    "colaborador_id": linha["colaborador_id"], "tipo": doc.get("tipo"), "nome_documento": doc.get("nome_documento"),
                    "data_emissao": date.today().isoformat(), "arquivo_url": link.strip(),
                    "documento_substituido_id": doc.get("id"), "observacao": motivo.strip(),
                })
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _invalidar()
            _fechar()
            for chave in ("pg_s_link", "pg_s_motivo"):
                st.session_state.pop(chave, None)
            st.session_state.aviso_toast = f"Documento de {linha['nome']} substituído."
            st.rerun()


def _visao_rh(token: str) -> None:
    render_hero("Pagamento — lançamentos", "Lance e acompanhe os holerites e informes de rendimentos de todos os colaboradores")
    with st.spinner("Carregando..."):
        try:
            dados, erro = _carregar_rh(token), None
        except ApiError as falha:
            dados, erro = None, falha
    if erro is not None:
        alerta(st.empty(), "erro", erro.message)
        return
    org = dados["org"]
    deps = {d.get("id"): d.get("nome") for d in org.get("departamentos") or []}

    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Aba", list(_ABAS), default="Holerites", required=True, key="pg_aba", label_visibility="collapsed")
        st.space("stretch")
        tipo = _ABAS[aba]
        if tipo == "holerite":
            opcoes = competencias_recentes(date.today())
            comp = st.selectbox("Competência", opcoes, format_func=lambda c: f"Competência: {MESES[c[1] - 1]}/{c[0]}", key="pg_comp", label_visibility="collapsed", width=230)
        else:
            opcoes = anos_recentes(date.today())
            comp = st.selectbox("Ano-calendário", opcoes, format_func=lambda a: f"Ano-calendário: {a}", key="pg_ano_cal", label_visibility="collapsed", width=200)
        dep = st.selectbox("Departamento", [None] + sorted(deps, key=deps.get), format_func=lambda d: "Departamento: Todos" if d is None else f"Departamento: {deps[d]}", key="pg_dep", label_visibility="collapsed", width=230)
        if st.button("Lançar holerite" if tipo == "holerite" else "Lançar informe", type="primary", key="pg_btn_lancar"):
            st.session_state.modal_pagamento = ("lancar", tipo, comp, None)
            st.rerun()

    visao = linhas_rh(org, dados["documentos"], tipo, comp, dep)
    nome_doc = "Holerites" if tipo == "holerite" else "Informes"
    render_indicadores([
        ("Colaboradores ativos", str(visao["ativos"]), ""),
        (f"{nome_doc} lançados", str(visao["lancados"]), "verde"),
        ("Faltando lançar", str(visao["faltando"]), "ambar"),
    ])
    _link_aberto()

    pesos = [3, 2.2, 1.6, 1.4, 1.3, 1.8]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Colaborador", "Departamento", "Competência" if tipo == "holerite" else "Ano-calendário", "Lançado em", "Situação", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not visao["linhas"]:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhum colaborador neste filtro.</p>')
        for i, l in enumerate(visao["linhas"]):
            with st.container(key=f"rh_linf_{i}" if not l["documento"] else f"rh_lin_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["nome"])}</p><p class="d">{html.escape(l["detalhe"])}</p></div>')
                c[1].html(f'<p class="crh-doc-prazo">{html.escape(l["departamento"])}</p>')
                c[2].html(f'<p class="crh-doc-prazo">{html.escape(l["competencia"])}</p>')
                c[3].html(f'<p class="crh-doc-prazo">{html.escape(l["lancado_em"])}</p>')
                c[4].html(f'<span class="crh-selo {l["situacao"][1]}">{l["situacao"][0]}</span>', width="content")
                with c[5]:
                    with st.container(horizontal=True, gap="small"):
                        if l["documento"]:
                            if st.button("Ver", type="tertiary", key=f"rh_abrir_{l['documento']['id']}"):
                                _abrir(l["documento"]["id"])
                            if st.button("Substituir", type="tertiary", key=f"pg_sub_{l['colaborador_id']}"):
                                st.session_state.modal_pagamento = ("substituir", tipo, comp, l["colaborador_id"])
                                st.rerun()
                        elif st.button("Lançar →", type="tertiary", key=f"pg_lan_{l['colaborador_id']}"):
                            st.session_state.modal_pagamento = ("lancar", tipo, comp, l["colaborador_id"])
                            st.rerun()
    st.html('<p class="crh-meta">Holerites e informes não passam por análise: nascem aprovados, não vencem e só RH ou Admin podem lançar.</p>')

    modal = st.session_state.get("modal_pagamento")
    if not modal:
        return
    acao, tipo_m, comp_m, colab = modal
    if acao == "lancar":
        _modal_lancar(tipo_m, comp_m, org, colab)
    else:
        linha = next((l for l in linhas_rh(org, dados["documentos"], tipo_m, comp_m)["linhas"] if l["colaborador_id"] == colab and l["documento"]), None)
        if linha is None:
            _fechar()
            return
        _modal_substituir(linha)


def pagina_pagamento() -> None:
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    if str(usuario.get("perfil", "")).upper() in ("RH", "ADMIN"):
        _visao_rh(st.session_state.token)
    else:
        _visao_colaborador(st.session_state.token)
