"""
Desenho do formulário de metas (change ciclo-de-metas), comum às telas da pessoa ("Metas do ciclo"), do RH ("Ciclos
de avaliação") e da equipe ("Metas da equipe"): a trilha das três etapas e, em cada etapa, as perguntas com as
respostas e a caixa de feedback. Sem Figma (docs/figma-pendencias.md); só componentes e tokens do tema.
"""

import html
from datetime import date

import streamlit as st

from ciclo_metas_modelo import ESCALA, ETAPAS, feedbacks_da_etapa, periodo, situacao_etapa
from theme import html_linha_onboarding


def trilha_etapas(ciclo: dict, hoje: date, enviadas: dict) -> None:
    """As três etapas ligadas pela trilha de pontos (o mesmo desenho da Trajetória)."""
    itens = ""
    for n in (1, 2, 3):
        badge, tom = situacao_etapa(ciclo, n, hoje, enviadas)
        itens += (f'<div class="crh-ct-item"><div class="crh-ct-ponto"><span class="p {tom}"></span><span class="l"></span></div>'
                  f'{html_linha_onboarding(f"Etapa {n} — {ETAPAS[n]}", periodo(ciclo, n), badge, tom)}</div>')
    st.html(f'<div class="crh-ct">{itens}</div>')


def _resposta(rotulo: str, valor: str | None) -> str:
    return f'<p class="r"><b>{html.escape(rotulo)}:</b> {html.escape(valor) if valor else "—"}</p>'


def _caixa_feedback(feedbacks: list[dict], n: int) -> str:
    itens = feedbacks_da_etapa(feedbacks, n)
    corpo = "".join(f'<p class="i">{html.escape(f["texto"])}</p><p class="q">{html.escape(f["autor"])} · {html.escape(f["quando"])}</p>' for f in itens)
    vazio = '<p class="q">Nenhum feedback nesta etapa ainda.</p>'
    return f'<div class="crh-cm-fb"><p class="t">Feedback do gestor</p>{corpo or vazio}</div>'


def etapa_leitura(ciclo: dict, n: int, perguntas: list[dict], enviadas: dict, feedbacks: list[dict], hoje: date) -> None:
    """Uma etapa só para ler: as respostas (quando enviada) e a caixa de feedback."""
    badge, tom = situacao_etapa(ciclo, n, hoje, enviadas)
    corpo = ""
    if enviadas.get(n):
        for p in perguntas:
            linhas = _resposta("Meta", p["meta"]) if n == 1 else (
                _resposta("Meta", p["meta"]) + _resposta("O que foi alcançado", p[f"alcancado{n}"])
                + _resposta("Autoavaliação", ESCALA.get(p[f"auto{n}"])))
            corpo += f'<div class="crh-cm-q"><p class="p">{html.escape(p["texto"])}</p>{linhas}</div>'
        corpo += _caixa_feedback(feedbacks, n)
    else:
        corpo = '<p class="crh-meta">Ainda não enviada.</p>'
    st.html(f'<div class="crh-painel crh-cm-etapa"><div class="crh-cm-cab"><div><p class="t">Etapa {n} — {html.escape(ETAPAS[n])}</p>'
            f'<p class="s">{html.escape(periodo(ciclo, n))}</p></div><span class="crh-selo {tom}">{html.escape(badge)}</span></div>{corpo}</div>')


def tabela_pessoas(linhas: list[dict], prefixo: str, vazio: str) -> int | None:
    """Pessoa, departamento e a situação das três etapas; devolve o formulário escolhido em "Abrir →"."""
    pesos = [2.6, 2, 1.7, 1.7, 1.7, 1.1]
    escolhido = None
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Pessoa", "Departamento", "Etapa 1", "Etapa 2", "Etapa 3", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            with st.container(key="rh_lin_vazio"):
                st.html(f'<p class="crh-meta">{html.escape(vazio)}</p>')
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_lin_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["nome"])}</p></div>')
                c[1].html(f'<p class="crh-doc-prazo">{html.escape(l["departamento"])}</p>')
                for coluna, (badge, tom) in zip(c[2:5], l["etapas"]):
                    coluna.html(f'<span class="crh-selo {tom}">{html.escape(badge)}</span>', width="content")
                with c[5]:
                    if l["formulario_id"] and st.button("Abrir →", type="tertiary", key=f"{prefixo}_abrir_{l['formulario_id']}"):
                        escolhido = l["formulario_id"]
    return escolhido
