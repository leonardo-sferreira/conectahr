"""
Página "Meus treinamentos" (Figma 550:1415 e 557:1383; changes treinamentos-obrigatorios e treinamento-em-video), no
menu de todos os perfis.

No alto, quando há treinamento obrigatório com vídeo: o player (`video_player`), o quanto a pessoa já assistiu e
"Concluir treinamento", liberado só depois do mínimo pedido (o backend confere de novo). Com mais de um vídeo, a
pessoa escolhe qual; o primeiro é o mais urgente. Depois, "Obrigatórios para você": cada treinamento obrigatório
para todos ou para o setor da pessoa, com a situação (vencido, pendente, vencendo, em dia) e a validade;
"Histórico": as conclusões registradas, com o link do certificado.
Endpoints: `meus_treinamentos`, `meus_treinamentos/{id}/progresso` e `meus_treinamentos/{id}/concluir`.
"""

import html
from datetime import date

import streamlit as st

from api_client import ApiError, concluir_treinamento, meus_treinamentos, progresso_treinamento
from drive_video import chave_api, url_video
from theme import alerta, render_hero, render_topbar
from treinamentos_modelo import meus, pode_concluir
from video_player import player_video


def _limpar_video() -> None:
    for chave in [k for k in st.session_state if str(k).startswith("mt_vistos_")]:
        st.session_state.pop(chave, None)


@st.fragment
def _cartao_video(videos: list[dict], token: str) -> None:
    with st.container(key="cfg_card_mt_video"):
        por_id = {v["id"]: v for v in videos}
        if len(videos) > 1:
            escolhido = st.selectbox("Treinamento com vídeo", list(por_id), format_func=lambda i: por_id[i]["nome"], key="mt_video_escolha")
            atual = por_id.get(escolhido, videos[0])
        else:
            atual = videos[0]
        st.html(f'<p class="crh-cfg-titulo">{html.escape(atual["nome"])}</p><p class="crh-meta">{html.escape(atual["detalhe"])}</p>')
        chave = chave_api()
        if not chave:
            alerta(st.empty(), "atencao", "O vídeo ainda não pode tocar aqui: falta configurar o Google Drive no app. Avise o RH.")
            return
        guardado = f"mt_vistos_{atual['id']}"
        vistos = max(atual["vistos"], st.session_state.get(guardado, 0))
        enviado = player_video(f'{atual["id"]}_{st.session_state.get("mt_rodada", 0)}', url_video(atual["video_id"], chave), atual["duracao"], atual["minimo"], vistos, atual["posicao"])
        slot = st.empty()
        # Cada envio do navegador chega uma vez: o "n" muda a cada envio.
        if enviado and enviado.get("n") != st.session_state.get("mt_ultimo_envio"):
            st.session_state.mt_ultimo_envio = enviado.get("n")
            try:
                r = progresso_treinamento(token, atual["id"], enviado.get("vistos") or 0, enviado.get("posicao") or 0)
                vistos = max(vistos, int(r.get("segundos_vistos") or 0))
                st.session_state[guardado] = vistos
            except ApiError as erro:
                alerta(slot, "atencao", erro.message)
        st.html('<p class="crh-meta">Trechos pulados não contam. Se fechar a página, o vídeo continua de onde parou.</p>')
        liberado = pode_concluir(vistos, atual["duracao"], atual["minimo"])
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Concluir treinamento", type="primary", key=f"mt_concluir_{atual['id']}", disabled=not liberado,
                         help=None if liberado else f"Assista pelo menos {atual['minimo']}% do vídeo para concluir."):
                try:
                    r = concluir_treinamento(token, atual["id"])
                except ApiError as erro:
                    alerta(slot, "erro", erro.message)
                    return
                _limpar_video()
                # Novo player (zerado) para a próxima renovação.
                st.session_state.mt_rodada = st.session_state.get("mt_rodada", 0) + 1
                validade = f" Válido até {date.fromisoformat(str(r['valido_ate'])[:10]).strftime('%d/%m/%Y')}." if r.get("valido_ate") else ""
                st.session_state.aviso_toast = f"Treinamento concluído.{validade}"
                st.rerun(scope="app")


def pagina_meus_treinamentos() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Meus treinamentos", "Os obrigatórios para você, o que vence e os certificados")
    if not usuario.get("colaborador_id"):
        alerta(st.empty(), "atencao", "Sua conta não tem ficha de colaborador, então não há treinamentos para mostrar.")
        return
    try:
        with st.spinner("Carregando..."):
            dados = meus(meus_treinamentos(token))
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    if dados["videos"]:
        _cartao_video(dados["videos"], token)
    with st.container(key="cfg_card_mt"):
        st.html('<p class="crh-cfg-titulo">Obrigatórios para você</p>')
        # st.html com texto vazio dá erro no Streamlit: a lista só é desenhada quando tem itens.
        if not dados["obrigatorios"]:
            st.html('<p class="crh-meta">Nenhum treinamento obrigatório para você agora.</p>')
        else:
            st.html("".join(f'<div class="crh-pc-item"><p class="t">{html.escape(o["nome"] or "")}</p><p class="d">{html.escape(o["detalhe"])}</p>'
                            f'<span class="crh-selo {o["tom"]}">{html.escape(o["rotulo"])}</span></div>' for o in dados["obrigatorios"]))
        st.html('<p class="crh-cfg-titulo" style="margin-top:18px">Histórico</p>')
        if not dados["historico"]:
            st.html('<p class="crh-meta">Nenhum treinamento registrado ainda.</p>')
        for h in dados["historico"]:
            link = (f' · <a href="{html.escape(h["certificado"])}" target="_blank" rel="noopener">Ver certificado →</a>'
                    if h["certificado"] and h["certificado"].lower().startswith(("http://", "https://")) else "")
            st.html(f'<p class="crh-doc-prazo">{html.escape(h["titulo"])}{link}</p>')
        st.html('<p class="crh-meta">O RH registra a conclusão depois de cada turma; os treinamentos com vídeo você conclui aqui. '
                'Se algo estiver errado, fale com o RH.</p>')
