"""
Página "Ciclos de avaliação" (change ciclo-de-metas, D1, D2 e D5), no grupo RH do menu. Só RH e Admin.

- Ciclos: um por ano, com as três janelas (sugeridas em fevereiro, junho e outubro). As datas só mudam antes de a
  etapa 1 abrir; depois, todos respondem no mesmo período.
- Perguntas: as perguntas pré-definidas do formulário (criar, editar, desativar), com o conjunto sugerido quando
  ainda não há nenhuma. Formulários já respondidos guardam o texto da época.
- Formulários: todas as pessoas ativas no ciclo escolhido, com quem enviou cada etapa, e o formulário de cada uma
  (o mesmo modal da tela "Metas da equipe").

Endpoints: `ciclos_metas` (GET, POST, PATCH), `perguntas_meta` (GET, POST, PATCH) e `formularios_meta`.

A aba "Avaliações de desempenho" (Figma F27 249:5068; change pesquisa-clima-e-avaliacao-360) fica em
`avaliacoes_ciclo_ui.py`: os ciclos da avaliação por competências, a atribuição, as contestações e o andamento.
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import ApiError, alterar_ciclo_metas, alterar_pergunta_meta, ciclos_metas, criar_ciclo_metas, criar_pergunta_meta, perguntas_meta
from avaliacoes_ciclo_ui import aba_desempenho, abrir_modal
from ciclo_metas_modelo import (ETAPAS, PERGUNTAS_SUGERIDAS, datas_para_api, datas_sugeridas, linhas_pessoas, periodo, pode_alterar_datas,
                                resumo_envios, situacao_ciclo, validar_ciclo, validar_pergunta)
from formulario_metas_ui import tabela_pessoas
from pagina_metas_equipe import modal_formulario, pessoas_do_ciclo
from theme import alerta, render_hero, render_indicadores, render_topbar

_VALIDADE_CACHE_S = 20
_ABAS = ["Ciclos de metas", "Perguntas", "Formulários", "Avaliações de desempenho"]


def _guardado(chave: str, buscar):
    item = st.session_state.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = buscar()
    st.session_state[chave] = {"em": time.time(), "dados": dados}
    return dados


def _invalidar() -> None:
    for chave in [k for k in st.session_state if str(k).startswith(("cav_cache_", "mf_lista_", "cm_cache"))]:
        st.session_state.pop(chave, None)


def fechar() -> None:
    st.session_state.pop("cav_modal", None)


def _concluir(aviso: str) -> None:
    _invalidar()
    fechar()
    st.session_state.aviso_toast = aviso
    st.rerun()


def _hoje(dados: dict) -> date:
    return date.fromisoformat(str(dados.get("hoje") or date.today())[:10])


# ---------------------------------------------------------------------------
# Modais
# ---------------------------------------------------------------------------
def _campos_datas(prefixo: str, iniciais: dict) -> dict:
    datas = {}
    for n in (1, 2, 3):
        st.html(f'<p class="crh-bloco-titulo" style="font-size:14px">Etapa {n} — {html.escape(ETAPAS[n])}</p>')
        c1, c2 = st.columns(2)
        datas[f"etapa{n}_inicio"] = c1.date_input("Abre em", value=iniciais[f"etapa{n}_inicio"], format="DD/MM/YYYY", key=f"{prefixo}_e{n}_ini")
        datas[f"etapa{n}_fim"] = c2.date_input("Fecha em", value=iniciais[f"etapa{n}_fim"], format="DD/MM/YYYY", key=f"{prefixo}_e{n}_fim")
    return datas


def _botoes(rotulo: str, chave: str) -> bool:
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key=f"{chave}_cancelar"):
            fechar()
            st.rerun()
        return st.button(rotulo, type="primary", key=f"{chave}_ok")


@st.dialog("Novo ciclo de metas", width="medium", on_dismiss=fechar)
def _modal_novo_ciclo(anos_existentes: list[int], hoje: date) -> None:
    padrao = hoje.year if hoje.year not in anos_existentes and hoje < date(hoje.year, 2, 1) else max(anos_existentes + [hoje.year]) + 1
    ano = int(st.number_input("Ano", min_value=2020, max_value=2100, value=padrao, step=1, key="cav_novo_ano"))
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">As janelas são iguais para toda a empresa. Sugestão: fevereiro, junho e '
            'outubro. Depois que a etapa 1 abrir, as datas não mudam mais.</p></div>')
    datas = _campos_datas(f"cav_novo_{ano}", datas_sugeridas(ano))
    slot = st.empty()
    if _botoes("Criar ciclo", "cav_novo"):
        erro_campo = "Já existe um ciclo para este ano." if ano in anos_existentes else validar_ciclo(ano, datas)
        if erro_campo:
            alerta(slot, "erro", erro_campo)
            return
        try:
            criar_ciclo_metas(st.session_state.token, ano, datas_para_api(datas))
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        _concluir(f"Ciclo de metas {ano} criado.")


@st.dialog("Datas do ciclo", width="medium", on_dismiss=fechar)
def _modal_datas(ciclo: dict) -> None:
    iniciais = {k: date.fromisoformat(str(ciclo[k])[:10]) for k in (f"etapa{n}_{p}" for n in (1, 2, 3) for p in ("inicio", "fim"))}
    st.html(f'<p class="crh-meta">Ciclo {html.escape(str(ciclo.get("ano")))}. As datas só mudam até a véspera da etapa 1.</p>')
    datas = _campos_datas(f"cav_dt_{ciclo['id']}", iniciais)
    slot = st.empty()
    if _botoes("Salvar datas", "cav_dt"):
        erro_campo = validar_ciclo(ciclo.get("ano"), datas)
        if erro_campo:
            alerta(slot, "erro", erro_campo)
            return
        try:
            alterar_ciclo_metas(st.session_state.token, ciclo["id"], datas_para_api(datas))
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        _concluir(f"Datas do ciclo {ciclo.get('ano')} alteradas.")


@st.dialog("Pergunta do formulário", width="medium", on_dismiss=fechar)
def _modal_pergunta(pergunta: dict | None, proxima_ordem: int) -> None:
    pid = pergunta.get("id") if pergunta else "nova"
    texto = st.text_area("Pergunta", value=(pergunta or {}).get("texto") or "", max_chars=300, height=70, key=f"cav_pg_{pid}_texto")
    orientacao = st.text_area("Orientação para quem responde (opcional)", value=(pergunta or {}).get("orientacao") or "", max_chars=1000, height=70,
                              key=f"cav_pg_{pid}_orient")
    ordem = st.number_input("Ordem", min_value=1, max_value=99, value=int((pergunta or {}).get("ordem") or proxima_ordem), step=1, key=f"cav_pg_{pid}_ordem")
    ativa = st.checkbox("Ativa (aparece nos formulários novos)", value=bool((pergunta or {}).get("ativa", True)), key=f"cav_pg_{pid}_ativa") if pergunta else True
    if pergunta:
        st.html('<p class="crh-meta">Formulários já respondidos continuam com o texto da época.</p>')
    slot = st.empty()
    if _botoes("Salvar pergunta", "cav_pg"):
        erro_campo = validar_pergunta(texto, ordem)
        if erro_campo:
            alerta(slot, "erro", erro_campo)
            return
        try:
            if pergunta:
                alterar_pergunta_meta(st.session_state.token, pergunta["id"], texto.strip(), orientacao.strip(), ordem, ativa)
            else:
                criar_pergunta_meta(st.session_state.token, texto.strip(), orientacao.strip(), ordem)
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        _concluir("Pergunta salva.")


# ---------------------------------------------------------------------------
# Abas
# ---------------------------------------------------------------------------
def _aba_ciclos(token: str) -> None:
    dados = _guardado("cav_cache_ciclos", lambda: ciclos_metas(token))
    ciclos, hoje = dados.get("ciclos") or [], _hoje(dados)
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Novo ciclo", type="primary", key="cav_novo_ciclo"):
            st.session_state.cav_modal = ("novo_ciclo", None)
            st.rerun()
    pesos = [1, 2, 2, 2, 1.6, 1.4]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Ano", "Etapa 1 — Metas", "Etapa 2 — Acompanhamento", "Etapa 3 — Fechamento", "Situação", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not ciclos:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhum ciclo ainda. Crie o do ano em "Novo ciclo".</p>')
        for i, c in enumerate(ciclos):
            with st.container(key=f"rh_lin_{i}"):
                col = st.columns(pesos, vertical_alignment="center")
                col[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(str(c.get("ano")))}</p></div>')
                for n in (1, 2, 3):
                    col[n].html(f'<p class="crh-doc-prazo">{html.escape(periodo(c, n))}</p>')
                badge, tom = situacao_ciclo(c, hoje)
                col[4].html(f'<span class="crh-selo {tom}">{html.escape(badge)}</span>', width="content")
                with col[5]:
                    if pode_alterar_datas(c, hoje) and st.button("Editar datas", type="tertiary", key=f"cav_datas_{c['id']}"):
                        st.session_state.cav_modal = ("datas", c["id"])
                        st.rerun()


def _aba_perguntas(token: str) -> None:
    perguntas = _guardado("cav_cache_perguntas", lambda: perguntas_meta(token)).get("perguntas") or []
    with st.container(horizontal=True, horizontal_alignment="right"):
        if not perguntas and st.button("Usar as perguntas sugeridas", key="cav_sugeridas"):
            try:
                for i, (texto, orientacao) in enumerate(PERGUNTAS_SUGERIDAS, start=1):
                    criar_pergunta_meta(token, texto, orientacao, i)
            except ApiError as erro:
                _invalidar()
                alerta(st.empty(), "erro", erro.message)
                return
            _concluir(f"{len(PERGUNTAS_SUGERIDAS)} perguntas sugeridas criadas. Ajuste o que quiser.")
        if st.button("Nova pergunta", type="primary", key="cav_nova_pergunta"):
            st.session_state.cav_modal = ("pergunta", None)
            st.rerun()
    pesos = [0.7, 5, 1.3, 1.2]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Ordem", "Pergunta", "Situação", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not perguntas:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhuma pergunta ainda. Sem perguntas, ninguém consegue preencher o formulário.</p>')
        for i, p in enumerate(perguntas):
            with st.container(key=f"rh_lin_{i}"):
                col = st.columns(pesos, vertical_alignment="center")
                col[0].html(f'<p class="crh-doc-prazo">{html.escape(str(p.get("ordem") or "—"))}</p>')
                orient = f'<p class="d">{html.escape(p["orientacao"])}</p>' if p.get("orientacao") else ""
                col[1].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(p.get("texto") or "")}</p>{orient}</div>')
                col[2].html(f'<span class="crh-selo {"ok" if p.get("ativa") else "neu"}">{"Ativa" if p.get("ativa") else "Inativa"}</span>', width="content")
                with col[3]:
                    if st.button("Editar", type="tertiary", key=f"cav_editar_pg_{p['id']}"):
                        st.session_state.cav_modal = ("pergunta", p["id"])
                        st.rerun()


def _aba_formularios(token: str) -> None:
    dados = _guardado("cav_cache_ciclos", lambda: ciclos_metas(token))
    ciclos, hoje = dados.get("ciclos") or [], _hoje(dados)
    if not ciclos:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">Nenhum ciclo ainda. Crie o do ano na aba Ciclos de metas.</p></div>')
        return
    por_id = {c["id"]: c for c in ciclos}
    lista = None
    with st.container(horizontal=True, vertical_alignment="center"):
        ciclo_id = st.selectbox("Ciclo", list(por_id), format_func=lambda i: f"Ciclo {por_id[i].get('ano')} — {situacao_ciclo(por_id[i], hoje)[0]}",
                                key="cav_f_ciclo", label_visibility="collapsed", width=300)
        lista = pessoas_do_ciclo(token, ciclo_id)
        pessoas = lista.get("pessoas") or []
        deps = sorted({(p.get("departamento_id"), p.get("departamento")) for p in pessoas if p.get("departamento_id")}, key=lambda d: d[1] or "")
        nomes = dict(deps)
        dep = st.selectbox("Departamento", [None] + [d[0] for d in deps], format_func=lambda d: "Departamento: Todos" if d is None else f"Departamento: {nomes[d]}",
                           key="cav_f_dep", label_visibility="collapsed", width=240)
        busca = st.text_input("Busca", placeholder="⌕  Nome", key="cav_f_busca", label_visibility="collapsed", width=220)
    render_indicadores(resumo_envios(pessoas))
    escolhido = tabela_pessoas(linhas_pessoas(pessoas, lista.get("ciclo") or por_id[ciclo_id], hoje, dep, busca), "cav", "Ninguém neste filtro.")
    if escolhido:
        st.session_state.mf_aberto = escolhido
        st.rerun()


# ---------------------------------------------------------------------------
def pagina_ciclos_avaliacao() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Ciclos de avaliação", "Abra o ciclo, acompanhe cada etapa e feche quando terminar")
    if str(usuario.get("perfil", "")).upper() not in ("RH", "ADMIN"):
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return
    with st.container(key="cfg_abas"):
        aba = st.segmented_control("Aba", _ABAS, default=_ABAS[0], required=True, key="cav_aba", label_visibility="collapsed")
    try:
        {"Ciclos de metas": _aba_ciclos, "Perguntas": _aba_perguntas, "Formulários": _aba_formularios, "Avaliações de desempenho": aba_desempenho}[aba](token)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return

    if aba == "Avaliações de desempenho":
        try:
            abrir_modal(token)
        except ApiError as erro:
            alerta(st.empty(), "erro", erro.message)
        return
    if st.session_state.get("mf_aberto") and aba == "Formulários":
        modal_formulario(st.session_state.mf_aberto)
        return
    modal = st.session_state.get("cav_modal")
    if not modal:
        return
    tipo, alvo = modal
    if tipo == "novo_ciclo":
        anos = [c.get("ano") for c in (st.session_state.get("cav_cache_ciclos") or {}).get("dados", {}).get("ciclos") or []]
        _modal_novo_ciclo(anos, _hoje((st.session_state.get("cav_cache_ciclos") or {}).get("dados") or {}))
    elif tipo == "datas":
        ciclo = next((c for c in (_guardado("cav_cache_ciclos", lambda: ciclos_metas(token)).get("ciclos") or []) if c["id"] == alvo), None)
        _modal_datas(ciclo) if ciclo else fechar()
    elif tipo == "pergunta":
        perguntas = _guardado("cav_cache_perguntas", lambda: perguntas_meta(token)).get("perguntas") or []
        pergunta = next((p for p in perguntas if p["id"] == alvo), None)
        _modal_pergunta(pergunta, max([p.get("ordem") or 0 for p in perguntas] + [0]) + 1)
    else:
        fechar()
