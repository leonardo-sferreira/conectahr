"""F17 — consulta, cancelamento e criação (change backend-gestor-pendencias, D3): o substituto vem do catálogo
`delegacoes/substitutos` (pessoas do setor e outros Gestores) e o Gestor delega só férias, correção de ponto ou todas.
Durante a delegação, a Central do substituto mostra os pedidos do titular, marcados "por delegação de"."""

import html
import time

import streamlit as st

from api_client import ApiError, criar_delegacao, delegacoes_substitutos
from delegacoes_dados import cancelar, carregar, invalidar
from delegacoes_modelo import ESCOPOS, hoje_brasilia, linhas, rotulo_substituto, validar_nova
from theme import alerta, render_hero, render_titulo_cartao, render_topbar


def _fechar() -> None:
    st.session_state.pop("dg_modal", None)


def _catalogo(token: str) -> dict:
    item = st.session_state.get("dg_catalogo")
    if item and item["token"] == token and time.time() - item["em"] < 60:
        return item["dados"]
    dados = delegacoes_substitutos(token)
    st.session_state.dg_catalogo = {"token": token, "em": time.time(), "dados": dados}
    return dados


@st.dialog("Nova delegação", width="small", on_dismiss=_fechar)
def _modal_nova_delegacao() -> None:
    token = st.session_state.token
    try:
        catalogo = _catalogo(token)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    substitutos = {s["user_id"]: s for s in catalogo.get("substitutos") or []}
    escopos = [e for e in catalogo.get("escopos") or [] if e in ESCOPOS]
    substituto = st.selectbox("Substituto", list(substitutos), index=None, format_func=lambda u: rotulo_substituto(substitutos[u]),
                              placeholder="Escolha quem decide no seu lugar", key="dg_substituto")
    escopo = st.selectbox("O que delegar", escopos, index=None, format_func=ESCOPOS.get, placeholder="Escolha", key="dg_escopo")
    hoje = hoje_brasilia()
    c1, c2 = st.columns(2)
    inicio = c1.date_input("Início", value=hoje, format="DD/MM/YYYY", key="dg_inicio")
    fim = c2.date_input("Fim", value=None, format="DD/MM/YYYY", key="dg_fim")
    motivo = st.text_area("Motivo", max_chars=1000, height=80, placeholder="Ex.: férias de 01/12 a 15/12", key="dg_motivo")
    st.html('<p class="crh-nota-neutra">O substituto recebe um aviso e, no período, vê na Central os pedidos que você decidiria. '
            'As outras decisões continuam com o RH.</p>')
    erro_slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="dg_fechar_nova"):
            _fechar()
            st.rerun()
        if st.button("Criar delegação", type="primary", key="dg_criar"):
            erro = validar_nova(substituto, escopo, inicio, fim, motivo, hoje)
            if erro:
                alerta(erro_slot, "erro", erro)
                return
            try:
                criar_delegacao(token, substituto, escopo, inicio.isoformat(), fim.isoformat(), motivo.strip())
            except ApiError as erro_api:
                alerta(erro_slot, "erro", erro_api.message)
                return
            invalidar()
            _fechar()
            st.session_state.dg_aviso = f"Delegação criada para {substitutos[substituto].get('nome')}."
            st.rerun()


def _mensagem(tipo: str, texto: str) -> None:
    with st.container(border=True):
        alerta(st.empty(), tipo, texto)


def _tabela(itens: list[dict]) -> None:
    pesos = [2.65, 2.2, 1.8, 1.2, .85]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, nome in zip(st.columns(pesos), ("Pessoa", "Escopo", "Período", "Situação", "")):
                coluna.html(f'<p class="crh-doc-cab">{nome}</p>')
        if not itens:
            st.html('<p class="crh-meta">Nenhuma delegação nesta aba.</p>')
        for item in itens:
            with st.container(key=f"rh_lin_dg_{item['id']}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(item["pessoa"])}</p>'
                          f'<p class="d">{html.escape(item["direcao"])}</p><p class="d">Motivo: {html.escape(item["motivo"])}</p></div>')
                c[1].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(item["escopo"])}</p>'
                          f'<p class="d">{html.escape(item["nota_escopo"])}</p></div>')
                c[2].html(f'<p class="crh-doc-prazo">{html.escape(item["periodo"])}</p>')
                c[3].html(f'<span class="crh-selo {item["tom"]}">{html.escape(item["situacao"])}</span>')
                if item["cancelavel"]:
                    with c[4], st.container(key=f"rh_recusar_dg_{item['id']}"):
                        if st.button("Cancelar", type="tertiary", key=f"dg_cancelar_{item['id']}"):
                            try:
                                with st.spinner("Cancelando..."):
                                    cancelar(st.session_state.token, st.session_state.usuario.get("id"), item["id"])
                            except ApiError as erro:
                                st.session_state.dg_erro = erro.message
                            else:
                                st.session_state.dg_aviso = "Delegação cancelada com sucesso."
                                st.session_state.dg_aba_pendente = "Encerradas"
                            st.rerun()


def _cartoes() -> None:
    esquerda, direita = st.columns(2, gap="medium")
    with esquerda, st.container(border=True):
        render_titulo_cartao("Como funciona")
        st.html('<p class="crh-meta">Crie uma delegação para alguém do seu setor ou outro Gestor e cancele quando quiser. '
                'Durante o período, a Central de Pendências do substituto mostra os pedidos que você decidiria, marcados '
                '"por delegação". As decisões ficam registradas na auditoria.</p>')
    with direita, st.container(border=True):
        render_titulo_cartao("Escopos possíveis")
        st.html('<p class="crh-meta">O Gestor delega férias, correção de ponto ou “Todas as aprovações” (as duas). '
                'Ausências, documentos, desligamentos e solicitações ao RH são decisões do RH.</p>')


def pagina_delegacoes() -> None:
    usuario = st.session_state.usuario
    render_topbar(usuario.get("nome") or "")
    render_hero("Delegações", "Passe suas aprovações para outra pessoa durante férias ou ausências")
    if str(usuario.get("perfil") or "").strip().upper() != "GESTOR":
        _mensagem("erro", "Você não tem permissão para acessar esta tela.")
        return
    if st.session_state.get("dg_sessao") == (st.session_state.token, usuario.get("id")):
        if aviso := st.session_state.pop("dg_aviso", None):
            _mensagem("sucesso", aviso)
        if erro := st.session_state.pop("dg_erro", None):
            _mensagem("erro", erro)
    try:
        with st.spinner("Carregando..."):
            dados = carregar(st.session_state.token, usuario.get("id"))
    except ApiError as erro:
        if erro.status_code != 401:
            _mensagem("erro", erro.message)
            if st.button("Tentar novamente", key="dg_repetir"):
                invalidar()
                st.rerun()
        return
    if pendente := st.session_state.pop("dg_aba_pendente", None):
        st.session_state.dg_aba = pendente
    st.session_state.setdefault("dg_aba", "Ativas e futuras")
    try:
        nomes = {s["user_id"]: s.get("nome") for s in _catalogo(st.session_state.token).get("substitutos") or []}
    except ApiError:
        nomes = {}
    itens = linhas(dados["delegacoes"], usuario.get("id"), hoje_brasilia(), nomes)
    if dados["incompletas"] or any(i["situacao"] == "Não disponível" or i["escopo"] == "Não disponível" for i in itens):
        _mensagem("atencao", "Algumas delegações chegaram com informações incompletas. Confira novamente em instantes.")
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Delegações", ["Ativas e futuras", "Encerradas"],
                                       required=True, key="dg_aba", label_visibility="collapsed")
        st.space("stretch")
        if st.button("Atualizar", type="tertiary", key="dg_atualizar"):
            invalidar()
            _fechar()
            st.rerun()
        if st.button("Nova delegação", type="primary", key="dg_nova"):
            st.session_state.dg_modal = "nova"
            st.rerun()
    _tabela([i for i in itens if i["encerrada"] == (aba == "Encerradas")])
    st.html('<p class="crh-meta">Os nomes aparecem quando a pessoa está no seu catálogo de substitutos. '
            'A vigência segue a data de referência do sistema (UTC).</p>')
    _cartoes()
    if st.session_state.get("dg_modal") == "nova":
        _modal_nova_delegacao()
