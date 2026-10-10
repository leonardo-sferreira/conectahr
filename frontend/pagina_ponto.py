"""
Página "Ponto" (Figma 39:18 e 233:1500; modais 221:196 e 221:285; fluxo F06; tarefas 19 a 21 da change
concluir-frontend-streamlit).

- Hoje: as quatro marcações (entrada, saída e volta do almoço, saída). "Marcar agora" chama
  `ponto/marcar`, que registra a próxima na ordem; "Editar" abre o pedido de correção daquela marcação.
- Saldo do banco de horas (`meu_banco_horas`) e o aviso de controle interno experimental.
- Espelho da semana (`meu_ponto`, `minhas_correcoes_ponto` e `minhas_ausencias`), com "Solicitar
  correção" (`ponto/{id}/solicitar_correcao`) e "Registrar ausência ou atestado" (`ausencias`).

Tudo é do próprio colaborador: nenhum endpoint daqui recebe id de pessoa. Quem decide correção e
ausência é o gestor ou o RH, em outra tela; ninguém aprova o próprio pedido (regra do backend).

Diferenças em relação ao Figma: o modal de ausência não tem o anexo do atestado (o sistema não recebe
arquivo) e o "Motivo" é a lista do backend (consulta, doença, acompanhamento familiar, outro) mais uma
observação; o saldo é o total do banco de horas, como o backend calcula, e não só o do mês.
"""

import html
import time
from datetime import date, datetime, timezone

import streamlit as st

from api_client import (
    ApiError,
    marcar_ponto,
    meu_banco_horas,
    meu_ponto,
    minhas_ausencias,
    minhas_correcoes_ponto,
    registrar_ausencia,
    solicitar_correcao_ponto,
)
from ponto_modelo import (
    MARCACOES,
    MOTIVOS_AUSENCIA,
    ROTULO_CAMPO,
    TIPOS_AUSENCIA,
    cartoes_hoje,
    espelho_da_semana,
    hora,
    registro_de_hoje,
    saldo,
    titulo_hoje,
    validar_ausencia,
    validar_correcao,
    valor_solicitado_ms,
)
from theme import alerta, render_hero, render_topbar

_CACHE = "ponto_cache"
_VALIDADE_CACHE_S = 20


def _carregar(token: str) -> dict:
    """{'registros', 'banco', 'correcoes', 'ausencias'} por 20 s. Erro de `meu_ponto` sobe (404 = sem
    colaborador); sem as outras consultas, a tela segue sem o saldo ou sem as ausências."""
    cache = st.session_state.get(_CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = {"registros": meu_ponto(token).get("registros") or []}
    for chave, funcao, campo in (
        ("banco", meu_banco_horas, None),
        ("correcoes", minhas_correcoes_ponto, "correcoes"),
        ("ausencias", minhas_ausencias, "ausencias"),
    ):
        try:
            resposta = funcao(token)
            dados[chave] = (resposta.get(campo) or []) if campo else resposta
        except ApiError:
            dados[chave] = None if campo is None else []
    st.session_state[_CACHE] = {"em": time.time(), "dados": dados}
    return dados


def _invalidar() -> None:
    st.session_state.pop(_CACHE, None)


def _fechar() -> None:
    st.session_state.pop("modal_ponto", None)


# ---------------------------------------------------------------------------
# Modais
# ---------------------------------------------------------------------------
@st.dialog("Solicitar correção de ponto", width="small", on_dismiss=_fechar)
def _modal_correcao(registro: dict, linha: dict, campo_inicial: str | None) -> None:
    st.html(
        '<div class="crh-campos crh-campos-direita">'
        f'<p class="r">Dia</p><p class="v">{html.escape(linha["dia"])}</p>'
        f'<p class="r">Situação</p><p class="v">{html.escape(linha["status"].capitalize())}</p></div>'
    )
    campos = [c for c, _ in MARCACOES]
    c1, c2 = st.columns(2)
    campo = c1.selectbox(
        "Marcação", campos, format_func=ROTULO_CAMPO.get, key="pt_corr_campo",
        index=campos.index(campo_inicial) if campo_inicial in campos else None, placeholder="Escolha",
    )
    horario = c2.time_input("Horário correto", value=None, step=60, key="pt_corr_hora")
    motivo = st.text_area("Motivo", max_chars=1000, key="pt_corr_motivo", height=80)
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">Quem decide é seu gestor ou o RH. Ninguém aprova o próprio pedido.</p></div>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="pt_corr_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Enviar pedido", type="primary", key="pt_corr_enviar"):
            erro_campo = validar_correcao(campo, horario, motivo)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                solicitar_correcao_ponto(
                    st.session_state.token, registro["id"], campo, valor_solicitado_ms(linha["data"], horario), motivo.strip()
                )
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _invalidar()
            _fechar()
            for chave in ("pt_corr_campo", "pt_corr_hora", "pt_corr_motivo"):
                st.session_state.pop(chave, None)
            st.session_state.aviso_toast = "Pedido de correção enviado. Seu gestor ou o RH decide."
            st.rerun()


@st.dialog("Registrar ausência", width="small", on_dismiss=_fechar)
def _modal_ausencia() -> None:
    tipo = st.radio("Tipo", list(TIPOS_AUSENCIA), format_func=TIPOS_AUSENCIA.get, key="pt_aus_tipo")
    c1, c2 = st.columns(2)
    inicio = c1.date_input("De", value=date.today(), format="DD/MM/YYYY", key="pt_aus_inicio")
    fim = c2.date_input("Até", value=date.today(), format="DD/MM/YYYY", key="pt_aus_fim")
    motivo = st.selectbox("Motivo", list(MOTIVOS_AUSENCIA), format_func=MOTIVOS_AUSENCIA.get, index=None, placeholder="Escolha o motivo", key="pt_aus_motivo")
    observacao = st.text_area("Observação (opcional)", max_chars=1000, key="pt_aus_obs", height=70, help="Não escreva diagnóstico nem código CID: isso fica só no atestado, com o RH.")
    st.html(
        '<p class="crh-nota-verde">O dia fica justificado no espelho de ponto e não desconta do banco de horas. O atestado é '
        "visto só pelo RH; o gestor vê apenas a ausência. Entregue o atestado ao RH: o sistema ainda não recebe arquivos.</p>"
    )
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="pt_aus_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Enviar", type="primary", key="pt_aus_enviar"):
            erro_campo = validar_ausencia(tipo, inicio, fim, motivo, observacao)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                registrar_ausencia(st.session_state.token, tipo, inicio.isoformat(), fim.isoformat(), motivo, observacao.strip() or None)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _invalidar()
            _fechar()
            for chave in ("pt_aus_tipo", "pt_aus_inicio", "pt_aus_fim", "pt_aus_motivo", "pt_aus_obs"):
                st.session_state.pop(chave, None)
            st.session_state.aviso_toast = "Ausência enviada para análise."
            st.rerun()


# ---------------------------------------------------------------------------
def _hoje(registro: dict | None) -> None:
    with st.container(key="ponto_card_hoje"):
        st.html(f'<p class="crh-cfg-titulo">{html.escape(titulo_hoje())}</p>')
        colunas = st.columns(4, gap="small")
        for coluna, cartao in zip(colunas, cartoes_hoje(registro)):
            with coluna:
                with st.container(key=f"ponto_box_{cartao['estado']}_{cartao['campo']}"):
                    st.html(
                        f'<p class="crh-ponto-rotulo">{html.escape(cartao["rotulo"])}</p>'
                        f'<p class="crh-ponto-hora">{html.escape(cartao["hora"] or "—")}</p>'
                    )
                    if cartao["estado"] == "proximo":
                        if st.button("Marcar agora", type="primary", key="pt_marcar"):
                            _marcar(cartao["rotulo"])
                    elif cartao["estado"] == "feito" and registro:
                        if st.button("Editar", type="tertiary", key=f"pt_editar_{cartao['campo']}"):
                            st.session_state.modal_ponto = ("correcao", registro.get("id"), cartao["campo"])
                            st.rerun()


def _marcar(rotulo: str) -> None:
    try:
        resposta = marcar_ponto(st.session_state.token)
    except ApiError as erro:
        st.session_state.ponto_erro_marcar = erro.message
        st.rerun()
    registro = resposta.get("registro") or {}
    campo = {r: c for c, r in MARCACOES}.get(rotulo)
    horario = hora(registro.get(campo)) if campo else None
    st.session_state.aviso_toast = f"{rotulo} registrada" + (f" às {horario}." if horario else ".")
    _invalidar()
    st.rerun()


def _espelho(linhas: list[dict]) -> None:
    pesos = [1.7, 1, 1.2, 1, 1, 1.1, 1.3, 1.7]
    with st.container(key="ponto_tabela"):
        with st.container(key="ponto_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Dia", "Entrada", "Saída almoço", "Volta", "Saída", "Trabalhado", "Status", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            with st.container(key="ponto_lin_vazio"):
                st.html('<p class="crh-meta">Nenhuma marcação nesta semana.</p>')
        for i, l in enumerate(linhas):
            with st.container(key=f"ponto_lina_{i}" if l["ausencia"] else f"ponto_lin_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<p class="crh-doc-prazo">{html.escape(l["dia"])}</p>')
                for coluna, marca in zip(c[1:5], l["marcas"]):
                    coluna.html(f'<p class="crh-ponto-marca">{html.escape(marca)}</p>')
                c[5].html(f'<p class="crh-ponto-trab">{html.escape(l["trabalhado"])}</p>')
                c[6].html(f'<p class="crh-ponto-status {l["tom"]}">{html.escape(l["status"])}</p>')
                with c[7]:
                    if l["acao"] == "corrigir":
                        if st.button("Solicitar correção", type="tertiary", key=f"pt_corrigir_{l['registro_id']}"):
                            st.session_state.modal_ponto = ("correcao", l["registro_id"], None)
                            st.rerun()
                    elif l["acao"] == "em_analise":
                        st.html('<p class="crh-meta">Correção em análise</p>')


def pagina_ponto() -> None:
    token = st.session_state.token
    render_topbar(st.session_state.usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Ponto", "Registre sua jornada e acompanhe o banco de horas")

    with st.spinner("Carregando o ponto..."):
        try:
            dados, erro = _carregar(token), None
        except ApiError as falha:
            dados, erro = None, falha
    if erro is not None:
        if erro.status_code == 404:
            st.html(
                '<div class="crh-painel crh-bloco"><p class="crh-bloco-titulo">Sem cadastro de colaborador</p>'
                '<p class="crh-meta">Sua conta não tem cadastro de colaborador, então não marca ponto.</p></div>'
            )
        else:
            alerta(st.empty(), "erro", erro.message)
        return

    registro = registro_de_hoje(dados["registros"])
    if erro_marcar := st.session_state.pop("ponto_erro_marcar", None):
        alerta(st.empty(), "erro", erro_marcar)
    _hoje(registro)

    with st.container(key="ponto_card_saldo"):
        if dados["banco"] is None:
            st.html('<p class="crh-cfg-texto">Saldo do banco de horas</p><p class="crh-meta">Não foi possível carregar o saldo agora.</p>')
        else:
            texto, tom = saldo(dados["banco"].get("saldo_horas"))
            st.html(f'<p class="crh-cfg-texto">Saldo do banco de horas</p><p class="crh-ponto-saldo {tom}">{html.escape(texto)}</p>')

    st.html(
        '<p class="crh-ponto-aviso">Controle interno experimental — este registro de ponto ainda não é um REP-P, REP-A ou '
        "REP-C conforme a Portaria nº 671/2021.</p>"
    )

    with st.container(horizontal=True, vertical_alignment="center", key="ponto_topo_espelho"):
        st.html('<p class="crh-bloco-titulo">Espelho de ponto — semana</p>', width="content")
        st.space("stretch")
        if st.button("Registrar ausência ou atestado", key="pt_btn_ausencia"):
            st.session_state.modal_ponto = ("ausencia",)

    hoje_local = datetime.now(timezone.utc).date()
    linhas = espelho_da_semana(dados["registros"], dados["ausencias"], dados["correcoes"], hoje_local)
    _espelho(linhas)

    modal = st.session_state.get("modal_ponto")
    if not modal:
        return
    if modal[0] == "ausencia":
        _modal_ausencia()
        return
    _, registro_id, campo = modal
    registro_alvo = next((r for r in dados["registros"] if r.get("id") == registro_id), None)
    linha = next((l for l in linhas if l["registro_id"] == registro_id), None)
    if registro_alvo is None or linha is None:
        _fechar()
        return
    _modal_correcao(registro_alvo, linha, campo)
