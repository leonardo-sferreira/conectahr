"""
Página "Benefícios" (tarefa 82 da change concluir-frontend-streamlit). A conferir com o Figma, que estava fora do ar.

- Todos: "Meus benefícios" — os ativos (com o valor pago pela empresa e o desconto) e o histórico (`meus_beneficios`).
- RH e Admin, também:
  - "Catálogo": cadastrar benefício (`beneficios` POST) e ativar ou desativar (`beneficios/{id}/status`);
  - "Por colaborador": os benefícios da pessoa (`colaboradores/{id}/beneficios`), vincular um do catálogo e encerrar
    (`colaborador_beneficios/{id}/encerrar`), sem apagar.
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import (
    ApiError,
    beneficios_catalogo,
    beneficios_da_pessoa,
    cadastrar_beneficio,
    colaboradores,
    encerrar_beneficio,
    meus_beneficios,
    organograma,
    status_beneficio,
    vincular_beneficio,
)
from beneficios_modelo import TIPOS, linhas, moeda, validar_beneficio, validar_vinculo
from cadastro_modelo import perfil
from theme import alerta, render_hero, render_indicadores, render_topbar

_VALIDADE_CACHE_S = 20


def _cache(chave: str, carregar):
    guardado = st.session_state.get("beneficios_cache") or {}
    item = guardado.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = carregar()
    guardado[chave] = {"em": time.time(), "dados": dados}
    st.session_state.beneficios_cache = guardado
    return dados


def _fechar() -> None:
    st.session_state.pop("modal_beneficio", None)


def _concluir(aviso: str) -> None:
    st.session_state.pop("beneficios_cache", None)
    _fechar()
    st.session_state.aviso_toast = aviso
    st.rerun()


def _cartoes(itens: list[dict], encerrados: bool = False) -> None:
    for l in itens:
        operadora = f" · {html.escape(l['operadora'])}" if l["operadora"] else ""
        vigencia = f"De {l['desde']} a {l['ate']}" if l["ate"] else f"Desde {l['desde']}"
        obs = f'<p class="d">{html.escape(l["observacao"])}</p>' if l["observacao"] else ""
        selo = '<span class="crh-selo neu">Encerrado</span>' if encerrados else '<span class="crh-selo ok">Ativo</span>'
        st.html(
            f'<div class="crh-linha-onb"><div class="txt"><p class="t">{html.escape(l["nome"])}</p>'
            f'<p class="d">{html.escape(l["tipo"])}{operadora} · {html.escape(vigencia)}</p>'
            f'<p class="d">Empresa paga {html.escape(l["valor_empresa"])} · Desconto {html.escape(l["desconto"])}</p>{obs}</div>{selo}</div>'
        )


def _meus(token: str) -> None:
    with st.spinner("Carregando..."):
        try:
            dados, erro = _cache("meus", lambda: meus_beneficios(token).get("beneficios") or []), None
        except ApiError as falha:
            dados, erro = None, falha
    if erro is not None:
        if erro.status_code == 404:
            st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">Sua conta ainda não está ligada a um cadastro de funcionário, então não há benefícios.</p></div>')
        else:
            alerta(st.empty(), "erro", erro.message)
        return
    visao = linhas(dados, date.today())
    render_indicadores([
        ("Benefícios ativos", str(len(visao["ativos"])), "verde"),
        ("A empresa paga por mês", visao["total_empresa"], ""),
        ("Desconto no seu pagamento", visao["total_desconto"], "ambar"),
        ("Encerrados", str(len(visao["encerrados"])), ""),
    ])
    st.html('<p class="crh-bloco-titulo">Ativos</p>')
    if visao["ativos"]:
        _cartoes(visao["ativos"])
    else:
        st.html('<p class="crh-meta">Você ainda não tem benefício ativo. Dúvidas: fale com o RH.</p>')
    if visao["encerrados"]:
        st.html('<p class="crh-bloco-titulo">Histórico</p>')
        _cartoes(visao["encerrados"], encerrados=True)


# ---------------------------------------------------------------------------
# RH e Admin
# ---------------------------------------------------------------------------
@st.dialog("Novo benefício", width="small", on_dismiss=_fechar)
def _modal_novo() -> None:
    nome = st.text_input("Nome", max_chars=100, placeholder="Ex.: Plano de saúde Unimed", key="ben_nome")
    tipo = st.selectbox("Tipo", list(TIPOS), format_func=TIPOS.get, index=None, placeholder="Escolha", key="ben_tipo")
    operadora = st.text_input("Operadora ou fornecedor (opcional)", max_chars=100, key="ben_operadora")
    descricao = st.text_area("Descrição (opcional)", max_chars=500, key="ben_descricao", height=70)
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="ben_novo_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Cadastrar", type="primary", key="ben_novo_ok"):
            erro_campo = validar_beneficio(nome, tipo)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                cadastrar_beneficio(st.session_state.token, nome.strip(), tipo, operadora.strip() or None, descricao.strip() or None)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            for chave in ("ben_nome", "ben_tipo", "ben_operadora", "ben_descricao"):
                st.session_state.pop(chave, None)
            _concluir(f"Benefício {nome.strip()} cadastrado.")


@st.dialog("Vincular benefício", width="small", on_dismiss=_fechar)
def _modal_vincular(pessoa: dict, catalogo: list[dict]) -> None:
    ativos = {b["id"]: b for b in catalogo if b.get("ativo", True)}
    st.html(f'<p class="crh-meta" style="margin:0">Para {html.escape(pessoa.get("nome") or "")}</p>')
    bid = st.selectbox("Benefício", list(ativos), format_func=lambda i: f"{ativos[i].get('nome')} — {TIPOS.get(ativos[i].get('tipo'), 'Outro')}", index=None,
                       placeholder="Escolha do catálogo" if ativos else "Cadastre um benefício no Catálogo antes", key="ben_v_id")
    c1, c2 = st.columns(2)
    valor = c1.number_input("A empresa paga (R$/mês)", min_value=0.0, value=0.0, step=10.0, format="%.2f", key="ben_v_valor")
    desconto = c2.number_input("Desconto do colaborador (R$/mês)", min_value=0.0, value=0.0, step=10.0, format="%.2f", key="ben_v_desc")
    c3, c4 = st.columns(2)
    inicio = c3.date_input("Início", value=date.today(), format="DD/MM/YYYY", key="ben_v_inicio")
    fim = c4.date_input("Fim (opcional)", value=None, format="DD/MM/YYYY", key="ben_v_fim")
    obs = st.text_input("Observação (opcional)", max_chars=500, key="ben_v_obs")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="ben_v_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Vincular", type="primary", key="ben_v_ok"):
            erro_campo = validar_vinculo(bid, valor, desconto, inicio, fim)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            dados = {"beneficio_id": bid, "valor_empresa": float(valor), "desconto_colaborador": float(desconto), "data_inicio": inicio.isoformat(),
                     "data_fim": fim.isoformat() if fim else None, "observacao": obs.strip() or None}
            try:
                vincular_beneficio(st.session_state.token, pessoa["id"], dados)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            for chave in ("ben_v_id", "ben_v_valor", "ben_v_desc", "ben_v_inicio", "ben_v_fim", "ben_v_obs"):
                st.session_state.pop(chave, None)
            _concluir(f"{ativos[bid].get('nome')} vinculado a {pessoa.get('nome')}.")


@st.dialog("Encerrar benefício", width="small", on_dismiss=_fechar)
def _modal_encerrar(pessoa: dict, linha: dict) -> None:
    st.html(f'<p class="crh-meta" style="margin:0">{html.escape(linha["nome"])} de {html.escape(pessoa.get("nome") or "")}, desde {html.escape(linha["desde"])}</p>')
    fim = st.date_input("Último dia", value=date.today(), format="DD/MM/YYYY", key="ben_e_fim")
    obs = st.text_input("Motivo (opcional)", max_chars=500, key="ben_e_obs")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="ben_e_voltar"):
            _fechar()
            st.rerun()
        if st.button("Encerrar", type="primary", key="ben_e_ok"):
            try:
                encerrar_beneficio(st.session_state.token, linha["id"], fim.isoformat(), obs.strip() or None)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            for chave in ("ben_e_fim", "ben_e_obs"):
                st.session_state.pop(chave, None)
            _concluir(f"{linha['nome']} de {pessoa.get('nome')} encerrado.")


def _catalogo(token: str) -> None:
    try:
        catalogo = _cache("catalogo", lambda: beneficios_catalogo(token).get("beneficios") or [])
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        st.html('<p class="crh-meta">O catálogo é a lista de benefícios que a empresa oferece. Benefício desativado não aceita novos vínculos; os atuais continuam.</p>', width="stretch")
        if st.button("Novo benefício", type="primary", key="ben_novo"):
            st.session_state.modal_beneficio = ("novo", None)
            st.rerun()
    pesos = [3, 2, 2.2, 1.2, 1.4]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Benefício", "Tipo", "Operadora", "Situação", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not catalogo:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhum benefício cadastrado. Use "Novo benefício".</p>')
        for i, b in enumerate(catalogo):
            with st.container(key=f"rh_lin_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(b.get("nome") or "")}</p><p class="d">{html.escape(b.get("descricao") or "")}</p></div>')
                c[1].html(f'<p class="crh-doc-prazo">{html.escape(TIPOS.get(b.get("tipo"), "Outro"))}</p>')
                c[2].html(f'<p class="crh-doc-prazo">{html.escape(b.get("operadora") or "—")}</p>')
                ativo = b.get("ativo", True)
                c[3].html(f'<span class="crh-selo {"ok" if ativo else "neu"}">{"Ativo" if ativo else "Desativado"}</span>', width="content")
                with c[4]:
                    if st.button("Desativar" if ativo else "Reativar", type="tertiary", key=f"ben_status_{b['id']}"):
                        try:
                            status_beneficio(token, b["id"], not ativo)
                        except ApiError as erro:
                            st.session_state.ben_erro = erro.message
                            st.rerun()
                        _concluir(f"{b.get('nome')} {'desativado' if ativo else 'reativado'}.")
    if erro := st.session_state.pop("ben_erro", None):
        alerta(st.empty(), "erro", erro)


def _por_colaborador(token: str) -> None:
    try:
        base = _cache("base", lambda: {"colabs": colaboradores(token).get("colaboradores") or [], "org": organograma(token)})
        catalogo = _cache("catalogo", lambda: beneficios_catalogo(token).get("beneficios") or [])
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    deps = {d.get("id"): d.get("nome") for d in base["org"].get("departamentos") or []}
    pessoas = {c["id"]: c for c in sorted(base["colabs"], key=lambda c: (c.get("nome") or "").casefold()) if str(c.get("status") or "").upper() != "DESLIGADO"}
    if not pessoas:
        st.html('<p class="crh-meta">Nenhum colaborador ativo.</p>')
        return
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        pid = st.selectbox("Pessoa", list(pessoas), format_func=lambda i: f"{pessoas[i].get('nome')} — {deps.get(pessoas[i].get('departamento_id')) or '—'}",
                           key="ben_pessoa", label_visibility="collapsed", width=360)
        st.space("stretch")
        if st.button("Vincular benefício", type="primary", key="ben_vincular"):
            st.session_state.modal_beneficio = ("vincular", pid)
            st.rerun()
    pessoa = pessoas[pid]
    try:
        vinculos = _cache(f"pessoa-{pid}", lambda: beneficios_da_pessoa(token, pid).get("beneficios") or [])
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    visao = linhas(vinculos, date.today())
    render_indicadores([
        ("Benefícios ativos", str(len(visao["ativos"])), "verde"),
        ("A empresa paga por mês", visao["total_empresa"], ""),
        ("Desconto do colaborador", visao["total_desconto"], "ambar"),
        ("Encerrados", str(len(visao["encerrados"])), ""),
    ])
    if not visao["ativos"] and not visao["encerrados"]:
        st.html('<p class="crh-meta">Esta pessoa ainda não tem benefício. Use "Vincular benefício".</p>')
    for l in visao["ativos"]:
        with st.container(horizontal=True, vertical_alignment="center", key=f"ben_lin_{l['id']}"):
            _cartoes([l])
            if st.button("Encerrar", type="tertiary", key=f"rh_recusar_ben_{l['id']}"):
                st.session_state.modal_beneficio = ("encerrar", (pid, l["id"]))
                st.rerun()
    if visao["encerrados"]:
        st.html('<p class="crh-bloco-titulo">Histórico</p>')
        _cartoes(visao["encerrados"], encerrados=True)

    modal = st.session_state.get("modal_beneficio")
    if modal and modal[0] == "vincular" and modal[1] == pid:
        _modal_vincular(pessoa, catalogo)
    elif modal and modal[0] == "encerrar" and modal[1][0] == pid:
        linha = next((l for l in visao["ativos"] if l["id"] == modal[1][1]), None)
        if linha is None:
            _fechar()
        else:
            _modal_encerrar(pessoa, linha)


def pagina_beneficios() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    rh = perfil(usuario.get("perfil")) in ("RH", "ADMIN")
    render_hero("Benefícios", "Os benefícios da empresa: valores, descontos e vigência" if rh else "Seus benefícios, o que a empresa paga e o que é descontado")
    if not rh:
        _meus(token)
        return
    abas = ["Meus benefícios", "Catálogo", "Por colaborador"]
    with st.container(key="cfg_abas", width="content"):
        aba = st.segmented_control("Aba", abas, default=abas[0], required=True, key="ben_aba", label_visibility="collapsed")
    if aba == "Meus benefícios":
        _meus(token)
    elif aba == "Catálogo":
        _catalogo(token)
        if (st.session_state.get("modal_beneficio") or (None,))[0] == "novo":
            _modal_novo()
    else:
        _por_colaborador(token)
