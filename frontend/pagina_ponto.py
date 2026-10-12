"""
Página "Ponto" no REP-P (Portaria MTP nº 671/2021; change ponto-rep-p-e-ferias-clt, tarefas 4.2 a 4.4; Figma 463:825
"Hoje", 464:826 "Mês", 465:856 e 465:894 pedido de correção, 465:932 estados; modal 221:285 de ausência).

- Hoje: relógio do servidor (horas, minutos e segundos), "Marcar ponto" sem ordem nem limite (art. 74), as marcações
  do dia com NSR e o comprovante em PDF de cada uma (art. 79), e os comprovantes das últimas 48 horas (art. 80).
- Mês: o cabeçalho do art. 84, o resumo e a planilha do mês (`st.dataframe`), um dia por linha; a correção é pedida
  pela seleção da linha (inclusão ou desconsideração, com motivo). Não há visão semanal.

Tudo é do próprio colaborador: nenhum endpoint daqui recebe id de pessoa. Quem decide é o superior ou o RH; a
marcação original nunca muda (o pedido aprovado vira tratamento). Diferença em relação ao Figma: o horário contratual
do cabeçalho mostra a jornada da regra do contrato (horas por dia e por semana, intervalo), porque o cadastro não
guarda os horários de entrada e saída.
"""

import html
import time
from datetime import date, datetime, timezone

import streamlit as st

from api_client import (
    ApiError,
    calendario,
    comprovantes_ponto,
    marcar_ponto,
    meu_banco_horas,
    meu_perfil_colaborador,
    meu_ponto,
    minhas_ausencias,
    minhas_correcoes_ponto,
    minhas_ferias,
    pedir_correcao_ponto,
    prazo_correcao,
    registrar_ausencia,
)
from comprovante_ponto import comprovante_pdf, formatar_nsr, nome_arquivo
from pagamento_modelo import MESES
from planilha_ponto import desmarcar_planilha, formulario_pedido, limpar_formulario, render_cabecalho, render_planilha, resumo_do_dia
from ponto_mensal_modelo import aviso_prazo, cabecalho_espelho, csv_do_mes, espelho_do_mes, legenda, meses_disponiveis, resumo_do_mes, texto_prazo
from ponto_modelo import (
    BRASILIA,
    MOTIVOS_AUSENCIA,
    TIPOS_AUSENCIA,
    comprovantes_recentes,
    hoje_brasilia,
    linhas_hoje,
    para_brasilia,
    saldo,
    situacao_hoje,
    texto_proxima,
    titulo_hoje,
    validar_ausencia,
    validar_pedido,
    valor_solicitado_ms,
)
from theme import alerta, render_hero, render_indicadores, render_topbar

_CACHE = "ponto_cache"
_VALIDADE_CACHE_S = 20
_BLOQUEADO = "ponto ainda nao esta liberado"
AVISO_REP = ("Ponto no modelo REP-P da Portaria MTP nº 671/2021. Nenhuma marcação pode ser alterada ou apagada; uma correção "
             "aprovada aparece como tratamento, com o motivo. Sem registro no INPI e sem assinatura ICP-Brasil, este ponto ainda "
             "não vale como REP-P para a fiscalização.")


def _carregar(token: str) -> dict:
    """{'ponto', 'banco', 'correcoes', 'ausencias', 'rep'} por 20 s. Erro de `meu_ponto` sobe (404 = sem colaborador);
    sem as outras consultas, a tela segue sem o saldo, sem as ausências ou sem os comprovantes."""
    cache = st.session_state.get(_CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = {"ponto": meu_ponto(token)}
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
    try:
        dados["rep"], dados["rep_erro"] = comprovantes_ponto(token), None
    except ApiError as erro:
        dados["rep"], dados["rep_erro"] = {}, erro
    st.session_state[_CACHE] = {"em": time.time(), "dados": dados}
    return dados


def _carregar_mes(token: str) -> dict:
    """{'ferias', 'feriados', 'admissao', 'prazo_dias'} para o mês, por 20 s. Cada uma que falhar fica vazia: o mês
    aparece do mesmo jeito, só sem marcar férias, feriados ou o início na admissão."""
    cache = st.session_state.get("ponto_mes_cache")
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = {"ferias": [], "feriados": [], "admissao": None, "prazo_dias": None}
    for chave, funcao, extrair in (
        ("prazo_dias", prazo_correcao, lambda r: r.get("prazo_dias")),
        ("ferias", minhas_ferias, lambda r: r.get("ferias") or []),
        ("feriados", calendario, lambda r: r.get("feriados") or []),
        ("admissao", meu_perfil_colaborador, lambda r: (r.get("colaborador") or {}).get("data_admissao")),
    ):
        try:
            dados[chave] = extrair(funcao(token))
        except ApiError:
            pass
    st.session_state["ponto_mes_cache"] = {"em": time.time(), "dados": dados}
    return dados


def _invalidar() -> None:
    st.session_state.pop(_CACHE, None)


def _fechar() -> None:
    st.session_state.pop("modal_ponto", None)


# ---------------------------------------------------------------------------
# Modais
# ---------------------------------------------------------------------------
@st.dialog("Pedir correção do dia", width="small", on_dismiss=_fechar)
def _modal_pedido(linha: dict) -> None:
    """`ponto/correcao`: inclusão de uma marcação que faltou ou desconsideração de uma feita por engano (Figma 465:856
    e 465:894). As marcações já em análise ficam fora da desconsideração."""
    resumo_do_dia(linha)
    if linha["nota"] and not linha["nota"].startswith(("Esqueceu", "Mês encerrado")):
        st.html(f'<p class="crh-meta" style="margin:0">{html.escape(linha["nota"])}</p>')
    tipo, horario, marcacao_id, motivo = formulario_pedido(linha, "pt_ped")
    if tipo == "inclusao":
        nota = ("A marcação original nunca é alterada. Aprovada, a correção vira um tratamento com o seu motivo e aparece na "
                "planilha como (I). Quem decide é o seu superior ou o RH.")
    else:
        nota = "A marcação continua gravada e no comprovante. Aprovada, ela aparece como (D) e deixa de contar nas horas."
    st.html(f'<div class="crh-incluso"><p class="n" style="margin:0">{html.escape(nota)}</p></div>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="pt_ped_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Enviar pedido", type="primary", key="pt_ped_enviar"):
            erro_campo = validar_pedido(tipo, horario, marcacao_id, motivo)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                pedir_correcao_ponto(st.session_state.token, linha["data"].isoformat(), tipo, motivo.strip(), marcacao_id=marcacao_id,
                                     data_hora_ms=valor_solicitado_ms(linha["data"], horario) if tipo == "inclusao" else None)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _invalidar()
            _fechar()
            limpar_formulario("pt_ped")
            st.session_state.aviso_toast = "Pedido de correção enviado. Seu superior ou o RH decide."
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
# Hoje
# ---------------------------------------------------------------------------
@st.fragment(run_every=1)
def _relogio() -> None:
    """Relógio digital com horas, minutos e segundos (Anexo IX). A hora é a do servidor do app, em Brasília; a da
    marcação é a do servidor do backend."""
    st.html(f'<p class="crh-relogio">{datetime.now(BRASILIA):%H:%M:%S}</p>')


def _marcar() -> None:
    try:
        resposta = marcar_ponto(st.session_state.token)
    except ApiError as erro:
        st.session_state.ponto_erro_marcar = erro.message
        return
    st.session_state.ponto_ultimo = {"marcacao": resposta.get("marcacao") or {}, "comprovante": resposta.get("comprovante") or {}}
    _invalidar()


def _pdf(marcacao: dict, rep: dict) -> bytes:
    return comprovante_pdf(marcacao, rep.get("empregador") or {}, rep.get("trabalhador") or {})


def _hoje(dados: dict) -> None:
    rep = dados["rep"] or {}
    hoje = hoje_brasilia()
    linhas = linhas_hoje((dados["ponto"].get("marcacoes") or []), hoje)
    with st.container(key="ponto_card_hoje"):
        if erro := st.session_state.pop("ponto_erro_marcar", None):
            if _BLOQUEADO in erro.lower():
                alerta(st.empty(), "atencao", 'O ponto ainda não está liberado: o RH precisa cadastrar os dados do empregador em "Ponto eletrônico (REP-P)".')
            else:
                alerta(st.empty(), "erro", erro)
                st.html('<p class="crh-meta">Nada foi gravado.</p>')
        if ultimo := st.session_state.pop("ponto_ultimo", None):
            mc = ultimo["marcacao"]
            momento = para_brasilia(mc.get("data_hora_marcacao"))
            alerta(st.empty(), "sucesso", f"Ponto marcado às {momento:%H:%M:%S} (UTC-03:00). NSR {formatar_nsr(mc.get('nsr'))}." if momento
                   else f"Ponto marcado. NSR {formatar_nsr(mc.get('nsr'))}.")
            st.download_button("Baixar comprovante (PDF)", comprovante_pdf(mc, ultimo["comprovante"].get("empregador") or {}, ultimo["comprovante"].get("trabalhador") or {}),
                               file_name=nome_arquivo(mc), mime="application/pdf", key="pt_baixar_ultimo")
        esquerda, direita = st.columns([1, 1.45], gap="large")
        with esquerda:
            st.html(f'<p class="crh-cfg-titulo">{html.escape(titulo_hoje())}</p>')
            _relogio()
            st.html('<p class="crh-relogio-nota">Horário de Brasília (UTC-03:00), pelo servidor</p>')
            st.button("Marcar ponto", type="primary", key="pt_marcar", on_click=_marcar)
            if selo := situacao_hoje(len(linhas)):
                st.html(f'<span class="crh-selo {selo[1]}">{html.escape(selo[0])}</span>')
        with direita:
            if not linhas:
                st.html('<div class="crh-incluso"><p class="t">Você ainda não marcou o ponto hoje.</p>'
                        '<p class="n" style="margin:0">Quando marcar, a marcação aparece aqui com o NSR e o comprovante em PDF.</p></div>')
                return
            pesos = [1.3, 0.9, 1.3, 1.6]
            with st.container(key="ponto_tabela"):
                with st.container(key="ponto_cab"):
                    for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Marcação", "Hora", "NSR", ""]):
                        coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
                for i, l in enumerate(linhas):
                    with st.container(key=f"ponto_lin_{i}"):
                        c = st.columns(pesos, vertical_alignment="center")
                        c[0].html(f'<p class="crh-doc-prazo">{html.escape(l["rotulo"])}</p>')
                        c[1].html(f'<p class="crh-ponto-marca">{html.escape(l["hora"])}</p>')
                        c[2].html(f'<p class="crh-ponto-marca">{html.escape(l["nsr"])}</p>')
                        if rep.get("empregador"):
                            c[3].download_button("Comprovante (PDF)", _pdf(l["marcacao"], rep), file_name=nome_arquivo(l["marcacao"]),
                                                 mime="application/pdf", type="tertiary", key=f"pt_cp_hoje_{l['marcacao'].get('id')}")
                with st.container(key="ponto_lin_proxima"):
                    st.html(f'<p class="crh-meta">{html.escape(texto_proxima(len(linhas)))}</p>')


def _comprovantes(dados: dict) -> None:
    with st.container(key="ponto_card_comprovantes"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html('<p class="crh-cfg-titulo">Comprovantes das últimas 48 horas</p>', width="stretch")
            st.html('<p class="crh-legenda-ponto">Disponíveis por pelo menos 48 horas (art. 80)</p>', width="content")
        erro = dados.get("rep_erro")
        if erro is not None:
            if erro.status_code == 403:
                alerta(st.empty(), "erro", "Você não tem permissão para ver este comprovante. Cada pessoa vê só os próprios.")
            else:
                alerta(st.empty(), "erro", erro.message)
            return
        rep = dados["rep"] or {}
        itens = comprovantes_recentes(rep.get("marcacoes") or [], datetime.now(timezone.utc))
        if not itens:
            st.html('<p class="crh-meta">Nenhuma marcação nas últimas 48 horas.</p>')
            return
        with st.container(key="ponto_comprovantes", gap=None):
            for item in itens:
                with st.container(horizontal=True, vertical_alignment="center", key=f"ponto_cp_{item['marcacao'].get('id')}"):
                    st.html(f'<p class="crh-doc-prazo">{html.escape(item["quando"])}</p>', width=170)
                    st.html(f'<p class="crh-ponto-marca">{html.escape(item["rotulo"])}</p>', width=120)
                    st.html(f'<p class="crh-ponto-marca">NSR {html.escape(item["nsr"])}</p>', width="stretch")
                    st.download_button("Baixar PDF", _pdf(item["marcacao"], rep), file_name=nome_arquivo(item["marcacao"]), mime="application/pdf",
                                       type="tertiary", key=f"pt_cp_{item['marcacao'].get('id')}")


def _saldo_e_ausencia(dados: dict) -> None:
    esquerda, direita = st.columns(2)
    with esquerda, st.container(key="ponto_card_saldo"):
        if dados["banco"] is None:
            st.html('<p class="crh-cfg-texto">Saldo do banco de horas</p><p class="crh-meta">Não foi possível carregar o saldo agora.</p>')
        else:
            texto, tom = saldo(dados["banco"].get("saldo_horas"))
            st.html(f'<p class="crh-cfg-texto">Saldo do banco de horas</p><p class="crh-ponto-saldo {tom}">{html.escape(texto)}</p>')
    with direita, st.container(key="ponto_card_ausencia"):
        st.html('<p class="crh-cfg-texto">Falta, atestado ou licença?</p>')
        if st.button("Registrar ausência ou atestado", key="pt_btn_ausencia"):
            st.session_state.modal_ponto = ("ausencia",)
            st.rerun()


# ---------------------------------------------------------------------------
# Mês
# ---------------------------------------------------------------------------
def _mes(token: str, dados: dict, meses: list[tuple[int, int]], ano: int, mes: int, extra: dict) -> list[dict]:
    ponto = dados["ponto"]
    hoje = hoje_brasilia()
    linhas = espelho_do_mes(ponto.get("registros") or [], dados["ausencias"], dados["correcoes"], extra["ferias"], extra["feriados"],
                            ano, mes, hoje, extra["admissao"], prazo_dias=extra.get("prazo_dias"),
                            marcacoes=ponto.get("marcacoes") if "marcacoes" in ponto else None, tratamentos=ponto.get("tratamentos") or [])
    render_cabecalho(cabecalho_espelho(dados["rep"] or {}, ano, mes, datetime.now(BRASILIA)))
    numeros = resumo_do_mes(linhas)
    render_indicadores([
        ("Horas no mês", numeros["horas"], ""),
        ("Dias com marcação", str(numeros["dias_trabalhados"]), ""),
        ("Sem registro", str(numeros["sem_registro"]), ""),
        ("Faltas injustificadas", str(numeros["faltas_injustificadas"]), "negativo"),
        ("Atestados", str(numeros["atestados"]), ""),
    ])
    prazo_txt = f' · Prazo para pedir correção: {texto_prazo(extra.get("prazo_dias"))}' if extra.get("prazo_dias") else ""
    if numeros["em_analise"] or prazo_txt:
        st.html(f'<p class="crh-meta">Correções em análise: {numeros["em_analise"]}{prazo_txt}</p>')
    if aviso := aviso_prazo(linhas, hoje, extra.get("prazo_dias")):
        alerta(st.empty(), "atencao", aviso)
    escolhida = render_planilha(linhas, "pt_planilha", ajustavel=lambda l: l["acao"] == "corrigir")
    st.html(f'<p class="crh-legenda-ponto">{html.escape(legenda(extra["admissao"]))}</p>')
    if escolhida:
        desmarcar_planilha("pt_planilha")
        if escolhida["acao"] == "corrigir":
            st.session_state.modal_ponto = ("pedido", escolhida["data"].isoformat())
        st.rerun()
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">Marque "Ajuste" no fim da linha para pedir a correção do dia. O pedido '
            'segue para o seu superior ou para o RH; a marcação original nunca é alterada.</p></div>')
    return linhas


def pagina_ponto() -> None:
    token = st.session_state.token
    render_topbar(st.session_state.usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Ponto", "Marque o ponto, baixe o comprovante de cada marcação e acompanhe o mês")

    with st.spinner("Carregando o ponto..."):
        try:
            dados, erro = _carregar(token), None
        except ApiError as falha:
            dados, erro = None, falha
    if erro is not None:
        if erro.status_code == 404:
            st.html(
                '<div class="crh-painel crh-bloco"><p class="crh-bloco-titulo">Sem cadastro de colaborador</p>'
                '<p class="crh-meta">Sua conta ainda não está ligada a um cadastro de funcionário, então não marca ponto. '
                'Peça ao Admin para vincular a sua ficha em Usuários e perfis → "Vincular ficha".</p></div>'
            )
        else:
            alerta(st.empty(), "erro", erro.message)
        return

    linhas_mes: list[dict] = []
    with st.container(horizontal=True, vertical_alignment="center", key="ponto_topo_espelho"):
        with st.container(key="cfg_abas", width="content"):
            visao = st.segmented_control("Visão", ["Hoje", "Mês"], default="Hoje", required=True, key="pt_visao", label_visibility="collapsed")
        st.space("stretch")
        if visao == "Mês":
            extra = _carregar_mes(token)
            meses = meses_disponiveis(extra["admissao"], dados["ponto"].get("registros") or [], hoje_brasilia())
            if st.session_state.get("pt_mes_ano") not in meses:
                st.session_state.pt_mes_ano = meses[0]
            ano, mes = st.selectbox("Mês", meses, format_func=lambda am: f"{MESES[am[1] - 1]} de {am[0]}", key="pt_mes_ano",
                                    label_visibility="collapsed", width=200)
            botao_csv = st.empty()

    if visao == "Hoje":
        _hoje(dados)
        _comprovantes(dados)
        _saldo_e_ausencia(dados)
        st.html(f'<div class="crh-incluso"><p class="n" style="margin:0">{html.escape(AVISO_REP)}</p></div>')
    else:
        linhas_mes = _mes(token, dados, meses, ano, mes, extra)
        cab = cabecalho_espelho(dados["rep"] or {}, ano, mes, datetime.now(BRASILIA))
        botao_csv.download_button("Baixar CSV", csv_do_mes(linhas_mes, cab), file_name=f"espelho-ponto-{ano}-{mes:02d}.csv", mime="text/csv", key="pt_baixar_mes")

    modal = st.session_state.get("modal_ponto")
    if not modal:
        return
    if modal[0] == "ausencia":
        _modal_ausencia()
    elif modal[0] == "pedido":
        linha = next((l for l in linhas_mes if l["data"].isoformat() == modal[1] and l["acao"] == "corrigir"), None)
        if linha is None:
            _fechar()
            return
        _modal_pedido(linha)
