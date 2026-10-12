"""
Página "Central de Pendências" (tarefas 11 a 13, 20, 21 e 24 da change concluir-frontend-streamlit).

- Gestor, RH e Admin (Figma seção 19): aba "Férias" (436:1145), com "Decidir →" no modal 436:1473, que
  mostra a conferência de conflitos (`ferias/{id}/verificar_conflito`, só informa) e aprova ou rejeita;
  aba "Correções de ponto" (436:1308), com "Aprovar" direto e "Rejeitar" com motivo (436:1506); e a
  aba "Minhas pendências".
- Colaborador (F13, 31:37): só "Minhas pendências", com a trilha por assunto.

As filas vêm no escopo de quem pede: `central_de_tarefas.fila_ferias_pendentes` e `correcoes_ponto`
(o Gestor só a própria equipe; RH e Admin todos). O backend confere cada decisão de novo e bloqueia
quem tenta decidir o próprio pedido; a tela não oferece o botão nesse caso.
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import (
    ApiError,
    aprovar_ausencia,
    aprovar_correcao_ponto,
    aprovar_ferias,
    central_de_tarefas,
    correcoes_ponto,
    minhas_ausencias,
    minhas_correcoes_ponto,
    minhas_ferias,
    minhas_pendencias_documento,
    minhas_solicitacoes,
    organograma,
    rejeitar_ausencia,
    rejeitar_correcao_ponto,
    rejeitar_ferias,
    solicitacoes_rh,
    verificar_conflito_ferias,
)
from decisoes_modelo import (
    conferencia_ferias,
    linhas_ausencias_fila,
    linhas_correcoes,
    linhas_ferias,
    minhas_pendencias,
    pessoas,
    tem_alerta,
    validar_motivo,
)
from theme import alerta, html_linha_onboarding, render_hero, render_indicadores, render_topbar

DECISORES = ("GESTOR", "RH", "ADMIN")
_CACHE = "central_cache"
_CACHE_MINHAS = "central_minhas_cache"
_VALIDADE_CACHE_S = 20
_ABAS = ["ferias", "correcoes", "ausencias", "minhas"]


def _invalidar() -> None:
    st.session_state.pop(_CACHE, None)
    st.session_state.pop(_CACHE_MINHAS, None)


def _fechar() -> None:
    st.session_state.pop("modal_central", None)
    st.session_state.pop("central_conflito", None)


def _concluir(aviso: str) -> None:
    _invalidar()
    _fechar()
    st.session_state.aviso_toast = aviso
    st.rerun()


def _carregar_filas(token: str) -> dict:
    """{'central', 'correcoes', 'erro_correcoes', 'organograma'} guardado por 20 s. Erro da central sobe;
    sem correções ou organograma a tela segue com o que tem."""
    cache = st.session_state.get(_CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = {"central": central_de_tarefas(token), "erro_correcoes": None, "solicitacoes": None}
    if str(st.session_state.usuario.get("perfil", "")).upper() in ("RH", "ADMIN"):
        try:
            dados["solicitacoes"] = sum(
                1 for s in solicitacoes_rh(token).get("solicitacoes") or []
                if s.get("tipo") != "privacidade_lgpd" and (s.get("status") or "recebida") in ("recebida", "em_analise")
            )
        except ApiError:
            dados["solicitacoes"] = None
    try:
        dados["correcoes"] = correcoes_ponto(token).get("correcoes") or []
    except ApiError as erro:
        dados["correcoes"], dados["erro_correcoes"] = [], erro.message
    try:
        dados["organograma"] = organograma(token)
    except ApiError:
        dados["organograma"] = {}
    st.session_state[_CACHE] = {"em": time.time(), "dados": dados}
    return dados


def _carregar_minhas(token: str, central: dict | None) -> dict:
    """As listas da própria pessoa. Cada uma que falhar (conta sem colaborador, por exemplo) fica vazia."""
    cache = st.session_state.get(_CACHE_MINHAS)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = {"falhas": 0}
    if central is None:
        try:
            central = central_de_tarefas(token)
        except ApiError:
            central, dados["falhas"] = {}, dados["falhas"] + 1
    dados["central"] = central
    for chave, funcao, campo in (
        ("solicitacoes", minhas_solicitacoes, "solicitacoes"),
        ("ferias", minhas_ferias, "ferias"),
        ("ausencias", minhas_ausencias, "ausencias"),
        ("pendencias", minhas_pendencias_documento, "pendencias"),
        ("correcoes", minhas_correcoes_ponto, "correcoes"),
    ):
        try:
            dados[chave] = funcao(token).get(campo) or []
        except ApiError as erro:
            dados[chave] = []
            if erro.status_code != 404:
                dados["falhas"] += 1
    st.session_state[_CACHE_MINHAS] = {"em": time.time(), "dados": dados}
    return dados


# ---------------------------------------------------------------------------
# Modais (abertos enquanto `modal_central` estiver na sessão)
# ---------------------------------------------------------------------------
def _campos(linhas: list[tuple[str, str]]) -> None:
    campos = "".join(f'<p class="r">{html.escape(r)}</p><p class="v">{html.escape(v)}</p>' for r, v in linhas)
    st.html(f'<div class="crh-campos crh-campos-direita">{campos}</div>')


@st.dialog("Decidir férias", width="small", on_dismiss=_fechar)
def _modal_ferias(linha: dict) -> None:
    _campos([("Pessoa", linha["pessoa"]), ("Período", f"{linha['periodo']} · {linha['dias']}"), ("Pedido em", linha["pedido_em"])])
    conflito = st.session_state.get("central_conflito")
    if conflito is None or conflito.get("_id") != linha["id"]:
        try:
            with st.spinner("Conferindo conflitos..."):
                conflito = verificar_conflito_ferias(st.session_state.token, linha["id"])
        except ApiError as erro:
            conflito = {"_erro": erro.message}
        conflito["_id"] = linha["id"]
        st.session_state.central_conflito = conflito
    st.html('<p class="crh-meta" style="margin:0">Conferência (só informa, não bloqueia)</p>')
    if conflito.get("_erro"):
        st.html(f'<p class="crh-nota-ambar">Não foi possível conferir agora: {html.escape(conflito["_erro"])}</p>')
    else:
        classe = "crh-nota-ambar" if tem_alerta(conflito) else "crh-pg-nota"
        st.html(f'<p class="{classe}">{html.escape(" · ".join(conferencia_ferias(conflito)))}</p>')
    if linha["observacao"] != "—":
        st.html(f'<p class="crh-meta" style="margin:0">Observação do colaborador</p><p class="crh-pg-nota">{html.escape(linha["observacao"])}</p>')
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">A pessoa recebe a decisão por notificação. Ninguém decide o próprio pedido.</p></div>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right", key="central_fe_botoes"):
        if st.button("Voltar", key="central_fe_voltar"):
            _fechar()
            st.rerun()
        rejeitar = st.button("Rejeitar", type="primary", key="central_fe_rejeitar")
        aprovar = st.button("Aprovar", type="primary", key="central_fe_aprovar")
    if rejeitar or aprovar:
        try:
            (aprovar_ferias if aprovar else rejeitar_ferias)(st.session_state.token, linha["id"])
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        _concluir(f"Férias de {linha['pessoa']} {'aprovadas' if aprovar else 'rejeitadas'}. A pessoa recebe o aviso.")


@st.dialog("Rejeitar ausência", width="small", on_dismiss=_fechar)
def _modal_rejeitar_ausencia(linha: dict) -> None:
    _campos([("Pessoa", linha["pessoa"]), ("Tipo", linha["tipo"]), ("Período", linha["periodo"])])
    texto = st.text_area("Justificativa (obrigatória)", max_chars=1000, key="central_aus_motivo", height=90,
                         help="Não escreva diagnóstico nem código CID: o diagnóstico fica só no atestado, com o RH.")
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">A pessoa recebe a justificativa. O comprovante é visto só pelo RH.</p></div>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="central_aus_voltar"):
            _fechar()
            st.rerun()
        if st.button("Rejeitar ausência", type="primary", key="aus_rej_ok"):
            erro_campo = validar_motivo(texto)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                rejeitar_ausencia(st.session_state.token, linha["id"], texto.strip())
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            st.session_state.pop("central_aus_motivo", None)
            _concluir(f"Ausência de {linha['pessoa']} rejeitada. A pessoa vê a justificativa.")


@st.dialog("Rejeitar correção de ponto", width="small", on_dismiss=_fechar)
def _modal_rejeitar_correcao(linha: dict) -> None:
    _campos([("Pessoa", linha["pessoa"]), ("Pedido", f"{linha['campo']} · {linha['horario']}"), ("Dia", linha["dia"])])
    motivo = st.text_area("Motivo (obrigatório, 5 caracteres ou mais)", max_chars=1000, key="central_cor_motivo", height=90)
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">O colaborador recebe o motivo por notificação. O registro do dia continua como estava.</p></div>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="central_cor_voltar"):
            _fechar()
            st.rerun()
        if st.button("Rejeitar correção", type="primary", key="central_cor_ok"):
            erro_campo = validar_motivo(motivo)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                rejeitar_correcao_ponto(st.session_state.token, linha["id"], motivo.strip())
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            st.session_state.pop("central_cor_motivo", None)
            _concluir(f"Correção de {linha['pessoa']} rejeitada. A pessoa vê o motivo.")


# ---------------------------------------------------------------------------
# Tabelas
# ---------------------------------------------------------------------------
def _cabecalho(titulos: list[str], pesos: list[float]) -> None:
    with st.container(key="rh_cab"):
        for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), titulos):
            coluna.html(f'<p class="crh-doc-cab">{html.escape(texto)}</p>')


def _pessoa(coluna, nome: str, detalhe: str) -> None:
    coluna.html(f'<div class="crh-doc-cel"><p class="t">{html.escape(nome)}</p><p class="d">{html.escape(detalhe)}</p></div>')


def _texto(coluna, texto: str) -> None:
    coluna.html(f'<p class="crh-doc-prazo">{html.escape(texto)}</p>')


def _vazio(texto: str) -> None:
    with st.container(key="rh_lin_vazio"):
        st.html(f'<p class="crh-meta">{html.escape(texto)}</p>')


def _tabela_ferias(linhas: list[dict]) -> None:
    pesos = [2.6, 1.1, 2, 3, 1.4, 1.5]
    with st.container(key="rh_tabela"):
        _cabecalho(["Pessoa", "Dias", "Período", "Observação", "Pedido em", ""], pesos)
        if not linhas:
            _vazio("Nenhum pedido de férias para decidir.")
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_linf_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                _pessoa(c[0], l["pessoa"], l["detalhe"])
                c[1].html(f'<span class="crh-selo neu">{html.escape(l["dias"])}</span>', width="content")
                _texto(c[2], l["periodo"])
                _texto(c[3], l["observacao"])
                _texto(c[4], l["pedido_em"])
                with c[5]:
                    if l["proprio"]:
                        st.html('<p class="crh-meta">Seu pedido: outra pessoa decide</p>')
                    elif st.button("Decidir →", type="tertiary", key=f"central_fe_{l['id']}"):
                        st.session_state.modal_central = ("ferias", l["id"])
                        st.session_state.pop("central_conflito", None)
                        st.rerun()


def _tabela_correcoes(linhas: list[dict], token: str) -> None:
    pesos = [2.6, 1.2, 1.4, 3, 1.4, 1.8]
    with st.container(key="rh_tabela"):
        _cabecalho(["Pessoa", "Campo", "Dia", "Justificativa", "Horário pedido", ""], pesos)
        if not linhas:
            _vazio("Nenhuma correção de ponto para decidir.")
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_linf_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                _pessoa(c[0], l["pessoa"], l["detalhe"])
                _texto(c[1], l["campo"])
                _texto(c[2], l["dia"])
                _texto(c[3], l["justificativa"])
                _texto(c[4], l["horario"] + (f" (era {l['original']})" if l["original"] else ""))
                with c[5]:
                    if l["proprio"]:
                        st.html('<p class="crh-meta">Sua correção: outra pessoa decide</p>')
                        continue
                    with st.container(horizontal=True, gap="small"):
                        if st.button("Rejeitar", type="tertiary", key=f"rh_recusar_cor_{l['id']}"):
                            st.session_state.modal_central = ("rejeitar_correcao", l["id"])
                            st.rerun()
                        if st.button("Aprovar", type="tertiary", key=f"central_cor_aprovar_{l['id']}"):
                            try:
                                aprovar_correcao_ponto(token, l["id"])
                            except ApiError as erro:
                                st.session_state.central_erro = erro.message
                                st.rerun()
                            _invalidar()
                            st.session_state.aviso_toast = f"Correção de {l['pessoa']} aprovada. O horário do dia foi trocado."
                            st.rerun()


def _tabela_ausencias(linhas: list[dict], token: str) -> None:
    pesos = [2.8, 1.4, 2.2, 3]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Pessoa", "Tipo", "Período", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            _vazio("Nenhuma ausência para decidir.")
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_linf_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                _pessoa(c[0], l["pessoa"], l["detalhe"])
                _texto(c[1], l["tipo"])
                _texto(c[2], l["periodo"])
                with c[3]:
                    if l["proprio"]:
                        st.html('<p class="crh-meta">Sua ausência: outra pessoa decide</p>')
                        continue
                    with st.container(horizontal=True, gap="small"):
                        if st.button("Rejeitar", type="tertiary", key=f"rh_recusar_aus_c_{l['id']}"):
                            st.session_state.modal_central = ("rejeitar_ausencia", l["id"])
                            st.rerun()
                        if st.button("Aprovar", type="tertiary", key=f"central_aus_aprovar_{l['id']}"):
                            try:
                                aprovar_ausencia(token, l["id"])
                            except ApiError as erro:
                                st.session_state.central_erro = erro.message
                                st.rerun()
                            _invalidar()
                            st.session_state.aviso_toast = f"Ausência de {l['pessoa']} aprovada. O RH registra."
                            st.rerun()


def _minhas(token: str, central: dict | None) -> None:
    with st.spinner("Carregando..."):
        dados = _carregar_minhas(token, central)
    secoes = minhas_pendencias(dados["central"], dados["solicitacoes"], dados["ferias"], dados["ausencias"], dados["pendencias"], dados["correcoes"], date.today())
    if dados["falhas"]:
        alerta(st.empty(), "atencao", "Parte das suas pendências não carregou agora. O que aparece abaixo pode estar incompleto.")
    if not secoes:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">Nada pendente por aqui. Pedidos e decisões dos últimos 30 dias aparecem nesta tela.</p></div>')
        return
    for s in secoes:
        itens = "".join(
            f'<div class="crh-ct-item"><div class="crh-ct-ponto"><span class="p {i["tom"]}"></span><span class="l"></span></div>'
            f'{html_linha_onboarding(i["titulo"], i["detalhe"], i["badge"], i["tom"])}</div>'
            for i in s["itens"]
        )
        st.html(f'<p class="crh-bloco-titulo">{html.escape(s["titulo"])}</p><div class="crh-ct">{itens}</div>')
    st.html('<p class="crh-meta">Avaliações, metas e PDI entram aqui quando a Trajetória existir.</p>')


# ---------------------------------------------------------------------------
def pagina_central() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    perfil = str(usuario.get("perfil", "")).upper()

    # Quem decide (tarefa 83): RH, Admin e Gestor, e também quem é superior direto de alguém, de qualquer perfil.
    central_leve = None
    if perfil not in DECISORES:
        try:
            central_leve = central_de_tarefas(token)
        except ApiError:
            central_leve = None
        if not (central_leve or {}).get("e_superior"):
            render_hero("Central de Pendências", "Suas solicitações, férias, ausências e documentos pendentes em um só lugar.")
            _minhas(token, central_leve)
            return

    render_hero("Central de Pendências", "Pedidos da sua equipe para decidir: quem tem você como superior direto (ou, sem superior, o departamento que você gerencia). RH e Admin veem todos.")
    with st.spinner("Carregando..."):
        try:
            dados, erro = _carregar_filas(token), None
        except ApiError as falha:
            dados, erro = None, falha
    if erro is not None:
        alerta(st.empty(), "erro", erro.message)
        return

    central = dados["central"]
    mapa = pessoas(dados["organograma"])
    fila_ferias = central.get("fila_ferias_pendentes") or []
    fila_ausencias = central.get("fila_ausencias_pendentes") or []
    render_indicadores([
        ("Férias para decidir", str(len(fila_ferias)), "ambar"),
        ("Correções de ponto", str(len(dados["correcoes"])), "azul"),
        ("Ausências para decidir", str(len(fila_ausencias)), "negativo"),
        ("Documentos para conferir", str(len(central.get("fila_documentos_pendentes") or [])), "verde"),
    ])

    rotulos = {"ferias": f"Férias ({len(fila_ferias)})", "correcoes": f"Correções de ponto ({len(dados['correcoes'])})",
               "ausencias": f"Ausências ({len(fila_ausencias)})", "minhas": "Minhas pendências"}
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Aba", _ABAS, default="ferias", required=True, format_func=rotulos.get, key="central_aba", label_visibility="collapsed")
        st.space("stretch")
        departamento = None
        if aba != "minhas" and perfil in ("RH", "ADMIN"):
            deps = {d.get("id"): d.get("nome") for d in dados["organograma"].get("departamentos") or []}
            departamento = st.selectbox(
                "Departamento", [None] + sorted(deps, key=deps.get), format_func=lambda d: "Departamento: Todos" if d is None else f"Departamento: {deps[d]}",
                key="central_dep", label_visibility="collapsed", width=230,
            )

    if dados.get("solicitacoes"):
        with st.container(horizontal=True, vertical_alignment="center", key="central_solicitacoes"):
            n = dados["solicitacoes"]
            st.html(f'<p class="crh-nota-ambar">{n} solicitaç{"ões" if n != 1 else "ão"} ao RH em aberto (alteração cadastral, declarações e documentos).</p>', width="stretch")
            if st.button("Abrir Solicitações ao RH →", type="tertiary", key="central_ir_solicitacoes"):
                st.session_state.ir_solicitacoes = True
                st.rerun()

    if erro_acao := st.session_state.pop("central_erro", None):
        alerta(st.empty(), "erro", erro_acao)

    meu = usuario.get("colaborador_id")
    if aba == "ferias":
        _tabela_ferias(linhas_ferias(fila_ferias, mapa, meu, departamento))
        st.html('<p class="crh-meta">"Decidir" mostra a conferência de conflitos (antecedência, período aquisitivo, sobreposições e colegas de férias), que só informa. Ninguém decide o próprio pedido; a tentativa fica na auditoria.</p>')
    elif aba == "correcoes":
        if dados["erro_correcoes"]:
            alerta(st.empty(), "erro", dados["erro_correcoes"])
        _tabela_correcoes(linhas_correcoes(dados["correcoes"], mapa, meu, departamento), token)
        st.html('<p class="crh-meta">Aprovar troca o horário no registro do dia e recalcula o banco de horas. Rejeitar exige motivo. Ninguém decide a própria correção.</p>')
    elif aba == "ausencias":
        _tabela_ausencias(linhas_ausencias_fila(fila_ausencias, mapa, meu, departamento), token)
        st.html('<p class="crh-meta">Aqui aparecem só o tipo e o período: o comprovante (atestado) é visto só pelo RH. Depois de aprovada, o RH registra a ausência. Rejeitar exige justificativa.</p>')
    else:
        _minhas(token, central)

    modal = st.session_state.get("modal_central")
    if not modal:
        return
    acao, item_id = modal
    if acao == "ferias":
        linha = next((l for l in linhas_ferias(fila_ferias, mapa, meu) if l["id"] == item_id and not l["proprio"]), None)
        if linha is None:
            _fechar()  # o pedido saiu da fila desde que a linha foi desenhada
            return
        _modal_ferias(linha)
    elif acao == "rejeitar_ausencia":
        linha = next((l for l in linhas_ausencias_fila(fila_ausencias, mapa, meu) if l["id"] == item_id and not l["proprio"]), None)
        if linha is None:
            _fechar()
            return
        _modal_rejeitar_ausencia(linha)
    elif acao == "rejeitar_correcao":
        linha = next((l for l in linhas_correcoes(dados["correcoes"], mapa, meu) if l["id"] == item_id and not l["proprio"]), None)
        if linha is None:
            _fechar()
            return
        _modal_rejeitar_correcao(linha)
