"""
Página "Canal de denúncias" (Figma 540:1196 e os modais 541:1547 e 541:1565; change canal-de-denuncias; Lei
14.457/2022). Para qualquer pessoa: no menu de quem está logado e, sem login, pelo link da tela Entrar.

À esquerda, "Fazer uma denúncia": o que aconteceu, o relato, quando e quem estava envolvido (opcionais) e "Quero me
identificar" (desligado: anônima). À direita, "Acompanhar uma denúncia" pelo código e "Como funciona". As chamadas vão
sempre sem token, mesmo logado: nada liga a denúncia à conta. O código aparece uma única vez, no modal depois do envio.
Endpoints públicos: `denuncias` POST, `denuncias/acompanhar` e `denuncias/responder`.
"""

import html

import streamlit as st

from api_client import ApiError, acompanhar_denuncia, enviar_denuncia, responder_denuncia
from campos import campo
from denuncias_modelo import (COMO_FUNCIONA, RESULTADOS, TIPOS, linhas_conversa, mascarar_codigo, situacao, tipo_legivel, validar_codigo,
                              validar_denuncia, validar_mensagem)
from onboarding_modelo import data_br
from theme import alerta, inject_base_styles, render_hero, render_logo_faixa, render_topbar


def _limpar_formulario() -> None:
    for chave in [k for k in st.session_state if str(k).startswith("cd_form_")]:
        st.session_state.pop(chave, None)


def _fechar_acompanhar() -> None:
    for chave in ("cd_acomp", "cd_acomp_dados", "cd_resposta"):
        st.session_state.pop(chave, None)


@st.dialog("Denúncia enviada", width="small", dismissible=False)
def _modal_codigo(protocolo: str, codigo: str) -> None:
    alerta(st.empty(), "sucesso", "Denúncia enviada. A comissão de ética vai analisar.")
    st.html(f'<div class="crh-cd-codigo"><p class="r">Código de acompanhamento</p><p class="c">{html.escape(codigo)}</p>'
            f'<p class="r">Protocolo {html.escape(protocolo)}</p></div>'
            '<p class="crh-meta">Guarde este código. É a única forma de acompanhar a denúncia, e ele não aparece de novo: '
            'nem a comissão consegue recuperá-lo.</p>')
    if st.button("Já guardei o código", type="primary", key="cd_guardei"):
        st.session_state.pop("cd_enviada", None)
        st.rerun()


@st.dialog("Acompanhar denúncia", width="medium", on_dismiss=_fechar_acompanhar)
def _modal_acompanhar(codigo: str) -> None:
    dados = st.session_state.get("cd_acomp_dados")
    if dados is None:
        try:
            dados = acompanhar_denuncia(codigo)
        except ApiError as erro:
            alerta(st.empty(), "erro", erro.message)
            return
        st.session_state.cd_acomp_dados = dados
    selo, tom = situacao(dados.get("status"))
    st.html(f'<p class="crh-cfg-titulo">Denúncia {html.escape(mascarar_codigo(codigo))}</p>'
            f'<div class="crh-pcr-topo" style="justify-content:flex-start"><span class="crh-selo {tom}">{html.escape(selo)}</span>'
            f'<span class="crh-meta">{html.escape(tipo_legivel(dados.get("tipo")))} · enviada em {html.escape(data_br(dados.get("recebida_em")))}</span></div>')
    if dados.get("status") == "concluida":
        st.html(f'<div class="crh-lgpd-resumo"><div><span>Resultado</span><b>{html.escape(RESULTADOS.get(dados.get("resultado"), "—"))}</b></div></div>'
                f'<p class="crh-meta">Parecer da comissão</p><p class="crh-lgpd-detalhe">{html.escape(dados.get("parecer") or "—")}</p>')
    conversa = linhas_conversa(dados.get("mensagens") or [], para_comissao=False)
    if conversa:
        st.html("".join(f'<div class="crh-cd-msg{" meu" if m["meu_lado"] else ""}"><p class="q">{html.escape(m["quem"])}</p><p class="t">{html.escape(m["texto"])}</p></div>'
                        for m in conversa))
    elif dados.get("status") != "concluida":
        st.html('<p class="crh-meta">A comissão ainda não escreveu. Volte a consultar com o mesmo código.</p>')
    if dados.get("status") == "concluida":
        return
    texto = campo(st, "Responder à comissão", "texto", "cd_resposta", area=True, max_chars=2000, height=90,
                  placeholder="Escreva sem colocar seu nome, se não quiser se identificar.")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Fechar", key="cd_acomp_fechar"):
            _fechar_acompanhar()
            st.rerun()
        if st.button("Enviar resposta", type="primary", key="cd_responder"):
            erro = validar_mensagem(texto, 2)
            if erro:
                alerta(slot, "erro", erro)
                return
            try:
                responder_denuncia(codigo, texto.strip())
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            st.session_state.pop("cd_acomp_dados", None)
            st.session_state.pop("cd_resposta", None)
            st.session_state.aviso_toast = "Mensagem enviada à comissão."
            st.rerun()


def _formulario() -> None:
    with st.container(key="cfg_card_cd_form"):
        st.html('<p class="crh-cfg-titulo">Fazer uma denúncia</p>')
        alerta(st.empty(), "atencao", "Se não se identificar, ninguém na empresa sabe quem enviou. Só a comissão de ética lê e apura.")
        tipo = st.selectbox("O que aconteceu", list(TIPOS), index=None, format_func=TIPOS.get, placeholder="Escolha o tipo", key="cd_form_tipo")
        relato = campo(st, "Conte o que aconteceu", "texto", "cd_form_relato", area=True, max_chars=4000, height=120,
                       placeholder="O que aconteceu, como e com que frequência. Não precisa colocar seu nome.")
        c1, c2 = st.columns(2)
        quando = campo(c1, "Quando aconteceu (opcional)", "texto", "cd_form_quando", max_chars=100, placeholder="Ex.: desde agosto de 2026")
        envolvidos = campo(c2, "Pessoas envolvidas (opcional)", "texto", "cd_form_envolvidos", max_chars=200, placeholder="Ex.: gestor da equipe")
        identificar = st.toggle("Quero me identificar", key="cd_form_identificar")
        st.html('<p class="crh-meta">Desligado: a denúncia é anônima. Ligado: só a comissão vê seu nome, e ele não é repassado a ninguém.</p>')
        identificacao = ""
        if identificar:
            identificacao = campo(st, "Seu nome e um contato", "texto", "cd_form_identificacao", max_chars=200, placeholder="Nome e e-mail ou telefone")
        slot = st.empty()
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Limpar", key="cd_limpar"):
                _limpar_formulario()
                st.rerun()
            if st.button("Enviar denúncia", type="primary", key="cd_enviar"):
                erro = validar_denuncia(tipo, relato, identificar, identificacao)
                if erro:
                    alerta(slot, "erro", erro)
                    return
                try:
                    r = enviar_denuncia(tipo, relato.strip(), (quando or "").strip(), (envolvidos or "").strip(), (identificacao or "").strip() if identificar else None)
                except ApiError as erro_api:
                    alerta(slot, "erro", erro_api.message)
                    return
                _limpar_formulario()
                st.session_state.cd_enviada = (r.get("protocolo") or "", r.get("codigo") or "")
                st.rerun()


def _lado_direito() -> None:
    with st.container(key="cfg_card_cd_acomp"):
        st.html('<p class="crh-cfg-titulo">Acompanhar uma denúncia</p>'
                '<p class="crh-meta">Use o código que você recebeu ao enviar. Por ele você vê a situação e conversa com a comissão, sem se identificar.</p>')
        codigo = st.text_input("Código de acompanhamento", key="cd_codigo", placeholder="XXXX-XXXX-XXXX-XXXX", max_chars=19)
        slot = st.empty()
        if st.button("Consultar", key="cd_consultar"):
            erro = validar_codigo(codigo)
            if erro:
                alerta(slot, "erro", erro)
            else:
                st.session_state.pop("cd_acomp_dados", None)
                st.session_state.cd_acomp = codigo.strip()
                st.rerun()
    passos = "".join(f'<div class="crh-pd-passo"><span class="n">{i}</span><div><p class="t">{html.escape(t)}</p><p class="d">{html.escape(d)}</p></div></div>'
                     for i, (t, d) in enumerate(COMO_FUNCIONA, start=1))
    st.html(f'<div class="crh-painel crh-bloco"><p class="crh-cfg-titulo">Como funciona</p>{passos}</div>')


def _conteudo() -> None:
    render_hero("Canal de denúncias", "Relate assédio, discriminação ou conduta irregular, com ou sem se identificar")
    esquerda, direita = st.columns([1.45, 1], gap="medium")
    with esquerda:
        _formulario()
    with direita:
        _lado_direito()
    if st.session_state.get("cd_enviada"):
        _modal_codigo(*st.session_state.cd_enviada)
    elif st.session_state.get("cd_acomp"):
        _modal_acompanhar(st.session_state.cd_acomp)


def pagina_canal_denuncias() -> None:
    render_topbar(st.session_state.usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    _conteudo()


def pagina_canal_publico() -> None:
    inject_base_styles("canal")
    with st.container(horizontal=True, key="aviso_faixa"):
        render_logo_faixa()
        if st.button("Entrar", type="primary", key="btn_cd_entrar"):
            st.session_state.ir_entrar = True
            st.rerun()
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    _conteudo()
