"""
Página "Rotina diária" dos grupos RH e Admin (Figma 289:900 e 289:1477, resultado 289:1190 e o modal 290:1164; tarefa 64
da change concluir-frontend-streamlit). Só RH e Admin, como o backend.

Antes de rodar, mostra o que a rotina mudaria agora (`status_operacional` GET, campo `rotina_diaria_pendente`, que conta
sem gravar) e a última execução (auditoria, ação `processar_rotinas_diarias`). "Executar rotina agora" confirma no modal e
chama `rotinas/processar_diarias` POST; o resultado mostra o que foi aplicado e o que ainda falta. Rodar de novo no mesmo
dia devolve tudo zerado.

Diferenças do Figma:
- a linha "Avisos do dia" (convites de pesquisa e do termômetro e avisos de prazo), que a rotina também faz e o Figma não
  lista;
- "Ver o que será feito" recalcula a lista na hora, porque ela já está na tela;
- a nota do rodapé diz "horário de Brasília" (tarefa 73), não UTC.
"""

import html
import time
from datetime import datetime

import streamlit as st

import rotina_modelo as rm
from api_client import ApiError, auditoria, processar_rotina_diaria, status_operacional
from delegacoes_modelo import BRASILIA
from theme import alerta, render_hero, render_indicadores, render_topbar

_VALIDADE_CACHE_S = 30


def _carregar(token: str) -> tuple[dict, dict | None]:
    item = st.session_state.get("rd_cache")
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    pendente = status_operacional(token).get("rotina_diaria_pendente") or {}
    try:
        trilha = auditoria(token, dias=90, recurso="rotina", acao="processar_rotinas_diarias")
        ultima = rm.ultima_execucao(trilha.get("eventos"), trilha.get("usuarios"))
    except ApiError:
        ultima = None  # a última execução é informativa: sem ela a tela continua
    st.session_state.rd_cache = {"em": time.time(), "dados": (pendente, ultima)}
    return pendente, ultima


def _lista(titulo: str, itens: list[dict], aplicado: bool) -> None:
    st.html(f'<p class="crh-rd-titulo">{html.escape(titulo)}</p>')
    linhas = []
    for i in itens:
        tom = "zero" if not i["quantidade"] else ("ok" if aplicado else "")
        selo = "ok" if aplicado else ("amb" if i["quantidade"] else "neu")
        linhas.append(f'<div class="crh-rd-item {tom}"><span class="ponto"></span><div class="txt"><p class="t">{html.escape(i["titulo"])}</p>'
                      f'<p class="d">{html.escape(i["detalhe"])}</p></div><span class="crh-selo {selo}">{i["quantidade"]}</span></div>')
    st.html('<div class="crh-rd-lista">' + "".join(linhas) + "</div>")


def _fechar() -> None:
    st.session_state.pop("rd_modal", None)


@st.dialog("Executar a rotina diária?", width="small", on_dismiss=_fechar)
def _modal_executar(pendente: dict, ultima: dict | None) -> None:
    trans, limpar = rm.totais(pendente)
    st.html('<div class="crh-lgpd-resumo">'
            f"<div><span>Transições a aplicar</span><b>{trans}</b></div>"
            f"<div><span>Registros a limpar</span><b>{limpar}</b></div>"
            f"<div><span>Última execução</span><b>{html.escape(ultima['quando'] if ultima else 'Nenhuma nos últimos 90 dias')}</b></div></div>"
            '<p class="crh-alerta-inline">A rotina aplica as transições e limpa os dados com prazo vencido. Rodar de novo no mesmo dia não repete nada.</p>'
            '<p class="crh-meta">A execução fica na auditoria com as contagens.</p>')
    slot = st.empty()
    with st.container(horizontal=True):
        if st.button("Cancelar", key="rd_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Executar agora", type="primary", key="rd_ok"):
            try:
                with st.spinner("Executando..."):
                    resposta = processar_rotina_diaria(st.session_state.token)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            st.session_state.rd_resultado = {"aplicadas": resposta.get("aplicadas") or {}, "em": datetime.now(BRASILIA)}
            for chave in ("rd_modal", "rd_cache", "int_cache_status"):
                st.session_state.pop(chave, None)
            st.rerun()


def pagina_rotina_diaria() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    render_hero("Rotina diária", "Aplica as transições que dependem de data. Rodar de novo no mesmo dia não repete nada.")
    if str(usuario.get("perfil", "")).upper() not in ("RH", "ADMIN"):
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return
    try:
        with st.spinner("Calculando o que a rotina mudaria..."):
            pendente, ultima = _carregar(token)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return

    resultado = st.session_state.get("rd_resultado")
    if resultado:
        aplicadas = resultado["aplicadas"]
        alerta(st.empty(), "sucesso", rm.resumo_execucao(aplicadas, resultado["em"], usuario["nome"]))
        trans, limpos = rm.totais(aplicadas)
        pend_trans, pend_limpar = rm.totais(pendente)
        render_indicadores([("Transições aplicadas", str(trans), "verde"), ("Registros limpos", str(limpos), ""),
                            ("Pendente agora", str(pend_trans + pend_limpar), "ambar" if pend_trans + pend_limpar else "")])
        listas = rm.linhas(aplicadas, aplicado=True)
        _lista("Transições de status — o que foi aplicado", listas["transicoes"], True)
        _lista("Retenção de dados — o que foi aplicado", listas["retencao"], True)
        with st.container(key="cfg_card_rd_rodape", horizontal=True, vertical_alignment="center"):
            st.html('<p class="crh-meta" style="margin:0">Se executar de novo agora, as contagens voltam zeradas: a rotina não repete transições. '
                    "O registro desta execução está na Auditoria.</p>")
            if st.button("Abrir na Auditoria", key="rd_auditoria"):
                st.session_state.ir_auditoria = True
                st.rerun()
            if st.button("Voltar ao pendente", key="rd_voltar", type="tertiary"):
                st.session_state.pop("rd_resultado", None)
                st.rerun()
        return

    trans, limpar = rm.totais(pendente)
    render_indicadores([("Alterações pendentes agora", str(trans), "ambar" if trans else ""), ("Dados a limpar", str(limpar), ""),
                        ("Última execução", ultima["quando"] if ultima else "—", "")])
    with st.container(key="cfg_card_rd_exec", horizontal=True, vertical_alignment="center"):
        st.html('<div><p class="crh-cfg-titulo" style="margin:0">Executar a rotina diária</p>'
                '<p class="crh-meta" style="margin:2px 0 0">Só RH e Admin acionam. A execução fica na auditoria, com as contagens.</p></div>')
        if st.button("Ver o que será feito", key="rd_ver"):
            st.session_state.pop("rd_cache", None)
            st.rerun()
        if st.button("Executar rotina agora", type="primary", key="rd_executar"):
            st.session_state.rd_modal = True
    listas = rm.linhas(pendente)
    _lista("Transições de status", listas["transicoes"], False)
    _lista("Retenção de dados", listas["retencao"], False)
    st.html('<p class="crh-meta">As datas são comparadas no horário de Brasília. Colaborador desligado nunca volta a Ativo. '
            "Os prazos de retenção estão a confirmar com o jurídico.</p>")
    if st.session_state.get("rd_modal"):
        _modal_executar(pendente, ultima)
