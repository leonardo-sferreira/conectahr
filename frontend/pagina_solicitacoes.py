"""
Página "Solicitações ao RH" do RH e do Admin (tarefa 47 da change concluir-frontend-streamlit; Figma 225:5299
e 206:1072 — a conferir com o Figma, que estava fora do ar quando a tela foi feita; ver design.md).

Abas Em aberto, Atendidas e Recusadas, com filtros de tipo e departamento. "Analisar →" abre o pedido:
- alteração cadastral: mostra o valor atual e o novo e já preenche o cadastro com o valor pedido; "Aplicar e
  atender" grava o cadastro (`colaboradores/{id}` PATCH, só o RH) e atende o pedido;
- outros pedidos: atender (justificativa opcional) ou recusar (justificativa obrigatória).
Endpoints: `solicitacoes`, `solicitacoes/{id}/atender|indeferir`, `colaboradores` e `organograma`.
Ninguém decide o próprio pedido. Os pedidos LGPD ficam na tela "Pedidos LGPD".
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import ApiError, atender_solicitacao, atualizar_dados_pessoais, colaboradores, indeferir_solicitacao, organograma, solicitacoes_rh
from cadastro_modelo import perfil
from decisoes_modelo import pessoas
from solicitacoes_modelo import ABAS, CAMPO_PARA_CADASTRO, TIPOS, aplicar_pedido, dados_atuais, linhas, resumo, validar_dados_pessoais, validar_justificativa
from theme import alerta, render_hero, render_indicadores, render_topbar

_CACHE = "solicitacoes_cache"
_VALIDADE_CACHE_S = 20
_ROTULOS = {"nome": "Nome completo", "cpf": "CPF (só números)", "email_pessoal": "E-mail pessoal", "telefone": "Telefone", "cep": "CEP",
            "logradouro": "Logradouro", "numero": "Número", "complemento": "Complemento", "bairro": "Bairro", "cidade": "Cidade", "estado": "Estado (UF)"}
_ENDERECO = ["cep", "logradouro", "numero", "complemento", "bairro", "cidade", "estado"]


def _carregar(token: str) -> dict:
    cache = st.session_state.get(_CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = {"solicitacoes": solicitacoes_rh(token).get("solicitacoes") or []}
    for chave, funcao, campo in (("colaboradores", colaboradores, "colaboradores"), ("organograma", organograma, None)):
        try:
            resposta = funcao(token)
            dados[chave] = (resposta.get(campo) or []) if campo else resposta
        except ApiError:
            dados[chave] = [] if campo else {}
    st.session_state[_CACHE] = {"em": time.time(), "dados": dados}
    return dados


def _fechar() -> None:
    st.session_state.pop("modal_solicitacao", None)
    for chave in [k for k in st.session_state if str(k).startswith("sol_campo_")]:
        st.session_state.pop(chave, None)


def _concluir(aviso: str) -> None:
    st.session_state.pop(_CACHE, None)
    st.session_state.pop("sol_justificativa", None)
    _fechar()
    st.session_state.aviso_toast = aviso
    st.rerun()


def _campos(linhas_: list[tuple[str, str]]) -> None:
    campos = "".join(f'<p class="r">{html.escape(r)}</p><p class="v">{html.escape(v)}</p>' for r, v in linhas_)
    st.html(f'<div class="crh-campos crh-campos-direita">{campos}</div>')


def _formulario_cadastro(atuais: dict, preenchido: dict, campo_pedido: str | None) -> dict:
    """Os campos que o RH confere antes de gravar: o campo pedido (ou o endereço) e, se o texto do pedido não
    for reconhecido, todos. Os demais vão como estão na ficha."""
    if campo_pedido in CAMPO_PARA_CADASTRO.values():
        visiveis = [campo_pedido]
    elif campo_pedido == "endereco":
        visiveis = _ENDERECO
    else:
        visiveis = [c for c in preenchido if c != "data_nascimento"] + ["data_nascimento"]
    dados = dict(preenchido)
    st.html('<p class="crh-meta" style="margin:0">Confira o valor que vai para o cadastro:</p>')
    for campo in visiveis:
        if campo == "data_nascimento":
            try:
                valor = date.fromisoformat(preenchido.get("data_nascimento") or "")
            except ValueError:
                valor = None
            escolhida = st.date_input("Data de nascimento", value=valor, min_value=date(1920, 1, 1), max_value=date.today(), format="DD/MM/YYYY", key="sol_campo_nasc")
            dados["data_nascimento"] = escolhida.isoformat() if escolhida else ""
        else:
            dados[campo] = st.text_input(_ROTULOS[campo], value=preenchido.get(campo, ""), key=f"sol_campo_{campo}")
    return dados


@st.dialog("Analisar solicitação", width="medium", on_dismiss=_fechar)
def _modal_analisar(linha: dict, colab: dict | None) -> None:
    _campos([("Pessoa", f"{linha['pessoa']} · {linha['detalhe']}"), ("Pedido", linha["tipo"]), ("Aberto em", linha["aberto_em"]), ("Responder até", linha["prazo"])])
    alt = linha["alteracao"]
    eh_rh = perfil(st.session_state.usuario.get("perfil")) == "RH"
    aplicar = linha["tipo_chave"] == "alteracao_cadastral" and eh_rh and colab is not None
    dados = None
    if alt:
        st.html(
            '<div class="crh-campos"><p class="r">Campo</p><p class="v">' + html.escape(alt["campo"]) + '</p>'
            '<p class="r">Valor atual</p><p class="v">' + html.escape(alt["atual"]) + '</p>'
            '<p class="r">Novo valor</p><p class="v" style="color:#D97706">' + html.escape(alt["novo"]) + '</p>'
            + (f'<p class="r">Motivo</p><p class="v">{html.escape(alt["motivo"])}</p>' if alt["motivo"] else "") + "</div>"
        )
    else:
        st.html(f'<p class="crh-pg-nota" style="white-space:pre-wrap">{html.escape(linha["descricao"])}</p>')
    if aplicar:
        campo = CAMPO_PARA_CADASTRO.get((alt or {}).get("campo")) or ("endereco" if (alt or {}).get("campo") == "Endereço" else None)
        atuais = dados_atuais(colab)
        dados = _formulario_cadastro(atuais, aplicar_pedido(atuais, alt), campo)
    justificativa = st.text_area("Justificativa (o colaborador vê; obrigatória para recusar)", max_chars=1000, key="sol_justificativa", height=70)
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="sol_voltar"):
            _fechar()
            st.rerun()
        indeferir = st.button("Recusar", type="primary", key="sol_indeferir")
        rotulo = "Aplicar e atender" if aplicar else "Atender"
        atender = (aplicar or linha["tipo_chave"] != "alteracao_cadastral") and st.button(rotulo, type="primary", key="sol_atender")
    if indeferir:
        erro_campo = validar_justificativa(justificativa)
        if erro_campo:
            alerta(slot, "erro", erro_campo)
            return
        try:
            indeferir_solicitacao(st.session_state.token, linha["id"], justificativa.strip())
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        _concluir(f"Pedido de {linha['pessoa']} recusado. A pessoa vê a justificativa.")
    if atender:
        if aplicar:
            erro_campo = validar_dados_pessoais(dados, date.today())
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                atualizar_dados_pessoais(st.session_state.token, linha["colaborador_id"], {k: v.strip() if isinstance(v, str) else v for k, v in dados.items()})
            except ApiError as erro:
                alerta(slot, "erro", f"O cadastro não foi alterado: {erro.message}")
                return
        try:
            atender_solicitacao(st.session_state.token, linha["id"], justificativa.strip() or None)
        except ApiError as erro:
            alerta(slot, "erro", ("O cadastro foi alterado, mas o pedido não foi marcado como atendido: " if aplicar else "") + erro.message)
            return
        _concluir(f"Pedido de {linha['pessoa']} atendido." + (" O cadastro foi atualizado." if aplicar else ""))


@st.dialog("Solicitação decidida", width="small", on_dismiss=_fechar)
def _modal_ver(linha: dict) -> None:
    _campos([("Pessoa", linha["pessoa"]), ("Pedido", linha["tipo"]), ("Situação", linha["situacao"][0]), ("Decidido em", linha["decidido_em"])])
    st.html(f'<p class="crh-pg-nota" style="white-space:pre-wrap">{html.escape(linha["descricao"])}</p>')
    if linha["justificativa"]:
        st.html(f'<p class="crh-meta" style="margin:0">Justificativa</p><p class="crh-pg-nota">{html.escape(linha["justificativa"])}</p>')
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Fechar", type="primary", key="sol_fechar"):
            _fechar()
            st.rerun()


def _tabela(itens: list[dict], aba: str, meu_colaborador_id) -> None:
    pesos = [2.4, 1.6, 3.4, 1.2, 1.2, 1.3, 1.3]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Pessoa", "Pedido", "O que pede", "Aberto em", "Responder até" if aba == "Em aberto" else "Decidido em", "Situação", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not itens:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhum pedido nesta aba.</p>')
        for i, l in enumerate(itens):
            with st.container(key=f"rh_linf_{i}" if aba == "Em aberto" else f"rh_lin_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["pessoa"])}</p><p class="d">{html.escape(l["detalhe"])}</p></div>')
                for coluna, texto in zip(c[1:4], (l["tipo"], l["pedido"], l["aberto_em"])):
                    coluna.html(f'<p class="crh-doc-prazo">{html.escape(texto)}</p>')
                quando = l["prazo"] if aba == "Em aberto" else l["decidido_em"]
                cor = ' style="color:#DC2626"' if l["atrasado"] else ""
                c[4].html(f'<p class="crh-doc-prazo"{cor}>{html.escape(quando)}{" (atrasado)" if l["atrasado"] else ""}</p>')
                c[5].html(f'<span class="crh-selo {l["situacao"][1]}">{html.escape(l["situacao"][0])}</span>', width="content")
                with c[6]:
                    if aba != "Em aberto":
                        if st.button("Ver", type="tertiary", key=f"sol_ver_{l['id']}"):
                            st.session_state.modal_solicitacao = ("ver", l["id"])
                            st.rerun()
                    elif meu_colaborador_id is not None and l["colaborador_id"] == meu_colaborador_id:
                        st.html('<p class="crh-meta">Seu pedido: outra pessoa do RH decide</p>')
                    elif st.button("Analisar →", type="tertiary", key=f"sol_analisar_{l['id']}"):
                        st.session_state.modal_solicitacao = ("analisar", l["id"])
                        st.rerun()


def pagina_solicitacoes() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Solicitações ao RH", "Pedidos dos colaboradores: alteração cadastral, declarações e documentos. Prazo de resposta: 15 dias.")
    if perfil(usuario.get("perfil")) not in ("RH", "ADMIN"):
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return
    with st.spinner("Carregando..."):
        try:
            dados, erro = _carregar(token), None
        except ApiError as falha:
            dados, erro = None, falha
    if erro is not None:
        alerta(st.empty(), "erro", erro.message)
        return

    hoje = date.today()
    numeros = resumo(dados["solicitacoes"], hoje)
    render_indicadores([
        ("Em aberto", str(numeros["em_aberto"]), "ambar"),
        ("Alterações cadastrais", str(numeros["cadastrais"]), "azul"),
        ("Fora do prazo", str(numeros["atrasadas"]), "negativo"),
        ("Atendidas no mês", str(numeros["atendidas_mes"]), "verde"),
    ])
    org = dados["organograma"]
    deps = {d.get("id"): d.get("nome") for d in org.get("departamentos") or []}
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Aba", list(ABAS), default="Em aberto", required=True, key="sol_aba", label_visibility="collapsed")
        st.space("stretch")
        tipo = st.selectbox("Tipo", [None] + list(TIPOS), format_func=lambda t: "Tipo: Todos" if t is None else f"Tipo: {TIPOS[t]}", key="sol_tipo", label_visibility="collapsed", width=230)
        dep = st.selectbox("Departamento", [None] + sorted(deps, key=deps.get), format_func=lambda d: "Departamento: Todos" if d is None else f"Departamento: {deps[d]}", key="sol_dep", label_visibility="collapsed", width=230)

    mapa = pessoas(org)
    itens = linhas(dados["solicitacoes"], mapa, aba, hoje, tipo, dep)
    _tabela(itens, aba, usuario.get("colaborador_id"))

    modal = st.session_state.get("modal_solicitacao")
    if not modal:
        return
    acao, sid = modal
    todas = [l for nome in ABAS for l in linhas(dados["solicitacoes"], mapa, nome, hoje)]
    linha = next((l for l in todas if l["id"] == sid), None)
    if linha is None:
        _fechar()
        return
    if acao == "ver":
        _modal_ver(linha)
    elif linha["situacao"][0] in ("Recebida", "Em análise") and linha["colaborador_id"] != usuario.get("colaborador_id"):
        _modal_analisar(linha, next((c for c in dados["colaboradores"] if c.get("id") == linha["colaborador_id"]), None))
    else:
        _fechar()
