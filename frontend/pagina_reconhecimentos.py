"""
Reconhecimentos (tarefa 66 da change concluir-frontend-streamlit): "Mural de reconhecimentos" (Figma 291:908, 291:1075
e 291:1239), com as abas Mural, Recebidos e Enviados e o modal "Reconhecer colega" (291:1631 e 291:1667), e "Moderar
reconhecimentos" do RH (291:1374, com o modal 291:1703). As duas páginas se abrem pela Trajetória, que fica marcada
no menu (decisão no `design.md` da change).

A visibilidade é do backend: quando quem envia é o gestor do departamento de quem recebe, o reconhecimento fica
privado; nos outros casos, vai para o mural. O mural respeita "Aparecer no mural" (Configurações → Privacidade).
Nenhuma tela oferece promoção nem punição a partir de um reconhecimento.

Endpoints: `mural_reconhecimento`, `meus_reconhecimentos_recebidos`, `meus_reconhecimentos_enviados`,
`competencias_reconhecimento`, `reconhecimentos` POST, `reconhecimentos_moderacao` e `reconhecimentos/{id}/moderar`.

Diferenças do Figma: o RH e o Admin veem "Moderar →" ao lado de "Reconhecer colega" (o Figma não desenha o caminho
até a moderação), e "Enviados" mostra o motivo quando o RH moderou, como diz o modal 291:1703 ("quem enviou vê").
"""

import html
import time

import streamlit as st

import reconhecimentos_modelo as rm
from api_client import (ApiError, competencias_reconhecimento, enviar_reconhecimento, meus_reconhecimentos_enviados, meus_reconhecimentos_recebidos,
                        minhas_preferencias_privacidade, moderar_reconhecimento, mural_reconhecimento, organograma, reconhecimentos_moderacao)
from campos import campo
from theme import alerta, render_hero, render_topbar

_VALIDADE_CACHE_S = 20
RH = ("RH", "ADMIN")


def _guardado(chave: str, buscar):
    item = st.session_state.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = buscar()
    st.session_state[chave] = {"em": time.time(), "dados": dados}
    return dados


def _limpar_cache() -> None:
    for chave in [k for k in st.session_state if str(k).startswith("rec_cache_")]:
        st.session_state.pop(chave, None)


def _cartao(c: dict, i: int, prefixo: str, botao: str | None = None) -> bool:
    selos = "".join(f'<span class="crh-selo {tom}">{html.escape(t)}</span>' for t, tom in c["selos"])
    nota = f'<p class="nota">{html.escape(c["nota"])}</p>' if c.get("nota") else ""
    with st.container(key=f"rec_card_{prefixo}_{i}"):
        st.html(f'<div class="crh-rc"><div class="av">{html.escape(rm.iniciais(c["autor"] if c["autor"] != "Você" else c["destinatario"]))}</div>'
                f'<div class="corpo"><div class="topo"><p class="quem"><b>{html.escape(c["autor"])}</b> {html.escape(c["frase"])}</p>'
                f'<div class="selos">{selos}</div></div><p class="t">{html.escape(c["titulo"])}</p><p class="m">{html.escape(c["mensagem"])}</p>'
                f'<p class="q">{html.escape(c["quando"])}</p>{nota}</div></div>')
        return bool(botao) and st.button(botao, key=f"rec_btn_{prefixo}_{c['id']}")


def _vazio(titulo: str, texto: str, com_botao: bool) -> None:
    with st.container(key="rec_card_vazio_0"):
        st.html(f'<div class="crh-rc-vazio"><div class="ic">★</div><p class="t">{html.escape(titulo)}</p><p class="d">{html.escape(texto)}</p></div>')
        if com_botao:
            with st.container(horizontal=True, horizontal_alignment="center"):
                if st.button("Reconhecer colega", type="primary", key="rec_novo_vazio"):
                    st.session_state.rec_modal = "novo"
                    st.rerun()


@st.dialog("Reconhecer colega", width="small", on_dismiss=lambda: st.session_state.pop("rec_modal", None))
def _modal_novo(meu_colaborador_id) -> None:
    token = st.session_state.token
    try:
        colegas = rm.opcoes_colegas(_guardado("rec_cache_org", lambda: organograma(token)))
        competencias = _guardado("rec_cache_comp", lambda: competencias_reconhecimento(token)).get("competencias") or []
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    nomes = dict(colegas)
    destinatario = st.selectbox("Colega", [c[0] for c in colegas], format_func=nomes.get, index=None, placeholder="Escolha o colega", key="rec_colega")
    comp_nomes = {c["id"]: c["nome"] for c in competencias}
    competencia = st.selectbox("Competência", list(comp_nomes), format_func=comp_nomes.get, index=None, placeholder="Escolha a competência", key="rec_comp")
    erro_si = rm.erro_destinatario(destinatario, meu_colaborador_id)
    if erro_si:
        st.html(f'<p class="crh-alerta-inline">{html.escape(erro_si)}</p>')
    titulo = campo(st, "Título", "texto", "rec_titulo", max_chars=rm.MAX_TITULO)
    mensagem = campo(st, "Mensagem", "texto", "rec_mensagem", area=True, max_chars=rm.MAX_MENSAGEM, height=100)
    if not erro_si:
        st.html('<div class="crh-nota-ambar">Vai para o mural e só pode ter conteúdo positivo. Se você é gestor desta pessoa, o reconhecimento '
                "fica privado e pode trazer pontos de melhoria.</div>")
    slot = st.empty()
    with st.container(horizontal=True):
        if st.button("Cancelar", key="rec_cancelar"):
            st.session_state.pop("rec_modal", None)
            st.rerun()
        if st.button("Enviar reconhecimento", type="primary", key="rec_enviar", disabled=bool(erro_si)):
            if erro := rm.validar_envio(destinatario, meu_colaborador_id, competencia, titulo, mensagem):
                alerta(slot, "erro", erro)
                return
            try:
                enviar_reconhecimento(token, destinatario, competencia, titulo.strip(), mensagem.strip())
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            for chave in ("rec_modal", "rec_colega", "rec_comp", "rec_titulo", "rec_mensagem"):
                st.session_state.pop(chave, None)
            _limpar_cache()
            st.session_state.aviso_toast = "Reconhecimento enviado."
            st.rerun()


def pagina_reconhecimentos() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Mural de reconhecimentos", "Elogios entre colegas, visíveis para toda a empresa. Só reconhecimento positivo aparece aqui.")
    with st.container(horizontal=True, vertical_alignment="center"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Aba", list(rm.ABAS), format_func=rm.ABAS.get, default="mural", required=True, key="rec_aba",
                                       label_visibility="collapsed")
        st.space("stretch")
        if str(usuario.get("perfil", "")).upper() in RH and st.button("Moderar →", type="tertiary", key="rec_ir_moderar"):
            st.session_state.ir_moderar_reconhecimentos = True
            st.rerun()
        with st.container(key="rec_topo", width="content"):
            if st.button("Reconhecer colega", type="primary", key="rec_novo"):
                st.session_state.rec_modal = "novo"
                st.rerun()
    try:
        with st.spinner("Carregando..."):
            if aba == "mural":
                itens = _guardado("rec_cache_mural", lambda: mural_reconhecimento(token)).get("mural") or []
            elif aba == "recebidos":
                itens = _guardado("rec_cache_recebidos", lambda: meus_reconhecimentos_recebidos(token)).get("recebidos") or []
            else:
                itens = _guardado("rec_cache_enviados", lambda: meus_reconhecimentos_enviados(token)).get("enviados") or []
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        itens = None
    if itens is not None:
        if aba == "mural":
            comps = {}
            for r in itens:
                if r.get("competencia_avaliacao_id") and r.get("competencia_nome"):
                    comps[r["competencia_avaliacao_id"]] = r["competencia_nome"]
            if itens:
                with st.container(horizontal=True):
                    comp = st.selectbox("Competência", [None] + sorted(comps, key=comps.get),
                                        format_func=lambda c: "Competência: todas" if c is None else f"Competência: {comps[c]}",
                                        key="rec_f_comp", label_visibility="collapsed", width=260)
                    dias = st.selectbox("Período", list(rm.PERIODOS), format_func=lambda d: f"Período: {rm.PERIODOS[d]}", key="rec_f_dias",
                                        label_visibility="collapsed", width=260)
                cartoes = rm.cartoes_mural(itens, comp, dias)
            else:
                cartoes = []
            if not itens:
                _vazio("Nenhum reconhecimento no mural ainda", "Seja a primeira pessoa a reconhecer o trabalho de um colega.", True)
            elif not cartoes:
                _vazio("Nenhum reconhecimento neste filtro", "Mude a competência ou o período.", False)
        elif aba == "recebidos":
            cartoes = rm.cartoes_recebidos(itens)
            if not cartoes:
                _vazio("Nenhum reconhecimento recebido ainda", "Quando um colega reconhecer o seu trabalho, ele aparece aqui.", False)
        else:
            cartoes = rm.cartoes_enviados(itens)
            if not cartoes:
                _vazio("Você ainda não enviou reconhecimentos", "Reconheça o trabalho de um colega.", True)
        for i, c in enumerate(cartoes):
            _cartao(c, i, aba)
        if aba == "mural":
            try:
                oculto = bool(_guardado("rec_cache_pref", lambda: minhas_preferencias_privacidade(token)).get("ocultar_mural"))
            except ApiError:
                oculto = None
            if oculto is not None:
                st.html('<p class="crh-meta">' + ("Você não aparece no mural. Para voltar, abra Configurações → Privacidade." if oculto
                                                  else "Você aparece no mural. Para sair, abra Configurações → Privacidade.") + "</p>")
        elif aba == "recebidos":
            st.html('<p class="crh-meta">Quando quem envia é o seu gestor, o reconhecimento fica privado e pode trazer pontos de melhoria. '
                    "Nenhuma promoção ou punição é decidida por isso.</p>")
    if st.session_state.get("rec_modal") == "novo":
        _modal_novo(usuario.get("colaborador_id"))


@st.dialog("Moderar reconhecimento", width="small", on_dismiss=lambda: st.session_state.pop("mod_alvo", None))
def _modal_moderar(c: dict) -> None:
    st.html('<div class="crh-lgpd-resumo">' + "".join(f"<div><span>{r}</span><b>{html.escape(v)}</b></div>" for r, v in
                                                       (("De", c["remetente"]), ("Para", c["destinatario"]), ("Título", c["titulo"]), ("Publicado em", c["quando"])))
            + "</div>")
    motivo = campo(st, "Motivo (quem enviou vê)", "texto", "mod_motivo", area=True, max_chars=1000, height=80)
    st.html('<div class="crh-nota-ambar">O reconhecimento sai do mural e fica marcado como moderado. Isto não pode ser desfeito.</div>')
    slot = st.empty()
    with st.container(horizontal=True):
        if st.button("Voltar", key="mod_voltar"):
            st.session_state.pop("mod_alvo", None)
            st.rerun()
        with st.container(key="ret_perigo", width="content"):
            clicou = st.button("Moderar", type="primary", key="mod_ok")
    if clicou:
        if erro := rm.validar_motivo(motivo):
            alerta(slot, "erro", erro)
            return
        try:
            moderar_reconhecimento(st.session_state.token, c["id"], motivo.strip())
        except ApiError as erro_api:
            alerta(slot, "erro", erro_api.message)
            return
        for chave in ("mod_alvo", "mod_motivo"):
            st.session_state.pop(chave, None)
        _limpar_cache()
        st.session_state.aviso_toast = "Reconhecimento moderado. Ele saiu do mural."
        st.rerun()


def pagina_moderar_reconhecimentos() -> None:
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Moderar reconhecimentos", "Reconhecimentos públicos no mural. O RH tira do ar o que não for positivo ou respeitoso, sempre com motivo.")
    if str(usuario.get("perfil", "")).upper() not in RH:
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return
    try:
        with st.spinner("Carregando..."):
            itens = _guardado("rec_cache_moderacao", lambda: reconhecimentos_moderacao(st.session_state.token)).get("reconhecimentos") or []
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    with st.container(key="cfg_abas", width="content"):
        filtro = st.segmented_control("Filtro", list(rm.FILTROS_MODERACAO), format_func=rm.FILTROS_MODERACAO.get, default="todos", required=True,
                                      key="mod_filtro", label_visibility="collapsed")
    cartoes = rm.cartoes_moderacao(itens, filtro)
    if not cartoes:
        _vazio("Nada para mostrar", "Nenhum reconhecimento público neste filtro.", False)
    for i, c in enumerate(cartoes):
        if _cartao(c, i, "mod", "Moderar" if c["pode_moderar"] else None):
            st.session_state.mod_alvo = c["id"]
            st.rerun()
    st.html('<p class="crh-meta">Moderar é definitivo: o reconhecimento sai do mural e continua guardado com o motivo.</p>')
    alvo = next((c for c in cartoes if c["id"] == st.session_state.get("mod_alvo")), None)
    if alvo:
        _modal_moderar(alvo)
