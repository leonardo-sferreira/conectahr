"""
Página "Pesquisas de clima" do grupo RH (Figma 249:4645 e o modal 249:4885; change pesquisa-clima-e-avaliacao-360, D3,
D4 e D8). Só RH e Admin.

Abas "Em andamento" (agendadas e abertas) e "Encerradas", e "Nova pesquisa" (nome, abre em, fecha em, perguntas de 1 a
5 e a de 0 a 10, numa chamada só). Cada pesquisa é um cartão com "Aberta até ... · N perguntas", a adesão geral e a de
cada departamento em barras (quem respondeu, nunca o quê), "Editar perguntas" (antes de abrir) ou "Ver perguntas", e
"Encerrar pesquisa". Ao lado, o cartão "Resultado" da última encerrada: eNPS geral, a primeira pergunta com a média e o
pior tema. Nas encerradas, "Ver resultados": por pergunta, a média, o % favorável e o NPS, no geral e por departamento
(grupos abaixo do mínimo não aparecem), e os comentários em ordem alfabética, sem autor.
Endpoints: `pesquisas_clima_rh`, `pesquisas_clima` POST, `pesquisas_clima/{id}/perguntas`, `encerrar` e `resultados`.
"""

import html
import time
from datetime import date, timedelta

import streamlit as st

from api_client import ApiError, adicionar_pergunta_clima, criar_pesquisa_clima, encerrar_pesquisa_clima, pesquisas_clima_rh, resultados_pesquisa_clima
from campos import campo
from clima_modelo import (ABAS_RH, ESCALAS, PERGUNTA_NPS, PERGUNTAS_SUGERIDAS, barras_adesao, da_aba, perguntas_do_texto, resultados_por_pergunta,
                          resumo_card, situacao_rh, subtitulo_card, validar_pesquisa)
from theme import alerta, render_hero, render_topbar

_VALIDADE_CACHE_S = 20
_MINIMO_PADRAO = 5


def _guardado(chave: str, buscar):
    item = st.session_state.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = buscar()
    st.session_state[chave] = {"em": time.time(), "dados": dados}
    return dados


def _fechar() -> None:
    st.session_state.pop("pcr_modal", None)


def _concluir(aviso: str) -> None:
    for chave in [k for k in st.session_state if str(k).startswith(("pcr_", "clima_cache_"))]:
        st.session_state.pop(chave, None)
    st.session_state.aviso_toast = aviso
    st.rerun()


def _hoje(dados: dict) -> date:
    try:
        return date.fromisoformat(str(dados.get("hoje"))[:10])
    except ValueError:
        return date.today()


def _resultados(pesquisa_id: int) -> dict:
    return _guardado(f"clima_cache_res_{pesquisa_id}", lambda: resultados_pesquisa_clima(st.session_state.token, pesquisa_id))


# ---------------------------------------------------------------------------
# Modais
# ---------------------------------------------------------------------------
@st.dialog("Nova pesquisa de clima", width="medium", on_dismiss=_fechar)
def _modal_nova(hoje: date) -> None:
    titulo = campo(st, "Nome", "texto", "pcr_titulo", max_chars=200, placeholder="Ex.: Clima — 1º semestre 2027")
    c1, c2 = st.columns(2)
    inicio = c1.date_input("Abre em", value=hoje, min_value=hoje, format="DD/MM/YYYY", key="pcr_inicio")
    fim = c2.date_input("Fecha em", value=hoje + timedelta(days=14), min_value=hoje, format="DD/MM/YYYY", key="pcr_fim")
    st.session_state.setdefault("pcr_perguntas", "\n".join(PERGUNTAS_SUGERIDAS))
    st.session_state.setdefault("pcr_nps", PERGUNTA_NPS)
    texto = campo(st, "Perguntas (escala de 1 a 5, uma por linha)", "texto", "pcr_perguntas", area=True, max_chars=8000, height=150)
    nps = campo(st, "Pergunta de 0 a 10 (opcional)", "texto", "pcr_nps", max_chars=500)
    st.html(f'<div class="crh-pc-anonimo">Respostas são anônimas. O resultado só mostra grupos com {_MINIMO_PADRAO} pessoas ou mais.</div>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="pcr_nova_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Criar pesquisa", type="primary", key="pcr_nova_ok"):
            perguntas = perguntas_do_texto(texto, nps)
            erro = validar_pesquisa(titulo, inicio, fim, _MINIMO_PADRAO, perguntas, hoje)
            if erro:
                alerta(slot, "erro", erro)
                return
            try:
                criar_pesquisa_clima(st.session_state.token, titulo.strip(), None, inicio.isoformat(), fim.isoformat(), _MINIMO_PADRAO, perguntas)
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            _concluir("Pesquisa criada." if inicio > hoje else "Pesquisa criada e aberta para respostas.")


@st.dialog("Perguntas da pesquisa", width="medium", on_dismiss=_fechar)
def _modal_perguntas(pesquisa: dict) -> None:
    perguntas = sorted(pesquisa.get("perguntas") or [], key=lambda p: p.get("ordem") or 0)
    linhas = "".join(f'<li>{html.escape(p.get("texto") or "")} <span class="crh-meta">— {html.escape(ESCALAS.get(p.get("escala") or "concordancia")["nome"])}</span></li>'
                     for p in perguntas) or '<li class="crh-meta">Nenhuma pergunta ainda.</li>'
    st.html(f'<ol class="crh-pcr-lista">{linhas}</ol>')
    if pesquisa.get("situacao") != "agendada":
        st.html('<p class="crh-meta">As perguntas não mudam depois que a pesquisa abre: quem já respondeu ficaria com a pesquisa incompleta.</p>')
        return
    nova = campo(st, "Nova pergunta", "texto", "pcr_nova_pergunta", max_chars=500)
    tipo = st.radio("Escala", list(ESCALAS), format_func=lambda e: ESCALAS[e]["nome"], horizontal=True, key="pcr_nova_escala")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Incluir pergunta", type="primary", key="pcr_incluir"):
            if len((nova or "").strip()) < 5:
                alerta(slot, "erro", "Escreva a pergunta (pelo menos 5 caracteres).")
                return
            try:
                adicionar_pergunta_clima(st.session_state.token, pesquisa["id"], nova.strip(), tipo, len(perguntas) + 1)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _concluir("Pergunta incluída.")


@st.dialog("Encerrar pesquisa", width="small", on_dismiss=_fechar)
def _modal_encerrar(pesquisa: dict) -> None:
    st.html(f'<p>Encerrar <b>{html.escape(pesquisa.get("titulo") or "")}</b>? Ninguém mais consegue responder, e os resultados ficam disponíveis.</p>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="pcr_enc_voltar"):
            _fechar()
            st.rerun()
        if st.button("Encerrar", type="primary", key="pcr_enc_ok"):
            try:
                encerrar_pesquisa_clima(st.session_state.token, pesquisa["id"])
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _concluir("Pesquisa encerrada. Os resultados já estão disponíveis.")


def _celula_resumo(r: dict | None) -> str:
    if not r:
        return '<span class="crh-meta">abaixo do mínimo</span>'
    extra = f' · NPS {r["nps"]:+d}' if r.get("nps") is not None else ""
    return f'<b>{html.escape(r["media"])}</b> · {r["favoravel"]}% favorável{extra} <span class="crh-meta">({r["n"]} respostas)</span>'


@st.dialog("Resultados", width="large", on_dismiss=_fechar)
def _modal_resultados(pesquisa: dict) -> None:
    try:
        dados = _resultados(pesquisa["id"])
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    minimo = dados.get("minimo_respostas") or pesquisa.get("minimo_respostas")
    st.html(f'<p class="crh-cfg-titulo">{html.escape(pesquisa.get("titulo") or "")}</p>'
            f'<p class="crh-meta">{dados.get("participantes") or 0} pessoas responderam. Grupos com menos de {minimo} respostas não aparecem, '
            'e, quando só um grupo fica de fora, o total também não aparece, para ninguém ser identificado por eliminação.</p>')
    for i, linha in enumerate(resultados_por_pergunta(pesquisa.get("perguntas") or [], dados), start=1):
        grupos = "".join(f'<tr><td>{html.escape(nome)}</td><td>{_celula_resumo(r)}</td></tr>' for nome, r in linha["grupos"])
        st.html(f'<div class="crh-painel crh-bloco crh-pcr-res"><p class="t">{i}. {html.escape(linha["texto"] or "")}</p>'
                f'<p class="d">{html.escape(ESCALAS[linha["escala"]]["nome"])}</p>'
                f'<table><tr><td><b>Empresa</b></td><td>{_celula_resumo(linha["geral"])}</td></tr>{grupos}</table></div>')
    comentarios = [c.get("texto") for c in dados.get("comentarios") or [] if c.get("texto")]
    if comentarios:
        itens = "".join(f"<li>{html.escape(c)}</li>" for c in comentarios)
        st.html(f'<div class="crh-painel crh-bloco"><p class="crh-cfg-titulo">Comentários ({len(comentarios)})</p><ul class="crh-pcr-lista">{itens}</ul></div>')
    elif (dados.get("participantes") or 0) < (minimo or 0):
        st.html('<p class="crh-meta">Os comentários só aparecem quando a pesquisa atinge o mínimo de respostas.</p>')


# ---------------------------------------------------------------------------
# Cartões
# ---------------------------------------------------------------------------
def _cartao_pesquisa(p: dict, elegiveis: int) -> None:
    with st.container(key=f"cfg_card_pcr_{p['id']}"):
        selo, tom = situacao_rh(p)
        barras = "".join(
            f'<div class="crh-pcr-barra"><div class="r"><span>{html.escape(rotulo)}</span><span>{parte} de {total}</span></div>'
            f'<div class="barra"><span style="width:{pct}%"></span></div></div>'
            for rotulo, parte, total, pct in barras_adesao(p, elegiveis))
        st.html(f'<div class="crh-pcr-topo"><p class="crh-cfg-titulo">{html.escape(p.get("titulo") or "")}</p><span class="crh-selo {tom}">{html.escape(selo)}</span></div>'
                f'<p class="crh-meta">{html.escape(subtitulo_card(p))}</p>{barras}')
        with st.container(horizontal=True):
            if p.get("situacao") == "encerrada":
                if st.button("Ver resultados", key=f"pcr_res_{p['id']}"):
                    st.session_state.pcr_modal = ("resultados", p["id"])
                    st.rerun()
            elif st.button("Editar perguntas" if p.get("situacao") == "agendada" else "Ver perguntas", key=f"pcr_perg_{p['id']}"):
                st.session_state.pcr_modal = ("perguntas", p["id"])
                st.rerun()
            if p.get("situacao") == "aberta" and st.button("Encerrar pesquisa", key=f"pcr_enc_{p['id']}"):
                st.session_state.pcr_modal = ("encerrar", p["id"])
                st.rerun()


def _cartao_resultado(pesquisa: dict | None) -> None:
    with st.container(key="cfg_card_pcr_resultado"):
        if pesquisa is None:
            st.html('<p class="crh-cfg-titulo">Resultado</p><p class="crh-meta">O resultado aparece aqui quando a primeira pesquisa for encerrada.</p>')
            return
        try:
            dados = _resultados(pesquisa["id"])
        except ApiError as erro:
            st.html(f'<p class="crh-cfg-titulo">Resultado — {html.escape(pesquisa.get("titulo") or "")}</p>')
            alerta(st.empty(), "erro", erro.message)
            return
        r = resumo_card(pesquisa.get("perguntas") or [], dados)
        linhas = [("eNPS geral", f'{r["enps"]:+d}' if r["enps"] is not None else "—", "")]
        if r["destaque"]:
            linhas.append((f'"{r["destaque"][0]}"', r["destaque"][1], ""))
        linhas.append(("Pior tema", r["pior_tema"] or "—", "ambar" if r["pior_tema"] else ""))
        corpo = "".join(f'<div class="crh-pcr-kv"><span>{html.escape(k)}</span><b class="{cls}">{html.escape(v)}</b></div>' for k, v, cls in linhas)
        minimo = dados.get("minimo_respostas") or pesquisa.get("minimo_respostas") or _MINIMO_PADRAO
        st.html(f'<p class="crh-cfg-titulo">Resultado — {html.escape(pesquisa.get("titulo") or "")}</p>{corpo}'
                f'<p class="crh-nota-ambar">Grupos com menos de {minimo} respostas não aparecem no resultado para proteger o anonimato.</p>')


def pagina_pesquisas_clima() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Pesquisas de clima", "Monte a pesquisa, acompanhe a adesão e veja o resultado agregado")
    if str(usuario.get("perfil", "")).upper() not in ("RH", "ADMIN"):
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return
    try:
        with st.spinner("Carregando..."):
            dados = _guardado("clima_cache_rh", lambda: pesquisas_clima_rh(token))
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    pesquisas, elegiveis, hoje = dados.get("pesquisas") or [], dados.get("elegiveis") or 0, _hoje(dados)
    with st.container(horizontal=True, vertical_alignment="center"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Aba", list(ABAS_RH), default="Em andamento", required=True, key="pcr_aba", label_visibility="collapsed")
        st.space("stretch")
        if st.button("Nova pesquisa", type="primary", key="pcr_nova"):
            st.session_state.pcr_modal = ("nova", None)
            st.rerun()
    lista = da_aba(pesquisas, aba)
    encerradas = da_aba(pesquisas, "Encerradas")
    esquerda, direita = st.columns([1, 1], gap="medium")
    with esquerda:
        if not lista:
            vazio = "Nenhuma pesquisa em andamento. Crie uma em \"Nova pesquisa\"." if aba == "Em andamento" else "Nenhuma pesquisa encerrada ainda."
            st.html(f'<div class="crh-painel crh-bloco"><p class="crh-meta">{html.escape(vazio)}</p></div>')
        for p in lista:
            _cartao_pesquisa(p, elegiveis)
    with direita:
        _cartao_resultado(encerradas[0] if encerradas else None)

    modal = st.session_state.get("pcr_modal")
    if not modal:
        return
    tipo, alvo = modal
    pesquisa = next((p for p in pesquisas if p["id"] == alvo), None)
    if tipo == "nova":
        _modal_nova(hoje)
    elif pesquisa is None:
        _fechar()
    elif tipo == "perguntas":
        _modal_perguntas(pesquisa)
    elif tipo == "encerrar":
        _modal_encerrar(pesquisa)
    elif tipo == "resultados":
        _modal_resultados(pesquisa)
