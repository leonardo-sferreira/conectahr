"""
Página "Trajetória" (Figma 64:42; change trajetoria-do-colaborador; tarefas 31 a 33 da change
concluir-frontend-streamlit). Para qualquer perfil com ficha de colaborador.

Blocos do Figma: plano de carreira (nível atual, próximo nível e competências; sem ação de promover),
Avaliação 360 do ciclo em andamento, Metas ativas, PDI e Reconhecimentos recebidos. Além deles, "Para você avaliar"
(as avaliações que a pessoa responde) e "Avaliações recebidas" (as enviadas sobre ela, para contestar), que só
aparecem quando há algo. Os modais de responder, contestar, check-in e progresso não têm nó no Figma
(docs/figma-pendencias.md) e usam os componentes do tema.

Endpoints: `minha_trajetoria` (uma leitura por carregamento), `avaliacoes/{id}/competencias`, `avaliacoes/{id}/respostas`,
`avaliacoes/{id}/enviar`, `avaliacoes/{id}/contestar`, `metas/{id}/checkin` e `pdi/{id}/progresso`. A autorização é do
backend; pares e subordinados chegam sem o nome do avaliador.
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import (ApiError, checkin_meta, competencias_avaliacao, contestar_avaliacao, enviar_avaliacao, minha_trajetoria, progresso_pdi,
                        responder_avaliacao)
from ciclo_metas_modelo import enviadas_do, etapa_editavel
from formulario_metas_ui import trilha_etapas
from pagina_metas_ciclo import carregar as carregar_ciclo_metas
from theme import alerta, html_linha_onboarding, render_hero, render_topbar
from trajetoria_modelo import (NOTAS, linhas_360, linhas_a_preencher, linhas_metas, linhas_pdi, linhas_recebidas, nivel, reconhecimentos,
                               respostas_alteradas, titulo_360, validar_contestacao, validar_envio)

CACHE = "traj_cache"
_VALIDADE_CACHE_S = 20
_SEM_FICHA = "Sua conta não tem ficha de colaborador, então não há trajetória para mostrar. Se isso estiver errado, fale com o RH."


def carregar(token: str) -> dict:
    """`minha_trajetoria` guardado por 20 s; o erro sobe."""
    guardado = st.session_state.get(CACHE)
    if guardado and time.time() - guardado["em"] < _VALIDADE_CACHE_S:
        return guardado["dados"]
    dados = minha_trajetoria(token)
    st.session_state[CACHE] = {"em": time.time(), "dados": dados}
    return dados


def fechar() -> None:
    st.session_state.pop("traj_modal", None)


def concluir(aviso: str) -> None:
    st.session_state.pop(CACHE, None)
    for chave in [k for k in st.session_state if str(k).startswith("traj_form_")]:
        st.session_state.pop(chave, None)
    fechar()
    st.session_state.aviso_toast = aviso
    st.rerun()


def _botoes_rodape(rotulo_ok: str, chave: str) -> bool:
    """Cancelar e o botão principal, à direita; True quando o principal é clicado."""
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key=f"{chave}_cancelar"):
            fechar()
            st.rerun()
        return st.button(rotulo_ok, type="primary", key=f"{chave}_ok")


def _escolher(rotulo: str, linhas: list[dict], chave: str, com_detalhe: bool = False):
    """Selectbox da linha a usar no modal; com uma só, já vem escolhida."""
    ids = [l["id"] for l in linhas]
    nomes = {l["id"]: f"{l['titulo']} — {l['detalhe']}" if com_detalhe and l.get("detalhe") else l["titulo"] for l in linhas}
    return st.selectbox(rotulo, ids, index=0 if len(ids) == 1 else None, format_func=nomes.get, placeholder="Escolha", key=chave)


# ---------------------------------------------------------------------------
# Modais
# ---------------------------------------------------------------------------
@st.dialog("Responder avaliação", width="large", on_dismiss=fechar)
def _modal_responder(linhas: list[dict]) -> None:
    aid = _escolher("Avaliação", linhas, "traj_resp_avaliacao")
    if aid is None:
        return
    chave_form = f"traj_form_{aid}"
    if chave_form not in st.session_state:
        try:
            st.session_state[chave_form] = competencias_avaliacao(st.session_state.token, aid)
        except ApiError as erro:
            alerta(st.empty(), "erro", erro.message)
            return
    form = st.session_state[chave_form]
    competencias = form.get("competencias") or []
    salvas = {r.get("competencia_avaliacao_id"): r for r in form.get("respostas") or []}
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">Dê uma nota de 1 a 5 a cada competência. "Salvar" guarda para continuar depois; '
            '"Enviar" fecha a avaliação, e ela não pode mais ser alterada.</p></div>')
    notas, comentarios = {}, {}
    for c in competencias:
        salva = salvas.get(c["id"]) or {}
        st.html(f'<p class="crh-bloco-titulo" style="font-size:14px">{html.escape(c.get("nome") or "")}</p>'
                + (f'<p class="crh-meta">{html.escape(c["descricao"])}</p>' if c.get("descricao") else ""))
        opcoes = list(NOTAS)
        notas[c["id"]] = st.radio("Nota", opcoes, index=opcoes.index(salva["nota"]) if salva.get("nota") in opcoes else None, format_func=NOTAS.get,
                                  horizontal=True, key=f"traj_nota_{aid}_{c['id']}", label_visibility="collapsed")
        comentarios[c["id"]] = st.text_input("Comentário (opcional)", value=salva.get("comentario") or "", max_chars=2000, key=f"traj_com_{aid}_{c['id']}")
    geral = st.text_area("Comentário geral (opcional, vai com o envio)", max_chars=2000, height=80, key=f"traj_geral_{aid}")
    confirmar = st.checkbox("Entendo que, depois de enviada, a avaliação não pode mais ser alterada.", key=f"traj_confirma_{aid}")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="traj_resp_cancelar"):
            fechar()
            st.rerun()
        salvar = st.button("Salvar", key="traj_resp_salvar")
        enviar = st.button("Enviar avaliação", type="primary", key="traj_resp_enviar")
    if not (salvar or enviar):
        return
    if enviar:
        erro_campo = validar_envio(competencias, notas) or (None if confirmar else "Marque a confirmação para enviar.")
        if erro_campo:
            alerta(slot, "erro", erro_campo)
            return
    token = st.session_state.token
    try:
        for cid, nota, comentario in respostas_alteradas(competencias, form.get("respostas"), notas, comentarios):
            responder_avaliacao(token, aid, cid, nota, comentario)
        if enviar:
            enviar_avaliacao(token, aid, geral.strip())
    except ApiError as erro:
        st.session_state.pop(chave_form, None)
        alerta(slot, "erro", erro.message)
        return
    concluir("Avaliação enviada." if enviar else "Respostas salvas. Você pode continuar depois.")


@st.dialog("Contestar avaliação", width="medium", on_dismiss=fechar)
def _modal_contestar(linhas: list[dict]) -> None:
    aid = _escolher("Avaliação", linhas, "traj_cont_avaliacao", com_detalhe=True)
    motivo = st.text_area("Motivo da contestação", max_chars=2000, height=120, key="traj_cont_motivo",
                          help="Diga o que você considera injusto ou errado. O RH revisa e responde.")
    slot = st.empty()
    if _botoes_rodape("Enviar contestação", "traj_cont"):
        erro_campo = "Escolha a avaliação." if aid is None else validar_contestacao(motivo)
        if erro_campo:
            alerta(slot, "erro", erro_campo)
            return
        try:
            contestar_avaliacao(st.session_state.token, aid, motivo.strip())
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        st.session_state.pop("traj_cont_motivo", None)
        concluir("Contestação enviada. O RH vai revisar.")


@st.dialog("Check-in da meta", width="medium", on_dismiss=fechar)
def _modal_checkin(linhas: list[dict]) -> None:
    mid = _escolher("Meta", linhas, "traj_ck_meta")
    atual = next((l["progresso"] for l in linhas if l["id"] == mid), 0)
    progresso = st.number_input("Progresso (%)", min_value=0, max_value=100, value=atual, step=5, key=f"traj_ck_prog_{mid}")
    comentario = st.text_area("Como está a meta", max_chars=2000, height=80, key="traj_ck_com")
    dificuldades = st.text_area("Dificuldades (opcional)", max_chars=2000, height=70, key="traj_ck_dif")
    evidencia = st.text_input("Evidência (opcional, ex.: link do entregável)", max_chars=1000, key="traj_ck_evid")
    slot = st.empty()
    if _botoes_rodape("Registrar check-in", "traj_ck"):
        if mid is None:
            alerta(slot, "erro", "Escolha a meta.")
            return
        try:
            checkin_meta(st.session_state.token, mid, progresso, comentario.strip(), dificuldades.strip(), evidencia.strip())
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        for chave in ("traj_ck_com", "traj_ck_dif", "traj_ck_evid"):
            st.session_state.pop(chave, None)
        concluir(f"Check-in registrado: {progresso}% concluído.")


@st.dialog("Progresso do PDI", width="medium", on_dismiss=fechar)
def _modal_pdi(linhas: list[dict]) -> None:
    pid = _escolher("Ação de desenvolvimento", linhas, "traj_pdi_acao")
    atual = next((l["progresso"] for l in linhas if l["id"] == pid), 0)
    progresso = st.number_input("Progresso (%)", min_value=0, max_value=100, value=atual, step=5, key=f"traj_pdi_prog_{pid}")
    evidencia = st.text_area("Evidência (opcional, ex.: certificado ou link)", max_chars=2000, height=80, key="traj_pdi_evid")
    slot = st.empty()
    if _botoes_rodape("Salvar progresso", "traj_pdi"):
        if pid is None:
            alerta(slot, "erro", "Escolha a ação de desenvolvimento.")
            return
        try:
            progresso_pdi(st.session_state.token, pid, progresso, evidencia.strip())
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        st.session_state.pop("traj_pdi_evid", None)
        concluir(f"Progresso do PDI salvo: {progresso}%.")


# ---------------------------------------------------------------------------
# Blocos
# ---------------------------------------------------------------------------
def _trilha(titulo: str, linhas: list[dict], vazio: str | None = None) -> None:
    """Título do bloco e a trilha de pontos ligando os cartões (Figma 64:42, igual à Central de Pendências)."""
    if not linhas:
        st.html(f'<p class="crh-bloco-titulo">{html.escape(titulo)}</p>'
                f'<div class="crh-painel crh-bloco"><p class="crh-meta">{html.escape(vazio or "")}</p></div>')
        return
    itens = "".join(
        f'<div class="crh-ct-item"><div class="crh-ct-ponto"><span class="p {l["tom"]}"></span><span class="l"></span></div>'
        f'{html_linha_onboarding(l["titulo"], l["detalhe"], l["badge"], l["tom"])}</div>'
        for l in linhas
    )
    st.html(f'<p class="crh-bloco-titulo">{html.escape(titulo)}</p><div class="crh-ct">{itens}</div>')


def _acao(rotulo: str, chave: str, modal: str) -> None:
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button(rotulo, key=chave, type="tertiary"):
            st.session_state.traj_modal = modal
            st.rerun()


def _carreira(dados: dict) -> None:
    comps = "".join(f'<span class="comp">{html.escape(c.get("nome") or "")}</span>' for c in dados.get("competencias_proximo_nivel") or [])
    if dados.get("proximo_nivel"):
        proximo = (f'<span class="seta">→</span><div><p class="r">Próximo nível — competências a desenvolver</p>'
                   f'<div class="prox"><p class="n">{html.escape(nivel(dados["proximo_nivel"]))}</p>{comps}</div></div>')
    else:
        proximo = '<div><p class="r">Próximo nível</p><p class="crh-meta">Você está no nível mais alto da trilha.</p></div>'
    st.html(f'<div class="crh-painel crh-carreira"><div><p class="r">Nível atual</p><p class="n">{html.escape(nivel(dados.get("nivel_atual")))}</p></div>'
            f'{proximo}</div>')


def _ciclo_metas(token: str) -> None:
    """Bloco "Ciclo de metas" (change ciclo-de-metas): as três etapas do ciclo atual e o caminho para "Metas do ciclo"."""
    try:
        dados = carregar_ciclo_metas(token)
    except ApiError as erro:
        if erro.status_code != 404:
            st.html('<p class="crh-bloco-titulo">Ciclo de metas</p>')
            alerta(st.empty(), "atencao", f"O ciclo de metas não carregou agora: {erro.message}")
        return
    ciclos = dados.get("ciclos") or []
    if not ciclos:
        st.html('<p class="crh-bloco-titulo">Ciclo de metas</p>'
                '<div class="crh-painel crh-bloco"><p class="crh-meta">O RH ainda não abriu um ciclo de metas.</p></div>')
        return
    ciclo = ciclos[0]
    hoje = date.fromisoformat(str(dados.get("hoje") or date.today())[:10])
    st.html(f'<p class="crh-bloco-titulo">Ciclo de metas {html.escape(str(ciclo.get("ano")))}</p>')
    trilha_etapas(ciclo, hoje, enviadas_do(ciclo))
    rotulo = f"Preencher a etapa {etapa_editavel(ciclo)} →" if etapa_editavel(ciclo) else "Abrir minhas metas do ciclo →"
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button(rotulo, key="traj_abrir_metas", type="primary" if etapa_editavel(ciclo) else "tertiary"):
            st.session_state.ir_metas_ciclo = True
            st.rerun()


def _reconhecimentos(dados: dict) -> None:
    itens = reconhecimentos(dados)
    if not itens:
        st.html('<p class="crh-bloco-titulo">Reconhecimentos recebidos</p>'
                '<div class="crh-painel crh-bloco"><p class="crh-meta">Nenhum reconhecimento recebido ainda.</p></div>')
        return
    corpo = "".join(
        f'<div class="item"><div class="cab"><p class="nome">{html.escape(i["nome"])}</p><p class="quando">{html.escape(i["data"])}</p></div>'
        f'<p class="msg">"{html.escape(i["mensagem"])}"</p></div>'
        for i in itens
    )
    st.html(f'<p class="crh-bloco-titulo">Reconhecimentos recebidos</p><div class="crh-painel crh-rec">{corpo}</div>')


# ---------------------------------------------------------------------------
def pagina_trajetoria() -> None:
    token = st.session_state.token
    render_topbar(st.session_state.usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)

    with st.spinner("Carregando sua trajetória..."):
        try:
            dados, erro = carregar(token), None
        except ApiError as falha:
            dados, erro = None, falha
    render_hero("Trajetória Profissional", "Avaliação 360, metas, PDI e evolução de carreira")
    if erro is not None:
        alerta(st.empty(), "atencao" if erro.status_code == 404 else "erro", _SEM_FICHA if erro.status_code == 404 else erro.message)
        return

    hoje = date.today()
    a_preencher = linhas_a_preencher(dados)
    recebidas = linhas_recebidas(dados)
    metas = linhas_metas(dados.get("metas"), hoje)
    pdi = linhas_pdi(dados.get("pdi"), hoje)

    _carreira(dados)
    _ciclo_metas(token)
    if a_preencher:
        _trilha("Para você avaliar", a_preencher)
        _acao("Responder avaliação →", "traj_abrir_responder", "responder")
    _trilha(titulo_360(dados) or "Avaliação 360", linhas_360(dados),
            "Nenhum ciclo de avaliação em andamento." if not dados.get("ciclo") else "Nenhuma avaliação sua neste ciclo ainda.")
    if recebidas:
        _trilha("Avaliações recebidas", recebidas)
        for l in recebidas:
            if l.get("resposta_rh"):
                st.html(f'<p class="crh-meta">Resposta do RH sobre a {html.escape(l["titulo"].lower())}: {html.escape(l["resposta_rh"])}</p>')
        if any(l["pode_contestar"] for l in recebidas):
            _acao("Contestar avaliação →", "traj_abrir_contestar", "contestar")
    _trilha("Metas ativas", metas, "Nenhuma meta ativa.")
    if metas:
        _acao("Registrar check-in →", "traj_abrir_checkin", "checkin")
    _trilha("PDI — Plano de Desenvolvimento Individual", pdi, "Nenhuma ação de PDI em andamento.")
    if pdi:
        _acao("Atualizar progresso →", "traj_abrir_pdi", "pdi")
    _reconhecimentos(dados)

    modal = st.session_state.get("traj_modal")
    if modal == "responder" and a_preencher:
        _modal_responder(a_preencher)
    elif modal == "contestar":
        _modal_contestar([l for l in recebidas if l["pode_contestar"]])
    elif modal == "checkin" and metas:
        _modal_checkin(metas)
    elif modal == "pdi" and pdi:
        _modal_pdi(pdi)
    elif modal:
        fechar()
