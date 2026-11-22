"""
Página "Metas da equipe". Para o Gestor, no alto, o F16 (Figma 248:1405; change concluir-metas-pdi-equipe, D1 a D5): as metas,
o PDI e as reuniões 1:1 dos liderados diretos, com "Nova meta", "Check-in", "Nova ação de PDI", "Registrar reunião 1:1" e
"Atualizar" (realizada ou cancelada). Endpoints: `minha_equipe/metas_pdi`, `metas` POST, `metas/{id}/checkin`, `pdi` POST,
`reunioes_individuais` POST e `reunioes_individuais/{id}/situacao`. Abaixo, separado, o ciclo anual de metas e feedback.
O ciclo anual (change ciclo-de-metas, D4 e D5) fica no grupo Equipe do menu: para o Gestor e para quem é
superior direto de alguém. Lista o ciclo de metas da equipe (quem enviou cada etapa) e abre o formulário de cada
pessoa, com as respostas e a caixa de feedback de cada etapa enviada, onde o superior direto ou o gestor do
departamento registra o feedback. O modal do formulário também serve à tela do RH ("Ciclos de avaliação").

Endpoints: `meu_ciclo_metas` (os ciclos), `formularios_meta`, `formularios_meta/{id}` e `formularios_meta/{id}/feedback`.
"""

import html
from datetime import date

import streamlit as st

from api_client import (ApiError, checkin_meta, criar_meta, criar_pdi, feedback_meta, formulario_meta, formularios_meta, metas_pdi_equipe,
                        registrar_reuniao, situacao_reuniao)
from ciclo_metas_modelo import enviadas_do, linhas_pessoas, perguntas_do_formulario, situacao_ciclo, validar_feedback
from formulario_metas_ui import etapa_leitura, tabela_pessoas, trilha_etapas
from metas_equipe_dados import consultar, garantir_sessao, invalidar_formulario
from pagina_metas_ciclo import carregar as carregar_meus_ciclos
from metas_equipe_modelo import (PROGRESSOS, fora_da_tela, hoje_brasilia, linhas_metas, linhas_pdi, pessoas_para_meta, reunioes, validar_checkin, validar_meta, validar_pdi,
                                 validar_reuniao, validar_situacao)
from theme import alerta, html_linha_onboarding, render_barra_progresso, render_hero, render_titulo_cartao, render_topbar


def pessoas_do_ciclo(token: str, ciclo_id: int) -> dict:
    return consultar(token, f"mf_lista_{ciclo_id}", lambda: formularios_meta(token, ciclo_id))


def fechar_formulario() -> None:
    st.session_state.pop("mf_aberto", None)


@st.dialog("Formulário de metas", width="large", on_dismiss=fechar_formulario)
def modal_formulario(formulario_id: int) -> None:
    """As três etapas com as respostas e o feedback; quem pode, registra feedback em cada etapa enviada."""
    token = st.session_state.token
    try:
        dados = consultar(token, f"mf_{formulario_id}", lambda: formulario_meta(token, formulario_id))
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    form = dados.get("formulario") or {}
    ciclo = dict(dados.get("ciclo") or {}, etapa_aberta=None, respostas=dados.get("respostas") or [])
    hoje = date.fromisoformat(str(dados.get("hoje") or date.today())[:10])
    enviadas = enviadas_do(form)
    perguntas = perguntas_do_formulario(ciclo, [])
    st.html(f'<div class="crh-cm-cab"><div><p class="t">{html.escape(dados.get("colaborador_nome") or "—")}</p>'
            f'<p class="s">{html.escape(dados.get("departamento") or "Sem departamento")} · Ciclo {html.escape(str(ciclo.get("ano")))}</p></div></div>')
    trilha_etapas(ciclo, hoje, enviadas)
    for n in (1, 2, 3):
        etapa_leitura(ciclo, n, perguntas, enviadas, dados.get("feedbacks"), hoje)
        if dados.get("pode_dar_feedback") and enviadas.get(n):
            texto = st.text_area(f"Seu feedback na etapa {n}", max_chars=2000, height=80, key=f"mf_{formulario_id}_fb{n}",
                                 help="Fica registrado na caixa da etapa, visível para a pessoa, para você e para o RH. Não dá para editar depois.")
            slot = st.empty()
            with st.container(horizontal=True, horizontal_alignment="right"):
                if st.button(f"Registrar feedback da etapa {n}", type="primary", key=f"mf_{formulario_id}_fb{n}_ok"):
                    erro_campo = validar_feedback(texto)
                    if erro_campo:
                        alerta(slot, "erro", erro_campo)
                        return
                    try:
                        feedback_meta(token, formulario_id, n, texto.strip())
                    except ApiError as erro:
                        alerta(slot, "erro", erro.message)
                        return
                    invalidar_formulario(formulario_id)
                    st.session_state.pop(f"mf_{formulario_id}_fb{n}", None)
                    st.toast(f"Feedback da etapa {n} registrado. A pessoa foi avisada.")
                    st.rerun()


def _hoje() -> date:
    return hoje_brasilia()


def _dados_f16(token: str) -> dict:
    return consultar(token, "mp_dados", lambda: metas_pdi_equipe(token))


def _depois_de_gravar(aviso: str) -> None:
    st.session_state.pop("mp_dados", None)
    for chave in [k for k in st.session_state if str(k).startswith("mp_modal")]:
        st.session_state.pop(chave, None)
    st.session_state.aviso_toast = aviso
    st.rerun()


def _fechar_modal() -> None:
    for chave in [k for k in st.session_state if str(k).startswith(("mp_modal", "mp_m_"))]:
        st.session_state.pop(chave, None)


def _ciclo(dados: dict, chave: str):
    """O ciclo em andamento: escolhido quando há mais de um; None quando não há nenhum."""
    ciclos = {c["id"]: c.get("nome") or f"Ciclo {c['id']}" for c in dados.get("ciclos") or [] if c.get("id") is not None}
    if not ciclos:
        st.html('<p class="crh-meta">Não há ciclo de avaliação em andamento. Peça ao RH para abrir um.</p>')
        return None
    if len(ciclos) == 1:
        return next(iter(ciclos))
    return st.selectbox("Ciclo de avaliação", list(ciclos), format_func=ciclos.get, key=chave)


def _botoes_modal(chave_ok: str, rotulo_ok: str) -> bool:
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key=f"{chave_ok}_cancelar"):
            _fechar_modal()
            st.rerun()
        return st.button(rotulo_ok, type="primary", key=chave_ok)


@st.dialog("Nova meta", width="medium", on_dismiss=_fechar_modal)
def _modal_nova_meta(token: str, dados: dict) -> None:
    pessoas = {p["id"]: p["nome"] for p in pessoas_para_meta(dados)}
    pessoa = st.selectbox("Pessoa", list(pessoas), format_func=pessoas.get, index=None, placeholder="Escolha", key="mp_m_meta_pessoa")
    ciclo = _ciclo(dados, "mp_m_meta_ciclo")
    titulo = st.text_area("Meta", key="mp_m_meta_titulo", max_chars=500, height=80, placeholder="O que a pessoa vai alcançar")
    prazo = st.date_input("Prazo", value=None, min_value=_hoje(), format="DD/MM/YYYY", key="mp_m_meta_prazo")
    como = st.text_area("Como medir", key="mp_m_meta_como", max_chars=300, height=70, placeholder="O indicador e onde ele é acompanhado")
    st.html('<p class="crh-meta">A pessoa recebe um aviso no sino e por e-mail.</p>')
    if quem := fora_da_tela(dados, pessoa):
        st.html(f'<p class="crh-meta">{html.escape(quem)} é do seu departamento, mas não é liderado direto: a meta fica registrada e '
                'aparece na Trajetória da pessoa, não nesta tela.</p>')
    slot = st.empty()
    if _botoes_modal("mp_m_meta_ok", "Criar meta"):
        if erro := validar_meta(pessoa, ciclo, titulo, como, prazo, _hoje()):
            alerta(slot, "erro", erro)
            return
        try:
            criar_meta(token, {"colaborador_id": int(pessoa), "ciclo_avaliacao_id": int(ciclo), "titulo": titulo.strip(), "descricao": titulo.strip(),
                               "indicador": como.strip(), "peso": 1, "data_prazo": prazo.isoformat()})
        except ApiError as erro_api:
            alerta(slot, "erro", erro_api.message)
            return
        _depois_de_gravar("Meta criada.")


@st.dialog("Check-in da meta", width="medium", on_dismiss=_fechar_modal)
def _modal_checkin(token: str, linha: dict) -> None:
    st.html(f'<div class="crh-pcr-kv"><span>Meta</span><b>{html.escape(linha["titulo"])}</b></div>'
            f'<div class="crh-pcr-kv"><span>Pessoa</span><b>{html.escape(linha["pessoa"])}</b></div>'
            f'<div class="crh-pcr-kv"><span>Progresso atual</span><b class="ambar">{linha["progresso"]}%</b></div>')
    progresso = st.selectbox("Novo progresso", PROGRESSOS, index=min(len(PROGRESSOS) - 1, linha["progresso"] // 5), format_func=lambda v: f"{v}%",
                             key="mp_m_ck_pct")
    comentario = st.text_area("O que foi combinado", key="mp_m_ck_texto", max_chars=2000, height=90)
    st.html('<p class="crh-meta">O check-in fica registrado em seu nome, e a pessoa vê o progresso na Trajetória.</p>')
    slot = st.empty()
    if _botoes_modal("mp_m_ck_ok", "Salvar check-in"):
        if erro := validar_checkin(progresso, comentario):
            alerta(slot, "erro", erro)
            return
        try:
            checkin_meta(token, linha["id"], progresso, (comentario or "").strip() or None, None, None)
        except ApiError as erro_api:
            alerta(slot, "erro", erro_api.message)
            return
        _depois_de_gravar("Check-in registrado.")


@st.dialog("Nova ação de PDI", width="medium", on_dismiss=_fechar_modal)
def _modal_pdi(token: str, dados: dict) -> None:
    pessoas = {p["id"]: p["nome"] for p in pessoas_para_meta(dados)}
    usuarios = {p.get("id"): p.get("user_id") for p in list(dados.get("pessoas_meta") or []) + list(dados.get("liderados") or [])}
    pessoa = st.selectbox("Pessoa", list(pessoas), format_func=pessoas.get, index=None, placeholder="Escolha", key="mp_m_pdi_pessoa")
    ciclo = _ciclo(dados, "mp_m_pdi_ciclo")
    titulo = st.text_input("Título", key="mp_m_pdi_titulo", max_chars=150, placeholder="Ex.: Curso de liderança técnica")
    acao = st.text_area("Ação de desenvolvimento", key="mp_m_pdi_acao", max_chars=2000, height=80)
    prazo = st.date_input("Prazo (opcional)", value=None, min_value=_hoje(), format="DD/MM/YYYY", key="mp_m_pdi_prazo")
    st.html('<p class="crh-meta">A pessoa recebe um aviso no sino e acompanha o PDI na Trajetória.</p>')
    if quem := fora_da_tela(dados, pessoa):
        st.html(f'<p class="crh-meta">{html.escape(quem)} não é liderado direto: a ação aparece na Trajetória da pessoa, não nesta tela.</p>')
    slot = st.empty()
    if _botoes_modal("mp_m_pdi_ok", "Criar ação"):
        if erro := validar_pdi(pessoa, ciclo, titulo, acao, prazo, _hoje()):
            alerta(slot, "erro", erro)
            return
        # A própria pessoa é a responsável pela ação; sem conta de acesso, quem cria fica responsável.
        responsavel = usuarios.get(pessoa) or dados.get("meu_user_id")
        try:
            criar_pdi(token, {"colaborador_id": int(pessoa), "ciclo_avaliacao_id": int(ciclo), "titulo": titulo.strip(), "descricao": acao.strip(),
                              "acao_desenvolvimento": acao.strip(), "responsavel_user_id": int(responsavel),
                              "data_prazo": prazo.isoformat() if prazo else None})
        except ApiError as erro_api:
            alerta(slot, "erro", erro_api.message)
            return
        _depois_de_gravar("Ação de PDI criada.")


@st.dialog("Agendar reunião 1:1", width="medium", on_dismiss=_fechar_modal)
def _modal_reuniao(token: str, dados: dict) -> None:
    pessoas = {p["id"]: p.get("nome") or "—" for p in dados.get("liderados") or []}
    pessoa = st.selectbox("Pessoa", list(pessoas), format_func=pessoas.get, index=None, placeholder="Escolha", key="mp_m_r_pessoa")
    c1, c2 = st.columns(2)
    dia = c1.date_input("Data", value=None, min_value=_hoje(), format="DD/MM/YYYY", key="mp_m_r_data")
    hora = c2.time_input("Hora", value=None, step=900, key="mp_m_r_hora")
    pauta = st.text_area("Pauta", key="mp_m_r_pauta", max_chars=2000, height=90, placeholder="O que vocês vão conversar")
    st.html('<p class="crh-meta">A pessoa recebe um aviso no sino e por e-mail. A reunião fica só entre vocês dois.</p>')
    slot = st.empty()
    if _botoes_modal("mp_m_r_ok", "Agendar"):
        texto_hora = hora.strftime("%H:%M") if hora else None
        if erro := validar_reuniao(pessoa, dia, texto_hora, pauta, _hoje()):
            alerta(slot, "erro", erro)
            return
        try:
            registrar_reuniao(token, {"colaborador_id": int(pessoa), "data_reuniao": dia.isoformat(), "hora": texto_hora, "assuntos": pauta.strip(),
                                      "situacao": "agendada"})
        except ApiError as erro_api:
            alerta(slot, "erro", erro_api.message)
            return
        _depois_de_gravar("Reunião agendada.")


@st.dialog("Reunião 1:1", width="medium", on_dismiss=_fechar_modal)
def _modal_situacao(token: str, linha: dict) -> None:
    st.html(f'<p class="crh-cfg-titulo">{html.escape(linha["pessoa"])}</p><p class="crh-meta">{html.escape(linha["detalhe"])}</p>')
    situacao = st.radio("O que aconteceu", ["realizada", "cancelada"], horizontal=True, key="mp_m_s_situacao",
                        format_func=lambda s: "Foi realizada" if s == "realizada" else "Foi cancelada")
    if situacao == "realizada":
        texto = st.text_area("Anotações (opcional)", key="mp_m_s_notas", max_chars=2000, height=90, placeholder="O que foi combinado")
        st.html('<p class="crh-meta">A pessoa recebe um aviso no sino.</p>')
    else:
        texto = st.text_area("Motivo (opcional)", key="mp_m_s_motivo", max_chars=500, height=70)
        st.html('<p class="crh-meta">A pessoa recebe um aviso no sino e por e-mail.</p>')
    slot = st.empty()
    if _botoes_modal("mp_m_s_ok", "Salvar"):
        if erro := validar_situacao(situacao, texto):
            alerta(slot, "erro", erro)
            return
        try:
            situacao_reuniao(token, linha["id"], situacao, acordos=(texto or "").strip() if situacao == "realizada" else None,
                             motivo=(texto or "").strip() if situacao == "cancelada" else None)
        except ApiError as erro_api:
            alerta(slot, "erro", erro_api.message)
            return
        _depois_de_gravar("Reunião marcada como realizada." if situacao == "realizada" else "Reunião cancelada.")


def _tabela_metas(linhas: list[dict]) -> None:
    pesos = [3, 2, 1.3, 1.8, 1.4, 1]
    with st.container(key="rh_tabela_comp"):
        with st.container(key="rh_cab_mp"):
            for coluna, titulo in zip(st.columns(pesos, vertical_alignment="center"), ("Meta", "Pessoa", "Prazo", "Progresso", "Situação", "")):
                coluna.html(f'<p class="crh-doc-cab">{titulo}</p>' if titulo else '<span class="crh-sr">Ação</span>')
        if not linhas:
            st.html('<p class="crh-meta" style="padding:12px 16px">Nenhuma meta aberta para os seus liderados diretos. Use "Nova meta" para criar.</p>')
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_linf_mp_{i}" if l["situacao"] == "Atrasada" else f"rh_lin_mp_{i}"):
                col = st.columns(pesos, vertical_alignment="center")
                col[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["titulo"])}</p><p class="d">{html.escape(l["detalhe"])}</p></div>')
                col[1].html(f'<p class="crh-doc-prazo">{html.escape(l["pessoa"])}</p>')
                col[2].html(f'<p class="crh-doc-prazo">{html.escape(l["prazo"])}</p>')
                col[3].html(f'<div class="crh-barra"><div class="topo"><span class="crh-sr">Progresso</span><span>{l["progresso"]}%</span></div>'
                            f'<div class="trilho"><div class="preenchido" style="width:{l["progresso"]}%"></div></div></div>')
                col[4].html(f'<span class="crh-selo {l["tom"]}">{html.escape(l["situacao"])}</span>')
                with col[5]:
                    if l["aberta"] and st.button("Check-in", type="tertiary", key=f"mp_checkin_{l['id']}", help=f"Registrar o andamento de {l['pessoa']}"):
                        st.session_state.mp_modal = ("checkin", l)
                        st.rerun()


def _cartao_reunioes(grupo: dict, completo: bool) -> None:
    with st.container(border=True, key="cfg_card_mp_reunioes"):
        render_titulo_cartao("Reuniões 1:1" if completo else "Próximas reuniões 1:1")
        if not grupo["proximas"]:
            st.html('<p class="crh-meta">Nenhuma reunião agendada.</p>')
        for r in grupo["proximas"]:
            with st.container(horizontal=True, vertical_alignment="center", key=f"mp_r_{r['id']}"):
                selo = "Data passou" if r["atrasada"] else r["situacao"]
                st.html(f'<div class="crh-mp-item">{html_linha_onboarding(r["pessoa"], r["detalhe"], selo, "amb" if r["atrasada"] else r["tom"])}</div>')
                if completo and st.button("Atualizar", type="tertiary", key=f"mp_r_sit_{r['id']}", help="Marcar como realizada ou cancelada"):
                    st.session_state.mp_modal = ("situacao", r)
                    st.rerun()
        if completo and grupo["historico"]:
            st.html('<p class="crh-cfg-titulo" style="margin-top:12px;font-size:15px">Anteriores</p>' + "".join(
                f'<div class="crh-mp-item">{html_linha_onboarding(r["pessoa"], r["detalhe"], r["situacao"], r["tom"])}</div>'
                for r in grupo["historico"][:20]))
        if st.button("Registrar reunião 1:1", key="mp_reuniao"):
            st.session_state.mp_modal = ("reuniao", None)
            st.rerun()


def _cartao_pdi(linhas: list[dict], completo: bool) -> None:
    with st.container(border=True, key="cfg_card_mp_pdi"):
        render_titulo_cartao("PDI da equipe")
        if not linhas:
            st.html('<p class="crh-meta">Nenhuma ação de PDI aberta para os seus liderados diretos.</p>')
        for l in linhas:
            render_barra_progresso(l["rotulo"] + (f" · até {l['prazo']}" if completo and l["prazo"] != "—" else ""), l["progresso"])
        if completo and st.button("Nova ação de PDI", key="mp_pdi_nova"):
            st.session_state.mp_modal = ("pdi", None)
            st.rerun()


def _f16(token: str) -> None:
    """Metas, PDI e reuniões 1:1 dos liderados diretos (F16; decisões D1 a D5)."""
    try:
        with st.spinner("Carregando..."):
            dados = _dados_f16(token)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    hoje = _hoje()
    liderados = {p["id"]: p.get("nome") or "—" for p in dados.get("liderados") or [] if p.get("id") is not None}
    pode_meta = bool(pessoas_para_meta(dados))
    if not liderados and not pode_meta:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">Você ainda não tem liderados diretos no cadastro. '
                'Quando o RH indicar você como superior de alguém, as metas, o PDI e as reuniões 1:1 dessa pessoa aparecem aqui.</p></div>')
        return
    st.session_state.setdefault("mp_aba", "Metas")
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Metas, PDI e reuniões 1:1", ["Metas", "PDI", "Reuniões 1:1"], required=True, key="mp_aba",
                                       label_visibility="collapsed")
        st.space("stretch")
        # 0 = todos (um valor fixo, para o campo não mostrar o "x" de limpar).
        escolha = st.selectbox("Pessoa", [0] + list(liderados), key="mp_pessoa", width=220, label_visibility="collapsed",
                               format_func=lambda i: "Pessoa: Todos" if i == 0 else f"Pessoa: {liderados[i]}")
        pessoa = escolha or None
        sem_ciclo = not dados.get("ciclos")
        if st.button("Nova meta", type="primary", key="mp_nova", disabled=not pode_meta or sem_ciclo,
                     help="Não há ciclo de avaliação em andamento. Peça ao RH para abrir um." if sem_ciclo else None):
            st.session_state.mp_modal = ("meta", None)
            st.rerun()
    grupo = reunioes(dados, hoje, pessoa)
    pdi = linhas_pdi(dados, pessoa)
    if aba == "Metas":
        _tabela_metas(linhas_metas(dados, hoje, pessoa))
        esquerda, direita = st.columns(2, gap="medium")
        with esquerda:
            _cartao_reunioes({"proximas": grupo["proximas"][:3], "historico": []}, completo=False)
        with direita:
            _cartao_pdi(pdi, completo=False)
    elif aba == "PDI":
        _cartao_pdi(pdi, completo=True)
    else:
        _cartao_reunioes(grupo, completo=True)
    modal = st.session_state.get("mp_modal")
    if modal:
        tipo, item = modal
        {"meta": lambda: _modal_nova_meta(token, dados), "checkin": lambda: _modal_checkin(token, item), "pdi": lambda: _modal_pdi(token, dados),
         "reuniao": lambda: _modal_reuniao(token, dados), "situacao": lambda: _modal_situacao(token, item)}[tipo]()


def _ciclo_anual(token: str) -> None:
    st.html('<p class="crh-bloco-titulo">Ciclo anual de metas e feedback</p>'
            '<p class="crh-meta">Acompanhe as três etapas do ciclo anual e registre seu feedback. '
            'Este formulário é independente das metas percentuais, PDI e reuniões 1:1.</p>')
    with st.spinner("Carregando..."):
        try:
            meus = carregar_meus_ciclos(token)
        except ApiError as erro:
            alerta(st.empty(), "erro", erro.message)
            return
    ciclos = meus.get("ciclos") or []
    if not ciclos:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">O RH ainda não abriu um ciclo de metas.</p></div>')
        return
    hoje = date.fromisoformat(str(meus.get("hoje") or date.today())[:10])
    por_id = {c["id"]: c for c in ciclos}
    with st.container(horizontal=True, vertical_alignment="center"):
        ciclo_id = st.selectbox("Ciclo", list(por_id), format_func=lambda i: f"Ciclo {por_id[i].get('ano')} — {situacao_ciclo(por_id[i], hoje)[0]}",
                                key="me_ciclo", label_visibility="collapsed", width=320)
        busca = st.text_input("Busca", placeholder="⌕  Nome", key="me_busca", label_visibility="collapsed", width=240)
    try:
        lista = pessoas_do_ciclo(token, ciclo_id)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    escolhido = tabela_pessoas(linhas_pessoas(lista.get("pessoas"), lista.get("ciclo") or por_id[ciclo_id], hoje, busca=busca), "me",
                               "Ninguém da sua equipe neste ciclo.")
    if escolhido:
        st.session_state.mf_aberto = escolhido
        st.rerun()
    if st.session_state.get("mf_aberto"):
        modal_formulario(st.session_state.mf_aberto)


def pagina_metas_equipe() -> None:
    token = st.session_state.token
    garantir_sessao(token)
    render_topbar(st.session_state.usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    gestor = str(st.session_state.usuario.get("perfil") or "").strip().upper() == "GESTOR"
    if gestor:
        render_hero("Metas e PDI da equipe", "Metas, check-ins, reuniões 1:1 e plano de desenvolvimento dos liderados")
        _f16(token)
        st.divider()
    else:
        render_hero("Metas da equipe", "Acompanhe o ciclo de metas da sua equipe e deixe o seu feedback em cada etapa")
    _ciclo_anual(token)
