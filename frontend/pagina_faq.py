"""
Página "Comunicados e FAQ" (Figma 217:154 para todos e 245:594 para o RH; pedido do usuário em 12/10/2026).

- Comunicados (`meus_comunicados`): os vigentes e visíveis à pessoa, do mais recente; "Ler" abre o texto.
- Perguntas frequentes (`artigos_faq`): busca, categorias e as perguntas que abrem ao clicar.
- RH e Admin: aba "Comunicados" (tarefa 46), com todos os comunicados e a situação de cada um, "Novo comunicado"
  (`comunicados` POST) e "Arquivar" (`comunicados/{id}/arquivar`, novo); e aba "Artigos da FAQ", com a lista e
  "Novo artigo" (`artigos_faq` POST, só RH e Admin no backend).

Diferenças em relação ao Figma: o comunicado não tem categoria no backend, então não há as abas RH, TI e Benefícios; as
categorias da FAQ são as do backend (Férias, Ponto, Documentos e Políticas internas, sem Pagamento); editar e arquivar
artigo e de comunicado ficam para depois (o backend ainda não tem a edição); a lista de comunicados não mostra o autor
(o `comunicados` GET só traz o id de quem publicou).
"""

import html
import time

import streamlit as st

from api_client import ApiError, arquivar_comunicado, artigos_faq, comunicados_rh, criar_artigo_faq, meus_comunicados, organograma, publicar_comunicado
from delegacoes_modelo import hoje_brasilia
from faq_modelo import (CATEGORIAS, PERFIS_ALVO, PUBLICOS, SITUACOES_COMUNICADO, comunicados_ordenados, contagem_por_categoria, filtrar_artigos,
                        linhas_comunicados_rh, meta_comunicado, validar_artigo, validar_comunicado)
from theme import alerta, render_hero, render_topbar

_CACHE = "faq_cache"
_VALIDADE_CACHE_S = 60
_CACHE_RH = "faq_cache_rh"
_ABAS_RH = ["Consulta", "Comunicados", "Artigos da FAQ"]


def _carregar(token: str) -> dict:
    """{'artigos', 'comunicados', 'erros'} por 60 s. Cada lista que falhar fica vazia, com o motivo em 'erros'."""
    cache = st.session_state.get(_CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = {"artigos": [], "comunicados": [], "erros": {}}
    for chave, funcao in (("artigos", artigos_faq), ("comunicados", meus_comunicados)):
        try:
            dados[chave] = funcao(token).get(chave) or []
        except ApiError as erro:
            dados["erros"][chave] = erro.message
    st.session_state[_CACHE] = {"em": time.time(), "dados": dados}
    return dados


def _fechar() -> None:
    st.session_state.pop("modal_faq", None)


@st.dialog("Novo artigo da FAQ", width="medium", on_dismiss=_fechar)
def _modal_novo() -> None:
    categoria = st.selectbox("Categoria", list(CATEGORIAS), format_func=CATEGORIAS.get, index=None, placeholder="Escolha a categoria", key="faq_novo_cat")
    titulo = st.text_input("Pergunta", max_chars=200, key="faq_novo_titulo", placeholder="Ex.: Posso dividir minhas férias?")
    conteudo = st.text_area("Resposta", max_chars=5000, key="faq_novo_conteudo", height=160)
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="faq_novo_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Publicar", type="primary", key="faq_novo_publicar"):
            erro_campo = validar_artigo(categoria, titulo, conteudo)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                criar_artigo_faq(st.session_state.token, categoria, titulo.strip(), conteudo.strip())
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            st.session_state.pop(_CACHE, None)
            for chave in ("faq_novo_cat", "faq_novo_titulo", "faq_novo_conteudo"):
                st.session_state.pop(chave, None)
            _fechar()
            st.session_state.aviso_toast = "Artigo publicado na FAQ."
            st.rerun()


def _comunicados(dados: dict) -> None:
    with st.container(key="faq_card_comunicados"):
        st.html('<p class="crh-cfg-titulo">Comunicados</p>')
        if erro := dados["erros"].get("comunicados"):
            alerta(st.empty(), "erro", erro)
            return
        lista = comunicados_ordenados(dados["comunicados"])
        if not lista:
            st.html('<p class="crh-meta">Nenhum comunicado vigente.</p>')
            return
        for c in lista:
            with st.expander(c.get("titulo") or "Comunicado"):
                st.html(f'<p class="crh-meta" style="margin:0">{html.escape(meta_comunicado(c))}</p>')
                st.html(f'<p class="crh-cfg-texto" style="white-space:pre-wrap">{html.escape(c.get("conteudo") or "")}</p>')


def _perguntas(dados: dict) -> None:
    with st.container(key="faq_card_perguntas"):
        st.html('<p class="crh-cfg-titulo">Perguntas frequentes</p>')
        if erro := dados["erros"].get("artigos"):
            alerta(st.empty(), "erro", erro)
            return
        busca = st.text_input("Busca", placeholder="⌕  Busque por férias, ponto, atestado...", key="faq_busca", label_visibility="collapsed")
        contagem = contagem_por_categoria(dados["artigos"])
        opcoes = [None] + [c for c in CATEGORIAS if contagem[c]]
        with st.container(key="faq_cats", width="content"):
            categoria = st.segmented_control("Categoria", opcoes, format_func=lambda c: "Todas" if c is None else CATEGORIAS[c],
                                             default=None, key="faq_categoria", label_visibility="collapsed")
        artigos = filtrar_artigos(dados["artigos"], categoria, busca)
        if not artigos:
            st.html(f'<p class="crh-meta">{"Nenhuma pergunta encontrada para essa busca." if busca else "Nenhuma pergunta nesta categoria."}</p>')
        for a in artigos:
            with st.expander(a.get("titulo") or "Pergunta"):
                st.html(f'<p class="crh-cfg-texto" style="white-space:pre-wrap;margin:0">{html.escape(a.get("conteudo") or "")}</p>')
        st.html('<div class="crh-incluso"><p class="n" style="margin:0">Não achou a resposta? Procure o RH do seu departamento.</p></div>')


@st.dialog("Novo comunicado", width="medium", on_dismiss=_fechar)
def _modal_comunicado(deps: dict) -> None:
    titulo = st.text_input("Título", max_chars=200, key="com_titulo", placeholder="Ex.: Nova política de home office")
    conteudo = st.text_area("Texto", max_chars=5000, height=150, key="com_conteudo")
    c1, c2 = st.columns(2)
    publico = c1.selectbox("Para quem", list(PUBLICOS), format_func=PUBLICOS.get, key="com_publico")
    departamento_id = perfil_alvo = None
    if publico == "departamento":
        ops = sorted(deps, key=lambda i: deps[i] or "")
        departamento_id = c2.selectbox("Departamento", ops, format_func=deps.get, index=None, placeholder="Escolha", key="com_dep")
    elif publico == "perfil":
        perfil_alvo = c2.selectbox("Perfil", PERFIS_ALVO, index=None, placeholder="Escolha", key="com_perfil")
    inicio = c1.date_input("Publicar em", value=hoje_brasilia(), format="DD/MM/YYYY", key="com_inicio")
    fim = c2.date_input("Vigente até (opcional)", value=None, format="DD/MM/YYYY", key="com_fim")
    st.html('<p class="crh-meta">Aparece no Início e nesta tela para quem estiver no público, a partir da data de publicação.</p>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="com_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Publicar comunicado", type="primary", key="com_publicar"):
            if erro_campo := validar_comunicado(titulo, conteudo, publico, departamento_id, perfil_alvo, inicio, fim):
                alerta(slot, "erro", erro_campo)
                return
            try:
                publicar_comunicado(st.session_state.token, {"titulo": titulo.strip(), "conteudo": conteudo.strip(), "publico_alvo": publico,
                                                             "departamento_id": departamento_id, "perfil_alvo": perfil_alvo,
                                                             "data_inicio": inicio.isoformat(), "data_fim": fim.isoformat() if fim else None})
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            for chave in [k for k in st.session_state if str(k).startswith("com_")]:
                st.session_state.pop(chave, None)
            _limpar_caches()
            _fechar()
            st.session_state.aviso_toast = "Comunicado publicado."
            st.rerun()


@st.dialog("Arquivar comunicado?", width="small", on_dismiss=_fechar)
def _modal_arquivar(linha: dict) -> None:
    st.html(f'<p class="crh-cfg-texto"><b>{html.escape(linha["titulo"])}</b></p>'
            '<p class="crh-meta">Sai do Início e desta tela para todos. O registro continua guardado, e a ação fica na auditoria.</p>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="com_arq_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Arquivar", type="primary", key="com_arq_ok"):
            try:
                arquivar_comunicado(st.session_state.token, linha["id"])
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _limpar_caches()
            _fechar()
            st.session_state.aviso_toast = "Comunicado arquivado."
            st.rerun()


def _limpar_caches() -> None:
    for chave in (_CACHE, _CACHE_RH):
        st.session_state.pop(chave, None)


def _carregar_rh(token: str) -> dict:
    cache = st.session_state.get(_CACHE_RH)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = {"comunicados": comunicados_rh(token).get("comunicados") or []}
    try:
        dados["deps"] = {d.get("id"): d.get("nome") for d in organograma(token).get("departamentos") or []}
    except ApiError:
        dados["deps"] = {}
    st.session_state[_CACHE_RH] = {"em": time.time(), "dados": dados}
    return dados


def _comunicados_rh(token: str) -> None:
    """Aba do RH (Figma 245:594, "Comunicados"): todos os comunicados, "Novo comunicado" e "Arquivar"."""
    try:
        dados = _carregar_rh(token)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        st.space("stretch")
        situacao = st.selectbox("Situação", list(SITUACOES_COMUNICADO), format_func=SITUACOES_COMUNICADO.get, key="com_situacao",
                                label_visibility="collapsed", width=200)
        if st.button("Novo comunicado", type="primary", key="com_novo"):
            st.session_state.modal_faq = ("comunicado", None)
            st.rerun()
    linhas = linhas_comunicados_rh(dados["comunicados"], dados["deps"], hoje_brasilia(), situacao)
    pesos = [2.6, 1.4, 1.1, 1.2, 1.0, 0.9]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Comunicado", "Público", "Publicação", "Vigência", "Situação", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">' + ("Nenhum comunicado nesta situação." if dados["comunicados"] else 'Nenhum comunicado. Use "Novo comunicado".') + "</p>")
        for l in linhas:
            with st.container(key=f"rh_lin_com_{l['id']}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["titulo"])}</p></div>')
                c[1].html(f'<p class="crh-doc-prazo">{html.escape(l["publico"])}</p>')
                c[2].html(f'<p class="crh-doc-prazo">{html.escape(l["publicacao"])}</p>')
                c[3].html(f'<p class="crh-doc-prazo">{html.escape(l["vigencia"])}</p>')
                c[4].html(f'<span class="crh-selo {l["situacao"][1]}">{html.escape(l["situacao"][0])}</span>')
                with c[5]:
                    if l["arquivavel"] and st.button("Arquivar", type="tertiary", key=f"com_arquivar_{l['id']}"):
                        st.session_state.modal_faq = ("arquivar", l["id"])
                        st.rerun()
    st.html('<p class="crh-meta">O colaborador vê os comunicados publicados e vigentes no Início e na aba "Consulta".</p>')


def _artigos_rh(dados: dict) -> None:
    """Aba do RH (Figma 245:594, "Artigos da FAQ")."""
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        st.space("stretch")
        if st.button("Novo artigo", type="primary", key="faq_novo"):
            st.session_state.modal_faq = True
            st.rerun()
    if erro := dados["erros"].get("artigos"):
        alerta(st.empty(), "erro", erro)
        return
    artigos = filtrar_artigos(dados["artigos"])
    pesos = [1.2, 4]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Categoria", "Pergunta"]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not artigos:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhum artigo publicado. Use "Novo artigo".</p>')
        for i, a in enumerate(artigos):
            with st.container(key=f"rh_lin_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<span class="crh-selo neu">{html.escape(CATEGORIAS.get(a.get("categoria"), "—"))}</span>')
                c[1].html(f'<p class="crh-doc-prazo">{html.escape(a.get("titulo") or "—")}</p>')


def pagina_faq() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    rh = str(usuario.get("perfil", "")).upper() in ("RH", "ADMIN")
    render_hero("Comunicados e FAQ", "Comunicados do RH e respostas para as dúvidas mais comuns")
    with st.spinner("Carregando..."):
        dados = _carregar(token)

    aba = _ABAS_RH[0]
    if rh:
        with st.container(key="cfg_abas", width="content"):
            if st.session_state.get("faq_aba") not in _ABAS_RH:
                st.session_state.faq_aba = _ABAS_RH[0]
            aba = st.segmented_control("Aba", _ABAS_RH, required=True, key="faq_aba", label_visibility="collapsed")
    if aba == "Artigos da FAQ":
        _artigos_rh(dados)
    elif aba == "Comunicados":
        _comunicados_rh(token)
    else:
        esquerda, direita = st.columns([1, 1.1], gap="medium")
        with esquerda:
            _comunicados(dados)
        with direita:
            _perguntas(dados)

    modal = st.session_state.get("modal_faq")
    if rh and modal:
        if isinstance(modal, tuple) and modal[0] == "comunicado":
            _modal_comunicado((st.session_state.get(_CACHE_RH) or {}).get("dados", {}).get("deps", {}))
        elif isinstance(modal, tuple) and modal[0] == "arquivar":
            linhas = linhas_comunicados_rh((st.session_state.get(_CACHE_RH) or {}).get("dados", {}).get("comunicados", []), {}, hoje_brasilia())
            linha = next((l for l in linhas if l["id"] == modal[1]), None)
            if linha:
                _modal_arquivar(linha)
            else:
                _fechar()
        else:
            _modal_novo()
