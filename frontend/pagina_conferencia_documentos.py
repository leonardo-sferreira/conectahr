"""
Página "Conferência de documentos" do RH e do Admin (tarefa 27 da change concluir-frontend-streamlit),
conforme a seção 18 do Figma:
- aba "Para conferir" (418:1108): aprovar (418:1642), recusar com motivo (244:1035), abrir o arquivo
  e arquivar (418:1666); "Pedir documento" (244:1059) e "Processar vencidos" (418:1723);
- aba "Pendências pedidas" (418:1276);
- aba "Obrigatórios por cargo" (418:1461) com "Nova regra" (418:1692).

Endpoints: `documentos`, `pendencias_documento` (GET e POST), `documentos_obrigatorios` (GET e
POST), `documentos/{id}/aprovar|rejeitar|arquivar|arquivo`, `documentos/processar_vencimentos` e
`organograma` (nomes e departamentos). A autorização é do backend (só RH e Admin); a tela só deixa de
oferecer o que o backend recusaria (ver conferencia_modelo.py). Não existe exclusão: só arquivamento.
"""

import html
import time
from datetime import date, timedelta

import streamlit as st

from api_client import (
    ApiError,
    abrir_arquivo_documento,
    aprovar_documento,
    arquivar_documento,
    criar_regra_documento,
    documentos_obrigatorios,
    documentos_rh,
    organograma,
    pedir_documento,
    pendencias_documento,
    processar_vencimentos,
    rejeitar_documento,
)
from conferencia_modelo import (
    CONTRATOS,
    EVENTOS_RETENCAO,
    linhas_para_conferir,
    linhas_pendencias,
    linhas_regras,
    pessoas,
    resumo,
    tipos_presentes,
    validar_motivo,
    validar_pedido,
    validar_regra,
)
from documentos_modelo import TIPOS_ENVIO, rotulo_tipo
from theme import alerta, render_hero, render_indicadores, render_topbar

_ABAS = ["Para conferir", "Pendências pedidas", "Obrigatórios por cargo"]
_CACHE = "conferencia_cache"
_VALIDADE_CACHE_S = 20


def _carregar(token: str) -> dict:
    """{'documentos', 'pendencias', 'organograma'} guardado por 20 s. Erro de `documentos` sobe (403 para
    quem não é RH nem Admin); sem pendências ou organograma a tela segue com o que tem."""
    cache = st.session_state.get(_CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = {"documentos": documentos_rh(st.session_state.token).get("documentos") or []}
    for chave, funcao, campo in (("pendencias", pendencias_documento, "pendencias"), ("organograma", organograma, None)):
        try:
            resposta = funcao(token)
            dados[chave] = resposta.get(campo) or [] if campo else resposta
        except ApiError:
            dados[chave] = [] if campo else {}
    st.session_state[_CACHE] = {"em": time.time(), "dados": dados}
    return dados


def _regras(token: str) -> list[dict] | ApiError:
    cache = st.session_state.get("conferencia_regras_cache")
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    try:
        regras = documentos_obrigatorios(token).get("regras") or []
    except ApiError as erro:
        return erro
    st.session_state["conferencia_regras_cache"] = {"em": time.time(), "dados": regras}
    return regras


def _invalidar() -> None:
    st.session_state.pop(_CACHE, None)
    st.session_state.pop("conferencia_regras_cache", None)


# ---------------------------------------------------------------------------
# Modais (abertos enquanto `modal_rh` estiver na sessão)
# ---------------------------------------------------------------------------
def _fechar() -> None:
    st.session_state.pop("modal_rh", None)


def _concluir(aviso: str) -> None:
    _invalidar()
    _fechar()
    st.session_state.aviso_toast = aviso
    st.rerun()


def _resumo_documento(linha: dict, terceira: tuple[str, str]) -> None:
    linhas = [("Pessoa", linha["pessoa"]), ("Documento", linha["documento"]), terceira]
    campos = "".join(f'<p class="r">{html.escape(r)}</p><p class="v">{html.escape(v)}</p>' for r, v in linhas)
    st.html(f'<div class="crh-campos crh-campos-direita">{campos}</div>')


def _botoes(rotulo: str, chave: str, tipo: str = "primary", voltar: str = "Voltar") -> bool:
    with st.container(horizontal=True, horizontal_alignment="right"):
        if voltar and st.button(voltar, key=f"{chave}_voltar"):
            _fechar()
            st.rerun()
        return st.button(rotulo, type=tipo, key=chave)


@st.dialog("Aprovar documento", width="small", on_dismiss=_fechar)
def _modal_aprovar(linha: dict) -> None:
    _resumo_documento(linha, ("Enviado em", linha["enviado"]))
    obs = st.text_area("Observação (opcional, o colaborador vê)", max_chars=1000, key="rh_aprovar_obs", height=80)
    slot = st.empty()
    if _botoes("Aprovar", "rh_aprovar_ok"):
        try:
            aprovar_documento(st.session_state.token, linha["id"], obs.strip() or None)
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        st.session_state.pop("rh_aprovar_obs", None)
        _concluir(f"Documento aprovado. {linha['pessoa']} recebe o aviso.")


@st.dialog("Recusar documento", width="small", on_dismiss=_fechar)
def _modal_recusar(linha: dict) -> None:
    _resumo_documento(linha, ("Enviado em", linha["enviado"]))
    if linha["arquivo"] == "bloqueado":
        st.html(f'<p class="crh-nota-ambar">Arquivo bloqueado na verificação: {html.escape(linha["motivo_bloqueio"] or "motivo não informado")}</p>')
    motivo = st.text_area("Motivo (o colaborador vê)", max_chars=1000, key="rh_recusar_motivo", height=80)
    slot = st.empty()
    if _botoes("Recusar", "rh_recusar_ok"):
        erro_campo = validar_motivo(motivo)
        if erro_campo:
            alerta(slot, "erro", erro_campo)
            return
        try:
            rejeitar_documento(st.session_state.token, linha["id"], motivo.strip())
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        st.session_state.pop("rh_recusar_motivo", None)
        _concluir(f"Documento recusado. {linha['pessoa']} vê o motivo e pode enviar outro.")


@st.dialog("Arquivar documento", width="small", on_dismiss=_fechar)
def _modal_arquivar(linha: dict) -> None:
    rotulo_data = "Venceu em" if linha["status"] == "vencido" else "Enviado em"
    _resumo_documento(linha, (rotulo_data, linha["validade"] if linha["status"] == "vencido" else linha["enviado"]))
    st.html(
        '<p class="crh-nota-ambar">Arquivar não apaga: o documento sai das listas, deixa de ser editável e fica '
        "guardado até o fim do prazo de retenção. Só documentos recusados, vencidos ou substituídos podem ser arquivados.</p>"
    )
    obs = st.text_area("Observação (opcional)", max_chars=1000, key="rh_arquivar_obs", height=80)
    slot = st.empty()
    if _botoes("Arquivar", "rh_arquivar_ok"):
        try:
            arquivar_documento(st.session_state.token, linha["id"], obs.strip() or None)
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        st.session_state.pop("rh_arquivar_obs", None)
        _concluir("Documento arquivado.")


@st.dialog("Pedir documento", width="small", on_dismiss=_fechar)
def _modal_pedir(mapa_pessoas: dict) -> None:
    ids = sorted(mapa_pessoas, key=lambda i: mapa_pessoas[i]["nome"])
    colaborador = st.selectbox(
        "Colaborador", ids, index=None, placeholder="Escolha a pessoa",
        format_func=lambda i: f"{mapa_pessoas[i]['nome']} — {mapa_pessoas[i]['detalhe']}", key="rh_pedir_colab",
    )
    tipo = st.selectbox("Documento", TIPOS_ENVIO, index=None, placeholder="Escolha o documento", format_func=rotulo_tipo, key="rh_pedir_tipo")
    prazo = st.date_input("Prazo", value=date.today() + timedelta(days=10), min_value=date.today(), format="DD/MM/YYYY", key="rh_pedir_prazo")
    obs = st.text_input("Observação", max_chars=500, key="rh_pedir_obs")
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">A pessoa recebe a pendência por e-mail e na tela Documentos. Não dá para abrir duas pendências iguais.</p></div>')
    slot = st.empty()
    if _botoes("Pedir documento", "rh_pedir_ok", voltar="Cancelar"):
        erro_campo = validar_pedido(colaborador, tipo, prazo, date.today())
        if erro_campo:
            alerta(slot, "erro", erro_campo)
            return
        try:
            pedir_documento(st.session_state.token, colaborador, tipo, prazo.isoformat(), obs.strip() or None)
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        for chave in ("rh_pedir_colab", "rh_pedir_tipo", "rh_pedir_prazo", "rh_pedir_obs"):
            st.session_state.pop(chave, None)
        _concluir(f"Pendência criada. {mapa_pessoas[colaborador]['nome']} recebe o aviso.")


@st.dialog("Vencidos processados", width="small", on_dismiss=_fechar)
def _modal_vencidos() -> None:
    resultado = st.session_state.get("rh_vencidos_resultado")
    if resultado is None:
        try:
            with st.spinner("Processando..."):
                resultado = processar_vencimentos(st.session_state.token)
        except ApiError as erro:
            alerta(st.empty(), "erro", erro.message)
            if st.button("Fechar", type="primary", key="rh_vencidos_fechar_erro"):
                _fechar()
                st.rerun()
            return
        st.session_state.rh_vencidos_resultado = resultado
        _invalidar()
    campos = "".join(
        f'<p class="r">{r}</p><p class="v">{v}</p>'
        for r, v in (('Viraram "Vencido"', int(resultado.get("total_vencidos") or 0)), ("Alertas enviados", int(resultado.get("total_alertas") or 0)))
    )
    st.html(f'<div class="crh-campos crh-campos-direita">{campos}</div>')
    st.html(
        '<p class="crh-nota-ambar">Os alertas saem 30, 15 e 7 dias antes e no dia do vencimento. Rodar de novo no mesmo '
        "dia não reenvia o mesmo alerta. O colaborador continua ativo.</p>"
    )
    if _botoes("Fechar", "rh_vencidos_fechar", voltar=None):
        st.session_state.pop("rh_vencidos_resultado", None)
        _fechar()
        st.rerun()


@st.dialog("Nova regra de documento", width="small", on_dismiss=_fechar)
def _modal_regra(cargos: dict) -> None:
    tipo = st.selectbox("Documento", TIPOS_ENVIO, index=None, placeholder="Escolha o documento", format_func=rotulo_tipo, key="rh_regra_tipo")
    c1, c2 = st.columns(2)
    with c1:
        contrato = st.selectbox("Vale para (contrato)", list(CONTRATOS), format_func=CONTRATOS.get, key="rh_regra_contrato")
    with c2:
        cargo = st.selectbox("Cargo", [None] + sorted(cargos, key=lambda i: cargos[i]), format_func=lambda i: "Todos os cargos" if i is None else cargos[i], key="rh_regra_cargo")
    prazo = st.number_input("Prazo para envio (dias depois da admissão)", min_value=1, max_value=365, value=10, step=1, key="rh_regra_prazo")
    c3, c4 = st.columns(2)
    with c3:
        anos = st.number_input("Guardar por (anos)", min_value=0, max_value=100, value=5, step=1, key="rh_regra_anos")
    with c4:
        evento = st.selectbox("Contando", list(EVENTOS_RETENCAO), format_func=EVENTOS_RETENCAO.get, key="rh_regra_evento")
    st.html(
        '<div class="crh-incluso"><p class="n" style="margin:0">A pessoa admitida recebe a pendência com esse prazo. "Guardar por" define '
        "quando o documento pode ser anonimizado. Prazos a confirmar com o jurídico.</p></div>"
    )
    slot = st.empty()
    if _botoes("Salvar regra", "rh_regra_ok", voltar="Cancelar"):
        erro_campo = validar_regra(tipo, prazo, anos)
        if erro_campo:
            alerta(slot, "erro", erro_campo)
            return
        regra = {
            "tipo_documento": tipo,
            "tipo_contrato": contrato or None,
            "cargo_id": cargo,
            "prazo_dias_para_envio": int(prazo),
            "obrigatorio": True,
            "retencao_prazo_dias": int(anos) * 365 if anos else None,
            "retencao_evento_inicial": evento if anos else None,
        }
        try:
            criar_regra_documento(st.session_state.token, regra)
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        for chave in ("rh_regra_tipo", "rh_regra_contrato", "rh_regra_cargo", "rh_regra_prazo", "rh_regra_anos", "rh_regra_evento"):
            st.session_state.pop(chave, None)
        _concluir("Regra cadastrada. Vale para as próximas admissões.")


# ---------------------------------------------------------------------------
# Tabelas
# ---------------------------------------------------------------------------
def _cabecalho(titulos: list[str], pesos: list[float]) -> None:
    with st.container(key="rh_cab"):
        for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), titulos):
            coluna.html(f'<p class="crh-doc-cab">{html.escape(texto)}</p>')


def _celula_pessoa(coluna, nome: str, detalhe: str) -> None:
    coluna.html(f'<div class="crh-doc-cel"><p class="t">{html.escape(nome)}</p><p class="d">{html.escape(detalhe)}</p></div>')


def _celula_texto(coluna, texto: str) -> None:
    coluna.html(f'<p class="crh-doc-prazo">{html.escape(texto)}</p>')


def _celula_selo(coluna, selo: tuple[str, str]) -> None:
    coluna.html(f'<span class="crh-selo {selo[1]}">{html.escape(selo[0])}</span>', width="content")


def _vazio(texto: str) -> None:
    with st.container(key="rh_lin_vazio"):
        st.html(f'<p class="crh-meta">{html.escape(texto)}</p>')


def _tabela_conferir(linhas: list[dict]) -> None:
    pesos = [3, 2.3, 1.3, 1.3, 1.1, 2]
    with st.container(key="rh_tabela"):
        _cabecalho(["Pessoa", "Documento", "Enviado em", "Validade", "Arquivo", ""], pesos)
        if not linhas:
            _vazio("Nada para conferir agora.")
        for i, l in enumerate(linhas):
            chave = f"rh_linf_{i}" if l["status"] == "pendente_analise" else f"rh_lin_{i}"
            with st.container(key=chave):
                c = st.columns(pesos, vertical_alignment="center")
                _celula_pessoa(c[0], l["pessoa"], l["detalhe"])
                _celula_texto(c[1], l["documento"])
                if l["situacao"]:
                    _celula_selo(c[2], l["situacao"])
                else:
                    _celula_texto(c[2], l["enviado"])
                _celula_texto(c[3], l["validade"])
                with c[4]:
                    if l["arquivo"] == "bloqueado":
                        _celula_selo(c[4], ("Bloqueado", "err"))
                    elif st.button("Abrir", type="tertiary", key=f"rh_abrir_{l['id']}"):
                        _abrir_arquivo(l["id"])
                        st.rerun()
                with c[5]:
                    if l["proprio"]:
                        st.html('<p class="crh-meta">Seu: outro RH decide</p>')
                    elif l["acoes"]:
                        with st.container(horizontal=True, gap="small"):
                            for acao in l["acoes"]:
                                if st.button(acao.capitalize(), type="tertiary", key=f"rh_{acao}_{l['id']}"):
                                    st.session_state.modal_rh = (acao, l["id"])
                                    st.rerun()


def _tabela_pendencias(linhas: list[dict]) -> None:
    pesos = [3, 2.6, 1.4, 1.4, 1.6]
    with st.container(key="rh_tabela"):
        _cabecalho(["Pessoa", "Documento", "Prazo", "Situação", "Pedido por"], pesos)
        if not linhas:
            _vazio("Nenhuma pendência pedida.")
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_lin_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                _celula_pessoa(c[0], l["pessoa"], l["detalhe"])
                _celula_texto(c[1], l["documento"])
                _celula_texto(c[2], l["prazo"])
                _celula_selo(c[3], l["situacao"])
                _celula_texto(c[4], l["pedido_por"])


def _tabela_regras(linhas: list[dict]) -> None:
    pesos = [2.4, 3, 1.4, 2.4, 1.2]
    with st.container(key="rh_tabela"):
        _cabecalho(["Documento", "Vale para", "Prazo de envio", "Guardar por", "Obrigatório"], pesos)
        if not linhas:
            _vazio("Nenhuma regra cadastrada. Use \"Nova regra\".")
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_lin_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                _celula_texto(c[0], l["documento"])
                _celula_texto(c[1], l["vale_para"])
                _celula_texto(c[2], l["prazo"])
                _celula_texto(c[3], l["guardar"])
                _celula_texto(c[4], l["obrigatorio"])


def _abrir_arquivo(documento_id: int) -> None:
    try:
        resposta = abrir_arquivo_documento(st.session_state.token, documento_id)
        st.session_state.rh_link_aberto = resposta.get("arquivo_url")
        st.session_state.pop("rh_link_erro", None)
    except ApiError as erro:
        st.session_state.rh_link_erro = erro.message
        st.session_state.pop("rh_link_aberto", None)


def _nota(texto: str) -> None:
    st.html(f'<p class="crh-meta">{html.escape(texto)}</p>')


# ---------------------------------------------------------------------------
def pagina_conferencia_documentos() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Conferência de documentos", "Confira o que os colaboradores enviaram e cobre o que falta")

    # Permissão negada: o menu já esconde a tela, mas o endereço pode ser aberto direto.
    if str(usuario.get("perfil", "")).upper() not in ("RH", "ADMIN"):
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
    mapa = pessoas(dados["organograma"])
    numeros = resumo(dados["documentos"], dados["pendencias"], hoje)
    render_indicadores([
        ("Aguardando análise", str(numeros["aguardando"]), "ambar"),
        ("Vencidos para processar", str(numeros["vencidos"]), "negativo"),
        ("Pendências abertas", str(numeros["pendencias"]), "azul"),
        ("Aprovados no mês", str(numeros["aprovados_mes"]), "verde"),
    ])

    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Aba", _ABAS, default=_ABAS[0], required=True, key="rh_aba", label_visibility="collapsed")
        st.space("stretch")
        tipo = None
        if aba == _ABAS[0]:
            tipo = st.selectbox(
                "Tipo", [None] + tipos_presentes(dados["documentos"]), format_func=lambda t: "Tipo: Todos" if t is None else rotulo_tipo(t),
                key="rh_tipo", label_visibility="collapsed", width=200,
            )
        if aba == _ABAS[2]:
            if st.button("Nova regra", key="rh_btn_regra"):
                st.session_state.modal_rh = ("regra", None)
        else:
            if st.button("Pedir documento", key="rh_btn_pedir"):
                st.session_state.modal_rh = ("pedir", None)
            if st.button("Processar vencidos", key="rh_btn_vencidos"):
                st.session_state.pop("rh_vencidos_resultado", None)
                st.session_state.modal_rh = ("vencidos", None)

    if link := st.session_state.get("rh_link_aberto"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html('<p class="crh-meta">Link do arquivo pronto (vale por 5 minutos). A abertura fica registrada na auditoria.</p>', width="content")
            st.link_button("Abrir arquivo", link)
    if erro_link := st.session_state.pop("rh_link_erro", None):
        alerta(st.empty(), "erro", erro_link)

    linhas = []
    if aba == _ABAS[0]:
        linhas = linhas_para_conferir(dados["documentos"], mapa, usuario.get("colaborador_id"), tipo)
        _tabela_conferir(linhas)
        _nota(
            "Ninguém decide o próprio documento. Arquivo bloqueado na verificação não pode ser aprovado: recuse e peça "
            'outro link. Arquivar não apaga: o documento fica guardado até o fim do prazo de retenção. Documento aprovado '
            'com validade vencida vira "Vencido" ao processar.'
        )
    elif aba == _ABAS[1]:
        _tabela_pendencias(linhas_pendencias(dados["pendencias"], mapa, usuario.get("id"), hoje))
        _nota('A pendência fecha sozinha quando a pessoa envia um documento do mesmo tipo. "Atrasada": o prazo passou e o documento não chegou. Pedido cancelado não aparece.')
    else:
        regras = _regras(token)
        if isinstance(regras, ApiError):
            alerta(st.empty(), "erro", regras.message)
        else:
            org = dados["organograma"]
            cargos = {c.get("id"): c.get("nome") for c in org.get("cargos") or []}
            deps = {d.get("id"): d.get("nome") for d in org.get("departamentos") or []}
            _tabela_regras(linhas_regras(regras, cargos, deps))
            _nota('As regras valem para as próximas admissões: cada pessoa recebe a pendência com o prazo de envio. "Guardar por" define quando o documento pode ser anonimizado (prazos a confirmar com o jurídico).')

    # Modal aberto (fica na tela enquanto a marca estiver na sessão).
    modal = st.session_state.get("modal_rh")
    if not modal:
        return
    acao, doc_id = modal
    por_id = {l["id"]: l for l in linhas_para_conferir(dados["documentos"], mapa, usuario.get("colaborador_id"))}
    if acao in ("aprovar", "recusar", "arquivar"):
        linha = por_id.get(doc_id)
        if linha is None or acao not in linha["acoes"]:
            _fechar()  # o documento mudou de situação desde que a linha foi desenhada
            return
        {"aprovar": _modal_aprovar, "recusar": _modal_recusar, "arquivar": _modal_arquivar}[acao](linha)
    elif acao == "pedir":
        _modal_pedir(mapa)
    elif acao == "vencidos":
        _modal_vencidos()
    elif acao == "regra":
        org = dados["organograma"]
        _modal_regra({c.get("id"): c.get("nome") for c in org.get("cargos") or []})
