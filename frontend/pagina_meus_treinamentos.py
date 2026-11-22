"""
Página "Meus treinamentos" (Figma 633:1470, seção 23; changes treinamentos-obrigatorios, treinamento-em-video e
cards-de-treinamentos), no menu de todos os perfis.

Grade: os treinamentos ativos do público da pessoa (obrigatórios e opcionais) em cards clicáveis, com capa, selo de
situação, nome, descrição cortada, tipo de conteúdo, categoria e carga horária. Filtros "Pendentes", "Em andamento" e
"Concluídos"; vem aberto o primeiro com itens. 3 colunas na tela larga, 2 na média e 1 na estreita.

Detalhe (o card clicado; `mt_aberto` na sessão): "Voltar" mantém o filtro; vídeo usa o player e o mínimo assistido;
PDF e apresentação mostram o visualizador embutido, "Abrir em nova aba" e "Li e compreendi o conteúdo", que libera
"Concluir treinamento" (o backend confere a abertura e a confirmação de novo). Abaixo da grade, o "Histórico".
Endpoints: `meus_treinamentos`, `meus_treinamentos/{id}/progresso`, `/conteudo`, `/abrir` e `/concluir`.
"""

import base64
import html
import time
from datetime import date

import streamlit as st

from api_client import ApiError, abrir_treinamento, concluir_treinamento, conteudo_treinamento, meus_treinamentos, progresso_treinamento
from theme import alerta, render_hero, render_topbar
from treinamentos_modelo import FILTROS, cards, contagem, filtro_inicial, meus, pode_concluir, url_embutida
from video_player import player_video

# O endereço assinado do PDF vale 10 minutos. Fica o mesmo enquanto o detalhe está aberto (trocar o endereço recarrega o
# PDF na página 1); só é renovado depois de 9 minutos, para "Abrir em nova aba" não levar a um endereço vencido.
_VALIDADE_CONTEUDO = 540
# Os dados da página (com as capas assinadas por 10 minutos) valem 5 minutos na sessão: cada clique não assina tudo de novo.
_VALIDADE_DADOS = 300


def _icone(desenho: str, cor: str) -> str:
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{cor}" '
           f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{desenho}</svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode("ascii")


_DESENHOS = {
    "video": '<path d="M7 5l12 7-12 7z"/>',
    "pdf": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    "apresentacao": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M12 16v4M8 20h8"/>',
}
# Ícone do rodapé (cinza, sobre o card) e o do centro da capa padrão (âmbar).
ICONE = {tipo: _icone(d, "#737A85") for tipo, d in _DESENHOS.items()}


def _url_css(url: str) -> str:
    """URL dentro de url('...') no atributo style: sem aspas, parênteses, barra invertida nem espaço."""
    for velho, novo in (("'", "%27"), ('"', "%22"), ("(", "%28"), (")", "%29"), ("\\", "%5C"), (" ", "%20")):
        url = url.replace(velho, novo)
    return html.escape(url)


def html_card(c: dict) -> str:
    """O card do Figma (633:1473). A capa é fundo em camadas: se a miniatura externa não carrega, aparece a ilustração
    da categoria por baixo (o st.html não aceita `onerror`)."""
    camadas = ([f"url('{_url_css(c['capa'])}')"] if c["capa"] else []) + [f"url('{_url_css(c['capa_padrao'])}')"]
    sit = c["situacao"]
    return (f'<div class="crh-tcard"><div class="capa" style="background-image:{", ".join(camadas)}" role="img" '
            f'aria-label="Capa de {html.escape(c["nome"])}"><span class="crh-selo {sit["tom"]}">{html.escape(sit["rotulo"])}</span></div>'
            f'<div class="corpo"><p class="t">{html.escape(c["nome"])}</p>'
            + (f'<p class="d">{html.escape(c["resumo"])}</p>' if c["resumo"] else "")
            + f'</div><div class="rodape"><span class="tipo"><img src="{ICONE[c["tipo"]]}" alt="" width="14" height="14">'
            f'{html.escape(c["tipo_rotulo"])}</span><span>{html.escape(c["carga"])}</span></div></div>')


def _limpar_video() -> None:
    st.session_state.pop("mt_dados", None)
    for chave in [k for k in st.session_state if str(k).startswith(("mt_vistos_", "mt_conteudo_", "mt_marcado_", "mt_li_"))]:
        st.session_state.pop(chave, None)


def _concluido(r: dict) -> None:
    _limpar_video()
    # Novo player (zerado) para a próxima renovação.
    st.session_state.mt_rodada = st.session_state.get("mt_rodada", 0) + 1
    st.session_state.pop("mt_aberto", None)
    validade = f" Válido até {date.fromisoformat(str(r['valido_ate'])[:10]).strftime('%d/%m/%Y')}." if r.get("valido_ate") else ""
    st.session_state.aviso_toast = f"Treinamento concluído.{validade}"
    st.rerun(scope="app")


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
        if atual["fonte"] != "youtube":
            # Treinamento antigo com vídeo do Google Drive (change remover-video-drive): não toca mais.
            alerta(st.empty(), "atencao", "Este vídeo estava no Google Drive, que o ConectaRH não usa mais. "
                                          "Avise o RH para trocar pelo link do YouTube.")
            return
        src = None
        guardado = f"mt_vistos_{atual['id']}"
        vistos = max(atual["vistos"], st.session_state.get(guardado, 0))
        enviado = player_video(f'{atual["id"]}_{st.session_state.get("mt_rodada", 0)}', atual["fonte"], atual["video_id"], src, atual["duracao"], atual["minimo"], vistos, atual["posicao"])
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
                _concluido(r)


def _conteudo(token: str, card: dict) -> dict:
    """O link do conteúdo (guardado por 8 minutos, porque o endereço assinado expira em 10)."""
    chave = f"mt_conteudo_{card['id']}"
    guardado = st.session_state.get(chave)
    if not guardado or time.time() - guardado["em"] > _VALIDADE_CONTEUDO:
        guardado = {"em": time.time(), "dados": conteudo_treinamento(token, card["id"])}
        st.session_state[chave] = guardado
    return guardado["dados"]


def _leitura(card: dict, token: str) -> None:
    """PDF ou apresentação: o visualizador, "Abrir em nova aba" e a conclusão com a confirmação (D5, D6)."""
    with st.container(key="cfg_card_mt_leitura"):
        if not card["com_conteudo"]:
            st.html('<p class="crh-meta">O RH ainda não anexou o conteúdo deste treinamento. Volte mais tarde.</p>')
            return
        try:
            dados = _conteudo(token, card)
        except ApiError as erro:
            alerta(st.empty(), "erro", erro.message)
            return
        url = dados.get("url") or ""
        # Só endereço https: o st.iframe trata texto que não é URL como HTML e o executaria.
        if not url.lower().startswith("https://"):
            alerta(st.empty(), "erro", "Não foi possível abrir o conteúdo agora. Tente de novo em instantes.")
            return
        # Mostrar o conteúdo conta como a primeira abertura (D6); uma vez por sessão.
        marcado = f"mt_marcado_{card['id']}"
        if not card["aberto"] and not st.session_state.get(marcado):
            try:
                abrir_treinamento(token, card["id"])
                st.session_state[marcado] = True
                st.session_state.pop("mt_dados", None)  # a grade passa a mostrar "Em andamento"
            except ApiError as erro:
                alerta(st.empty(), "atencao", erro.message)
        # `arquivo` é true quando o conteúdo é o PDF do bucket (o backend não manda o nome do arquivo).
        if dados.get("arquivo") is True:
            nome = "PDF da apresentação" if card["tipo"] == "apresentacao" else "PDF do treinamento"
        else:
            nome = "Apresentação no Google Slides" if "docs.google.com" in url else "Arquivo no Google Drive"
        with st.container(horizontal=True, vertical_alignment="center", key="mt_leitura_topo"):
            st.html(f'<p class="crh-tdet-arquivo"><img src="{ICONE[card["tipo"]]}" alt="" width="16" height="16">{html.escape(nome)}</p>')
            st.link_button("Abrir em nova aba ↗", url, type="tertiary")
        st.iframe(url_embutida(url), height=620)

    aberto = card["aberto"] or st.session_state.get(f"mt_marcado_{card['id']}")
    with st.container(key="cfg_card_mt_concluir"):
        li = st.checkbox("Li e compreendi o conteúdo", key=f"mt_li_{card['id']}", disabled=not aberto)
        st.html('<p class="crh-meta">A conclusão fica registrada com a validade do treinamento. '
                'Não medimos a leitura: a confirmação é sua.</p>')
        slot = st.empty()
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Concluir treinamento", type="primary", key=f"mt_concluir_{card['id']}", disabled=not (aberto and li),
                         help=None if (aberto and li) else "Abra o conteúdo e marque “Li e compreendi o conteúdo” para concluir."):
                try:
                    r = concluir_treinamento(token, card["id"], confirmo_leitura=True)
                except ApiError as erro:
                    alerta(slot, "erro", erro.message)
                    return
                _concluido(r)


def _voltar() -> None:
    st.session_state.pop("mt_aberto", None)
    for chave in [k for k in st.session_state if str(k).startswith("mt_conteudo_")]:
        st.session_state.pop(chave, None)


def _detalhe(card: dict, token: str) -> None:
    filtro = st.session_state.get("mt_filtro_salvo") or "pendentes"
    with st.container(key="mt_voltar"):
        st.button(f"← Voltar para {FILTROS.get(filtro, 'Pendentes')}", key="mt_btn_voltar", type="tertiary", on_click=_voltar)
    sit = card["situacao"]
    meta = " · ".join(p for p in (card["tipo_rotulo"], card["categoria_rotulo"], card["carga"], card["validade"]) if p)
    camadas = ([f"url('{_url_css(card['capa'])}')"] if card["capa"] else []) + [f"url('{_url_css(card['capa_padrao'])}')"]
    with st.container(key="cfg_card_mt_cabeca"):
        st.html(f'<div class="crh-tdet"><div class="capa" style="background-image:{", ".join(camadas)}" role="img" aria-label="Capa"></div>'
                f'<div class="txt"><div class="linha"><p class="t">{html.escape(card["nome"])}</p>'
                f'<span class="crh-selo {sit["tom"]}">{html.escape(sit["rotulo"])}</span></div><p class="m">{html.escape(meta)}</p>'
                + (f'<p class="d">{html.escape(card["descricao"])}</p>' if card["descricao"] else "") + "</div></div>")
    if card["tipo"] == "video":
        if card["video"]:
            _cartao_video([card["video"]], token)
        else:
            with st.container(key="cfg_card_mt_leitura"):
                st.html('<p class="crh-meta">Este treinamento não tem vídeo no ConectaRH: o RH registra a conclusão depois da turma.</p>')
        return
    _leitura(card, token)


def _grade(lista: list[dict]) -> None:
    conta = contagem(lista)
    if "mt_filtro" not in st.session_state:
        st.session_state.mt_filtro = st.session_state.get("mt_filtro_salvo") or filtro_inicial(lista)
    with st.container(key="cfg_abas", width="content"):
        filtro = st.segmented_control("Filtro", list(FILTROS), format_func=lambda f: f"{FILTROS[f]} ({conta[f]})", required=True,
                                      key="mt_filtro", label_visibility="collapsed")
    st.session_state.mt_filtro_salvo = filtro
    visiveis = [c for c in lista if c["situacao"]["filtro"] == filtro]
    if not visiveis:
        vazio = {"pendentes": "Nada pendente: você está em dia com os seus treinamentos.",
                 "andamento": "Nenhum treinamento em andamento.", "concluidos": "Você ainda não concluiu nenhum treinamento."}[filtro]
        st.html(f'<div class="crh-tvazio"><p class="t">{vazio}</p></div>')
        return
    with st.container(key="mt_grade"):
        for c in visiveis:
            with st.container(key=f"mt_card_{c['id']}"):
                st.html(html_card(c))
                if st.button(f"Abrir: {c['nome']}", key=f"mt_abrir_{c['id']}"):
                    st.session_state.mt_aberto = c["id"]
                    st.rerun()


def _historico(dados: dict) -> None:
    with st.container(key="cfg_card_mt"):
        st.html('<p class="crh-cfg-titulo">Histórico</p>')
        if not dados["historico"]:
            st.html('<p class="crh-meta">Nenhum treinamento registrado ainda.</p>')
        for h in dados["historico"]:
            link = (f' · <a href="{html.escape(h["certificado"])}" target="_blank" rel="noopener">Ver certificado →</a>'
                    if h["certificado"] and h["certificado"].lower().startswith(("http://", "https://")) else "")
            st.html(f'<p class="crh-doc-prazo">{html.escape(h["titulo"])}{link}</p>')
        st.html('<p class="crh-meta">O RH registra a conclusão das turmas presenciais; vídeo, PDF e apresentação você conclui aqui. '
                'Se algo estiver errado, fale com o RH.</p>')


def pagina_meus_treinamentos() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Meus treinamentos", "Obrigatórios e opcionais: o que vence, o que está em andamento e o que você já concluiu")
    if not usuario.get("colaborador_id"):
        alerta(st.empty(), "atencao", "Sua conta não tem ficha de colaborador, então não há treinamentos para mostrar.")
        return
    try:
        guardado = st.session_state.get("mt_dados")
        if guardado and time.time() - guardado["em"] < _VALIDADE_DADOS:
            bruto = guardado["dados"]
        else:
            with st.spinner("Carregando..."):
                bruto = meus_treinamentos(token)
            st.session_state.mt_dados = {"em": time.time(), "dados": bruto}
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    dados = meus(bruto)
    lista = cards(bruto)
    aberto = next((c for c in lista if c["id"] == st.session_state.get("mt_aberto")), None)
    if aberto:
        _detalhe(aberto, token)
        return
    st.session_state.pop("mt_aberto", None)
    if not lista:
        st.html('<div class="crh-tvazio"><p class="t">Nenhum treinamento para você agora</p>'
                '<p class="d">Quando o RH publicar um treinamento para você ou para o seu setor, ele aparece aqui.</p></div>')
    else:
        _grade(lista)
    _historico(dados)
