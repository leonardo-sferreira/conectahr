"""
Página "Pedir desligamento" (Figma 224:4056; change fluxo-de-desligamento; tarefa 54 de concluir-frontend-streamlit).
Aberta por "Pedir desligamento →" no Perfil. Qualquer pessoa com ficha pede o próprio desligamento; quem é gestor de
um departamento também pode pedir o de alguém da equipe ("Para quem", que o Figma não desenha).

Novo pedido (último dia, motivo e comentário opcionais, confirmação), "Como funciona" e "Meus pedidos", com "Cancelar"
no pendente. Endpoints: `solicitacoes_desligamento` POST, `minhas_solicitacoes_desligamento`,
`solicitacoes_desligamento/{id}/cancelar` e `organograma` (a equipe).
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import ApiError, cancelar_desligamento, meus_desligamentos, organograma, pedir_desligamento
from campos import campo
from desligamento_modelo import COMO_FUNCIONA, MOTIVOS, linhas_meus, montar_pedido, pedido_em_andamento, validar_pedido
from theme import alerta, html_linha_onboarding, render_hero, render_topbar

_VALIDADE_CACHE_S = 20


def _guardado(chave: str, buscar):
    item = st.session_state.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = buscar()
    st.session_state[chave] = {"em": time.time(), "dados": dados}
    return dados


def _limpar() -> None:
    for chave in [k for k in st.session_state if str(k).startswith(("pd_", "dlg_cache_"))]:
        st.session_state.pop(chave, None)


def _equipe(token: str, meu_colaborador_id) -> dict:
    """{id: nome} de quem é dos departamentos que a pessoa gere (vazio se não gere nenhum)."""
    try:
        org = _guardado("dlg_cache_org", lambda: organograma(token))
    except ApiError:
        return {}
    geridos = {d.get("id") for d in org.get("departamentos") or [] if d.get("gestor_colaborador_id") == meu_colaborador_id}
    return {c.get("id"): c.get("nome") for c in org.get("colaboradores") or [] if c.get("departamento_id") in geridos and c.get("id") != meu_colaborador_id}


@st.dialog("Cancelar pedido", width="small", on_dismiss=lambda: st.session_state.pop("pd_cancelar", None))
def _modal_cancelar(solicitacao_id: int) -> None:
    motivo = campo(st, "Por que cancelar?", "texto", "pd_cancelar_motivo", area=True, max_chars=500, height=70)
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="pd_cancelar_voltar"):
            st.session_state.pop("pd_cancelar", None)
            st.rerun()
        if st.button("Cancelar pedido", type="primary", key="pd_cancelar_ok"):
            if len((motivo or "").strip()) < 5:
                alerta(slot, "erro", "Escreva o motivo (pelo menos 5 caracteres).")
                return
            try:
                cancelar_desligamento(st.session_state.token, solicitacao_id, motivo.strip())
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _limpar()
            st.session_state.aviso_toast = "Pedido cancelado."
            st.rerun()


def _formulario(token: str, meu_colaborador_id, equipe: dict, hoje: date) -> None:
    with st.container(key="cfg_card_pd_novo"):
        st.html('<p class="crh-cfg-titulo">Novo pedido</p>'
                '<p class="crh-nota-ambar">Recomendamos conversar com seu gestor antes. O pedido vai para o RH, que entra em contato para combinar os próximos passos.</p>')
        alvo = meu_colaborador_id
        if equipe:
            opcoes = {meu_colaborador_id: "Para mim"} | {i: f"{n} (da sua equipe)" for i, n in sorted(equipe.items(), key=lambda p: p[1] or "")}
            alvo = st.selectbox("Para quem", list(opcoes), format_func=opcoes.get, key="pd_alvo")
        data_prevista = st.date_input("Último dia de trabalho desejado", value=None, min_value=hoje, format="DD/MM/YYYY", key="pd_data")
        motivo = st.selectbox("Motivo (opcional)", MOTIVOS, index=None, placeholder="Selecione um motivo", key="pd_motivo")
        comentario = campo(st, "Comentário (opcional)", "texto", "pd_comentario", area=True, max_chars=900, height=90, placeholder="Conte o que quiser para o RH.")
        confirmado = st.checkbox("Entendo que o aviso prévio, a devolução de equipamentos e o último acesso serão combinados com o RH.", key="pd_confirma")
        slot = st.empty()
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Cancelar", key="pd_limpar"):
                _limpar()
                st.rerun()
            if st.button("Enviar pedido", type="primary", key="pd_enviar"):
                erro = validar_pedido(data_prevista, hoje, confirmado, comentario)
                if erro:
                    alerta(slot, "erro", erro)
                    return
                tipo, dias, texto = montar_pedido(data_prevista, hoje, motivo, comentario)
                try:
                    pedir_desligamento(token, alvo, tipo, data_prevista.isoformat(), dias, texto)
                except ApiError as erro_api:
                    alerta(slot, "erro", erro_api.message)
                    return
                _limpar()
                st.session_state.aviso_toast = "Pedido enviado ao RH. Você recebe a resposta no sino."
                st.rerun()


def pagina_pedir_desligamento() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    if st.button("← Voltar para o Perfil", type="tertiary", key="pd_voltar"):
        st.session_state.ir_perfil = True
        st.rerun()
    render_hero("Pedir desligamento", "Solicite e acompanhe seu pedido de desligamento")
    meu_colaborador_id = usuario.get("colaborador_id")
    if not meu_colaborador_id:
        alerta(st.empty(), "atencao", "Sua conta não tem ficha de colaborador, então não há desligamento a pedir. Fale com o RH.")
        return
    try:
        with st.spinner("Carregando..."):
            meus = _guardado("dlg_cache_meus", lambda: meus_desligamentos(token)).get("solicitacoes") or []
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    hoje = date.today()
    equipe = _equipe(token, meu_colaborador_id)

    esquerda, direita = st.columns([1.45, 1], gap="medium")
    with esquerda:
        andamento = pedido_em_andamento(meus, meu_colaborador_id)
        if andamento and not equipe:
            with st.container(key="cfg_card_pd_novo"):
                st.html('<p class="crh-cfg-titulo">Novo pedido</p>')
                alerta(st.empty(), "atencao", "Você já tem um pedido de desligamento em andamento. Acompanhe abaixo.")
        else:
            _formulario(token, meu_colaborador_id, equipe, hoje)
    with direita:
        passos = "".join(f'<div class="crh-pd-passo"><span class="n">{i}</span><div><p class="t">{html.escape(t)}</p><p class="d">{html.escape(d)}</p></div></div>'
                         for i, (t, d) in enumerate(COMO_FUNCIONA, start=1))
        st.html(f'<div class="crh-painel crh-bloco"><p class="crh-cfg-titulo">Como funciona</p>{passos}</div>')

    st.html('<p class="crh-bloco-titulo">Meus pedidos</p>')
    linhas = linhas_meus(meus)
    if not linhas:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">Você ainda não fez nenhum pedido.</p></div>')
    for l in linhas:
        with st.container(horizontal=True, vertical_alignment="center", key=f"pd_meu_{l['id']}"):
            st.html(html_linha_onboarding(l["titulo"], l["detalhe"], l["badge"], l["tom"]))
            if l["pode_cancelar"] and st.button("Cancelar", key=f"pd_cancelar_{l['id']}"):
                st.session_state.pd_cancelar = l["id"]
                st.rerun()
    if st.session_state.get("pd_cancelar"):
        _modal_cancelar(st.session_state.pd_cancelar)
