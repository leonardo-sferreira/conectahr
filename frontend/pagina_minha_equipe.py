"""Minha equipe do Gestor: F14, frame 248:409. Nenhuma decisão é feita nesta tela."""

import html
from datetime import date

import streamlit as st

from api_client import ApiError
from minha_equipe_dados import carregar
from minha_equipe_modelo import (
    ferias_do_periodo, filtrar_pessoas, indicadores, pendencias_por_pessoa,
    ponto_da_semana, rotulo_pendencias, situacao_ponto,
)
from ponto_modelo import hoje_brasilia
from theme import alerta, html_linha_onboarding, render_hero, render_indicadores, render_topbar


def _selo(texto: str, tom: str) -> str:
    if texto == "—":
        return '<p class="crh-doc-prazo">—</p>'
    return f'<span class="crh-selo {tom}">{html.escape(texto)}</span>'


def _cabecalho(subtitulo: str) -> None:
    with st.container(key="me_cabecalho"):
        render_hero("Minha equipe", subtitulo)


def _periodo(f: dict, curto: bool = False) -> str:
    de, ate = date.fromisoformat(f["data_inicio"]), date.fromisoformat(f["data_fim"])
    inicio = de.strftime("%d") if curto and (de.year, de.month) == (ate.year, ate.month) else de.strftime("%d/%m/%Y")
    return f'{inicio} a {ate:%d/%m/%Y}'


def _central() -> None:
    # A Central já tem suas abas e filtros; não alteramos seu escopo nem seus controles.
    st.session_state.ir_central = True
    st.rerun()


def _tabela(pessoas: list[dict], org: dict, pontos: dict, pendencias: dict, ferias: list[dict] | None) -> None:
    cargos = {c["id"]: c for c in org.get("cargos") or []}
    niveis = {n["id"]: n.get("nome") for n in org.get("niveis") or []}
    pesos = [2.56, 2.2, 1.5, 1.7, 1.2, .9]
    with st.container(key="me_tabela"), st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, nome in zip(st.columns(pesos), ("Pessoa", "Cargo", "Ponto da semana", "Férias", "Pendências", "")):
                coluna.html(f'<p class="crh-doc-cab">{nome}</p>')
        if not pessoas:
            st.html('<p class="crh-meta">Nenhum liderado encontrado.</p>')
        for p in pessoas:
            pid = p["id"]
            cargo = cargos.get(p.get("cargo_id"), {})
            nome_cargo = cargo.get("nome") or "—"
            nivel = niveis.get(cargo.get("nivel_hierarquico_id"))
            detalhe = f"{nome_cargo} — {nivel}" if nivel else nome_cargo
            rotulo, tom = situacao_ponto(pontos[pid])
            pendencia = pendencias[pid]
            atencao = tom in ("err", "amb")
            futuras = [f for f in ferias or [] if f["colaborador_id"] == pid]
            ferias_texto = _periodo(futuras[0], curto=True) if futuras else "—" if ferias is not None else "Não disponível"
            with st.container(key=f"rh_linf_me_{pid}" if atencao else f"rh_lin_me_{pid}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(p.get("nome") or "—")}</p>'
                          f'<p class="d">{html.escape(detalhe)}</p></div>')
                c[1].html(f'<p class="crh-doc-prazo">{html.escape(nome_cargo)}</p>')
                c[2].html(_selo(rotulo, tom))
                c[3].html(f'<p class="crh-doc-prazo">{html.escape(ferias_texto)}</p>')
                c[4].html(_selo(rotulo_pendencias(pendencia), "amb" if pendencia["total"] else "neu"))
                with c[5]:
                    if st.button("Ver →", key=f"me_ver_{pid}", type="tertiary"):
                        _central()


def _cartoes(pessoas: list[dict], ferias: list[dict] | None) -> None:
    esquerda, direita = st.columns(2, gap="medium")
    with esquerda:
        linhas = []
        for p in pessoas:
            periodos = [f for f in ferias or [] if f["colaborador_id"] == p["id"]]
            for f in periodos:
                linhas.append(html_linha_onboarding(p.get("nome") or "—", _periodo(f), f["status"],
                                                    "amb" if f["status"] == "Pendente" else "ok"))
            if not periodos:
                linhas.append(html_linha_onboarding(p.get("nome") or "—",
                              "Sem férias marcadas" if ferias is not None else "Não disponível", "", "neu"))
        st.html('<div class="crh-painel crh-bloco crh-me-card"><div class="crh-card-h">'
                '<p class="t">Férias da equipe — próximos 90 dias</p></div>' + "".join(linhas) + '</div>')
    with direita:
        st.html('<div class="crh-painel crh-bloco crh-me-card"><div class="crh-card-h"><p class="t">O que o gestor vê</p></div>'
                '<p class="crh-meta">Ponto, férias, ausências aprovadas, avaliações e metas dos liderados. '
                'Dados bancários e documentos pessoais nunca aparecem para o gestor.</p></div>')


def pagina_minha_equipe() -> None:
    usuario = st.session_state.usuario
    render_topbar(usuario.get("nome") or "")
    if str(usuario.get("perfil") or "").strip().upper() != "GESTOR":
        _cabecalho("")
        with st.container(key="me_estado"):
            alerta(st.empty(), "erro", "Você não tem permissão para acessar esta tela.")
        return
    hoje = hoje_brasilia()
    try:
        with st.spinner("Carregando..."):
            dados = carregar(st.session_state.token, hoje)
    except ApiError as erro:
        _cabecalho("")
        if erro.status_code == 401:
            return  # O app encerra a sessão e volta para Entrar.
        with st.container(key="me_estado"):
            mensagem = ("Sua conta ainda não está ligada a um cadastro de funcionário." if erro.status_code == 404
                        else "Você não tem permissão para consultar esta equipe." if erro.status_code == 403
                        else "O servidor recebeu muitas consultas seguidas. Espere alguns segundos e tente de novo." if erro.status_code == 429
                        else "Não foi possível carregar a equipe. Tente novamente em instantes.")
            alerta(st.empty(), "atencao" if erro.status_code in (404, 429) else "erro", mensagem)
        return
    pessoas = dados["pessoas"]
    org = dados["organograma"] or {}
    deps = {d["id"]: d.get("nome") for d in org.get("departamentos") or []}
    departamento = deps.get(dados["gestor"].get("departamento_id")) or "—"
    quantidade = f'{len(pessoas)} liderado' + ("s" if len(pessoas) != 1 else "")
    _cabecalho(f"{departamento} · {quantidade}")
    if not pessoas:
        render_indicadores([(r, "0", tom) for r, _, tom in indicadores([], {}, {}, [], hoje)])
        with st.container(key="me_estado"):
            st.html('<p class="crh-bloco-titulo">Você ainda não tem equipe</p>'
                    '<p class="crh-meta">Aqui aparecem as pessoas que têm você como superior direto.</p>')
        return
    ferias = ferias_do_periodo(pessoas, dados["ferias"], hoje)
    feriados = (dados["calendario"] or {}).get("feriados")
    pontos = {p["id"]: ponto_da_semana(p, dados["meses"], feriados, hoje) for p in pessoas}
    pendencias = pendencias_por_pessoa(pessoas, dados["central"], dados["correcoes"])
    if dados["erros"]:
        with st.container(key="me_estado"):
            alerta(st.empty(), "atencao", "Algumas informações não estão disponíveis. Tente novamente em instantes.")
    with st.container(key="me_resumo"):
        render_indicadores(indicadores(pessoas, pontos, pendencias, ferias, hoje))
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        busca = st.text_input("Buscar liderado", placeholder="⌕ Buscar liderado", key="me_busca", label_visibility="collapsed", width=260)
        st.space("stretch")
        situacoes = [""] + sorted({p.get("status") for p in pessoas if p.get("status")})
        if st.session_state.get("me_situacao") not in situacoes:
            st.session_state.me_situacao = ""
        situacao = st.selectbox("Situação", situacoes, format_func=lambda s: f"Situação: {s or 'Todos'}",
                                key="me_situacao", label_visibility="collapsed", width=160)
    _tabela(filtrar_pessoas(pessoas, busca, situacao), org, pontos, pendencias, ferias)
    _cartoes(pessoas, ferias)
