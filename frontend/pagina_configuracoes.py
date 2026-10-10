"""
Página "Configurações", aba "Privacidade" (Figma 286:878; tarefas 5 e 67 da change
concluir-frontend-streamlit). Aberta pelo menu da conta (chip do nome, Figma 198:158).

Cartões, como no Figma:
- Aviso de privacidade: versão do aviso e "Ler aviso completo →" (pagina_aviso.py);
- Meus dados: "Baixar meus dados" (modal 286:1062, sucesso 286:1092; `meus_dados?formato=`) e
  "Fazer um pedido" (modal 224:2379; `solicitacoes` com tipo `privacidade_lgpd`);
- Fale com o encarregado: nome e contato do aviso (docs/lgpd/aviso-de-privacidade.md);
- O que os colegas veem: aniversariantes e mural (`minhas_preferencias_privacidade`);
- Meus pedidos de privacidade: os pedidos `privacidade_lgpd` de `minhas_solicitacoes`.

Tudo é do próprio usuário: nenhum endpoint daqui recebe id de outra pessoa. As abas "Segurança"
e "Notificações" já têm desenho (213:142 e 213:236), mas ainda não foram construídas (tarefas da
seção 2 do tasks.md).
"""

import base64
import html
import time

import streamlit as st

from api_client import (
    ApiError,
    criar_pedido_privacidade,
    meus_dados,
    minhas_preferencias_privacidade,
    minhas_solicitacoes,
    salvar_preferencias_privacidade,
)
from aviso_privacidade import encarregado, versao
from privacidade_modelo import FORMATOS, OPCOES_PEDIDO, arquivo_exportado, pedidos_privacidade, validar_pedido
from theme import alerta, render_linhas_onboarding, render_titulo_pagina, render_topbar

_ABAS = ["Segurança", "Notificações", "Privacidade"]
_CACHE = "privacidade_cache"
_VALIDADE_CACHE_S = 20


def _carregar(token: str) -> dict:
    """{'preferencias': dict | ApiError, 'pedidos': list | ApiError}, guardado por 20 s (limite do Xano)."""
    cache = st.session_state.get(_CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = {}
    try:
        dados["preferencias"] = minhas_preferencias_privacidade(token)
    except ApiError as erro:
        dados["preferencias"] = erro
    try:
        dados["pedidos"] = pedidos_privacidade(minhas_solicitacoes(token).get("solicitacoes") or [])
    except ApiError as erro:
        dados["pedidos"] = erro
    st.session_state[_CACHE] = {"em": time.time(), "dados": dados}
    return dados


def _invalidar() -> None:
    st.session_state.pop(_CACHE, None)


# ---------------------------------------------------------------------------
# Modais. Ficam abertos enquanto `modal_privacidade` estiver na sessão, para continuarem na
# tela mesmo quando o app inteiro roda de novo (e não só o modal).
# ---------------------------------------------------------------------------
def _fechar_modal() -> None:
    st.session_state.pop("modal_privacidade", None)
    st.session_state.pop("exportacao_gerada", None)


def _disparar_download(nome: str, conteudo: bytes, mime: str) -> None:
    """Começa o download no navegador (Figma 286:1092: "O download começou"). O script não usa o
    sinal de menor: o DOMPurify do st.html descartaria o bloco."""
    dados = base64.b64encode(conteudo).decode("ascii")
    st.html(
        f'<div id="crh-download" data-nome="{html.escape(nome)}" data-mime="{html.escape(mime)}" data-b64="{dados}" style="display:none"></div>'
        "<script>(function(){var el=document.getElementById('crh-download');if(!el||el.dataset.feito)return;"
        "el.dataset.feito='1';var a=document.createElement('a');"
        "a.href='data:'+el.dataset.mime+';base64,'+el.dataset.b64;a.download=el.dataset.nome;"
        "document.body.appendChild(a);a.click();a.remove();})();</script>",
        unsafe_allow_javascript=True,
    )


@st.dialog("Baixar meus dados", width="small", on_dismiss=_fechar_modal)
def _modal_baixar() -> None:
    gerado = st.session_state.get("exportacao_gerada")
    if gerado:
        nome, conteudo, mime = gerado
        alerta(st.empty(), "sucesso", f"Arquivo gerado. O download começou ({nome}).")
        st.html(
            '<p class="crh-cfg-texto">Se o download não abrir, gere o arquivo de novo. Guarde o arquivo '
            "em local seguro: ele tem dados pessoais seus.</p>"
        )
        if st.session_state.pop("exportacao_disparar", False):
            _disparar_download(nome, conteudo, mime)
        with st.container(horizontal=True):
            if st.button("Gerar de novo", key="btn_exp_de_novo"):
                st.session_state.pop("exportacao_gerada", None)
                st.rerun()
            if st.button("Fechar", type="primary", key="btn_exp_fechar"):
                _fechar_modal()
                st.rerun()
        return

    st.html(
        '<p class="crh-cfg-texto">Escolha o formato do arquivo. Ele traz só os seus dados e a exportação '
        "fica registrada na auditoria.</p>"
    )
    formato = st.radio(
        "Formato",
        list(FORMATOS),
        format_func=lambda f: FORMATOS[f][0],
        captions=[FORMATOS[f][1] for f in FORMATOS],
        key="exp_formato",
        label_visibility="collapsed",
    )
    st.html(
        '<div class="crh-incluso"><p class="t">O arquivo inclui</p><ul>'
        "<li>Cadastro, contrato e histórico</li><li>Metadados de documentos</li>"
        "<li>Férias, ausências, ponto e banco de horas</li><li>Avaliações, metas e PDI</li>"
        "<li>Solicitações e notificações</li><li>Sessões</li></ul>"
        '<p class="n">Não inclui respostas de pesquisa de clima (são anônimas) nem dados de outras pessoas.</p></div>'
    )
    slot = st.empty()
    with st.container(horizontal=True):
        if st.button("Cancelar", key="btn_exp_cancelar"):
            _fechar_modal()
            st.rerun()
        if st.button("Baixar arquivo", type="primary", key="btn_exp_baixar"):
            try:
                with st.spinner("Gerando o arquivo..."):
                    resposta = meus_dados(st.session_state.token, formato)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            st.session_state.exportacao_gerada = arquivo_exportado(resposta, formato)
            st.session_state.exportacao_disparar = True
            st.rerun()


@st.dialog("Fazer um pedido", width="small", on_dismiss=_fechar_modal)
def _modal_pedido() -> None:
    st.html(
        '<p class="crh-cfg-texto">O RH recebe o pedido e responde em até 15 dias. Você acompanha em '
        '"Meus pedidos".</p>'
    )
    subtipo = st.radio(
        "O que você precisa?", list(OPCOES_PEDIDO), format_func=OPCOES_PEDIDO.get, index=None, key="pedido_subtipo"
    )
    descricao = st.text_area("Detalhe o pedido", max_chars=2000, key="pedido_descricao", height=110)
    slot = st.empty()
    with st.container(horizontal=True):
        if st.button("Cancelar", key="btn_pedido_cancelar"):
            _fechar_modal()
            st.rerun()
        if st.button("Enviar pedido", type="primary", key="btn_pedido_enviar"):
            erro_campo = validar_pedido(subtipo, descricao)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                criar_pedido_privacidade(st.session_state.token, subtipo, descricao.strip())
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _invalidar()
            _fechar_modal()
            for chave in ("pedido_subtipo", "pedido_descricao"):
                st.session_state.pop(chave, None)
            st.session_state.aviso_toast = "Pedido enviado. O RH responde em até 15 dias."
            st.rerun()


# ---------------------------------------------------------------------------
# Cartões
# ---------------------------------------------------------------------------
def _cartao_aviso() -> None:
    with st.container(key="cfg_card_aviso"):
        st.html(
            '<p class="crh-cfg-titulo">Aviso de privacidade</p>'
            '<p class="crh-cfg-texto">Explica quais dados seus o ConectaRH usa, para quê, por quanto tempo e '
            "com quem compartilha (por exemplo, o envio de e-mails).</p>"
            f'<div class="crh-cfg-selos"><span class="crh-selo neu">{html.escape(versao())}</span></div>'
        )
        if st.button("Ler aviso completo →", type="tertiary", key="btn_ler_aviso"):
            st.session_state.ir_aviso = True
            st.rerun()


def _cartao_meus_dados() -> None:
    with st.container(key="cfg_card_dados"):
        st.html(
            '<p class="crh-cfg-titulo">Meus dados</p>'
            '<p class="crh-cfg-texto">Baixe uma cópia dos seus dados ou peça ao RH para corrigir, apagar o que '
            "não é obrigatório ou explicar com quem eles são compartilhados.</p>"
        )
        with st.container(horizontal=True):
            if st.button("Baixar meus dados", key="btn_baixar_dados"):
                st.session_state.pop("exportacao_gerada", None)
                st.session_state.modal_privacidade = "baixar"
            if st.button("Fazer um pedido", type="primary", key="btn_fazer_pedido"):
                st.session_state.modal_privacidade = "pedido"
        st.html(
            '<p class="crh-cfg-nota">Você escolhe JSON ou CSV. O arquivo fica pronto na hora e a exportação '
            "fica registrada na auditoria.</p>"
        )


def _cartao_encarregado() -> None:
    contato = encarregado()
    with st.container(key="cfg_card_encarregado"):
        campos = "".join(
            f'<p class="r">{html.escape(rotulo)}</p><p class="v">{html.escape(valor)}</p>' for rotulo, valor in contato.items()
        )
        st.html(
            '<p class="crh-cfg-titulo">Fale com o encarregado</p>'
            '<p class="crh-cfg-texto">O encarregado recebe os seus pedidos de privacidade e responde às '
            "dúvidas. O prazo de resposta é de 15 dias.</p>"
            f'<div class="crh-campos">{campos}</div>'
            '<p class="crh-cfg-nota">Se não ficar satisfeito com a resposta, você também pode falar com a ANPD.</p>'
        )


def _salvar_preferencias(atual: dict) -> None:
    """Callback dos dois botões: grava os dois campos juntos (o PATCH exige os dois)."""
    aniversario = st.session_state.get("pref_aniversario", not atual["ocultar_aniversario"])
    mural = st.session_state.get("pref_mural", not atual["ocultar_mural"])
    try:
        salvar_preferencias_privacidade(st.session_state.token, not aniversario, not mural)
        st.session_state.aviso_toast = "Preferência salva."
    except ApiError as erro:
        st.session_state.aviso_toast = erro.message
        # Volta o botão para o valor que está gravado.
        st.session_state.pref_aniversario = not atual["ocultar_aniversario"]
        st.session_state.pref_mural = not atual["ocultar_mural"]
    _invalidar()


def _cartao_colegas(preferencias) -> None:
    with st.container(key="cfg_card_colegas"):
        st.html(
            '<p class="crh-cfg-titulo">O que os colegas veem</p>'
            '<p class="crh-cfg-texto">Você pode sair das listas abertas para toda a empresa.</p>'
        )
        if isinstance(preferencias, ApiError):
            if preferencias.status_code == 404:
                st.html(
                    '<p class="crh-cfg-nota">Sua conta não tem cadastro de colaborador, então não aparece nos '
                    "aniversariantes nem no mural.</p>"
                )
            else:
                alerta(st.empty(), "erro", preferencias.message)
            return
        # O valor inicial vai pela Session State (e não por `value=`), porque o callback pode
        # desfazer a mudança quando o backend recusa.
        st.session_state.setdefault("pref_aniversario", not preferencias["ocultar_aniversario"])
        st.session_state.setdefault("pref_mural", not preferencias["ocultar_mural"])
        st.toggle(
            "Aparecer em aniversariantes",
            key="pref_aniversario",
            on_change=_salvar_preferencias,
            args=(preferencias,),
        )
        st.html('<p class="crh-cfg-nota" style="margin-top:-10px">Mostra só dia e mês, nunca o ano</p>')
        st.toggle(
            "Aparecer no mural de reconhecimentos",
            key="pref_mural",
            on_change=_salvar_preferencias,
            args=(preferencias,),
        )
        st.html('<p class="crh-cfg-nota" style="margin-top:-10px">Elogios que você recebe ficam visíveis</p>')
        if preferencias.get("padrao") and preferencias.get("menor_de_idade"):
            st.html('<p class="crh-cfg-nota">Por você ter menos de 18 anos, as duas opções começam desligadas.</p>')


def _cartao_pedidos(pedidos) -> None:
    with st.container(key="cfg_card_pedidos"):
        st.html(
            '<p class="crh-cfg-titulo">Meus pedidos de privacidade</p>'
            '<p class="crh-cfg-texto">O RH responde em até 15 dias.</p>'
        )
        if isinstance(pedidos, ApiError):
            if pedidos.status_code == 404:
                st.html(
                    '<p class="crh-cfg-nota">Sua conta não tem cadastro de colaborador: envie o pedido ao '
                    "encarregado pelo contato ao lado.</p>"
                )
            else:
                alerta(st.empty(), "erro", pedidos.message)
            return
        if not pedidos:
            st.html('<p class="crh-cfg-nota">Você ainda não fez nenhum pedido.</p>')
            return
        render_linhas_onboarding(pedidos)


def pagina_configuracoes() -> None:
    token = st.session_state.token
    render_topbar(st.session_state.usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)

    render_titulo_pagina(
        "Configurações", "Cuide da sua senha, dos seus acessos, dos avisos que recebe e da sua privacidade."
    )
    with st.container(key="cfg_abas"):
        aba = st.segmented_control(
            "Seção", _ABAS, default="Privacidade", required=True, key="cfg_aba", label_visibility="collapsed"
        )
    if aba != "Privacidade":
        st.html(
            f'<p class="crh-nota-ambar">A aba {html.escape(aba)} ainda está em construção. Por enquanto, '
            "use a aba Privacidade.</p>"
        )
        return

    with st.spinner("Carregando..."):
        dados = _carregar(token)

    esquerda, direita = st.columns(2, gap="medium")
    with esquerda:
        _cartao_aviso()
        _cartao_meus_dados()
        _cartao_encarregado()
    with direita:
        _cartao_colegas(dados["preferencias"])
        _cartao_pedidos(dados["pedidos"])

    modal = st.session_state.get("modal_privacidade")
    if modal == "baixar":
        _modal_baixar()
    elif modal == "pedido":
        _modal_pedido()
