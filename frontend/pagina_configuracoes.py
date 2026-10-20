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

Aba "Segurança" (Figma 213:142; change configuracoes-seguranca-notificacoes): trocar senha (`auth/senha`, que
encerra as outras sessões) e sessões e dispositivos (`auth/minhas_sessoes`, `auth/sessoes/{id}/encerrar` e
`auth/sessoes/encerrar_outras`).

Aba "Notificações" (Figma 213:236): por assunto, "Na plataforma" e "E-mail" (`minhas_preferencias_aviso`). Benefícios,
alertas de segurança e pedidos para decidir são sempre ligados. Sem "Comunicados" nem "Frequência dos e-mails": o
backend não manda aviso de comunicado nem resumo diário (docs/figma-pendencias.md).

Tudo é do próprio usuário: nenhum endpoint daqui recebe id de outra pessoa.
"""

import base64
import html
import time

import streamlit as st

from api_client import (
    ApiError,
    criar_pedido_privacidade,
    encerrar_outras_sessoes,
    encerrar_sessao,
    meus_dados,
    minhas_preferencias_aviso,
    minhas_preferencias_privacidade,
    minhas_sessoes,
    minhas_solicitacoes,
    salvar_preferencia_aviso,
    salvar_preferencias_privacidade,
    trocar_senha,
)
from configuracoes_modelo import ASSUNTOS, SEMPRE_LIGADOS, alteradas, linhas_sessoes, preferencias_por_assunto, regras_senha, validar_troca
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


# ---------------------------------------------------------------------------
# Aba Segurança (Figma 213:142)
# ---------------------------------------------------------------------------
_CACHE_SEG = "cfg_seg_cache"
_CACHE_AVISOS = "cfg_avisos_cache"


def _guardado(chave: str, buscar):
    item = st.session_state.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = buscar()
    st.session_state[chave] = {"em": time.time(), "dados": dados}
    return dados


def _plural(n: int, um: str, varios: str) -> str:
    return f"{n} {um if n == 1 else varios}"


def _cartao_senha(token: str) -> None:
    with st.container(key="cfg_card_senha"):
        st.html('<p class="crh-cfg-titulo">Trocar senha</p>'
                '<p class="crh-cfg-texto">Use pelo menos 8 caracteres, com letras e números. Ao trocar, as outras sessões são encerradas.</p>')
        atual = st.text_input("Senha atual", type="password", max_chars=64, key="cfg_senha_atual")
        nova = st.text_input("Nova senha", type="password", max_chars=64, key="cfg_senha_nova")
        confirmar = st.text_input("Confirmar nova senha", type="password", max_chars=64, key="cfg_senha_confirmar")
        regras = "".join(
            f'<p class="crh-cfg-nota crh-regra{" ok" if ok else ""}" style="margin:0">{"✓" if ok else "•"} {html.escape(texto)}</p>'
            for texto, ok in regras_senha(nova, atual)
        )
        st.html(regras)
        slot = st.empty()
        if st.button("Salvar nova senha", type="primary", key="cfg_senha_salvar", width="stretch"):
            erro_campo = validar_troca(atual, nova, confirmar)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                resposta = trocar_senha(token, atual, nova, confirmar)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            for chave in ("cfg_senha_atual", "cfg_senha_nova", "cfg_senha_confirmar", _CACHE_SEG):
                st.session_state.pop(chave, None)
            encerradas = resposta.get("sessoes_encerradas") or 0
            aviso = "Senha alterada."
            if encerradas:
                aviso += " " + _plural(encerradas, "outra sessão encerrada.", "outras sessões encerradas.")
            st.session_state.aviso_toast = aviso
            st.rerun()


def _cartao_sessoes(token: str) -> None:
    with st.container(key="cfg_card_sessoes"):
        st.html('<p class="crh-cfg-titulo">Sessões e dispositivos</p>'
                '<p class="crh-cfg-texto">Lugares onde sua conta está aberta agora. Se não reconhecer algum, encerre e troque a senha.</p>')
        try:
            dados = _guardado(_CACHE_SEG, lambda: minhas_sessoes(token))
        except ApiError as erro:
            alerta(st.empty(), "erro", erro.message)
            return
        linhas = linhas_sessoes(dados.get("sessoes"), dados.get("sessao_atual_id"))
        slot = st.empty()
        for l in linhas:
            with st.container(key=f"cfg_sessao_{l['id']}", horizontal=True, vertical_alignment="center"):
                st.html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["titulo"])}</p><p class="d">{html.escape(l["detalhe"])}</p></div>')
                if l["atual"]:
                    st.html('<span class="crh-selo ok">Este dispositivo</span>', width="content")
                elif st.button("Encerrar", key=f"cfg_encerrar_{l['id']}"):
                    try:
                        encerrar_sessao(token, l["id"])
                    except ApiError as erro:
                        alerta(slot, "erro", erro.message)
                        return
                    st.session_state.pop(_CACHE_SEG, None)
                    st.session_state.aviso_toast = f"Sessão encerrada: {l['titulo']}."
                    st.rerun()
        outras = [l for l in linhas if not l["atual"]]
        if not outras:
            st.html('<p class="crh-cfg-nota">Só este dispositivo está conectado.</p>')
        elif st.button("Encerrar todas as outras sessões", key="cfg_encerrar_todas", width="stretch"):
            try:
                resposta = encerrar_outras_sessoes(token)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            st.session_state.pop(_CACHE_SEG, None)
            total = resposta.get("total_encerradas", len(outras))
            st.session_state.aviso_toast = _plural(total, "sessão encerrada.", "sessões encerradas.") + " Só este dispositivo continua conectado."
            st.rerun()


def _aba_seguranca(token: str) -> None:
    esquerda, direita = st.columns(2, gap="medium")
    with esquerda:
        _cartao_senha(token)
    with direita:
        _cartao_sessoes(token)


# ---------------------------------------------------------------------------
# Aba Notificações (Figma 213:236)
# ---------------------------------------------------------------------------
def _desfazer_avisos(salvas: dict) -> None:
    for assunto, (plataforma, email) in salvas.items():
        st.session_state[f"cfg_av_{assunto}_pl"] = plataforma
        st.session_state[f"cfg_av_{assunto}_em"] = email


def _aba_notificacoes(token: str) -> None:
    with st.container(key="cfg_card_avisos"):
        st.html('<p class="crh-cfg-titulo">Avisos que você recebe</p>'
                '<p class="crh-cfg-texto">Escolha por onde quer ser avisado de cada assunto. Alertas de segurança, avisos de benefícios e '
                'pedidos que esperam a sua decisão não podem ser desligados.</p>')
        try:
            salvas = preferencias_por_assunto(_guardado(_CACHE_AVISOS, lambda: minhas_preferencias_aviso(token)).get("preferencias"))
        except ApiError as erro:
            alerta(st.empty(), "erro", erro.message)
            return
        pesos = [5, 1.4, 1.2]
        with st.container(key="cfg_av_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Assunto", "Na plataforma", "E-mail"]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        escolhidas = {}
        for assunto, titulo, descricao, tem_email in ASSUNTOS:
            st.session_state.setdefault(f"cfg_av_{assunto}_pl", salvas[assunto][0])
            st.session_state.setdefault(f"cfg_av_{assunto}_em", salvas[assunto][1])
            with st.container(key=f"cfg_av_{assunto}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(titulo)}</p><p class="d">{html.escape(descricao)}</p></div>')
                plataforma = c[1].toggle(f"{titulo}: na plataforma", key=f"cfg_av_{assunto}_pl", label_visibility="collapsed")
                if tem_email:
                    email = c[2].toggle(f"{titulo}: e-mail", key=f"cfg_av_{assunto}_em", label_visibility="collapsed")
                else:
                    c[2].html('<p class="crh-cfg-nota" style="margin:0">Sem e-mail</p>')
                    email = salvas[assunto][1]
                escolhidas[assunto] = (plataforma, email)
        for i, (titulo, descricao) in enumerate(SEMPRE_LIGADOS):
            with st.container(key=f"cfg_av_sempre_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(titulo)} <span class="crh-selo amb">Sempre ligado</span></p>'
                          f'<p class="d">{html.escape(descricao)}</p></div>')
                c[1].toggle(f"{titulo}: na plataforma", value=True, disabled=True, key=f"cfg_av_sempre_pl_{i}", label_visibility="collapsed")
                c[2].toggle(f"{titulo}: e-mail", value=True, disabled=True, key=f"cfg_av_sempre_em_{i}", label_visibility="collapsed")
        mudou = alteradas(salvas, escolhidas)
        slot = st.empty()
        with st.container(horizontal=True, horizontal_alignment="right"):
            st.button("Desfazer", key="cfg_av_desfazer", disabled=not mudou, on_click=_desfazer_avisos, args=(salvas,))
            if st.button("Salvar preferências", type="primary", key="cfg_av_salvar", disabled=not mudou):
                try:
                    for assunto, plataforma, email in mudou:
                        salvar_preferencia_aviso(token, assunto, plataforma, email)
                except ApiError as erro:
                    st.session_state.pop(_CACHE_AVISOS, None)
                    alerta(slot, "erro", erro.message)
                    return
                st.session_state.pop(_CACHE_AVISOS, None)
                st.session_state.aviso_toast = "Preferências salvas."
                st.rerun()


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
            "Seção", _ABAS, default="Segurança", required=True, key="cfg_aba", label_visibility="collapsed"
        )
    if aba == "Segurança":
        _aba_seguranca(token)
        return
    if aba == "Notificações":
        _aba_notificacoes(token)
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
