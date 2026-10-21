"""
Página "Riscos psicossociais" do grupo RH (NR-1; Figma, seção 21: 545:1274, 548:1287 e os modais 548:1592 e 548:1916;
change riscos-psicossociais). Só RH e Admin.

Abas:
- Avaliações: as avaliações psicossociais (pesquisas do tipo "psicossocial"), com a adesão por setor e "Encerrar";
  "Nova avaliação" cria com o questionário padrão (16 perguntas em 8 dimensões, por frequência) e uma pergunta extra.
- Resultado: o mapa de risco (dimensão × setor, de 0 a 100) de uma avaliação encerrada e os riscos altos sem ação,
  com "Criar ação".
- Plano de ação: indicadores, as ações com setor e risco, medida, responsável, prazo e situação, e "Atualizar".
- Relatório PGR: o inventário, a participação e o plano em Markdown, para baixar e anexar ao PGR.
As pessoas respondem pela tela "Pesquisa de clima" (escala de frequência). Endpoints: `pesquisas_clima_rh`,
`pesquisas_clima` POST (tipo psicossocial), `pesquisas_clima/{id}/encerrar`, `pesquisas_clima/{id}/resultados` e
`acoes_psicossociais` (GET, POST e `{id}` PATCH).
"""

import html
import time
from datetime import date, timedelta

import streamlit as st

from api_client import (ApiError, acoes_psicossociais, atualizar_acao_psicossocial, criar_acao_psicossocial, criar_pesquisa_clima, encerrar_pesquisa_clima,
                        pesquisas_clima_rh, resultados_pesquisa_clima)
from campos import campo
from clima_modelo import barras_adesao, situacao_rh, subtitulo_card
from psicossocial_modelo import (ABAS, DIMENSOES, EMPRESA, MINIMO_PADRAO, NIVEIS, STATUS_ACAO, indicadores_plano, matriz, perguntas_padrao, relatorio_pgr,
                                 riscos_sem_acao, selo, situacao_acao, validar_acao, validar_avaliacao)
from onboarding_modelo import data_br
from theme import alerta, render_hero, render_indicadores, render_topbar

_VALIDADE_CACHE_S = 20


def _guardado(chave: str, buscar):
    item = st.session_state.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = buscar()
    st.session_state[chave] = {"em": time.time(), "dados": dados}
    return dados


def _fechar() -> None:
    for chave in [k for k in st.session_state if str(k).startswith(("nr1_modal", "nr1_form_"))]:
        st.session_state.pop(chave, None)


def _concluir(aviso: str) -> None:
    for chave in [k for k in st.session_state if str(k).startswith(("nr1_cache", "nr1_modal", "nr1_form_"))]:
        st.session_state.pop(chave, None)
    st.session_state.aviso_toast = aviso
    st.rerun()


def _hoje(dados: dict) -> date:
    try:
        return date.fromisoformat(str(dados.get("hoje"))[:10])
    except ValueError:
        return date.today()


def _resultados(pesquisa_id: int) -> dict:
    return _guardado(f"nr1_cache_res_{pesquisa_id}", lambda: resultados_pesquisa_clima(st.session_state.token, pesquisa_id))


# ---------------------------------------------------------------------------
# Modais
# ---------------------------------------------------------------------------
@st.dialog("Nova avaliação psicossocial", width="medium", on_dismiss=_fechar)
def _modal_nova(hoje: date) -> None:
    titulo = campo(st, "Nome", "texto", "nr1_form_titulo", max_chars=200, placeholder=f"Ex.: Avaliação psicossocial {hoje.year}")
    c1, c2 = st.columns(2)
    inicio = c1.date_input("Abre em", value=hoje, min_value=hoje, format="DD/MM/YYYY", key="nr1_form_inicio")
    fim = c2.date_input("Fecha em", value=hoje + timedelta(days=14), min_value=hoje, format="DD/MM/YYYY", key="nr1_form_fim")
    with st.expander("Questionário: padrão NR-1, 16 perguntas em 8 dimensões"):
        st.html("<ol class='crh-pcr-lista'>" + "".join(f"<li>{html.escape(p['texto'])} <span class='crh-meta'>— {html.escape(p['dimensao'])}</span></li>"
                                                       for p in perguntas_padrao()) + "</ol>")
    extra = campo(st, "Pergunta extra (opcional)", "texto", "nr1_form_extra", max_chars=500, placeholder="Ex.: As metas do trimestre são possíveis de cumprir?")
    st.html(f'<div class="crh-pc-anonimo">Respostas anônimas, por frequência (Nunca a Sempre). Setores com menos de {MINIMO_PADRAO} respostas não aparecem. '
            'Repita a avaliação pelo menos uma vez por ano.</div>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="nr1_nova_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Abrir avaliação", type="primary", key="nr1_nova_ok"):
            erro = validar_avaliacao(titulo, inicio, fim, hoje, extra)
            if erro:
                alerta(slot, "erro", erro)
                return
            try:
                criar_pesquisa_clima(st.session_state.token, titulo.strip(), "Avaliação de riscos psicossociais (NR-1).", inicio.isoformat(), fim.isoformat(),
                                     MINIMO_PADRAO, perguntas_padrao(extra), tipo="psicossocial")
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            _concluir("Avaliação criada. As pessoas respondem pela tela Pesquisa de clima.")


@st.dialog("Encerrar avaliação", width="small", on_dismiss=_fechar)
def _modal_encerrar(pesquisa: dict) -> None:
    st.html(f'<p>Encerrar <b>{html.escape(pesquisa.get("titulo") or "")}</b>? Ninguém mais responde, e o resultado fica disponível.</p>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="nr1_enc_voltar"):
            _fechar()
            st.rerun()
        if st.button("Encerrar", type="primary", key="nr1_enc_ok"):
            try:
                encerrar_pesquisa_clima(st.session_state.token, pesquisa["id"])
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _concluir("Avaliação encerrada. O resultado já está na aba Resultado.")


@st.dialog("Nova ação", width="medium", on_dismiss=_fechar)
def _modal_acao(avaliacoes: list[dict], setores: dict, preset: dict) -> None:
    ids = [a["id"] for a in avaliacoes]
    st.session_state.setdefault("nr1_form_av", preset.get("pesquisa_id") if preset.get("pesquisa_id") in ids else (ids[0] if ids else None))
    nomes_av = {a["id"]: a.get("titulo") for a in avaliacoes}
    av = st.selectbox("Avaliação", ids, format_func=nomes_av.get, key="nr1_form_av")
    c1, c2 = st.columns(2)
    opcoes_setor = [0] + sorted(setores, key=lambda s: setores[s] or "")
    st.session_state.setdefault("nr1_form_setor", preset.get("departamento_id") or 0)
    setor = c1.selectbox("Setor", opcoes_setor, format_func=lambda s: EMPRESA if s == 0 else setores.get(s, f"Setor {s}"), key="nr1_form_setor")
    st.session_state.setdefault("nr1_form_dim", preset.get("dimensao"))
    dimensao = c2.selectbox("Dimensão", DIMENSOES, placeholder="Escolha a dimensão", key="nr1_form_dim")
    medida = campo(st, "Medida", "texto", "nr1_form_medida", area=True, max_chars=1000, height=80,
                   placeholder="O que muda nas condições de trabalho do setor.")
    c3, c4 = st.columns(2)
    responsavel = campo(c3, "Responsável", "texto", "nr1_form_resp", max_chars=150, placeholder="Ex.: Gestor de TI")
    prazo = c4.date_input("Prazo", value=None, format="DD/MM/YYYY", key="nr1_form_prazo")
    alerta(st.empty(), "atencao", "Foque nas condições de trabalho do setor, não em pessoas. A ação entra no relatório do PGR.")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="nr1_acao_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Criar ação", type="primary", key="nr1_acao_ok"):
            erro = validar_acao(dimensao, medida, responsavel, prazo) or (None if av else "Escolha a avaliação.")
            if erro:
                alerta(slot, "erro", erro)
                return
            try:
                criar_acao_psicossocial(st.session_state.token, av, setor or None, dimensao, preset.get("nivel"), medida.strip(), responsavel.strip(), prazo.isoformat())
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            _concluir("Ação criada no plano.")


@st.dialog("Atualizar ação", width="medium", on_dismiss=_fechar)
def _modal_atualizar(acao: dict) -> None:
    st.html(f'<p class="crh-meta">{html.escape(acao.get("dimensao") or "")}</p>')
    st.session_state.setdefault("nr1_form_status", acao.get("status"))
    status = st.selectbox("Situação", list(STATUS_ACAO), format_func=lambda s: STATUS_ACAO[s][0], key="nr1_form_status")
    st.session_state.setdefault("nr1_form_medida_ed", acao.get("medida") or "")
    medida = campo(st, "Medida", "texto", "nr1_form_medida_ed", area=True, max_chars=1000, height=80)
    c1, c2 = st.columns(2)
    st.session_state.setdefault("nr1_form_resp_ed", acao.get("responsavel") or "")
    responsavel = campo(c1, "Responsável", "texto", "nr1_form_resp_ed", max_chars=150)
    try:
        prazo_atual = date.fromisoformat(str(acao.get("prazo"))[:10])
    except ValueError:
        prazo_atual = None
    prazo = c2.date_input("Prazo", value=prazo_atual, format="DD/MM/YYYY", key="nr1_form_prazo_ed")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="nr1_upd_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Salvar", type="primary", key="nr1_upd_ok"):
            if len((medida or "").strip()) < 10:
                alerta(slot, "erro", "Descreva a medida (pelo menos 10 caracteres).")
                return
            try:
                atualizar_acao_psicossocial(st.session_state.token, acao["id"], status, medida.strip(), (responsavel or "").strip(), prazo.isoformat() if prazo else None)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _concluir("Ação atualizada.")


# ---------------------------------------------------------------------------
# Abas
# ---------------------------------------------------------------------------
def _aba_avaliacoes(avaliacoes: list[dict], elegiveis: int) -> None:
    if not avaliacoes:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">Nenhuma avaliação ainda. Abra a primeira em "Nova avaliação".</p></div>')
    for p in avaliacoes:
        with st.container(key=f"cfg_card_nr1_{p['id']}"):
            selo_p, tom = situacao_rh(p)
            barras = "".join(f'<div class="crh-pcr-barra"><div class="r"><span>{html.escape(r)}</span><span>{parte} de {total}</span></div>'
                             f'<div class="barra"><span style="width:{pct}%"></span></div></div>' for r, parte, total, pct in barras_adesao(p, elegiveis))
            st.html(f'<div class="crh-pcr-topo"><p class="crh-cfg-titulo">{html.escape(p.get("titulo") or "")}</p><span class="crh-selo {tom}">{html.escape(selo_p)}</span></div>'
                    f'<p class="crh-meta">{html.escape(subtitulo_card(p))}</p>{barras}')
            if p.get("situacao") == "aberta" and st.button("Encerrar avaliação", key=f"nr1_enc_{p['id']}"):
                st.session_state.nr1_modal = ("encerrar", p["id"])
                st.rerun()


def _tabela_mapa(mat: dict) -> str:
    cab = "".join(f"<th>{html.escape(n)}</th>" for _, n in mat["colunas"])
    corpo = ""
    for dim, valores in mat["linhas"]:
        cels = "".join(f'<td><span class="crh-nr1-cel {selo(valores.get(g))[1]}">{html.escape(selo(valores.get(g))[0])}</span></td>' for g, _ in mat["colunas"])
        corpo += f"<tr><td class='d'>{html.escape(dim)}</td>{cels}</tr>"
    return f'<table class="crh-nr1-mapa"><tr><th>Dimensão</th>{cab}</tr>{corpo}</table>'


def _aba_resultado(token: str, encerradas: list[dict], acoes: list[dict], elegiveis: int) -> None:
    if not encerradas:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">O resultado aparece quando uma avaliação é encerrada.</p></div>')
        return
    por_id = {p["id"]: p for p in encerradas}
    with st.container(key="cfg_card_nr1_mapa"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.space("stretch")
            escolhida = st.selectbox("Avaliação", list(por_id), format_func=lambda i: por_id[i].get("titulo"), key="nr1_res_av", width=320)
        p = por_id[escolhida]
        dados = _resultados(p["id"])
        mat = matriz(p.get("perguntas") or [], dados)
        participantes = dados.get("participantes") or p.get("participantes") or 0
        pct = f" ({round(participantes / elegiveis * 100)}%)" if elegiveis else ""
        st.html(f'<p class="crh-cfg-titulo">{html.escape(p.get("titulo") or "")}</p>'
                f'<p class="crh-meta">Encerrada em {html.escape(data_br(p.get("data_fim")))} · {participantes} de {elegiveis} pessoas responderam{pct}</p>'
                + _tabela_mapa(mat)
                + f'<p class="crh-meta">Grupos com menos de {dados.get("minimo_respostas") or MINIMO_PADRAO} respostas não aparecem (—). Risco de 0 a 100: até 33 baixo, '
                  'de 34 a 66 moderado, a partir de 67 alto. O questionário é uma referência inicial: o responsável pelo PGR valida o método.</p>')
    pendentes = riscos_sem_acao(mat, acoes, p["id"])
    with st.container(key="cfg_card_nr1_sem_acao"):
        st.html('<p class="crh-cfg-titulo">Riscos altos sem ação</p>')
        if not pendentes:
            st.html('<p class="crh-meta">Nenhum risco alto sem ação nesta avaliação.</p>')
        for i, r in enumerate(pendentes):
            with st.container(horizontal=True, vertical_alignment="center", key=f"nr1_risco_{i}"):
                st.html(f'<div class="crh-pc-item"><p class="t">{html.escape(r["setor"] or EMPRESA)} · {html.escape(r["dimensao"])}</p>'
                        f'<p class="d">Alto {r["score"]} · nenhuma ação no plano</p></div>')
                if st.button("Criar ação", type="primary", key=f"nr1_criar_{i}"):
                    st.session_state.nr1_modal = ("acao", {"pesquisa_id": p["id"], "departamento_id": r["departamento_id"], "dimensao": r["dimensao"], "nivel": "alto"})
                    st.rerun()


def _aba_plano(acoes: list[dict], setores: dict, hoje: date, sem_acao: int, nomes_av: dict) -> None:
    render_indicadores(indicadores_plano(acoes, hoje, sem_acao))
    pesos = [2.2, 3.2, 1.5, 1, 1.2, 0.9]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Setor e risco", "Medida", "Responsável", "Prazo", "Situação", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not acoes:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhuma ação ainda. Crie a partir dos riscos da aba Resultado ou em "Nova ação".</p>')
        for i, a in enumerate(acoes):
            with st.container(key=f"rh_lin_{i}"):
                col = st.columns(pesos, vertical_alignment="center")
                setor = EMPRESA if not a.get("departamento_id") else setores.get(a.get("departamento_id"), f"Setor {a.get('departamento_id')}")
                nivel_txt = f" ({NIVEIS[a['nivel_risco']][0].lower()})" if a.get("nivel_risco") in NIVEIS else ""
                col[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(setor)} · {html.escape(a.get("dimensao") or "")}{html.escape(nivel_txt)}</p>'
                            f'<p class="d">{html.escape(nomes_av.get(a.get("pesquisa_id"), ""))}</p></div>')
                col[1].html(f'<p class="crh-doc-prazo">{html.escape(a.get("medida") or "")}</p>')
                col[2].html(f'<p class="crh-doc-prazo">{html.escape(a.get("responsavel") or "")}</p>')
                col[3].html(f'<p class="crh-doc-prazo">{html.escape(data_br(a.get("prazo")))}</p>')
                s, tom = situacao_acao(a, hoje)
                col[4].html(f'<span class="crh-selo {tom}">{html.escape(s)}</span>', width="content")
                with col[5]:
                    if st.button("Atualizar", type="tertiary", key=f"nr1_upd_{a['id']}"):
                        st.session_state.nr1_modal = ("atualizar", a["id"])
                        st.rerun()
    st.html('<p class="crh-meta">O plano de ação entra no PGR com o inventário de riscos e a evidência de participação (adesão por setor). '
            'Cada ação criada ou atualizada fica na auditoria.</p>')


def _aba_relatorio(encerradas: list[dict], acoes: list[dict], elegiveis: int, setores: dict, hoje: date) -> None:
    if not encerradas:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">O relatório fica disponível depois que uma avaliação é encerrada.</p></div>')
        return
    por_id = {p["id"]: p for p in encerradas}
    escolhida = st.selectbox("Avaliação", list(por_id), format_func=lambda i: por_id[i].get("titulo"), key="nr1_rel_av", width=320)
    p = por_id[escolhida]
    texto = relatorio_pgr(p, matriz(p.get("perguntas") or [], _resultados(p["id"])), acoes, elegiveis, setores, hoje)
    st.download_button("Baixar relatório (Markdown)", texto.encode("utf-8"), file_name=f"inventario-psicossocial-{p['id']}.md", mime="text/markdown",
                       type="primary", key="nr1_baixar")
    with st.container(key="cfg_card_nr1_rel"):
        st.markdown(texto)


def pagina_riscos_psicossociais() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Riscos psicossociais", "NR-1: avaliação anônima por setor, inventário de riscos e plano de ação para o PGR")
    if str(usuario.get("perfil", "")).upper() not in ("RH", "ADMIN"):
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return
    try:
        with st.spinner("Carregando..."):
            dados = _guardado("nr1_cache_rh", lambda: pesquisas_clima_rh(token))
            acoes = _guardado("nr1_cache_acoes", lambda: acoes_psicossociais(token)).get("acoes") or []
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    avaliacoes = [p for p in dados.get("pesquisas") or [] if p.get("tipo") == "psicossocial"]
    encerradas = [p for p in avaliacoes if p.get("situacao") == "encerrada"]
    elegiveis, hoje = dados.get("elegiveis") or 0, _hoje(dados)
    setores = {d.get("departamento_id"): d.get("nome") for p in avaliacoes for d in p.get("adesao_departamentos") or []}
    with st.container(horizontal=True, vertical_alignment="center"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Aba", ABAS, default=ABAS[1] if encerradas else ABAS[0], required=True, key="nr1_aba", label_visibility="collapsed")
        st.space("stretch")
        if aba == "Plano de ação":
            if st.button("Nova ação", type="primary", key="nr1_nova_acao"):
                st.session_state.nr1_modal = ("acao", {})
                st.rerun()
        elif st.button("Nova avaliação", type="primary", key="nr1_nova"):
            st.session_state.nr1_modal = ("nova", None)
            st.rerun()
    try:
        if aba == "Avaliações":
            _aba_avaliacoes(avaliacoes, elegiveis)
        elif aba == "Resultado":
            _aba_resultado(token, encerradas, acoes, elegiveis)
        elif aba == "Plano de ação":
            sem = 0
            if encerradas:
                ultima = encerradas[0]
                sem = len(riscos_sem_acao(matriz(ultima.get("perguntas") or [], _resultados(ultima["id"])), acoes, ultima["id"]))
            _aba_plano(acoes, setores, hoje, sem, {a["id"]: a.get("titulo") for a in avaliacoes})
        else:
            _aba_relatorio(encerradas, acoes, elegiveis, setores, hoje)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
    modal = st.session_state.get("nr1_modal")
    if not modal:
        return
    tipo, alvo = modal
    if tipo == "nova":
        _modal_nova(hoje)
    elif tipo == "encerrar":
        p = next((x for x in avaliacoes if x["id"] == alvo), None)
        _modal_encerrar(p) if p else _fechar()
    elif tipo == "acao":
        _modal_acao(avaliacoes, setores, alvo or {})
    elif tipo == "atualizar":
        a = next((x for x in acoes if x["id"] == alvo), None)
        _modal_atualizar(a) if a else _fechar()
