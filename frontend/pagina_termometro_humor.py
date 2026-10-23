"""
Página "Termômetro de humor" (Figma 564:855; change termometro-de-humor), no grupo RH (RH e Admin) e no grupo Equipe
(Gestor). Só resultados agregados, nunca uma resposta individual.

- Filtro de departamento: RH e Admin escolhem entre todos; o Gestor, entre os setores que gerencia (o backend recusa
  outro).
- Indicadores do ciclo atual (humor médio, bem ou muito bem, mal ou muito mal, participação), a evolução nos últimos
  9 ciclos de 10 dias, os setores com a variação sobre o ciclo anterior e o que mais pesou.
- Grupo com menos respostas que o mínimo aparece como "—" (o backend não manda a distribuição).
Endpoint: `humor/resultados`.
"""

import html
import time

import streamlit as st

from api_client import ApiError, resultados_humor
from humor_modelo import resumo
from theme import alerta, render_hero, render_indicadores, render_topbar

_VALIDADE_CACHE_S = 20


def _carregar(token: str, departamento_id: int | None) -> dict:
    chave = f"hm_res_{departamento_id or 0}"
    item = st.session_state.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = resultados_humor(token, departamento_id)
    st.session_state[chave] = {"em": time.time(), "dados": dados}
    return dados


def _evolucao(r: dict) -> None:
    colunas = "".join(f'<div class="col{" atual" if b["atual"] else ""}{" vazio" if b["media"] is None else ""}"><p class="v">{html.escape(b["texto"])}</p>'
                      f'<div class="b" style="height:{b["altura"]}px"></div><p class="d">{html.escape(b["rotulo"])}</p></div>' for b in r["barras"])
    st.html(f'<div class="crh-painel crh-bloco"><p class="crh-cfg-titulo">Evolução nos últimos {len(r["barras"])} ciclos ({10 * len(r["barras"])} dias)</p>'
            f'<div class="crh-hm-barras">{colunas}</div>'
            f'<p class="crh-meta">Média de 1 (muito mal) a 5 (muito bem). Ciclo com menos de {r["minimo"]} respostas não aparece.</p></div>')


def _departamentos(r: dict) -> str:
    if not r["departamentos"]:
        return '<p class="crh-meta">Nenhuma resposta nos setores neste ciclo nem no anterior.</p>'
    return "".join(f'<div class="crh-hm-dep"><p class="n">{html.escape(d["nome"])}</p><p class="m">{html.escape(d["media"])}</p>'
                   + (f'<p class="v">{html.escape(d["variacao"])}</p>' if d["variacao"] else "")
                   + f'<span class="crh-selo {d["tom"]}">{html.escape(d["selo"])}</span></div>' for d in r["departamentos"])


def _motivos(r: dict) -> str:
    if r["motivos"] is None:
        return f'<p class="crh-meta">Aparece com pelo menos {r["minimo"]} respostas no ciclo.</p>'
    if not r["motivos"]:
        return '<p class="crh-meta">Ninguém marcou um motivo neste ciclo.</p>'
    return "".join(f'<div class="crh-hm-mot"><p class="l"><span>{html.escape(m["nome"])}</span><b>{m["quantidade"]}</b></p>'
                   f'<div class="barra"><span style="width:{m["pct"]}%"></span></div></div>' for m in r["motivos"])


def pagina_termometro_humor() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    render_hero("Termômetro de humor", "Como as pessoas estão se sentindo, a cada 10 dias, sem identificar ninguém")
    if str(usuario.get("perfil", "")).upper() not in ("RH", "ADMIN", "GESTOR"):
        alerta(st.empty(), "erro", "Esta tela é do RH, do Admin e dos gestores.")
        return
    filtro = st.session_state.get("hm_f_dep")
    try:
        with st.spinner("Carregando..."):
            dados = _carregar(token, filtro)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    r = resumo(dados)
    deps = {d["id"]: d["nome"] for d in dados.get("pode_filtrar") or [] if d.get("id")}
    rh = str(usuario.get("perfil", "")).upper() in ("RH", "ADMIN")
    opcoes = ([None] if rh or len(deps) > 1 else []) + list(deps)
    with st.container(horizontal=True, vertical_alignment="center"):
        if len(opcoes) > 1:
            st.selectbox("Departamento", opcoes, format_func=lambda d: "Departamento: Todos" if d is None else f"Departamento: {deps[d]}", key="hm_f_dep",
                         label_visibility="collapsed", width=280)
        st.html(f'<p class="crh-meta" style="margin:0">Ciclo atual: {html.escape(r["periodo"])} · próximo abre em {html.escape(r["proximo"])}</p>')
    render_indicadores(r["indicadores"])
    _evolucao(r)
    esquerda, direita = st.columns([1.6, 1], gap="medium")
    with esquerda:
        st.html(f'<div class="crh-painel crh-bloco"><p class="crh-cfg-titulo">Por departamento (ciclo atual)</p>{_departamentos(r)}</div>')
    with direita:
        st.html(f'<div class="crh-painel crh-bloco"><p class="crh-cfg-titulo">O que mais pesou (ciclo atual)</p>{_motivos(r)}'
                '<p class="crh-meta" style="margin-top:12px">Opcional na resposta. Contado à parte da nota, para não ligar uma coisa à outra.</p></div>')
    quem = "Você vê só os setores que gerencia. " if not rh else ""
    st.html(f'<p class="crh-meta">Grupos com menos de {r["minimo"]} respostas não aparecem (—). {quem}A resposta não guarda nome, data nem hora: '
            'só a soma por ciclo e setor.</p>')
