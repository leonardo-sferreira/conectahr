"""
Página "Pesquisa de clima" (Figma 225:4668; change pesquisa-clima-e-avaliacao-360; tarefa 48 de concluir-frontend-streamlit).
Para qualquer pessoa com ficha, qualquer que seja o perfil.

À esquerda, a pesquisa aberta: uma pergunta por vez ("Pergunta 3 de 10" e a barra), a escala de cada uma (concordância
de 1 a 5 ou recomendação de 0 a 10), "Voltar" e "Próxima pergunta"; na última, o comentário opcional e "Enviar
respostas". As notas vão todas numa chamada só. À direita, o cartão "Pesquisas" com a situação de cada uma.
Endpoints: `minhas_pesquisas_clima` e `pesquisas_clima/{id}/responder`.
"""

import html
import time

import streamlit as st

from api_client import ApiError, minhas_pesquisas_clima, responder_pesquisa_clima
from campos import campo
from clima_modelo import a_responder, escala, montar_respostas, prazo_minha, progresso, situacao_minha, validar_respostas
from theme import alerta, render_hero, render_topbar

_VALIDADE_CACHE_S = 20


def _guardado(chave: str, buscar):
    item = st.session_state.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = buscar()
    st.session_state[chave] = {"em": time.time(), "dados": dados}
    return dados


def _limpar() -> None:
    for chave in [k for k in st.session_state if str(k).startswith(("pc_", "clima_cache_"))]:
        st.session_state.pop(chave, None)


def _notas(pesquisa: dict) -> dict:
    """Notas já escolhidas. Ficam num dicionário próprio: o Streamlit apaga o valor de um seletor que não aparece na
    rodada, e só a pergunta da vez aparece."""
    return st.session_state.setdefault(f"pc_notas_{pesquisa['id']}", {})


def _questionario(token: str, pesquisa: dict) -> None:
    perguntas = sorted(pesquisa["perguntas"], key=lambda p: p.get("ordem") or 0)
    total = len(perguntas)
    chave_passo = f"pc_passo_{pesquisa['id']}"
    passo = min(st.session_state.setdefault(chave_passo, 0), total - 1)
    pergunta = perguntas[passo]
    rotulo, pct = progresso(passo, total)
    esc = escala(pergunta)
    minimo = pesquisa.get("minimo_respostas") or 5
    with st.container(key="cfg_card_pc"):
        st.html(f'<p class="crh-cfg-titulo">{html.escape(pesquisa.get("titulo") or "Pesquisa de clima")}</p>'
                f'<div class="crh-pc-anonimo">Sua resposta é anônima. O RH só vê resultados de grupos com {minimo} pessoas ou mais.</div>'
                f'<div class="crh-pc-progresso"><p>{html.escape(rotulo)}</p><div class="barra"><span style="width:{pct}%"></span></div></div>'
                f'<p class="crh-pc-pergunta">{html.escape(pergunta.get("texto") or "")}</p>')
        notas = _notas(pesquisa)
        rotulos = esc.get("rotulos") or {}
        notas[pergunta["id"]] = st.segmented_control("Nota", esc["notas"], default=notas.get(pergunta["id"]), key=f"pc_nota_{pesquisa['id']}_{pergunta['id']}",
                                                     format_func=lambda n: rotulos.get(n, str(n)), label_visibility="collapsed")
        st.html(f'<div class="crh-pc-extremos"><span>{html.escape(esc["min"])}</span><span>{html.escape(esc["max"])}</span></div>')
        ultima = passo == total - 1
        comentario = ""
        if ultima:
            comentario = campo(st, "Quer comentar? (opcional)", "texto", f"pc_comentario_{pesquisa['id']}", area=True, max_chars=1000, height=90,
                               placeholder="Não escreva nomes ou dados que identifiquem você.")
        slot = st.empty()
        with st.container(horizontal=True, horizontal_alignment="right"):
            if passo > 0 and st.button("Voltar", key="pc_voltar"):
                st.session_state[chave_passo] = passo - 1
                st.rerun()
            if not ultima and st.button("Próxima pergunta", type="primary", key="pc_proxima"):
                if notas.get(pergunta["id"]) is None:
                    alerta(slot, "erro", "Escolha uma nota para seguir.")
                    return
                st.session_state[chave_passo] = passo + 1
                st.rerun()
            if ultima and st.button("Enviar respostas", type="primary", key="pc_enviar"):
                erro = validar_respostas(perguntas, notas, comentario)
                if erro:
                    alerta(slot, "erro", erro)
                    return
                try:
                    responder_pesquisa_clima(token, pesquisa["id"], montar_respostas(perguntas, notas), (comentario or "").strip())
                except ApiError as erro_api:
                    alerta(slot, "erro", erro_api.message)
                    return
                _limpar()
                st.session_state.aviso_toast = "Respostas enviadas. Obrigado por participar!"
                st.rerun()


def _sem_pendente(pesquisas: list[dict]) -> None:
    with st.container(key="cfg_card_pc"):
        st.html('<p class="crh-cfg-titulo">Pesquisa de clima</p>')
        if any(p.get("aberta") and p.get("respondida") for p in pesquisas):
            texto = "Você já respondeu a pesquisa aberta. Obrigado! Quando houver outra, ela aparece aqui."
        else:
            texto = "Não há pesquisa aberta agora. Quando o RH abrir uma, ela aparece aqui."
        st.html(f'<p class="crh-meta">{html.escape(texto)}</p>')


def pagina_pesquisa_clima() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Pesquisa de clima", "Responda de forma anônima — ninguém vê sua resposta individual")
    if not usuario.get("colaborador_id"):
        alerta(st.empty(), "atencao", "Sua conta não tem ficha de colaborador, então não há pesquisa para responder.")
        return
    try:
        with st.spinner("Carregando..."):
            pesquisas = _guardado("clima_cache_minhas", lambda: minhas_pesquisas_clima(token)).get("pesquisas") or []
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    pendentes = a_responder(pesquisas)
    ids = [p["id"] for p in pendentes]
    if st.session_state.get("pc_sel") not in ids:
        st.session_state.pc_sel = ids[0] if ids else None

    esquerda, direita = st.columns([2.2, 1], gap="medium")
    with esquerda:
        atual = next((p for p in pendentes if p["id"] == st.session_state.pc_sel), None)
        _questionario(token, atual) if atual else _sem_pendente(pesquisas)
    with direita:
        with st.container(key="cfg_card_pc_lista"):
            st.html('<p class="crh-cfg-titulo">Pesquisas</p>')
            if not pesquisas:
                st.html('<p class="crh-meta">Nenhuma pesquisa ainda.</p>')
            for p in pesquisas:
                selo, tom = situacao_minha(p)
                st.html(f'<div class="crh-pc-item"><p class="t">{html.escape(p.get("titulo") or "")}</p><p class="d">{html.escape(prazo_minha(p))}</p>'
                        f'<span class="crh-selo {tom}">{html.escape(selo)}</span></div>')
                if p["id"] in ids and p["id"] != st.session_state.pc_sel and st.button("Responder", key=f"pc_abrir_{p['id']}", type="tertiary"):
                    st.session_state.pc_sel = p["id"]
                    st.rerun()
