"""F17 — consulta e cancelamento; criação e encaminhamento de filas continuam indisponíveis."""

import html

import streamlit as st

from api_client import ApiError
from delegacoes_dados import cancelar, carregar, invalidar
from delegacoes_modelo import hoje_utc, linhas
from theme import alerta, render_hero, render_titulo_cartao, render_topbar


def _fechar() -> None:
    st.session_state.pop("dg_modal", None)


@st.dialog("Nova delegação", width="small", on_dismiss=_fechar)
def _modal_nova_delegacao() -> None:
    st.selectbox("Substituto", [], placeholder="Seleção de substituto indisponível", disabled=True, key="dg_substituto")
    alerta(st.empty(), "atencao", "Não é possível selecionar um substituto nesta versão. A criação de delegações depende da disponibilização dessa seleção.")
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="dg_fechar_nova"):
            _fechar()
            st.rerun()
        st.button("Criar delegação", type="primary", disabled=True, key="dg_criar")


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
        st.html('<p class="crh-meta">Consulte as delegações concedidas e recebidas. Você pode cancelar as que concedeu. '
                'As filas da Central de Pendências ainda não incluem pedidos recebidos por delegação. '
                'As decisões continuam registradas na auditoria.</p>')
    with direita, st.container(border=True):
        render_titulo_cartao("Escopos possíveis")
        st.html('<p class="crh-meta">Férias e correção de ponto possuem integração com delegações. '
                'Os demais escopos cadastrados não têm essa integração. '
                '“Todas as aprovações” também se limita a férias e correção de ponto.</p>')


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
    itens = linhas(dados["delegacoes"], usuario.get("id"), hoje_utc())
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
    st.html('<p class="crh-meta">Nomes de titulares e substitutos não estão disponíveis nesta versão. '
            'A vigência segue a data de referência do sistema (UTC).</p>')
    _cartoes()
    if st.session_state.get("dg_modal") == "nova":
        _modal_nova_delegacao()
