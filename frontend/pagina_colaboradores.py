"""
Página "Colaboradores" do RH e do Admin (Figma 243:580; modal 243:1075 "Admitir colaborador"; parte da
tarefa 53 da change concluir-frontend-streamlit).

Lista com busca e filtros, a ficha da pessoa e o caminho de cadastro de um novo funcionário:
"Admitir colaborador" (só o RH; `colaboradores` POST) e, em seguida, "Criar acesso" (`usuarios` POST),
que manda a senha temporária por e-mail. O modal "Criar acesso / Novo usuário" (246:1245) também é usado
na tela Usuários e perfis. Endpoints: `colaboradores`, `organograma` e `usuarios`.
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import ApiError, admitir_colaborador, colaboradores, criar_usuario, organograma, trocar_perfil, usuarios
from cadastro_modelo import (
    CONTRATOS,
    NIVEIS,
    PERFIS,
    SITUACOES_COLAB,
    corpo_admissao,
    ficha,
    fichas_sem_conta,
    linhas_colaboradores,
    perfil,
    resumo_colaboradores,
    senha_temporaria,
    validar_admissao,
    validar_novo_usuario,
)
from theme import alerta, render_hero, render_topbar

CACHE = "cadastro_cache"
_VALIDADE_CACHE_S = 20


def carregar(token: str) -> dict:
    """{'colaboradores', 'organograma', 'usuarios'} por 20 s. Erro de `colaboradores` sobe; sem organograma
    ou sem a lista de usuários a tela segue com o que tem."""
    cache = st.session_state.get(CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = {"colaboradores": colaboradores(token).get("colaboradores") or []}
    for chave, funcao, campo in (("organograma", organograma, None), ("usuarios", usuarios, "usuarios")):
        try:
            resposta = funcao(token)
            dados[chave] = (resposta.get(campo) or []) if campo else resposta
        except ApiError:
            dados[chave] = [] if campo else {}
    st.session_state[CACHE] = {"em": time.time(), "dados": dados}
    return dados


def fechar() -> None:
    st.session_state.pop("modal_cadastro", None)


def concluir(aviso: str) -> None:
    st.session_state.pop(CACHE, None)
    fechar()
    st.session_state.aviso_toast = aviso
    st.rerun()


# ---------------------------------------------------------------------------
# Modais
# ---------------------------------------------------------------------------
@st.dialog("Admitir colaborador", width="medium", on_dismiss=fechar)
def _modal_admitir(org: dict) -> None:
    deps = {d.get("id"): d.get("nome") for d in org.get("departamentos") or [] if d.get("ativo", True)}
    cargos = {c.get("id"): c.get("nome") for c in org.get("cargos") or [] if c.get("ativo", True)}
    hoje = date.today()
    dados = {"nome": st.text_input("Nome completo", max_chars=100, key="adm_nome")}
    c1, c2 = st.columns(2)
    dados["cpf"] = c1.text_input("CPF", max_chars=14, placeholder="000.000.000-00", key="adm_cpf")
    dados["data_nascimento"] = c2.date_input("Nascimento", value=None, min_value=date(1940, 1, 1), max_value=hoje, format="DD/MM/YYYY", key="adm_nasc")
    dados["email_pessoal"] = st.text_input("E-mail pessoal", max_chars=120, key="adm_email")
    c1, c2 = st.columns(2)
    dados["telefone"] = c1.text_input("Telefone", max_chars=20, key="adm_tel")
    dados["bairro"] = c2.text_input("Bairro", max_chars=100, key="adm_bairro")
    c1, c2 = st.columns(2)
    dados["departamento_id"] = c1.selectbox("Departamento", sorted(deps, key=deps.get), index=None, format_func=deps.get, placeholder="Escolha", key="adm_dep")
    dados["cargo_id"] = c2.selectbox("Cargo", sorted(cargos, key=cargos.get), index=None, format_func=cargos.get, placeholder="Escolha", key="adm_cargo")
    c1, c2 = st.columns(2)
    dados["tipo_contrato"] = c1.selectbox("Contrato", list(CONTRATOS), format_func=CONTRATOS.get, key="adm_contrato")
    dados["data_admissao"] = c2.date_input("Admissão", value=hoje, format="DD/MM/YYYY", key="adm_admissao")
    c1, c2 = st.columns(2)
    dados["logradouro"] = c1.text_input("Logradouro", max_chars=150, key="adm_logradouro")
    dados["numero"] = c2.text_input("Número", max_chars=20, key="adm_numero")
    c1, c2 = st.columns(2)
    dados["nivel"] = c1.selectbox("Nível", list(NIVEIS), format_func=NIVEIS.get, key="adm_nivel")
    dados["carga_horaria_semanal"] = c2.number_input("Carga horária semanal", min_value=1.0, max_value=60.0, value=44.0, step=1.0, key="adm_carga")
    dados["salario"] = st.number_input("Salário (R$, só o RH vê)", min_value=0.0, value=None, step=100.0, format="%.2f", key="adm_salario")
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">Depois de admitir, crie o acesso: a pessoa recebe por e-mail uma senha temporária e começa no Onboarding. Só o RH admite.</p></div>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="adm_cancelar"):
            fechar()
            st.rerun()
        if st.button("Admitir", type="primary", key="adm_ok"):
            erro_campo = validar_admissao(dados, hoje)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                resposta = admitir_colaborador(st.session_state.token, corpo_admissao(dados))
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            for chave in [k for k in st.session_state if str(k).startswith("adm_")]:
                st.session_state.pop(chave, None)
            novo_id = (resposta.get("colaborador") or {}).get("id")
            st.session_state.pop(CACHE, None)
            st.session_state.aviso_toast = f"{dados['nome'].strip()} admitido(a). Agora crie o acesso."
            st.session_state.modal_cadastro = ("acesso", novo_id) if novo_id else None
            st.rerun()


@st.dialog("Criar acesso", width="small", on_dismiss=fechar)
def modal_criar_acesso(colabs: list[dict], deps: dict, colaborador_id=None) -> None:
    """Figma 246:1245 ("Novo usuário"). A conta nasce Colaborador; só o Admin escolhe outro perfil, que o
    backend aplica em seguida (`usuarios/{id}/perfil`). A senha temporária é sorteada aqui e vai só por
    e-mail: quem cria a conta não a vê."""
    sem_conta = {c.get("id"): c for c in fichas_sem_conta(colabs)}
    ids = list(sem_conta)
    rotulo = lambda i: f"{sem_conta[i].get('nome')} — {deps.get(sem_conta[i].get('departamento_id')) or '—'}"
    colab = st.selectbox("Colaborador", ids, index=ids.index(colaborador_id) if colaborador_id in ids else None, format_func=rotulo,
                         placeholder="Escolha a pessoa (só fichas sem conta)", key="acesso_colab")
    email = st.text_input("E-mail de acesso", max_chars=120, placeholder="nome@empresa.com", key="acesso_email")
    admin = perfil(st.session_state.usuario.get("perfil")) == "ADMIN"
    escolhido = "COLABORADOR"
    if admin:
        escolhido = st.radio("Perfil", list(PERFIS), format_func=PERFIS.get, key="acesso_perfil")
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">A pessoa recebe uma senha temporária por e-mail e troca no primeiro acesso.'
            + ("" if admin else " A conta nasce com o perfil Colaborador; outro perfil é o Admin quem define.") + '</p></div>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="acesso_cancelar"):
            fechar()
            st.rerun()
        if st.button("Criar usuário", type="primary", key="acesso_ok"):
            erro_campo = validar_novo_usuario(colab, email)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                resposta = criar_usuario(st.session_state.token, colab, email.strip().lower(), senha_temporaria())
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            nome = sem_conta[colab].get("nome")
            aviso = f"Acesso de {nome} criado."
            if escolhido != "COLABORADOR":
                try:
                    trocar_perfil(st.session_state.token, (resposta.get("usuario") or {}).get("id"), escolhido)
                    aviso += f" Perfil: {PERFIS[escolhido]}."
                except ApiError as erro:
                    aviso += f" O perfil continuou Colaborador: {erro.message}"
            if resposta.get("email_enviado") is False:
                aviso += ' O e-mail com a senha não saiu: peça à pessoa para usar "Esqueci minha senha" na tela Entrar.'
            else:
                aviso += " A senha temporária foi por e-mail."
            for chave in ("acesso_colab", "acesso_email", "acesso_perfil"):
                st.session_state.pop(chave, None)
            concluir(aviso)


# ---------------------------------------------------------------------------
def _tabela(linhas: list[dict]) -> None:
    pesos = [3, 2, 2.4, 1.3, 1.3, 1.4]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Pessoa", "Departamento", "Cargo", "Admissão", "Situação", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Ninguém neste filtro.</p>')
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_lin_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["nome"])}</p><p class="d">{html.escape(l["email"])}</p></div>')
                for coluna, texto in zip(c[1:4], (l["departamento"], l["cargo"], l["admissao"])):
                    coluna.html(f'<p class="crh-doc-prazo">{html.escape(texto)}</p>')
                c[4].html(f'<span class="crh-selo {l["situacao"][1]}">{html.escape(l["situacao"][0])}</span>', width="content")
                with c[5]:
                    if st.button("Abrir ficha →", type="tertiary", key=f"col_ficha_{l['id']}"):
                        st.session_state.col_ficha = l["id"]
                        st.rerun()


def _ficha(colab: dict, dados: dict) -> None:
    with st.container(key="col_ficha_card"):
        st.html(f'<p class="crh-cfg-titulo">Ficha — {html.escape(colab.get("nome") or "")}</p>')
        campos = "".join(f'<p class="r">{html.escape(r)}</p><p class="v">{html.escape(v)}</p>' for r, v in ficha(colab, dados["organograma"], dados["usuarios"]))
        st.html(f'<div class="crh-campos crh-campos-direita">{campos}</div>')
        with st.container(horizontal=True, vertical_alignment="center", gap="small"):
            st.html('<p class="crh-meta">Editar cadastro, mudar cargo ou salário e a linha do tempo chegam depois (tarefa 53).</p>', width="stretch")
            if not colab.get("user_id") and str(colab.get("status") or "").upper() != "DESLIGADO":
                if st.button("Criar acesso", type="primary", key="col_criar_acesso"):
                    st.session_state.modal_cadastro = ("acesso", colab.get("id"))
                    st.rerun()


def pagina_colaboradores() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    meu_perfil = perfil(usuario.get("perfil"))
    if meu_perfil not in ("RH", "ADMIN"):
        render_hero("Colaboradores", "Cadastro de pessoas")
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return

    with st.spinner("Carregando..."):
        try:
            dados, erro = carregar(token), None
        except ApiError as falha:
            dados, erro = None, falha
    if erro is not None:
        render_hero("Colaboradores", "Cadastro de pessoas")
        alerta(st.empty(), "erro", erro.message)
        return

    colabs, org = dados["colaboradores"], dados["organograma"]
    render_hero("Colaboradores", resumo_colaboradores(colabs, date.today()))
    deps = {d.get("id"): d.get("nome") for d in org.get("departamentos") or []}
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        busca = st.text_input("Busca", placeholder="⌕  Nome, CPF ou e-mail", key="col_busca", label_visibility="collapsed", width=260)
        st.space("stretch")
        dep = st.selectbox("Departamento", [None] + sorted(deps, key=deps.get), format_func=lambda d: "Departamento: Todos" if d is None else f"Departamento: {deps[d]}",
                           key="col_dep", label_visibility="collapsed", width=230)
        situacao = st.selectbox("Situação", list(SITUACOES_COLAB), format_func=SITUACOES_COLAB.get, key="col_situacao", label_visibility="collapsed", width=190)
        if meu_perfil == "RH" and st.button("Admitir colaborador", type="primary", key="col_admitir"):
            st.session_state.modal_cadastro = ("admitir", None)
            st.rerun()

    _tabela(linhas_colaboradores(colabs, org, busca, dep, situacao))
    nota = "Só o RH admite. A conta de acesso vem depois, pela ficha (\"Criar acesso\"): a pessoa recebe a senha temporária por e-mail."
    st.html(f'<p class="crh-meta">{html.escape(nota)}</p>')

    selecionado = next((c for c in colabs if c.get("id") == st.session_state.get("col_ficha")), None)
    if selecionado:
        _ficha(selecionado, dados)

    modal = st.session_state.get("modal_cadastro")
    if not modal:
        return
    acao, alvo = modal
    if acao == "admitir" and meu_perfil == "RH":
        _modal_admitir(org)
    elif acao == "acesso":
        modal_criar_acesso(colabs, deps, alvo)
    else:
        fechar()
