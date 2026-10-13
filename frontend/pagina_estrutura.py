"""
Página "Estrutura da empresa" do RH e do Admin. Abas:

- "Feriados" (Figma 468:838; change ponto-rep-p-e-ferias-clt, tarefas 7.1 e 7.3): a lista do ano (`calendario`) e
  "Importar feriados nacionais" (`feriados/importar`), que traz os nacionais da BrasilAPI.
- "Níveis" (Figma 500:888; change organograma-hierarquia, D2 e D3): a hierarquia da empresa, com nome e ordem (1 é o
  topo); "Novo nível" e "Editar" (nome, ordem e situação), auditados no backend.
- "Cargos" (Figma 500:1156): o nível de cada cargo e quantas pessoas o ocupam; "Mudar nível".

Diferenças em relação ao Figma: sem a aba "Departamentos"; nos feriados, sem "Novo feriado", "Editar" e "Desativar"
(o backend ainda não tem a edição nem a desativação, e o cadastro não guarda o tipo).
"""

import html
from datetime import date

import streamlit as st

from api_client import (
    ApiError,
    calendario,
    criar_nivel_hierarquico,
    definir_nivel_cargo,
    editar_nivel_hierarquico,
    importar_feriados,
    niveis_hierarquicos,
    organograma,
)
from feriados_modelo import NOTA, anos_feriados, linhas_feriados, mensagem_importacao
from organograma_modelo import SEM_NIVEL, linhas_cargos, linhas_niveis, validar_nivel
from theme import alerta, render_hero, render_topbar

_PESOS = [0.8, 2.6, 1.3, 1.8]
_ABAS = ["Feriados", "Níveis", "Cargos"]


def _fechar() -> None:
    st.session_state.pop("modal_estr", None)


def _invalidar_hierarquia() -> None:
    for chave in ("estr_niveis", "estr_org", "org_cache"):
        st.session_state.pop(chave, None)


def _importar(ano: int) -> None:
    try:
        resposta = importar_feriados(st.session_state.token, ano)
    except ApiError as erro:
        st.session_state.estr_erro = erro.message
        return
    st.session_state.pop("estr_feriados", None)
    st.session_state.pop("fe_feriados", None)  # o calendário de férias também lê de novo
    st.session_state.aviso_toast = mensagem_importacao(resposta)


def _feriados(token: str) -> None:
    hoje = date.today()
    anos = anos_feriados(hoje)
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        st.space("stretch")
        ano = st.selectbox("Ano", anos, index=anos.index(hoje.year), format_func=lambda a: f"Ano: {a}", key="estr_ano", label_visibility="collapsed", width=130)
        st.button("Importar feriados nacionais", type="primary", key="estr_importar", on_click=_importar, args=(ano,),
                  help="Traz os feriados nacionais do ano.")
    if erro_acao := st.session_state.pop("estr_erro", None):
        alerta(st.empty(), "erro", erro_acao)
    if "estr_feriados" not in st.session_state:
        with st.spinner("Carregando os feriados..."):
            try:
                st.session_state.estr_feriados = calendario(token).get("feriados") or []
            except ApiError as erro:
                alerta(st.empty(), "erro", erro.message)
                return
    linhas = linhas_feriados(st.session_state.estr_feriados, ano)
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(_PESOS, vertical_alignment="center"), ["Data", "Nome", "Tipo", "Abrangência"]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            with st.container(key="rh_lin_vazio"):
                st.html(f'<p class="crh-meta">Nenhum feriado cadastrado em {ano}. Use "Importar feriados nacionais".</p>')
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_lin_{i}"):
                c = st.columns(_PESOS, vertical_alignment="center")
                c[0].html(f'<p class="crh-doc-prazo">{html.escape(l["data"])}</p>')
                c[1].html(f'<p class="crh-doc-prazo">{html.escape(l["nome"])}</p>')
                c[2].html(f'<span class="crh-selo {l["tom"]}">{html.escape(l["tipo"])}</span>')
                c[3].html(f'<p class="crh-doc-prazo">{html.escape(l["abrangencia"])}</p>')
    st.html(f'<div class="crh-incluso"><p class="n" style="margin:0">{html.escape(NOTA)}</p></div>')


# ---------------------------------------------------------------------------
# Níveis e cargos (change organograma-hierarquia)
# ---------------------------------------------------------------------------
def _hierarquia(token: str) -> tuple[list[dict], dict] | None:
    """(níveis com os inativos, organograma) guardados na sessão; None se não carregou (o erro já aparece)."""
    try:
        if "estr_niveis" not in st.session_state:
            st.session_state.estr_niveis = niveis_hierarquicos(token).get("niveis") or []
        if "estr_org" not in st.session_state:
            st.session_state.estr_org = organograma(token)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return None
    return st.session_state.estr_niveis, st.session_state.estr_org


@st.dialog("Nível da hierarquia", width="small", on_dismiss=_fechar)
def _modal_nivel(nivel: dict | None) -> None:
    nome = st.text_input("Nome do nível", value=(nivel or {}).get("nome", ""), max_chars=60, key="estr_nv_nome", placeholder="Ex.: Coordenação")
    ordem = st.number_input("Ordem (1 é o topo)", min_value=1, max_value=99, value=int((nivel or {}).get("ordem") or 1), step=1, key="estr_nv_ordem")
    ativo = st.toggle("Ativo", value=bool((nivel or {}).get("ativo", True)), key="estr_nv_ativo") if nivel else True
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="estr_nv_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Salvar nível", type="primary", key="estr_nv_salvar"):
            erro_campo = validar_nivel(nome, ordem)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                if nivel:
                    editar_nivel_hierarquico(st.session_state.token, nivel["id"], nome.strip(), int(ordem), ativo)
                else:
                    criar_nivel_hierarquico(st.session_state.token, nome.strip(), int(ordem))
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            for chave in ("estr_nv_nome", "estr_nv_ordem", "estr_nv_ativo"):
                st.session_state.pop(chave, None)
            _invalidar_hierarquia()
            _fechar()
            st.session_state.aviso_toast = "Nível salvo."
            st.rerun()


@st.dialog("Nível do cargo", width="small", on_dismiss=_fechar)
def _modal_cargo(cargo: dict, niveis: list[dict]) -> None:
    st.html(f'<p class="crh-meta" style="margin:0">Cargo: <b>{html.escape(cargo["nome"])}</b></p>')
    ativos = [n for n in sorted(niveis, key=lambda n: int(n.get("ordem") or 0)) if n.get("ativo", True)]
    opcoes = [None] + [n["id"] for n in ativos]
    nomes = {n["id"]: f'{n.get("ordem")}. {n.get("nome")}' for n in ativos}
    atual = cargo["nivel_id"] if cargo["nivel_id"] in opcoes else None
    escolha = st.selectbox("Nível", opcoes, index=opcoes.index(atual), format_func=lambda i: SEM_NIVEL if i is None else nomes[i], key="estr_cg_nivel")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="estr_cg_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Salvar", type="primary", key="estr_cg_salvar"):
            try:
                definir_nivel_cargo(st.session_state.token, cargo["id"], escolha)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            st.session_state.pop("estr_cg_nivel", None)
            _invalidar_hierarquia()
            _fechar()
            st.session_state.aviso_toast = f"Nível de {cargo['nome']} atualizado."
            st.rerun()


def _niveis(token: str) -> None:
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        st.space("stretch")
        if st.button("Novo nível", type="primary", key="estr_novo_nivel"):
            st.session_state.modal_estr = ("nivel", None)
            st.rerun()
    dados = _hierarquia(token)
    if dados is None:
        return
    niveis, org = dados
    linhas = linhas_niveis(niveis, org.get("cargos") or [])
    pesos = [0.7, 2.4, 1.2, 1.2, 1]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Ordem", "Nível", "Situação", "Cargos", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhum nível cadastrado. Use "Novo nível" para montar a hierarquia da empresa.</p>')
        for l in linhas:
            with st.container(key=f"rh_lin_nv_{l['id']}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<p class="crh-doc-prazo">{l["ordem"]}</p>')
                c[1].html(f'<p class="crh-doc-prazo">{html.escape(l["nome"])}</p>')
                c[2].html(f'<span class="crh-selo {"ok" if l["ativo"] else "neu"}">{"Ativo" if l["ativo"] else "Inativo"}</span>')
                c[3].html(f'<p class="crh-doc-prazo">{l["cargos"]} cargo{"s" if l["cargos"] != 1 else ""}</p>')
                with c[4]:
                    if st.button("Editar", type="tertiary", key=f"estr_editar_nv_{l['id']}"):
                        st.session_state.modal_estr = ("nivel", l["id"])
                        st.rerun()
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">A ordem define quem fica acima no organograma: 1 é o topo. '
            'Cada empresa cadastra a própria hierarquia.</p></div>')


def _cargos(token: str) -> None:
    dados = _hierarquia(token)
    if dados is None:
        return
    niveis, org = dados
    linhas = linhas_cargos(org.get("cargos") or [], niveis, org.get("colaboradores") or [])
    pesos = [2.6, 1.4, 1, 1.2]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Cargo", "Nível", "Pessoas", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhum cargo ativo.</p>')
        for l in linhas:
            with st.container(key=f"rh_lin_cg_{l['id']}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<p class="crh-doc-prazo">{html.escape(l["nome"])}</p>')
                c[1].html(f'<span class="crh-selo neu">{html.escape(l["nivel"])}</span>')
                c[2].html(f'<p class="crh-doc-prazo">{l["pessoas"]}</p>')
                with c[3]:
                    if st.button("Mudar nível", type="tertiary", key=f"estr_nivel_cg_{l['id']}"):
                        st.session_state.modal_estr = ("cargo", l["id"])
                        st.rerun()
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">O nível do cargo ordena e rotula as pessoas no organograma.</p></div>')


def pagina_estrutura() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Estrutura da empresa", "Departamentos, cargos e feriados usados no ponto, nas férias e no calendário")
    if str(usuario.get("perfil", "")).upper() not in ("ADMIN", "RH"):
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return
    with st.container(key="cfg_abas", width="content"):
        if st.session_state.get("estr_aba") not in _ABAS:
            st.session_state.estr_aba = _ABAS[0]
        aba = st.segmented_control("Aba", _ABAS, required=True, key="estr_aba", label_visibility="collapsed")
    if aba == "Níveis":
        _niveis(token)
    elif aba == "Cargos":
        _cargos(token)
    else:
        _feriados(token)

    modal = st.session_state.get("modal_estr")
    if not modal or aba == "Feriados":
        return
    tipo, alvo = modal
    niveis = st.session_state.get("estr_niveis") or []
    if tipo == "nivel":
        nivel = next((n for n in niveis if n.get("id") == alvo), None)
        if alvo is not None and nivel is None:
            _fechar()
            return
        _modal_nivel(nivel)
    elif tipo == "cargo":
        org = st.session_state.get("estr_org") or {}
        cargo = next((l for l in linhas_cargos(org.get("cargos") or [], niveis, org.get("colaboradores") or []) if l["id"] == alvo), None)
        if cargo is None:
            _fechar()
            return
        _modal_cargo(cargo, niveis)
