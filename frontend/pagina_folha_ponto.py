"""
Página "Folha de ponto" do gestor e do RH (tarefa 81 da change concluir-frontend-streamlit). A conferir com o Figma,
que estava fora do ar quando a tela foi feita (ver design.md).

- "Resumo do mês": uma linha por pessoa que quem está logado pode ver, com horas, dias com marcação, sem registro,
  faltas injustificadas e atestados — o fechamento do mês para o pagamento. CSV do resumo.
- "Por pessoa": a folha mensal da pessoa na mesma planilha do colaborador (change ponto-rep-p-e-ferias-clt, tarefa
  4.5): marcações da ARP e tratamentos juntos, a incluída como "(I)" e a desconsiderada como "(D)"; os pedidos de
  correção pendentes (aprovar ou recusar) e o ajuste direto pela seleção do dia, como inclusão ou desconsideração de
  uma marcação, com motivo (auditado; a pessoa é avisada). A marcação original nunca muda.
Ninguém ajusta nem decide o próprio ponto: o pedido de quem tem superior vai para o superior. O escopo é do backend
(`folha_ponto/pessoas`, `folha_ponto/mes`, `folha_ponto/tratar`, `correcoes_ponto/{id}/aprovar|rejeitar`).
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import (
    ApiError,
    aprovar_correcao_ponto,
    calendario,
    definir_prazo_correcao,
    folha_mes,
    folha_pessoas,
    organograma,
    prazo_correcao,
    rejeitar_correcao_ponto,
    tratar_ponto,
)
from decisoes_modelo import validar_motivo
from folha_modelo import csv_resumo, espelho_da_pessoa, linhas_resumo, meses_da_equipe, meses_da_pessoa, pendentes_da_pessoa
from pagamento_modelo import MESES
from planilha_ponto import desmarcar_planilha, formulario_pedido, limpar_formulario, render_planilha, resumo_do_dia
from ponto_mensal_modelo import anos_disponiveis, csv_do_mes, descricao_pedido, legenda, meses_do_ano, resumo_do_mes, tem_saldo, texto_prazo
from ponto_modelo import hoje_brasilia, validar_pedido, valor_solicitado_ms
from theme import alerta, render_hero, render_indicadores, render_topbar

_VALIDADE_CACHE_S = 20
_ABAS = ["Resumo do mês", "Por pessoa"]


def _cache(chave: str, carregar):
    guardado = st.session_state.get("folha_cache") or {}
    item = guardado.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = carregar()
    guardado[chave] = {"em": time.time(), "dados": dados}
    st.session_state.folha_cache = guardado
    return dados


def _invalidar() -> None:
    st.session_state.pop("folha_cache", None)


def _fechar() -> None:
    st.session_state.pop("modal_folha", None)


def _base(token: str) -> dict:
    def carregar():
        dados = {"pessoas": folha_pessoas(token)}
        for chave, funcao in (("org", organograma), ("cal", calendario)):
            try:
                dados[chave] = funcao(token)
            except ApiError:
                dados[chave] = {}
        return dados
    return _cache("base", carregar)


def _mes(token: str, ano: int, mes: int, colaborador_id=None) -> dict:
    return _cache(f"mes-{ano}-{mes}-{colaborador_id}", lambda: folha_mes(token, ano, mes, colaborador_id))


def _seletor_ano_mes(meses: list[tuple[int, int]], prefixo: str) -> tuple[int, int]:
    ano = st.selectbox("Ano", anos_disponiveis(meses), format_func=lambda a: f"Ano: {a}", key=f"{prefixo}_ano", label_visibility="collapsed", width=140)
    opcoes = meses_do_ano(meses, ano)
    if st.session_state.get(f"{prefixo}_mes") not in opcoes:
        st.session_state[f"{prefixo}_mes"] = opcoes[0]
    mes = st.selectbox("Mês", opcoes, format_func=lambda m: MESES[m - 1], key=f"{prefixo}_mes", label_visibility="collapsed", width=170)
    return ano, mes


# ---------------------------------------------------------------------------
# Modais
# ---------------------------------------------------------------------------
@st.dialog("Ajustar o ponto do dia", width="small", on_dismiss=_fechar)
def _modal_ajustar(pessoa: dict, linha: dict) -> None:
    """`folha_ponto/tratar`: inclui ou desconsidera uma marcação, com motivo. Vale na hora, como tratamento."""
    st.html(f'<p class="crh-meta" style="margin:0">Pessoa: <b>{html.escape(pessoa.get("nome") or "")}</b></p>')
    resumo_do_dia(linha)
    if linha["nota"] and not linha["nota"].startswith(("Esqueceu", "Mês encerrado")):
        st.html(f'<p class="crh-meta" style="margin:0">{html.escape(linha["nota"])}</p>')
    tipo, horario, alvo, motivo = formulario_pedido(linha, "fp_aj")
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">O ajuste vale na hora como tratamento: a marcação original não muda, '
            'o motivo fica no histórico do dia e a pessoa é avisada. Marcações com pedido pendente ficam fora: decida o pedido.</p></div>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="fp_aj_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Ajustar", type="primary", key="fp_aj_ok"):
            erro_campo = validar_pedido(tipo, horario, alvo, motivo)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                tratar_ponto(st.session_state.token, pessoa["id"], linha["data"].isoformat(), tipo, motivo.strip(), marcacao_id=(alvo or {}).get("marcacao_id"), tratamento_id=(alvo or {}).get("tratamento_id"),
                             data_hora_ms=valor_solicitado_ms(linha["data"], horario) if tipo != "desconsideracao" else None)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            limpar_formulario("fp_aj")
            _invalidar()
            _fechar()
            st.session_state.aviso_toast = f"Ponto de {pessoa.get('nome')} ajustado. A pessoa foi avisada."
            st.rerun()


@st.dialog("Recusar correção de ponto", width="small", on_dismiss=_fechar)
def _modal_recusar(pessoa: dict, correcao: dict, marcacoes: dict) -> None:
    st.html(
        '<div class="crh-campos crh-campos-direita">'
        f'<p class="r">Pessoa</p><p class="v">{html.escape(pessoa.get("nome") or "")}</p>'
        f'<p class="r">Pedido</p><p class="v">{html.escape(descricao_pedido(correcao, marcacoes))}</p></div>'
    )
    motivo = st.text_area("Motivo (obrigatório, 5 caracteres ou mais)", max_chars=1000, key="fp_rec_motivo", height=80)
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="fp_rec_voltar"):
            _fechar()
            st.rerun()
        if st.button("Recusar correção", type="primary", key="central_cor_ok"):
            erro_campo = validar_motivo(motivo)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                rejeitar_correcao_ponto(st.session_state.token, correcao["id"], motivo.strip())
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            st.session_state.pop("fp_rec_motivo", None)
            _invalidar()
            _fechar()
            st.session_state.aviso_toast = "Correção recusada. A pessoa vê o motivo."
            st.rerun()


# ---------------------------------------------------------------------------
@st.dialog("Prazo para pedir correção de ponto", width="small", on_dismiss=_fechar)
def _modal_prazo(atual: int | None) -> None:
    st.html('<p class="crh-meta">Até quantos dias depois o colaborador pode pedir a correção de um dia. Depois disso, só o gestor ou o RH '
            'ajustam (ajuste direto, auditado). Sem limite: qualquer dia desde o primeiro ponto.</p>')
    sem_limite = st.toggle("Sem limite", value=not atual, key="fp_prazo_sem")
    dias = st.number_input("Dias", min_value=1, max_value=3650, value=int(atual or 30), step=1, key="fp_prazo_dias", disabled=sem_limite)
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="fp_prazo_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Salvar prazo", type="primary", key="fp_prazo_salvar"):
            novo = None if sem_limite else int(dias)
            try:
                definir_prazo_correcao(st.session_state.token, novo)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _fechar()
            _invalidar()
            st.session_state.aviso_toast = f"Prazo para pedir correção: {texto_prazo(novo)}."
            st.rerun()


def _cartao_prazo(token: str) -> None:
    """RH e Admin (tarefa 79): o prazo que o colaborador tem para pedir correção. Gestor e RH ajustam sem prazo."""
    try:
        atual = _cache("prazo", lambda: prazo_correcao(token)).get("prazo_dias")
    except ApiError:
        atual = None
    with st.container(horizontal=True, vertical_alignment="center", key="fp_prazo"):
        st.html(f'<p class="crh-meta" style="margin:0">Prazo para o colaborador pedir correção: <b>{html.escape(texto_prazo(atual))}</b>. '
                'Depois dele, só o gestor ou o RH ajustam.</p>', width="stretch")
        if st.button("Alterar prazo", type="tertiary", key="fp_prazo_alterar"):
            st.session_state.modal_folha = ("prazo", atual)
            st.rerun()
    modal = st.session_state.get("modal_folha")
    if modal and modal[0] == "prazo":
        _modal_prazo(modal[1])


def _ir_para_pessoa(pid: int) -> None:
    st.session_state.fp_aba = "Por pessoa"
    st.session_state.fp_pessoa = pid


def _resumo(token: str, pessoas: list[dict], deps: dict, cargos: dict, feriados: list[dict], ve_todos: bool, hoje: date) -> None:
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        ano, mes = _seletor_ano_mes(meses_da_equipe(pessoas, hoje), "fp_r")
        st.space("stretch")
        dep = None
        if ve_todos:
            dep = st.selectbox("Departamento", [None] + sorted(deps, key=deps.get), format_func=lambda d: "Departamento: Todos" if d is None else f"Departamento: {deps[d]}",
                               key="fp_dep", label_visibility="collapsed", width=230)
    with st.spinner("Carregando o mês..."):
        try:
            dados = _mes(token, ano, mes)
        except ApiError as erro:
            alerta(st.empty(), "erro", erro.message)
            return
    linhas = linhas_resumo(pessoas, dados, feriados, ano, mes, hoje, deps, cargos, dep)
    pesos = [2.6, 1.8, 1, 1.1, 1.3, 1.3, 1, 1.2]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Pessoa", "Departamento", "Horas", "Dias com marcação", "Sem registro", "Faltas injustificadas", "Atestados", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Ninguém neste filtro.</p>')
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_linf_{i}" if l["faltas"] or l["sem_registro"] else f"rh_lin_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["nome"])}{" (você)" if l["e_voce"] else ""}</p><p class="d">{html.escape(l["cargo"])}</p></div>')
                for coluna, valor in zip(c[1:7], (l["departamento"], l["horas"], str(l["dias"]), str(l["sem_registro"]), str(l["faltas"]), str(l["atestados"]))):
                    coluna.html(f'<p class="crh-doc-prazo">{html.escape(valor)}</p>')
                with c[7]:
                    st.button("Abrir folha →", type="tertiary", key=f"fp_abrir_{l['id']}", on_click=_ir_para_pessoa, args=(l["id"],))
    with st.container(horizontal=True, vertical_alignment="center"):
        st.html('<p class="crh-meta">Faltas injustificadas: ausência recusada pelo RH ou dia útil sem marcação nem ausência em mês encerrado. '
                'No mês corrente, o dia útil sem marcação aparece como "sem registro" enquanto a pessoa ainda pode resolver.</p>', width="stretch")
        st.download_button("Baixar resumo do mês (CSV)", csv_resumo(linhas, ano, mes), file_name=f"folha-ponto-{ano}-{mes:02d}.csv", mime="text/csv", key="fp_baixar_resumo")


def _por_pessoa(token: str, pessoas: list[dict], deps: dict, feriados: list[dict], hoje: date) -> None:
    por_id = {p["id"]: p for p in pessoas}
    ids = list(por_id)
    if st.session_state.get("fp_pessoa") not in ids:
        st.session_state.fp_pessoa = ids[0]
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        pid = st.selectbox("Pessoa", ids, format_func=lambda i: f"{por_id[i].get('nome')} — {deps.get(por_id[i].get('departamento_id')) or '—'}" + (" (você)" if por_id[i].get("e_voce") else ""),
                           key="fp_pessoa", label_visibility="collapsed", width=340)
        ano, mes = _seletor_ano_mes(meses_da_pessoa(por_id[pid], hoje), "fp_p")
        st.space("stretch")
    pessoa = por_id[pid]
    with st.spinner("Carregando a folha..."):
        try:
            dados = _mes(token, ano, mes, pid)
        except ApiError as erro:
            alerta(st.empty(), "erro", erro.message)
            return
    linhas = espelho_da_pessoa(pessoa, dados, feriados, ano, mes, hoje)
    numeros = resumo_do_mes(linhas)
    horas_saldo = [("Horas positivas", numeros["positivas"], "verde"), ("Horas negativas", numeros["negativas"], "negativo")] if numeros["positivas"] else []
    render_indicadores([
        ("Horas trabalhadas no mês", numeros["horas"], ""),
        *horas_saldo,
        ("Dias com marcação", str(numeros["dias_trabalhados"]), "verde"),
        ("Sem registro ou incompletos", str(numeros["sem_registro"]), "ambar"),
        ("Faltas injustificadas", str(numeros["faltas_injustificadas"]), "negativo"),
    ])
    proprio = bool(pessoa.get("e_voce"))
    if proprio:
        st.html('<p class="crh-nota-ambar">Esta é a sua folha: só consulta. Para corrigir o seu ponto, peça a correção na tela Ponto; quem decide é o seu superior.</p>')

    pendentes = pendentes_da_pessoa(dados)
    marcacoes = {mc.get("id"): mc for mc in dados.get("marcacoes") or []}
    linha_do_registro = {l["registro_id"]: f'{l["data"]:%d/%m}' for l in linhas if l["registro_id"]}
    if pendentes:
        st.html(f'<p class="crh-bloco-titulo">Pedidos de correção pendentes ({len(pendentes)})</p>')
        with st.container(key="rh_tabela_pend"):
            for c in pendentes:
                quando = linha_do_registro.get(c.get("registro_ponto_id")) or ""
                with st.container(horizontal=True, vertical_alignment="center", key=f"fp_pend_{c['id']}"):
                    st.html(f'<p class="crh-doc-prazo">{html.escape(quando)}: {html.escape(descricao_pedido(c, marcacoes))} · '
                            f'{html.escape((c.get("justificativa") or "").strip() or "sem motivo")}</p>', width="stretch")
                    if not proprio:
                        if st.button("Recusar", type="tertiary", key=f"rh_recusar_fp_{c['id']}"):
                            st.session_state.modal_folha = ("recusar", c["id"])
                            st.rerun()
                        if st.button("Aprovar", type="tertiary", key=f"fp_aprovar_{c['id']}"):
                            try:
                                aprovar_correcao_ponto(token, c["id"])
                            except ApiError as erro:
                                st.session_state.folha_erro = erro.message
                                st.rerun()
                            _invalidar()
                            st.session_state.aviso_toast = "Correção aprovada. Virou um tratamento no dia; a marcação original não muda."
                            st.rerun()

    if erro_acao := st.session_state.pop("folha_erro", None):
        alerta(st.empty(), "erro", erro_acao)

    chave = f"fp_planilha_{pid}_{ano}_{mes}"
    escolhida = render_planilha(linhas, chave, ajustavel=None if proprio else lambda l: l["data"] < hoje)
    st.html(f'<p class="crh-legenda-ponto">{html.escape(legenda(pessoa.get("data_admissao"), tem_saldo(linhas)))}</p>')
    if escolhida:
        desmarcar_planilha(chave)
        st.session_state.modal_folha = ("ajustar", escolhida["data"].isoformat())
        st.rerun()
    if not proprio:
        st.html('<div class="crh-incluso"><p class="n" style="margin:0">Marque "Ajuste" no fim da linha para incluir ou desconsiderar uma marcação '
                'do dia. A marcação original nunca é alterada: o ajuste fica ao lado dela, com o motivo.</p></div>')
    st.download_button("Baixar folha do mês (CSV)", csv_do_mes(linhas), file_name=f"folha-ponto-{pessoa.get('id')}-{ano}-{mes:02d}.csv", mime="text/csv", key="fp_baixar_pessoa")

    modal = st.session_state.get("modal_folha")
    if not modal or proprio:
        return
    if modal[0] == "ajustar":
        linha = next((l for l in linhas if l["data"].isoformat() == modal[1] and not l["em_branco"] and l["data"] < hoje), None)
        if linha is None:
            _fechar()
            return
        _modal_ajustar(pessoa, linha)
    elif modal[0] == "recusar":
        correcao = next((c for c in pendentes if c["id"] == modal[1]), None)
        if correcao is None:
            _fechar()
            return
        _modal_recusar(pessoa, correcao, marcacoes)


def pagina_folha_ponto() -> None:
    token = st.session_state.token
    render_topbar(st.session_state.usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Folha de ponto", "Registros mensais da equipe: consulta, correções e o fechamento do mês")
    with st.spinner("Carregando..."):
        try:
            base, erro = _base(token), None
        except ApiError as falha:
            base, erro = None, falha
    if erro is not None:
        if erro.status_code == 404:
            st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">Sua conta ainda não está ligada a um cadastro de funcionário.</p></div>')
        else:
            alerta(st.empty(), "erro", erro.message)
        return
    pessoas = base["pessoas"].get("pessoas") or []
    ve_todos = bool(base["pessoas"].get("ve_todos"))
    if not ve_todos and not [p for p in pessoas if not p.get("e_voce")]:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-bloco-titulo">Você ainda não tem equipe</p>'
                '<p class="crh-meta">Aqui aparecem as pessoas que têm você como superior direto (ou do departamento que você gerencia). '
                'A sua própria folha está em Ponto → Espelho de ponto → Mês.</p></div>')
        return
    org = base.get("org") or {}
    deps = {d.get("id"): d.get("nome") for d in org.get("departamentos") or []}
    cargos = {c.get("id"): c.get("nome") for c in org.get("cargos") or []}
    feriados = (base.get("cal") or {}).get("feriados") or []
    hoje = hoje_brasilia()
    with st.container(key="cfg_abas", width="content"):
        if st.session_state.get("fp_aba") not in _ABAS:
            st.session_state.fp_aba = _ABAS[0]
        aba = st.segmented_control("Aba", _ABAS, required=True, key="fp_aba", label_visibility="collapsed")
    if aba == "Resumo do mês":
        if str(st.session_state.usuario.get("perfil", "")).upper() in ("RH", "ADMIN"):
            _cartao_prazo(token)
        _resumo(token, pessoas, deps, cargos, feriados, ve_todos, hoje)
    else:
        _por_pessoa(token, pessoas, deps, feriados, hoje)
