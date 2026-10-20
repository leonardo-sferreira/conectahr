"""
Página "Metas do ciclo" (change ciclo-de-metas), aberta pela Trajetória. Para qualquer pessoa com ficha de
colaborador, seja Colaborador, Gestor, RH ou Admin: o próprio formulário do ciclo anual de metas.

Etapa 1 (fevereiro): a meta de cada pergunta pré-definida. Etapas 2 (junho) e 3 (outubro): o que foi alcançado e a
autoavaliação (abaixo, dentro ou acima do esperado). "Salvar" guarda para continuar depois, dentro da janela; "Enviar"
fecha a etapa. Fora da janela, ou depois do envio, só leitura. Cada etapa enviada mostra a caixa de feedback do
gestor. Endpoints: `meu_ciclo_metas`, `meu_ciclo_metas/{ciclo_id}/respostas` e `/enviar`.
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import ApiError, enviar_etapa_meta, meu_ciclo_metas, responder_meta
from ciclo_metas_modelo import (ESCALA, ETAPAS, ciclo_em_foco, enviadas_do, etapa_editavel, perguntas_do_formulario, periodo, proxima_abertura,
                                respostas_alteradas, situacao_ciclo, validar_envio)
from formulario_metas_ui import etapa_leitura, trilha_etapas
from onboarding_modelo import data_br
from theme import alerta, render_hero, render_topbar

CACHE = "cm_cache"
_VALIDADE_CACHE_S = 20
_SEM_FICHA = "Sua conta não tem ficha de colaborador, então não há metas para preencher. Se isso estiver errado, fale com o RH."


def carregar(token: str) -> dict:
    """`meu_ciclo_metas` guardado por 20 s (a Trajetória usa o mesmo); o erro sobe."""
    guardado = st.session_state.get(CACHE)
    if guardado and time.time() - guardado["em"] < _VALIDADE_CACHE_S:
        return guardado["dados"]
    dados = meu_ciclo_metas(token)
    st.session_state[CACHE] = {"em": time.time(), "dados": dados}
    return dados


def _limpar(ciclo_id) -> None:
    st.session_state.pop(CACHE, None)
    for chave in [k for k in st.session_state if str(k).startswith(f"cm_{ciclo_id}_")]:
        st.session_state.pop(chave, None)


def _formulario(ciclo: dict, etapa: int, perguntas: list[dict]) -> None:
    """A etapa aberta, para preencher: Salvar (rascunho) e Enviar (definitivo, com confirmação)."""
    cid = ciclo["id"]
    st.html(f'<div class="crh-cm-cab"><div><p class="t">Etapa {etapa} — {html.escape(ETAPAS[etapa])}</p>'
            f'<p class="s">Aberta até {html.escape(data_br(ciclo.get(f"etapa{etapa}_fim")) or "—")}. Salve quantas vezes quiser; '
            'depois de enviada, a etapa não muda mais.</p></div></div>')
    if not perguntas:
        alerta(st.empty(), "atencao", "O RH ainda não cadastrou as perguntas do formulário.")
        return
    textos, autos = {}, {}
    escala = list(ESCALA)
    for p in perguntas:
        pid = p["pergunta_id"]
        st.html(f'<p class="crh-bloco-titulo" style="font-size:14px;margin-top:6px">{html.escape(p["texto"])}</p>'
                + (f'<p class="crh-meta">{html.escape(p["orientacao"])}</p>' if p.get("orientacao") else ""))
        if etapa == 1:
            textos[pid] = st.text_area("Sua meta", value=p["meta"], max_chars=2000, height=90, key=f"cm_{cid}_meta_{pid}")
        else:
            st.html(f'<p class="crh-meta"><b>Sua meta:</b> {html.escape(p["meta"] or "—")}</p>')
            textos[pid] = st.text_area("O que você alcançou", value=p[f"alcancado{etapa}"], max_chars=2000, height=90, key=f"cm_{cid}_alc{etapa}_{pid}")
            atual = p[f"auto{etapa}"]
            autos[pid] = st.radio("Autoavaliação", escala, index=escala.index(atual) if atual in escala else None, format_func=ESCALA.get,
                                  horizontal=True, key=f"cm_{cid}_auto{etapa}_{pid}")
    confirmar = st.checkbox(f"Entendo que, depois de enviada, a etapa {etapa} não pode mais ser alterada.", key=f"cm_{cid}_confirma{etapa}")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        salvar = st.button("Salvar", key=f"cm_{cid}_salvar")
        enviar = st.button(f"Enviar etapa {etapa}", type="primary", key=f"cm_{cid}_enviar")
    if not (salvar or enviar):
        return
    if enviar:
        erro_campo = validar_envio(etapa, perguntas, textos, autos) or (None if confirmar else "Marque a confirmação para enviar.")
        if erro_campo:
            alerta(slot, "erro", erro_campo)
            return
    token = st.session_state.token
    try:
        for pid, texto, auto in respostas_alteradas(etapa, perguntas, textos, autos):
            responder_meta(token, cid, pid, texto, auto)
        if enviar:
            enviar_etapa_meta(token, cid)
    except ApiError as erro:
        st.session_state.pop(CACHE, None)
        alerta(slot, "erro", erro.message)
        return
    _limpar(cid)
    st.session_state.aviso_toast = f"Etapa {etapa} enviada. Seu gestor foi avisado." if enviar else "Respostas salvas. Você pode continuar depois."
    st.rerun()


def pagina_metas_ciclo() -> None:
    token = st.session_state.token
    render_topbar(st.session_state.usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Metas do ciclo", "Defina suas metas, acompanhe o que alcançou e feche o ciclo do ano")
    with st.container(horizontal=True):
        if st.button("← Voltar para a Trajetória", type="tertiary", key="cm_voltar"):
            st.session_state.ir_trajetoria = True
            st.rerun()

    with st.spinner("Carregando suas metas..."):
        try:
            dados, erro = carregar(token), None
        except ApiError as falha:
            dados, erro = None, falha
    if erro is not None:
        alerta(st.empty(), "atencao" if erro.status_code == 404 else "erro", _SEM_FICHA if erro.status_code == 404 else erro.message)
        return
    ciclos = dados.get("ciclos") or []
    if not ciclos:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">O RH ainda não abriu um ciclo de metas.</p></div>')
        return
    hoje = date.fromisoformat(str(dados.get("hoje") or date.today())[:10])
    por_id = {c["id"]: c for c in ciclos}
    foco = ciclo_em_foco(ciclos)["id"]
    escolhido = st.selectbox("Ciclo", list(por_id), index=list(por_id).index(foco), format_func=lambda i: f"Ciclo {por_id[i].get('ano')} — {situacao_ciclo(por_id[i], hoje)[0]}",
                             key="cm_ciclo", width=320) if len(ciclos) > 1 else ciclos[0]["id"]
    ciclo = por_id[escolhido]
    enviadas = enviadas_do(ciclo)
    perguntas = perguntas_do_formulario(ciclo, dados.get("perguntas_ativas"))

    st.html(f'<p class="crh-bloco-titulo">Ciclo {ciclo.get("ano")}</p>')
    trilha_etapas(ciclo, hoje, enviadas)
    aberta = etapa_editavel(ciclo)
    if aberta:
        with st.container(key="cm_form", border=True):
            _formulario(ciclo, aberta, perguntas)
    elif ciclo.get("etapa_aberta") and not enviadas.get(1) and ciclo["etapa_aberta"] > 1:
        alerta(st.empty(), "atencao", f"A etapa {ciclo['etapa_aberta']} está aberta, mas você não enviou as metas na etapa 1 ({periodo(ciclo, 1)}). Fale com o seu gestor.")
    elif not ciclo.get("etapa_aberta"):
        # Fora das janelas não há campo para preencher: diz quando abre (pedido do usuário, 20/10/2026).
        proxima = proxima_abertura(ciclo, hoje)
        alerta(st.empty(), "atencao", f"Nenhuma etapa está aberta agora. A etapa {proxima[0]} ({ETAPAS[proxima[0]].lower()}) abre em {proxima[1]}; "
                                      "os campos aparecem aqui nesse dia." if proxima else "As três etapas deste ciclo já terminaram: o formulário fica só para consulta.")
    # Com a etapa 1 aberta, o próprio formulário avisa; antes dela, o aviso fica aqui.
    if not aberta and not enviadas.get(1) and not dados.get("perguntas_ativas"):
        alerta(st.empty(), "atencao", "O RH ainda não cadastrou as perguntas do formulário.")
    for n in (1, 2, 3):
        if n != aberta:
            etapa_leitura(ciclo, n, perguntas, enviadas, ciclo.get("feedbacks"), hoje)
