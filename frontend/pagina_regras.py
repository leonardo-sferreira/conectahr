"""
Página "Regras e Conformidade" (Figma 287:884; simulação 288:886; modais 288:1186 a 288:1391; change tela-de-regras;
tarefas 36 e 37 de concluir-frontend-streamlit). Só RH e Admin; a autorização é do backend.

- Lista: filtros (todos, pendentes, com conflito, vigentes), instrumentos normativos e regras de override, cada um com
  selo e ações conforme a situação (`regras_modelo.acoes_*`).
- Simulação de impacto: aberta por "Simular" ou depois de criar uma regra. Mostra pessoas, departamentos, regra atual x
  nova, conflitos (com "Definir prioridade"), processos afetados e a tabela de pessoas; dali sai "Enviar para aprovação".
- Aprovar uma regra já a deixa vigente (a versão anterior fica no histórico): o modal usa o texto do "Aplicar regra".

Endpoints: `instrumentos_normativos` (GET, POST, enviar_aprovacao, aprovar, rejeitar), `regras_override` (GET, POST,
enviar_aprovacao, aprovar, rejeitar, prioridade, simular), `organograma` e `usuarios` (nomes).
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import (ApiError, aprovar_instrumento, aprovar_override, criar_instrumento, criar_override, enviar_instrumento, enviar_override,
                        instrumentos_normativos, organograma, prioridade_override, regras_override, rejeitar_instrumento, rejeitar_override,
                        simular_override, usuarios)
from campos import campo
from cadastro_modelo import CONTRATOS
from perfil_modelo import UFS
from regras_modelo import (ABRANGENCIAS, FILTROS, PARAMETROS, TIPOS_INSTRUMENTO, acoes_instrumento, acoes_regra, corpo_instrumento, corpo_regra,
                           dados_nova_versao, filtrar, historico, linha_instrumento, linha_regra, simulacao, titulo_regra, validar_instrumento,
                           validar_regra, valor_legivel, vigencia)
from theme import alerta, render_hero, render_indicadores, render_topbar

_VALIDADE_CACHE_S = 20
_ROTULOS_ACAO = {"enviar": "Enviar para aprovação", "detalhes": "Ver detalhes", "rejeitar": "Rejeitar", "aprovar": "Aprovar", "simular": "Simular",
                 "nova_versao": "Nova versão", "historico": "Histórico"}


def _guardado(chave: str, buscar):
    item = st.session_state.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = buscar()
    st.session_state[chave] = {"em": time.time(), "dados": dados}
    return dados


def _invalidar() -> None:
    for chave in [k for k in st.session_state if str(k).startswith("reg_cache_")]:
        st.session_state.pop(chave, None)


def _carregar(token: str) -> dict:
    dados = {"instrumentos": _guardado("reg_cache_instr", lambda: instrumentos_normativos(token)).get("instrumentos") or [],
             "regras": _guardado("reg_cache_regras", lambda: regras_override(token)).get("overrides") or []}
    try:
        org = _guardado("reg_cache_org", lambda: organograma(token))
    except ApiError:
        org = {}
    try:
        contas = _guardado("reg_cache_usuarios", lambda: usuarios(token)).get("usuarios") or []
    except ApiError:
        contas = []
    dados["nomes"] = {"departamentos": {d.get("id"): d.get("nome") for d in org.get("departamentos") or []},
                      "cargos": {c.get("id"): c.get("nome") for c in org.get("cargos") or []},
                      "pessoas": {c.get("id"): c.get("nome") for c in org.get("colaboradores") or []}}
    dados["contas"] = {u.get("id"): u.get("nome") for u in contas}
    dados["titulos"] = {i.get("id"): i.get("titulo") for i in dados["instrumentos"]}
    return dados


def fechar() -> None:
    st.session_state.pop("reg_modal", None)
    for chave in [k for k in st.session_state if str(k).startswith(("reg_ov_", "reg_in_", "reg_rej_", "reg_apr_", "reg_prio_"))]:
        st.session_state.pop(chave, None)


def _concluir(aviso: str, simular: int | None = None) -> None:
    _invalidar()
    fechar()
    if simular is not None:
        st.session_state.reg_simular = simular
    st.session_state.aviso_toast = aviso
    st.rerun()


def _botoes(rotulo: str, chave: str, tipo: str = "primary", perigo: bool = False) -> bool:
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key=f"{chave}_voltar"):
            fechar()
            st.rerun()
        with st.container(key=f"{chave}_perigo" if perigo else f"{chave}_ok_box", width="content"):
            return st.button(rotulo, type=tipo, key=f"{chave}_ok")


def _quadro(pares: list[tuple[str, str]]) -> None:
    campos_ = "".join(f'<p class="r">{html.escape(r)}</p><p class="v">{html.escape(v)}</p>' for r, v in pares)
    st.html(f'<div class="crh-campos crh-campos-direita">{campos_}</div>')


def _criado_por(item: dict, dados: dict) -> str:
    if item.get("criado_por_user_id") == st.session_state.usuario.get("id"):
        return f"Você ({st.session_state.usuario.get('nome')})"
    return dados["contas"].get(item.get("criado_por_user_id")) or "Outra pessoa do RH ou Admin"


# ---------------------------------------------------------------------------
# Modais
# ---------------------------------------------------------------------------
@st.dialog("Novo instrumento normativo", width="medium", on_dismiss=fechar)
def _modal_instrumento() -> None:
    d = {"tipo": st.selectbox("Tipo", list(TIPOS_INSTRUMENTO), index=None, format_func=TIPOS_INSTRUMENTO.get, placeholder="Escolha", key="reg_in_tipo")}
    d["titulo"] = campo(st, "Título", "texto", "reg_in_titulo", max_chars=200)
    d["entidade_responsavel"] = campo(st, "Entidade responsável", "texto", "reg_in_entidade", max_chars=200)
    c1, c2 = st.columns(2)
    d["numero_solicitacao_mediador"] = campo(c1, "Solicitação no Mediador", "texto", "reg_in_mediador", max_chars=20, placeholder="MR12345/2027")
    d["numero_registro_mte"] = campo(c2, "Registro no MTE", "texto", "reg_in_registro", max_chars=20, placeholder="AB123456/2027")
    c1, c2 = st.columns(2)
    d["numero_processo_mte"] = campo(c1, "Processo no MTE", "texto", "reg_in_processo", max_chars=30)
    d["data_registro"] = c2.date_input("Data do registro no MTE", value=None, format="DD/MM/YYYY", key="reg_in_data_registro")
    st.html('<p class="crh-meta">Formatos: MR12345/2027 e AB123456/2027. A solicitação é obrigatória em acordo, convenção e termo aditivo; '
            'registro, processo e data do registro no MTE são exigidos para ativar.</p>')
    c1, c2 = st.columns(2)
    d["data_inicio"] = c1.date_input("Início da vigência", value=None, format="DD/MM/YYYY", key="reg_in_inicio")
    d["data_fim"] = c2.date_input("Fim da vigência", value=None, format="DD/MM/YYYY", key="reg_in_fim")
    d["documento_url"] = campo(st, "Documento (link https)", "texto", "reg_in_documento", max_chars=500, placeholder="https://...")
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">O instrumento vai para aprovação e só vigora quando outra pessoa aprovar.</p></div>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="reg_in_cancelar"):
            fechar()
            st.rerun()
        if st.button("Enviar para aprovação", type="primary", key="reg_in_ok"):
            erro = validar_instrumento(d)
            if erro:
                alerta(slot, "erro", erro)
                return
            token = st.session_state.token
            try:
                criado = (criar_instrumento(token, corpo_instrumento(d)).get("instrumento") or {}).get("id")
                enviar_instrumento(token, criado)
            except ApiError as erro_api:
                _invalidar()
                alerta(slot, "erro", erro_api.message)
                return
            _concluir("Instrumento enviado para aprovação.")


def _referencia(d: dict, dados: dict, prefixo: str) -> None:
    ab = d.get("abrangencia")
    if ab == "departamento":
        opcoes = dados["nomes"]["departamentos"]
        d["departamento_id"] = st.selectbox("Referência", list(opcoes), format_func=opcoes.get, placeholder="Escolha", key=f"{prefixo}_dep")
    elif ab == "cargo":
        opcoes = dados["nomes"]["cargos"]
        d["cargo_id"] = st.selectbox("Referência", list(opcoes), format_func=opcoes.get, placeholder="Escolha", key=f"{prefixo}_cargo")
    elif ab == "colaborador":
        opcoes = dict(sorted(dados["nomes"]["pessoas"].items(), key=lambda par: par[1] or ""))
        d["colaborador_id"] = st.selectbox("Referência", list(opcoes), format_func=opcoes.get, placeholder="Escolha", key=f"{prefixo}_colab")
    elif ab == "tipo_contrato":
        d["tipo_contrato"] = st.selectbox("Referência", list(CONTRATOS), format_func=CONTRATOS.get, placeholder="Escolha", key=f"{prefixo}_contrato")
    elif ab == "estado":
        d["estado"] = st.selectbox("Referência", UFS, placeholder="UF", key=f"{prefixo}_uf")
    elif ab == "municipio":
        d["municipio"] = campo(st, "Município", "endereco", f"{prefixo}_municipio", max_chars=120)
    else:
        st.text_input("Referência", value="Empresa inteira", disabled=True, key=f"{prefixo}_empresa")


def _valor_novo(parametro: str | None, prefixo: str):
    unidade = PARAMETROS.get(parametro, ("", ""))[1]
    if unidade == "bool":
        return st.selectbox("Valor novo", ["true", "false"], format_func=lambda v: "Habilitado" if v == "true" else "Desabilitado", key=f"{prefixo}_bool")
    if parametro == "controle_ponto":
        return st.selectbox("Valor novo", ["obrigatorio", "manual", "nao_aplicavel"], format_func=lambda v: valor_legivel("controle_ponto", v), key=f"{prefixo}_ponto")
    numero = st.number_input(f"Valor novo ({unidade})" if unidade else "Valor novo", min_value=0.0, value=None, step=1.0, key=f"{prefixo}_num")
    return None if numero is None else (str(int(numero)) if float(numero).is_integer() else str(numero))


@st.dialog("Nova regra de override", width="medium", on_dismiss=fechar)
def _modal_regra(dados: dict, base: dict | None) -> None:
    prefixo = "reg_ov"
    if base and not st.session_state.get(f"{prefixo}_preenchido"):
        st.session_state.update({f"{prefixo}_param": base.get("parametro"), f"{prefixo}_prio": int(base.get("prioridade") or 1),
                                 f"{prefixo}_ab": base.get("abrangencia"), f"{prefixo}_instr": base.get("instrumento_normativo_id"),
                                 f"{prefixo}_dep": base.get("departamento_id"), f"{prefixo}_cargo": base.get("cargo_id"),
                                 f"{prefixo}_colab": base.get("colaborador_id"), f"{prefixo}_contrato": base.get("tipo_contrato"),
                                 f"{prefixo}_uf": base.get("estado"), f"{prefixo}_municipio": base.get("municipio") or "", f"{prefixo}_preenchido": True})
    # Valor inicial só pela sessão (sem index/value no widget), para a "Nova versão" poder vir preenchida.
    for chave, padrao in (("param", None), ("prio", 1), ("ab", None), ("instr", None), ("dep", None), ("cargo", None), ("colab", None), ("contrato", None), ("uf", None)):
        st.session_state.setdefault(f"{prefixo}_{chave}", padrao)
    hoje = date.today()
    d = {}
    c1, c2 = st.columns(2)
    d["parametro"] = c1.selectbox("Parâmetro", list(PARAMETROS), format_func=lambda p: PARAMETROS[p][0], placeholder="Escolha", key=f"{prefixo}_param")
    d["prioridade"] = c2.number_input("Prioridade", min_value=1, max_value=99, step=1, key=f"{prefixo}_prio",
                                      help="Entre regras do mesmo parâmetro que atingem a mesma pessoa, vale a de prioridade maior. Prioridade igual com valor diferente é conflito.")
    c1, c2 = st.columns(2)
    with c1:
        d["abrangencia"] = st.selectbox("Abrangência", list(ABRANGENCIAS), format_func=ABRANGENCIAS.get, placeholder="Escolha", key=f"{prefixo}_ab")
    with c2:
        _referencia(d, dados, prefixo)
    c1, c2 = st.columns(2)
    if base:
        c1.text_input("Valor atual", value=valor_legivel(base.get("parametro"), base.get("valor_novo")), disabled=True, key=f"{prefixo}_atual")
    else:
        c1.text_input("Valor atual", value="Aparece na simulação", disabled=True, key=f"{prefixo}_atual")
    with c2:
        d["valor_novo"] = _valor_novo(d["parametro"], prefixo)
    vigentes = {i.get("id"): i.get("titulo") for i in dados["instrumentos"] if i.get("status") == "vigente"}
    d["instrumento_normativo_id"] = st.selectbox("Instrumento de origem", list(vigentes), format_func=vigentes.get,
                                                 placeholder="Escolha um instrumento vigente" if vigentes else "Nenhum instrumento vigente", key=f"{prefixo}_instr")
    c1, c2 = st.columns(2)
    d["data_inicio"] = c1.date_input("Início da vigência", value=None, format="DD/MM/YYYY", key=f"{prefixo}_inicio")
    d["data_fim"] = c2.date_input("Fim da vigência", value=None, format="DD/MM/YYYY", key=f"{prefixo}_fim", help="Vazio: sem fim.")
    d["justificativa"] = campo(st, "Justificativa", "texto", f"{prefixo}_just", area=True, max_chars=2000, height=80)
    st.html('<p class="crh-meta">Vigência no passado (retroativa) exige justificativa e aprovação especial.</p>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key=f"{prefixo}_cancelar"):
            fechar()
            st.rerun()
        if st.button("Simular impacto", type="primary", key=f"{prefixo}_ok"):
            erro = validar_regra(d, hoje)
            if erro:
                alerta(slot, "erro", erro)
                return
            try:
                criada = (criar_override(st.session_state.token, corpo_regra(d, hoje)).get("override") or {}).get("id")
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            for chave in [k for k in st.session_state if str(k).startswith(f"{prefixo}_")]:
                st.session_state.pop(chave, None)
            _concluir("Regra salva como rascunho. Confira a simulação antes de enviar.", simular=criada)


@st.dialog("Aprovar", width="small", on_dismiss=fechar)
def _modal_aprovar(tipo: str, item: dict, dados: dict) -> None:
    eh_regra = tipo == "regra"
    titulo = titulo_regra(item, dados["nomes"]) if eh_regra else item.get("titulo")
    pares = [("Regra" if eh_regra else "Instrumento", titulo), ("Criada por" if eh_regra else "Criado por", _criado_por(item, dados)), ("Vigência", vigencia(item))]
    if eh_regra and item.get("conflitos"):
        _quadro(pares[:1] + pares[2:])
        c = item["conflitos"][0]
        st.html(f'<div class="crh-incluso"><p class="n" style="margin:0">🔒 Conflito não resolvido com "{html.escape(titulo_regra(c, dados["nomes"]))}". '
                'Resolva antes de aplicar.</p></div>')
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Fechar", key="reg_apr_fechar"):
                fechar()
                st.rerun()
            if st.button("Ver conflito", type="primary", key="reg_apr_ver_conflito"):
                fechar()
                st.session_state.reg_simular = item["id"]
                st.rerun()
        return
    _quadro(pares)
    justificativa = campo(st, "Justificativa (opcional)", "texto", "reg_apr_just", area=True, max_chars=1000, height=70) if eh_regra else None
    st.html('<p class="crh-meta">' + ("Ao aprovar, a regra vira vigente nos próximos cálculos. A versão anterior continua no histórico e a decisão fica na auditoria."
                                      if eh_regra else "Ao aprovar, o instrumento passa a vigorar e a decisão fica na auditoria.") + "</p>")
    slot = st.empty()
    if _botoes("Aprovar", "reg_apr"):
        try:
            if eh_regra:
                aprovar_override(st.session_state.token, item["id"], (justificativa or "").strip())
            else:
                aprovar_instrumento(st.session_state.token, item["id"])
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        st.session_state.pop("reg_apr_just", None)
        _concluir("Regra aprovada e vigente." if eh_regra else "Instrumento aprovado e vigente.")


@st.dialog("Rejeitar", width="small", on_dismiss=fechar)
def _modal_rejeitar(tipo: str, item: dict, dados: dict) -> None:
    eh_regra = tipo == "regra"
    _quadro([("Regra" if eh_regra else "Instrumento", titulo_regra(item, dados["nomes"]) if eh_regra else item.get("titulo")),
             ("Criada por" if eh_regra else "Criado por", _criado_por(item, dados)), ("Vigência", vigencia(item))])
    motivo = campo(st, "Motivo (a pessoa que criou vê)", "texto", "reg_rej_motivo", area=True, max_chars=1000, height=80)
    slot = st.empty()
    if _botoes("Rejeitar", "reg_rej", perigo=True):
        if len((motivo or "").strip()) < 5:
            alerta(slot, "erro", "Escreva o motivo (pelo menos 5 caracteres).")
            return
        try:
            (rejeitar_override if eh_regra else rejeitar_instrumento)(st.session_state.token, item["id"], motivo.strip())
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        st.session_state.pop("reg_rej_motivo", None)
        _concluir("Rejeitada. A pessoa que criou foi avisada." if eh_regra else "Instrumento rejeitado.")


@st.dialog("Detalhes", width="medium", on_dismiss=fechar)
def _modal_detalhes(item: dict, dados: dict) -> None:
    _quadro([("Tipo", TIPOS_INSTRUMENTO.get(item.get("tipo"), item.get("tipo") or "—")), ("Título", item.get("titulo") or "—"),
             ("Entidade", item.get("entidade_responsavel") or "—"), ("Solicitação no Mediador", item.get("numero_solicitacao_mediador") or "—"),
             ("Registro no MTE", item.get("numero_registro_mte") or "—"), ("Processo no MTE", item.get("numero_processo_mte") or "—"),
             ("Vigência", vigencia(item)), ("Documento", item.get("documento_url") or "—"), ("Criado por", _criado_por(item, dados))])
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Fechar", key="reg_det_fechar"):
            fechar()
            st.rerun()


@st.dialog("Histórico", width="medium", on_dismiss=fechar)
def _modal_historico(item: dict, dados: dict) -> None:
    st.html(f'<p class="crh-bloco-titulo" style="font-size:15px">{html.escape(titulo_regra(item, dados["nomes"]))}</p>')
    for v in historico(item, dados["regras"]):
        linha = linha_regra(v, dados["nomes"], dados["titulos"])
        st.html(f'<div class="crh-linha-onb"><div class="txt"><p class="t">Versão {v.get("versao") or 1} · {html.escape(valor_legivel(v.get("parametro"), v.get("valor_novo")))}</p>'
                f'<p class="d">vigência {html.escape(vigencia(v))}</p></div><span class="crh-selo {linha["tom"]}">{html.escape(linha["badge"])}</span></div>')
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Fechar", key="reg_hist_fechar"):
            fechar()
            st.rerun()


@st.dialog("Definir prioridade", width="small", on_dismiss=fechar)
def _modal_prioridade(item: dict) -> None:
    st.html('<p class="crh-meta">Use uma prioridade diferente da regra em conflito. Entre regras do mesmo parâmetro que atingem a mesma pessoa, vale a de prioridade maior.</p>')
    prioridade = st.number_input("Prioridade", min_value=1, max_value=99, value=int(item.get("prioridade") or 1), step=1, key="reg_prio_valor")
    slot = st.empty()
    if _botoes("Salvar prioridade", "reg_prio"):
        try:
            prioridade_override(st.session_state.token, item["id"], prioridade)
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        st.session_state.pop(f"reg_cache_sim_{item['id']}", None)
        _concluir(f"Prioridade alterada para {prioridade}.", simular=item["id"])


# ---------------------------------------------------------------------------
# Lista (Figma 287:884)
# ---------------------------------------------------------------------------
def _cartao(chave: str, linha: dict, acoes: dict, nota: str | None, tom_nota: str = "neu") -> str | None:
    """Um item da trilha: o texto à esquerda, o selo e os botões à direita. Devolve a ação clicada."""
    clicada = None
    with st.container(key=f"reg_card_{chave}"):
        c = st.columns([3.4, 1.6], vertical_alignment="center")
        nota_html = f'<p class="crh-reg-nota {tom_nota}">{html.escape(nota)}</p>' if nota else ""
        c[0].html(f'<div class="crh-reg-txt"><p class="cat">{html.escape(linha["categoria"])}</p><p class="t">{html.escape(linha["titulo"])}</p>'
                  f'<p class="d">{html.escape(linha["detalhe"])}</p>{nota_html}</div>')
        with c[1]:
            with st.container(horizontal=True, horizontal_alignment="right"):
                st.html(f'<span class="crh-selo {linha["tom"]}">{html.escape(linha["badge"])}</span>', width="content")
            with st.container(horizontal=True, horizontal_alignment="right"):
                for acao, motivo in acoes.items():
                    principal = acao == "aprovar" and motivo is None and linha["badge"] != "Conflito"
                    if st.button(_ROTULOS_ACAO[acao], key=f"reg_{acao}_{chave}", type="primary" if principal else "secondary", disabled=motivo is not None):
                        clicada = acao
    return clicada


def _lista(dados: dict) -> None:
    eu = st.session_state.usuario.get("id")
    with st.container(horizontal=True, vertical_alignment="center"):
        with st.container(key="cfg_abas", width="content"):
            filtro = st.segmented_control("Filtro", FILTROS, default=FILTROS[0], required=True, key="reg_filtro", label_visibility="collapsed")
        st.space("stretch")
        if st.button("Novo instrumento", key="reg_novo_instr"):
            st.session_state.reg_modal = ("instrumento", None)
            st.rerun()
        if st.button("Nova regra de override", type="primary", key="reg_nova_regra"):
            st.session_state.reg_modal = ("regra", None)
            st.rerun()

    st.html('<p class="crh-bloco-titulo">Instrumentos normativos</p>')
    instrumentos = filtrar(dados["instrumentos"], filtro)
    if not instrumentos:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">Nenhum instrumento neste filtro.</p></div>')
    for i in instrumentos:
        acoes = acoes_instrumento(i, eu)
        nota = next((m for m in acoes.values() if m), None)
        acao = _cartao(f"in_{i['id']}", linha_instrumento(i), acoes, nota)
        if acao == "enviar":
            try:
                enviar_instrumento(st.session_state.token, i["id"])
            except ApiError as erro:
                alerta(st.empty(), "erro", erro.message)
                return
            _concluir("Instrumento enviado para aprovação.")
        elif acao:
            st.session_state.reg_modal = (acao, ("instrumento", i["id"]))
            st.rerun()

    st.html('<p class="crh-bloco-titulo">Regras de override</p>')
    regras = filtrar(dados["regras"], filtro)
    if not regras:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">Nenhuma regra neste filtro.</p></div>')
    for r in regras:
        linha = linha_regra(r, dados["nomes"], dados["titulos"])
        acoes = acoes_regra(r, eu)
        nota, tom = (linha["conflito"], "err") if linha["conflito"] else (next((m for m in acoes.values() if m), None), "neu")
        acao = _cartao(f"ov_{r['id']}", linha, acoes, nota, tom)
        if acao == "simular":
            st.session_state.reg_simular = r["id"]
            st.rerun()
        elif acao == "enviar":
            try:
                enviar_override(st.session_state.token, r["id"])
            except ApiError as erro:
                alerta(st.empty(), "erro", erro.message)
                return
            _concluir("Regra enviada para aprovação.")
        elif acao:
            st.session_state.reg_modal = (acao, ("regra", r["id"]))
            st.rerun()
    st.html('<p class="crh-meta">Regras aplicadas pelo backend. Regra retroativa exige justificativa e aprovação especial. Quem cria não aprova.</p>')


# ---------------------------------------------------------------------------
# Simulação de impacto (Figma 288:886)
# ---------------------------------------------------------------------------
def _simulacao(dados: dict, regra_id: int) -> None:
    regra = next((r for r in dados["regras"] if r.get("id") == regra_id), None)
    if st.button("← Voltar para Regras", type="tertiary", key="reg_sim_voltar_topo"):
        st.session_state.pop("reg_simular", None)
        st.rerun()
    if regra is None:
        alerta(st.empty(), "atencao", "Regra não encontrada. Volte para a lista.")
        return
    try:
        with st.spinner("Simulando..."):
            sim = _guardado(f"reg_cache_sim_{regra_id}", lambda: simular_override(st.session_state.token, regra_id))
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    vm = simulacao(sim, regra, dados["nomes"], dados["titulos"])
    render_hero("Simulação de impacto", f"{titulo_regra(regra, dados['nomes'])} · simulada em {date.today():%d/%m/%Y} por {st.session_state.usuario.get('nome')} "
                                        "· nada foi alterado nas regras vigentes")
    render_indicadores(vm["cartoes"])
    c1, c2, c3 = st.columns([5, 0.4, 5], vertical_alignment="center")
    for coluna, titulo, pares in ((c1, "Regra atual", vm["atual"]), (c3, "Regra nova", vm["nova"])):
        linhas_ = "".join(f'<p class="r">{html.escape(r)}</p><p class="v">{html.escape(v)}</p>' for r, v in pares)
        coluna.html(f'<div class="crh-painel crh-bloco"><p class="crh-bloco-titulo">{titulo}</p><div class="crh-campos crh-campos-direita">{linhas_}</div></div>')
    c2.html('<p class="crh-reg-seta">→</p>')

    with st.container(key="reg_sim_conflitos"):
        st.html('<p class="crh-bloco-titulo">Conflitos</p><p class="crh-meta">Um conflito não resolvido bloqueia a publicação e pede análise humana.</p>')
        if not vm["conflitos"]:
            st.html('<p class="crh-meta">Nenhum conflito.</p>')
        for c in vm["conflitos"]:
            with st.container(key=f"reg_conf_{c['id']}", horizontal=True, vertical_alignment="center"):
                st.html(f'<div class="crh-reg-conf"><p class="t">{html.escape(c["titulo"])}</p><p class="d">{html.escape(c["detalhe"])}</p></div>')
                if st.button("Abrir regra em conflito", key=f"reg_conf_abrir_{c['id']}"):
                    st.session_state.reg_modal = ("historico", ("regra", c["id"]))
                    st.rerun()
                if regra.get("status") in ("rascunho", "pendente_aprovacao") and st.button("Definir prioridade", key=f"reg_conf_prio_{c['id']}"):
                    st.session_state.reg_modal = ("prioridade", ("regra", regra_id))
                    st.rerun()

    st.html('<div class="crh-painel crh-bloco"><p class="crh-bloco-titulo">Processos futuros afetados</p><ul class="crh-reg-lista">'
            + "".join(f"<li>{html.escape(p)}</li>" for p in vm["processos"]) + "</ul></div>")

    pesos = [2, 2, 1.3, 1.3]
    st.html(f'<p class="crh-bloco-titulo">Colaboradores afetados ({min(len(vm["pessoas"]), 50)} de {len(vm["pessoas"])})</p>')
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos), ["Pessoa", "Cargo", "Regra atual", "Regra nova"]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not vm["pessoas"]:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Ninguém ativo é atingido por esta regra.</p>')
        for i, p in enumerate(vm["pessoas"][:50]):
            with st.container(key=f"rh_lin_{i}"):
                for coluna, texto in zip(st.columns(pesos), (p["nome"], p["cargo"], p["atual"], p["nova"])):
                    coluna.html(f'<p class="crh-doc-prazo">{html.escape(texto)}</p>')

    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button("Voltar", key="reg_sim_voltar"):
            st.session_state.pop("reg_simular", None)
            st.rerun()
        if regra.get("status") == "rascunho":
            if st.button("Enviar para aprovação", type="primary", key="reg_sim_enviar", disabled=bool(vm["conflitos"])):
                try:
                    enviar_override(st.session_state.token, regra_id)
                except ApiError as erro:
                    alerta(st.empty(), "erro", erro.message)
                    return
                st.session_state.pop("reg_simular", None)
                _concluir("Regra enviada para aprovação.")
            st.html('<p class="crh-meta">' + ("Resolva o conflito antes de enviar. " if vm["conflitos"] else "") + "Simular não altera nenhuma regra vigente.</p>")


# ---------------------------------------------------------------------------
def pagina_regras() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    if str(usuario.get("perfil", "")).upper() not in ("RH", "ADMIN"):
        render_hero("Regras e Conformidade", "Instrumentos normativos e exceções em análise")
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return
    try:
        with st.spinner("Carregando..."):
            dados = _carregar(token)
    except ApiError as erro:
        render_hero("Regras e Conformidade", "Instrumentos normativos e exceções em análise")
        alerta(st.empty(), "erro", erro.message)
        return

    if st.session_state.get("reg_simular"):
        _simulacao(dados, st.session_state.reg_simular)
    else:
        render_hero("Regras e Conformidade", "Instrumentos normativos e exceções em análise")
        _lista(dados)

    modal = st.session_state.get("reg_modal")
    if not modal:
        return
    acao, alvo = modal
    if acao == "instrumento":
        _modal_instrumento()
        return
    if acao == "regra":
        _modal_regra(dados, None)
        return
    tipo, alvo_id = alvo
    lista = dados["regras"] if tipo == "regra" else dados["instrumentos"]
    item = next((x for x in lista if x.get("id") == alvo_id), None)
    if item is None:
        fechar()
    elif acao == "nova_versao":
        _modal_regra(dados, dados_nova_versao(item))
    elif acao == "aprovar":
        _modal_aprovar(tipo, item, dados)
    elif acao == "rejeitar":
        _modal_rejeitar(tipo, item, dados)
    elif acao == "detalhes":
        _modal_detalhes(item, dados)
    elif acao == "historico":
        _modal_historico(item, dados)
    elif acao == "prioridade":
        _modal_prioridade(item)
    else:
        fechar()
