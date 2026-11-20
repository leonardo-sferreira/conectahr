"""
Aba "Avaliações de desempenho" da tela "Ciclos de avaliação" (Figma F27, 249:5068 e o modal 249:5364; change
pesquisa-clima-e-avaliacao-360, D5 a D8). Só RH e Admin; a tela chama `aba_desempenho` e `abrir_modal`.

- "Ano" e "Abrir novo ciclo": o modal cria o ciclo, já o abre e atribui a autoavaliação e/ou a avaliação do gestor a
  todos os ativos (três chamadas; cada avaliador recebe aviso no sino e por e-mail).
- Tabela: ciclo (nome e descrição), período, autoavaliações e avaliações do gestor (% enviado, em barras) e situação
  ("Aberto", "Fechado"...). Ações que o Figma não desenha: "Atribuir" (lote ou uma a uma, como par), "Ver avaliações"
  e as mudanças de situação (iniciar fechamento, concluir, cancelar), com confirmação.
- Embaixo, do ciclo em foco (o aberto, ou o de "Ver avaliações"): "Contestações do ciclo" com "Responder" e
  "Andamento por departamento".

- No fim, "Competências avaliadas" (etapas 4 e 5 do F27; change backend-gestor-pendencias, D1): a tabela, "Nova
  competência" e "Editar" (o mesmo modal, com "Salvar"). Não há exclusão: desativar tira do formulário.

Endpoints: `competencias_avaliacao` (GET, POST e `{id}` PATCH), `ciclos_avaliacao_rh`, `ciclos_avaliacao` POST, `ciclos_avaliacao/{id}/status`, `{id}/avaliacoes`,
`{id}/atribuir`, `avaliacoes` POST e `contestacoes_avaliacao/{id}/revisar`.
"""

import html
import time
from datetime import date, timedelta

import streamlit as st

from api_client import (ApiError, atribuir_avaliacao, atribuir_avaliacoes_lote, avaliacoes_do_ciclo, ciclos_avaliacao_rh, competencias_avaliacao_rh,
                        criar_ciclo_avaliacao, criar_competencia_avaliacao, editar_competencia_avaliacao, mudar_status_ciclo_avaliacao,
                        revisar_contestacao)
from avaliacao_ciclo_modelo import (CATEGORIAS_COMPETENCIA, DESCRICAO_PADRAO, NIVEIS_COMPETENCIA, NOTA_COMPETENCIA, RELACOES, TEXTO_COMPETENCIAS,
                                    competencias_ordenadas, nivel_legivel, peso_legivel, validar_competencia, STATUS_AVALIACAO, acoes, andamento_departamentos, anos, confirmacao, contestacoes_do_ciclo,
                                    do_ano, em_foco, filtrar_avaliacoes, linha_contestacao, nota_legivel, pct_relacao, periodo, pode_atribuir, progresso,
                                    resumo_lote, situacao, situacao_avaliacao, validar_avulsa, validar_ciclo)
from campos import campo
from onboarding_modelo import data_br
from theme import alerta

_VALIDADE_CACHE_S = 20


def _guardado(chave: str, buscar):
    item = st.session_state.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = buscar()
    st.session_state[chave] = {"em": time.time(), "dados": dados}
    return dados


def dados_rh(token: str) -> dict:
    return _guardado("av360_cache_rh", lambda: ciclos_avaliacao_rh(token))


def _competencias(token: str) -> list[dict]:
    return _guardado("av360_cache_comp", lambda: competencias_avaliacao_rh(token)).get("competencias") or []


def _avaliacoes(token: str, ciclo_id: int) -> list[dict]:
    return _guardado(f"av360_cache_lista_{ciclo_id}", lambda: avaliacoes_do_ciclo(token, ciclo_id)).get("avaliacoes") or []


def _fechar() -> None:
    st.session_state.pop("av360_modal", None)


def _concluir(aviso: str) -> None:
    for chave in [k for k in st.session_state if str(k).startswith("av360_") and k not in ("av360_foco", "av360_ano")]:
        st.session_state.pop(chave, None)
    st.session_state.aviso_toast = aviso
    st.rerun()


def _abrir(tipo: str, alvo=None) -> None:
    st.session_state.av360_modal = (tipo, alvo)
    st.rerun()


# ---------------------------------------------------------------------------
# Modais
# ---------------------------------------------------------------------------
@st.dialog("Abrir ciclo de avaliação", width="medium", on_dismiss=_fechar)
def _modal_novo() -> None:
    hoje = date.today()
    nome = campo(st, "Nome", "texto", "av360_nome", max_chars=100, placeholder=f"Ex.: Ciclo {hoje.year}.2")
    c1, c2 = st.columns(2)
    inicio = c1.date_input("Início", value=hoje, format="DD/MM/YYYY", key="av360_inicio")
    fim = c2.date_input("Fim", value=hoje + timedelta(days=30), format="DD/MM/YYYY", key="av360_fim")
    auto = st.checkbox("Autoavaliação", value=True, key="av360_novo_auto")
    gestor = st.checkbox("Avaliação do gestor", value=True, key="av360_novo_gestor")
    st.html('<p class="crh-nota-neutra">Todos os colaboradores ativos entram no ciclo e recebem aviso no sino e por e-mail. '
            'Avaliações de pares e outras entram depois, em "Atribuir".</p>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="av360_novo_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Abrir ciclo", type="primary", key="av360_novo_ok"):
            erro = validar_ciclo(nome, inicio, fim, auto, gestor)
            if erro:
                alerta(slot, "erro", erro)
                return
            token = st.session_state.token
            try:
                criado = criar_ciclo_avaliacao(token, nome.strip(), DESCRICAO_PADRAO, inicio.isoformat(), fim.isoformat())
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            ciclo_id = (criado.get("ciclo") or {}).get("id")
            try:
                mudar_status_ciclo_avaliacao(token, ciclo_id, "em_andamento")
                r = atribuir_avaliacoes_lote(token, ciclo_id, None, auto, gestor)
            except ApiError as erro_api:
                st.session_state.av360_foco = ciclo_id
                _concluir(f"Ciclo criado, mas a abertura não terminou: {erro_api.message} Use \"Iniciar ciclo\" ou \"Atribuir\" na tabela.")
            st.session_state.av360_foco = ciclo_id
            _concluir(f"Ciclo aberto. {resumo_lote(r)}")


def _modal_competencia(atual: dict | None) -> None:
    """Figma F27, etapa 5 ("Nova competência"). Editar usa o mesmo modal, com "Salvar"."""
    chave = f"av360_comp_{atual['id'] if atual else 'nova'}"
    dados = atual or {}
    nome = campo(st, "Nome", "texto", f"{chave}_nome", max_chars=200, value=dados.get("nome") or "", placeholder="Ex.: Comunicação")
    descricao = campo(st, "Descrição", "texto", f"{chave}_desc", max_chars=1000, value=dados.get("descricao") or "",
                      placeholder="Ex.: Fala com clareza e escuta a equipe")
    c1, c2 = st.columns(2)
    categorias = list(CATEGORIAS_COMPETENCIA)
    categoria = c1.selectbox("Categoria", categorias, index=categorias.index(dados["categoria"]) if dados.get("categoria") in categorias else None,
                             format_func=CATEGORIAS_COMPETENCIA.get, placeholder="Escolha", key=f"{chave}_cat")
    nivel = c2.selectbox("Nível", NIVEIS_COMPETENCIA, index=NIVEIS_COMPETENCIA.index(dados["nivel"]) if dados.get("nivel") in NIVEIS_COMPETENCIA else None,
                         format_func=nivel_legivel, placeholder="Escolha", key=f"{chave}_nivel")
    c3, _ = st.columns(2)
    peso = c3.number_input("Peso", min_value=0.1, max_value=100.0, value=float(dados.get("peso") or 1), step=0.5, key=f"{chave}_peso")
    ativa = st.checkbox("Ativa (entra no formulário das avaliações)", value=bool(dados.get("ativo", True)), key=f"{chave}_ativa",
                        disabled=atual is None)
    st.html(f'<p class="crh-nota-neutra">{html.escape(NOTA_COMPETENCIA)}</p>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key=f"{chave}_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Salvar" if atual else "Cadastrar", type="primary", key=f"{chave}_ok"):
            erro = validar_competencia(nome, descricao, categoria, nivel, peso)
            if erro:
                alerta(slot, "erro", erro)
                return
            token = st.session_state.token
            try:
                if atual:
                    editar_competencia_avaliacao(token, atual["id"], nome.strip(), (descricao or "").strip(), categoria, nivel, peso, ativa)
                else:
                    criar_competencia_avaliacao(token, nome.strip(), (descricao or "").strip(), categoria, nivel, peso)
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            _concluir("Competência atualizada." if atual else "Competência cadastrada.")


@st.dialog("Nova competência", width="medium", on_dismiss=_fechar)
def _modal_competencia_nova() -> None:
    _modal_competencia(None)


@st.dialog("Editar competência", width="medium", on_dismiss=_fechar)
def _modal_competencia_editar(atual: dict) -> None:
    _modal_competencia(atual)


@st.dialog("Mudar a situação do ciclo", width="small", on_dismiss=_fechar)
def _modal_status(ciclo: dict, destino: str) -> None:
    st.html(f'<p><b>{html.escape(ciclo.get("nome") or "")}</b>: {html.escape(situacao(ciclo.get("status"))[0])} → '
            f'{html.escape(situacao(destino)[0])}.</p><p class="crh-meta">{html.escape(confirmacao(destino))}</p>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="av360_st_voltar"):
            _fechar()
            st.rerun()
        if st.button("Confirmar", type="primary", key="av360_st_ok"):
            try:
                r = mudar_status_ciclo_avaliacao(st.session_state.token, ciclo["id"], destino)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            canceladas = r.get("avaliacoes_canceladas") or 0
            _concluir(f"Ciclo: {situacao(destino)[0].lower()}." + (f" {canceladas} avaliações em aberto foram canceladas." if canceladas else ""))


@st.dialog("Atribuir avaliações", width="medium", on_dismiss=_fechar)
def _modal_atribuir(ciclo: dict, dados: dict) -> None:
    st.html(f'<p class="crh-meta">{html.escape(ciclo.get("nome") or "")} · {html.escape(periodo(ciclo))}</p>')
    modo = st.segmented_control("Como", ["Em lote", "Uma avaliação"], default="Em lote", required=True, key="av360_modo", label_visibility="collapsed")
    slot = st.empty()
    if modo == "Em lote":
        deps = {d["id"]: d.get("nome") for d in dados.get("departamentos") or []}
        dep = st.selectbox("Quem é avaliado", [0] + list(deps), format_func=lambda d: "Todos os departamentos" if d == 0 else deps[d], key="av360_lote_dep")
        auto = st.checkbox("Autoavaliação (cada pessoa avalia a si mesma)", value=True, key="av360_lote_auto")
        gestor = st.checkbox("Avaliação do gestor (o superior direto; sem ele, o gestor do departamento)", value=True, key="av360_lote_gestor")
        st.html('<p class="crh-meta">O que já foi atribuído neste ciclo é pulado. Cada avaliador recebe aviso no sino e por e-mail.</p>')
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Atribuir", type="primary", key="av360_lote_ok"):
                if not auto and not gestor:
                    alerta(slot, "erro", "Escolha pelo menos um tipo de avaliação.")
                    return
                try:
                    r = atribuir_avaliacoes_lote(st.session_state.token, ciclo["id"], dep or None, auto, gestor)
                except ApiError as erro:
                    alerta(slot, "erro", erro.message)
                    return
                _concluir(resumo_lote(r))
        return
    pessoas = {p["id"]: p for p in dados.get("pessoas") or []}
    nome = lambda i: (pessoas[i].get("nome") or "—") + ("" if pessoas[i].get("user_id") else " (sem conta)")
    avaliado = st.selectbox("Quem é avaliado", list(pessoas), index=None, format_func=nome, placeholder="Escolha a pessoa", key="av360_av_avaliado")
    avaliador = st.selectbox("Quem avalia", list(pessoas), index=None, format_func=nome, placeholder="Escolha a pessoa", key="av360_av_avaliador")
    relacao = st.selectbox("Relação", [r for r in RELACOES if r != "gestor"], index=None, format_func=RELACOES.get, placeholder="Escolha a relação",
                           key="av360_av_relacao", help="A avaliação do gestor é feita pelo lote, que acha o gestor de cada pessoa.")
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Atribuir", type="primary", key="av360_av_ok"):
            erro = validar_avulsa(pessoas.get(avaliado), pessoas.get(avaliador), relacao)
            if erro:
                alerta(slot, "erro", erro)
                return
            try:
                atribuir_avaliacao(st.session_state.token, ciclo["id"], avaliado, pessoas[avaliador]["user_id"], relacao, ciclo.get("data_inicio"), ciclo.get("data_fim"))
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            _concluir("Avaliação atribuída.")


@st.dialog("Avaliações do ciclo", width="large", on_dismiss=_fechar)
def _modal_avaliacoes(ciclo: dict) -> None:
    try:
        avaliacoes = _avaliacoes(st.session_state.token, ciclo["id"])
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    st.html(f'<p class="crh-meta">{html.escape(ciclo.get("nome") or "")} · {html.escape(progresso(ciclo))}</p>')
    deps = sorted({(a.get("departamento_id"), a.get("departamento")) for a in avaliacoes if a.get("departamento_id")}, key=lambda d: d[1] or "")
    nomes = dict(deps)
    with st.container(horizontal=True):
        status = st.selectbox("Situação", [None] + list(STATUS_AVALIACAO), format_func=lambda s: "Situação: Todas" if s is None else f"Situação: {STATUS_AVALIACAO[s][0]}",
                              key="av360_f_status", label_visibility="collapsed", width=220)
        dep = st.selectbox("Departamento", [None] + [d[0] for d in deps], format_func=lambda d: "Departamento: Todos" if d is None else f"Departamento: {nomes[d]}",
                           key="av360_f_dep", label_visibility="collapsed", width=240)
        busca = st.text_input("Busca", placeholder="⌕  Nome", key="av360_f_busca", label_visibility="collapsed", width=200)
    linhas = filtrar_avaliacoes(avaliacoes, status, dep, busca)
    if not linhas:
        st.html('<p class="crh-meta">Nenhuma avaliação neste filtro.</p>')
        return
    corpo = "".join(
        f'<tr><td>{html.escape(a.get("avaliado_nome") or "—")}<br><span class="crh-meta">{html.escape(a.get("departamento") or "")}</span></td>'
        f'<td>{html.escape(a.get("avaliador_nome") or "—")}</td><td>{html.escape(RELACOES.get(a.get("relacao_avaliador"), "—"))}</td>'
        f'<td><span class="crh-selo {situacao_avaliacao(a.get("status"))[1]}">{html.escape(situacao_avaliacao(a.get("status"))[0])}</span></td>'
        f'<td>{html.escape(nota_legivel(a.get("nota")))}</td><td>{html.escape(data_br(a.get("data_avaliacao")) if a.get("data_avaliacao") else "—")}</td></tr>'
        for a in linhas)
    st.html('<table class="crh-av360-tabela"><tr><th>Avaliado</th><th>Avaliador</th><th>Relação</th><th>Situação</th><th>Nota</th><th>Enviada em</th></tr>'
            f'{corpo}</table>')


@st.dialog("Responder contestação", width="medium", on_dismiss=_fechar)
def _modal_contestacao(c: dict) -> None:
    st.html(f'<p><b>{html.escape(c.get("avaliado_nome") or "—")}</b> contestou a avaliação de {html.escape(c.get("avaliador_nome") or "—")} '
            f'({html.escape(RELACOES.get(c.get("relacao_avaliador"), "—"))}, nota {html.escape(nota_legivel(c.get("nota")))}).</p>'
            f'<div class="crh-painel crh-bloco"><p class="crh-meta">Motivo</p><p>{html.escape(c.get("motivo") or "")}</p></div>')
    resposta = campo(st, "Resposta do RH", "texto", "av360_resposta", area=True, max_chars=2000, height=110,
                     placeholder="O que foi revisto e a decisão. A pessoa vê esta resposta.")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="av360_ct_voltar"):
            _fechar()
            st.rerun()
        if st.button("Enviar resposta", type="primary", key="av360_ct_ok"):
            if len((resposta or "").strip()) < 5:
                alerta(slot, "erro", "Escreva a resposta (pelo menos 5 caracteres).")
                return
            try:
                revisar_contestacao(st.session_state.token, c["id"], resposta.strip())
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _concluir("Contestação respondida.")


# ---------------------------------------------------------------------------
# Aba
# ---------------------------------------------------------------------------
def _barra(pct: int | None) -> str:
    if pct is None:
        return '<p class="crh-doc-prazo">—</p>'
    return f'<div class="crh-av360-barra"><div class="barra"><span style="width:{pct}%"></span></div><span class="v">{pct}%</span></div>'


def _tabela(ciclos: list[dict]) -> None:
    pesos = [2.4, 1.6, 1.6, 1.6, 1.1, 2.6]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Ciclo", "Período", "Autoavaliações", "Avaliações do gestor", "Situação", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not ciclos:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhum ciclo neste ano. Abra um em "Abrir novo ciclo".</p>')
        for i, c in enumerate(ciclos):
            with st.container(key=f"rh_lin_{i}"):
                col = st.columns(pesos, vertical_alignment="center")
                desc = f'<p class="d">{html.escape(c["descricao"])}</p>' if c.get("descricao") else ""
                col[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(c.get("nome") or "")}</p>{desc}</div>')
                col[1].html(f'<p class="crh-doc-prazo">{html.escape(periodo(c))}</p>')
                col[2].html(_barra(pct_relacao(c, "auto")))
                col[3].html(_barra(pct_relacao(c, "gestor")))
                selo, tom = situacao(c.get("status"))
                col[4].html(f'<span class="crh-selo {tom}">{html.escape(selo)}</span>', width="content")
                with col[5]:
                    with st.container(horizontal=True):
                        if pode_atribuir(c) and st.button("Atribuir", type="tertiary", key=f"av360_atr_{c['id']}"):
                            _abrir("atribuir", c["id"])
                        if (c.get("contagens") or {}).get("total") and st.button("Ver avaliações", type="tertiary", key=f"av360_ver_{c['id']}"):
                            st.session_state.av360_foco = c["id"]
                            _abrir("avaliacoes", c["id"])
                        for destino, rotulo in acoes(c.get("status")):
                            if st.button(rotulo, type="tertiary", key=f"av360_st_{c['id']}_{destino}"):
                                _abrir("status", (c["id"], destino))


def _cartoes(token: str, foco: dict | None, contestacoes: list[dict]) -> None:
    esquerda, direita = st.columns(2, gap="medium")
    with esquerda:
        with st.container(key="cfg_card_av360_contest"):
            titulo = f'Contestações do ciclo {foco.get("nome")}' if foco else "Contestações"
            st.html(f'<p class="crh-cfg-titulo">{html.escape(titulo)}</p>')
            do_ciclo = contestacoes_do_ciclo(contestacoes, foco["id"]) if foco else []
            if not do_ciclo:
                st.html('<p class="crh-meta">Nenhuma contestação esperando resposta.</p>')
            for c in do_ciclo:
                quem, quando = linha_contestacao(c)
                with st.container(horizontal=True, vertical_alignment="center", key=f"av360_ct_lin_{c['id']}"):
                    st.html(f'<div class="crh-pc-item"><p class="t">{html.escape(quem)}</p><p class="d">{html.escape(quando)} · '
                            f'{html.escape(RELACOES.get(c.get("relacao_avaliador"), "—"))}, nota {html.escape(nota_legivel(c.get("nota")))}</p>'
                            '<span class="crh-selo amb">Aguardando resposta</span></div>')
                    if st.button("Responder", type="tertiary", key=f"av360_ct_{c['id']}"):
                        _abrir("contestacao", c["id"])
    with direita:
        with st.container(key="cfg_card_av360_dep"):
            st.html('<p class="crh-cfg-titulo">Andamento por departamento</p>')
            linhas = []
            if foco and (foco.get("contagens") or {}).get("total"):
                try:
                    linhas = andamento_departamentos(_avaliacoes(token, foco["id"]))
                except ApiError as erro:
                    alerta(st.empty(), "erro", erro.message)
                    return
            if not linhas:
                st.html('<p class="crh-meta">Sem avaliações atribuídas neste ciclo.</p>')
                return
            st.html("".join(f'<div class="crh-pcr-barra"><div class="r"><span>{html.escape(nome)}</span><span>{pct}%</span></div>'
                            f'<div class="barra"><span style="width:{pct}%"></span></div></div>' for nome, pct in linhas))


def _secao_competencias(token: str) -> None:
    """Figma F27, etapa 4: a tabela de competências, com "Nova competência" e "Editar" em cada linha."""
    st.html(f'<p class="crh-cfg-titulo">Competências avaliadas</p><p class="crh-meta">{html.escape(TEXTO_COMPETENCIAS)}</p>')
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Nova competência", type="primary", key="av360_comp_novo"):
            _abrir("competencia", None)
    try:
        competencias = competencias_ordenadas(_competencias(token))
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    pesos = [3.2, 1.6, 0.8, 0.8, 1.1, 1.0]
    with st.container(key="rh_tabela_comp"):
        with st.container(key="rh_cab_comp"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Competência", "Categoria", "Nível", "Peso", "Situação", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not competencias:
            with st.container(key="rh_lin_comp_vazio"):
                st.html('<p class="crh-meta">Nenhuma competência cadastrada: as avaliações ficam sem formulário. Cadastre em "Nova competência".</p>')
        for c in competencias:
            with st.container(key=f"rh_lin_comp_{c['id']}"):
                col = st.columns(pesos, vertical_alignment="center")
                desc = f'<p class="d">{html.escape(c["descricao"])}</p>' if c.get("descricao") else ""
                col[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(c.get("nome") or "")}</p>{desc}</div>')
                col[1].html(f'<p class="crh-doc-prazo">{html.escape(CATEGORIAS_COMPETENCIA.get(c.get("categoria"), "—"))}</p>')
                col[2].html(f'<p class="crh-doc-prazo">{html.escape(nivel_legivel(c.get("nivel")))}</p>')
                col[3].html(f'<p class="crh-doc-prazo">{html.escape(peso_legivel(c.get("peso")))}</p>')
                selo, tom = ("Ativa", "azul") if c.get("ativo", True) else ("Inativa", "neu")
                col[4].html(f'<span class="crh-selo {tom}">{selo}</span>', width="content")
                if col[5].button("Editar", type="tertiary", key=f"av360_comp_ed_{c['id']}"):
                    _abrir("competencia", c["id"])


def aba_desempenho(token: str) -> None:
    dados = dados_rh(token)
    ciclos = dados.get("ciclos") or []
    opcoes = anos(ciclos)
    with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
        if opcoes:
            ano_escolhido = st.selectbox("Ano", opcoes, format_func=lambda a: f"Ano: {a}", key="av360_ano", label_visibility="collapsed", width=140)
        else:
            ano_escolhido = None
        if st.button("Abrir novo ciclo", type="primary", key="av360_novo"):
            _abrir("novo")
    do_periodo = do_ano(ciclos, ano_escolhido) + [c for c in ciclos if ano_escolhido is not None and c.get("data_inicio") is None and c.get("data_fim") is None]
    _tabela(do_periodo)
    _cartoes(token, em_foco(do_periodo, st.session_state.get("av360_foco")), dados.get("contestacoes") or [])
    _secao_competencias(token)


def abrir_modal(token: str) -> bool:
    """Abre o modal pedido, se houver. Devolve True quando havia um modal desta aba."""
    modal = st.session_state.get("av360_modal")
    if not modal:
        return False
    tipo, alvo = modal
    if tipo == "competencia":
        if alvo is None:
            _modal_competencia_nova()
            return True
        try:
            atual = next((c for c in _competencias(token) if c["id"] == alvo), None)
        except ApiError:
            atual = None
        if atual:
            _modal_competencia_editar(atual)
        else:
            _fechar()
        return True
    dados = dados_rh(token)
    ciclos = {c["id"]: c for c in dados.get("ciclos") or []}
    if tipo == "novo":
        _modal_novo()
    elif tipo == "status" and alvo[0] in ciclos:
        _modal_status(ciclos[alvo[0]], alvo[1])
    elif tipo == "atribuir" and alvo in ciclos:
        _modal_atribuir(ciclos[alvo], dados)
    elif tipo == "avaliacoes" and alvo in ciclos:
        _modal_avaliacoes(ciclos[alvo])
    elif tipo == "contestacao":
        c = next((x for x in dados.get("contestacoes") or [] if x["id"] == alvo), None)
        _modal_contestacao(c) if c else _fechar()
    else:
        _fechar()
    return True
