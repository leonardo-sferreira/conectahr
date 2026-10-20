"""
Página "Colaboradores" do RH e do Admin (Figma 243:580; modal 243:1075 "Admitir colaborador"; parte da
tarefa 53 da change concluir-frontend-streamlit).

Lista com busca e filtros, a ficha da pessoa e o caminho de cadastro de um novo funcionário:
"Admitir colaborador" (só o RH; `colaboradores` POST) e, em seguida, "Criar acesso" (`usuarios` POST),
que manda a senha temporária por e-mail. O modal "Criar acesso / Novo usuário" (246:1245) também é usado
na tela Usuários e perfis. Endpoints: `colaboradores`, `organograma` e `usuarios`.

Ficha (pedido do usuário em 13/10/2026): dados pessoais, endereço, vínculo e conta bancária (mascarada; sem salário),
os documentos enviados pela pessoa (`documentos`, com a seta "Ver dados e arquivo" da Conferência) e "Baixar ficha em
PDF" (`ficha_colaborador.ficha_pdf`).

Tipo de acesso (change pedido-de-acesso): a admissão já escolhe o perfil, que "Criar acesso" traz marcado. O Admin
cria com o perfil e troca direto pela ficha ("Alterar acesso"); o RH, quando escolhe um perfil diferente de
Colaborador, manda um pedido com justificativa ao Admin (`solicitacoes_acesso`), que aprova ou recusa em Usuários e
perfis. A ficha mostra o perfil da conta e o pedido pendente. Admin não é oferecido na admissão nem no "Criar acesso":
só pela ficha de quem já está cadastrado.
"""

import html
import time
from datetime import date, datetime

import streamlit as st

from api_client import (ApiError, admitir_colaborador, colaboradores, criar_usuario, definir_superior, documentos_rh, organograma, pedir_acesso,
                        solicitacoes_acesso, trocar_perfil, usuarios)
from cadastro_modelo import (
    CONTRATOS,
    JORNADA_SEMANAL,
    NIVEIS,
    PERFIS,
    PERFIS_NOVA_CONTA,
    SITUACOES_COLAB,
    candidatos_superior,
    conta_do_colaborador,
    corpo_admissao,
    fichas_sem_conta,
    linhas_colaboradores,
    pedidos_da_conta,
    perfil,
    resumo_colaboradores,
    senha_temporaria,
    validar_admissao,
    validar_novo_usuario,
    validar_pedido_acesso,
)
from cargos_modelo import cargos_do_departamento, rotulo_cargo
from ficha_colaborador import documentos_da_pessoa, ficha_pdf, nome_arquivo_ficha, secoes
from pagina_conferencia_documentos import _detalhes as detalhes_documento
from campos import campo, data_por_partes
from theme import alerta, render_hero, render_topbar

CACHE = "cadastro_cache"
_VALIDADE_CACHE_S = 20
_VALIDADE_FALHA_S = 5
_SEM_ORGANOGRAMA = "Os departamentos e cargos não carregaram agora"
_CACHE_PEDIDOS = "pedidos_acesso_cache"
_AJUDA_PEDIDO = "Só o Admin libera outro tipo de acesso. Diga por que a pessoa precisa dele (ex.: assume a coordenação da equipe)."


def pedidos_acesso(token: str) -> list[dict] | str:
    """Os pedidos de alteração de acesso (`solicitacoes_acesso`), guardados por 20 s; a mensagem do erro, se falhar."""
    guardado = st.session_state.get(_CACHE_PEDIDOS)
    if guardado and time.time() - guardado["em"] < _VALIDADE_CACHE_S:
        return guardado["dados"]
    try:
        dados = solicitacoes_acesso(token).get("solicitacoes") or []
    except ApiError as erro:
        return erro.message
    st.session_state[_CACHE_PEDIDOS] = {"em": time.time(), "dados": dados}
    return dados


def carregar(token: str) -> dict:
    """{'colaboradores', 'organograma', 'usuarios', 'erros'} por 20 s. Erro de `colaboradores` sobe; sem organograma
    ou sem a lista de usuários a tela segue com o que tem, e `erros` guarda a mensagem de cada falha. Com falha, o
    cache vale só 5 s: antes, um organograma vazio (ex.: limite de requisições) ficava 20 s guardado e o modal Admitir
    abria sem departamentos nem cargos, sem dizer por quê."""
    cache = st.session_state.get(CACHE)
    if cache and time.time() - cache["em"] < cache.get("validade", _VALIDADE_CACHE_S):
        return cache["dados"]
    dados = {"colaboradores": colaboradores(token).get("colaboradores") or [], "erros": {}}
    for chave, funcao, campo in (("organograma", organograma, None), ("usuarios", usuarios, "usuarios")):
        try:
            resposta = funcao(token)
            dados[chave] = (resposta.get(campo) or []) if campo else resposta
        except ApiError as erro:
            dados[chave] = [] if campo else {}
            dados["erros"][chave] = erro.message
    st.session_state[CACHE] = {"em": time.time(), "dados": dados, "validade": _VALIDADE_FALHA_S if dados["erros"] else _VALIDADE_CACHE_S}
    return dados


def recarregar() -> None:
    """Descarta o que está guardado e roda a tela de novo (botão "Tentar de novo")."""
    st.session_state.pop(CACHE, None)
    st.rerun()


def fechar() -> None:
    st.session_state.pop("modal_cadastro", None)
    st.session_state.pop("acesso_dep", None)


def concluir(aviso: str) -> None:
    st.session_state.pop(CACHE, None)
    st.session_state.pop(_CACHE_PEDIDOS, None)
    fechar()
    st.session_state.aviso_toast = aviso
    st.rerun()


# ---------------------------------------------------------------------------
# Modais
# ---------------------------------------------------------------------------
def _jornada_do_contrato() -> None:
    """Ao trocar o contrato na admissão, sugere a carga horária da matriz; PJ e Outro mantêm o que está no campo."""
    if (jornada := JORNADA_SEMANAL.get(st.session_state.get("adm_contrato"))) is not None:
        st.session_state.adm_carga = jornada


@st.dialog("Admitir colaborador", width="medium", on_dismiss=fechar)
def _modal_admitir(org: dict, erro_org: str | None = None) -> None:
    deps = {d.get("id"): d.get("nome") for d in org.get("departamentos") or [] if d.get("ativo", True)}
    niveis = {n.get("id"): n for n in org.get("niveis") or []}
    hoje = date.today()
    if not deps:
        # Sem departamentos não dá para escolher o cargo nem admitir: diz por quê e deixa tentar de novo (o que já foi
        # digitado fica, porque os campos guardam o valor pela key).
        alerta(st.empty(), "erro", f"{_SEM_ORGANOGRAMA}: {erro_org}" if erro_org else "Nenhum departamento ativo. Cadastre um em Estrutura da empresa.")
        if erro_org and st.button("Tentar de novo", key="adm_recarregar"):
            recarregar()
    # Cada campo aceita só o seu tipo (campos.py; pedido do usuário em 20/10/2026): o que não é permitido ganha um aviso
    # embaixo do campo, e o botão Admitir não grava enquanto houver.
    dados = {"nome": campo(st, "Nome completo", "nome", "adm_nome", max_chars=100)}
    c1, c2 = st.columns(2)
    dados["cpf"] = campo(c1, "CPF", "numero", "adm_cpf", max_chars=11, placeholder="Só os 11 números")
    with c2:
        dados["data_nascimento"] = data_por_partes(st, "Nascimento", "adm_nasc", 1940, hoje.year)
    dados["email_pessoal"] = campo(st, "E-mail pessoal", "email", "adm_email", max_chars=120)
    c1, c2 = st.columns(2)
    dados["telefone"] = campo(c1, "Telefone", "numero", "adm_tel", max_chars=11, placeholder="DDD + número, só números")
    dados["bairro"] = campo(c2, "Bairro", "endereco", "adm_bairro", max_chars=100)
    c1, c2 = st.columns(2)
    dados["departamento_id"] = c1.selectbox("Departamento", sorted(deps, key=deps.get), index=None, format_func=deps.get, placeholder="Escolha", key="adm_dep")
    # Os cargos do departamento escolhido e os sem departamento (change cadastro-de-cargos, D3), com o nível do cargo.
    cargos = {c.get("id"): rotulo_cargo(c, niveis) for c in cargos_do_departamento(org.get("cargos") or [], dados["departamento_id"])}
    if st.session_state.get("adm_cargo") not in cargos:
        st.session_state.adm_cargo = None
    dados["cargo_id"] = c2.selectbox("Cargo", list(cargos), index=None, format_func=cargos.get, key="adm_cargo",
                                     placeholder="Escolha" if dados["departamento_id"] else "Escolha o departamento antes")
    c1, c2 = st.columns(2)
    dados["tipo_contrato"] = c1.selectbox("Contrato", list(CONTRATOS), format_func=CONTRATOS.get, key="adm_contrato", on_change=_jornada_do_contrato)
    dados["data_admissao"] = c2.date_input("Admissão", value=hoje, format="DD/MM/YYYY", key="adm_admissao")
    c1, c2 = st.columns(2)
    dados["logradouro"] = campo(c1, "Logradouro", "endereco", "adm_logradouro", max_chars=150)
    dados["numero"] = campo(c2, "Número", "numero", "adm_numero", max_chars=10, placeholder="Só números")
    dados["complemento"] = campo(st, "Complemento (opcional)", "endereco", "adm_complemento", max_chars=100, placeholder="Ex.: casa B, apto 12, bloco 3")
    c1, c2 = st.columns(2)
    dados["nivel"] = c1.selectbox("Nível", list(NIVEIS), format_func=NIVEIS.get, key="adm_nivel")
    dados["carga_horaria_semanal"] = c2.number_input("Carga horária semanal", min_value=1.0, max_value=60.0, value=JORNADA_SEMANAL["CLT"], step=1.0, key="adm_carga",
                                                 help="Vem do contrato (CLT 44h, estágio e aprendiz 30h); PJ não tem jornada definida. Dá para ajustar.")
    dados["salario"] = st.number_input("Salário (R$)", min_value=0.0, value=None, step=100.0, format="%.2f", key="adm_salario")
    acesso = st.radio("Tipo de acesso", list(PERFIS_NOVA_CONTA), format_func=PERFIS_NOVA_CONTA.get, horizontal=True, key="adm_acesso",
                      help="A conta é criada no passo seguinte (Criar acesso). Gestor ou RH vai como pedido ao Admin. "
                           "Acesso Admin só depois, pela ficha da pessoa.")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="adm_cancelar"):
            fechar()
            st.rerun()
        if st.button("Admitir", type="primary", key="adm_ok"):
            # Algum campo acabou de ser limpo (emoji, letra no número...): mostra e espera um novo clique.
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
            pedidos = resposta.get("pendencias_documento_criadas") or 0
            docs = f" {pedidos} documento{'s' if pedidos != 1 else ''} obrigatório{'s' if pedidos != 1 else ''} pedido{'s' if pedidos != 1 else ''}." if pedidos else ""
            st.session_state.aviso_toast = f"{dados['nome'].strip()} admitido(a).{docs} Agora crie o acesso."
            st.session_state.modal_cadastro = ("acesso", novo_id) if novo_id else None
            st.session_state.acesso_perfil = acesso
            st.rerun()


@st.dialog("Criar acesso", width="small", on_dismiss=fechar)
def modal_criar_acesso(colabs: list[dict], deps: dict, colaborador_id=None) -> None:
    """Figma 246:1245 ("Novo usuário"). A conta nasce Colaborador. O Admin escolhe outro perfil, que o backend aplica em
    seguida (`usuarios/{id}/perfil`); o RH também escolhe, e o perfil diferente de Colaborador vira um pedido com
    justificativa ao Admin (`solicitacoes_acesso`). A senha temporária é sorteada aqui e vai só por e-mail: quem cria a
    conta não a vê."""
    sem_conta = {c.get("id"): c for c in fichas_sem_conta(colabs)}
    # Filtro de departamento: só os departamentos que têm ficha sem conta; aberto pela ficha, já vem com o dela.
    deps_com_ficha = sorted({c.get("departamento_id") for c in sem_conta.values() if c.get("departamento_id")}, key=lambda d: deps.get(d) or "")
    if colaborador_id in sem_conta and "acesso_dep" not in st.session_state:
        st.session_state.acesso_dep = sem_conta[colaborador_id].get("departamento_id")
    dep = st.selectbox("Departamento", [None] + deps_com_ficha, format_func=lambda d: "Todos os departamentos" if d is None else deps.get(d) or f"Departamento nº {d}", key="acesso_dep")
    ids = [i for i, c in sem_conta.items() if not dep or c.get("departamento_id") == dep]
    rotulo = lambda i: f"{sem_conta[i].get('nome')} — {deps.get(sem_conta[i].get('departamento_id')) or '—'}"
    colab = st.selectbox("Colaborador", ids, index=ids.index(colaborador_id) if colaborador_id in ids else None, format_func=rotulo,
                         placeholder="Escolha a pessoa (só fichas sem conta)" if ids else "Nenhuma ficha sem conta neste departamento", key="acesso_colab")
    email = campo(st, "E-mail de acesso", "email", "acesso_email", max_chars=120, placeholder="nome@empresa.com")
    admin = perfil(st.session_state.usuario.get("perfil")) == "ADMIN"
    if st.session_state.get("acesso_perfil") not in PERFIS_NOVA_CONTA:
        st.session_state.acesso_perfil = "COLABORADOR"
    escolhido = st.radio("Tipo de acesso", list(PERFIS_NOVA_CONTA), format_func=PERFIS_NOVA_CONTA.get, horizontal=True, key="acesso_perfil",
                         help="Acesso Admin só depois, pela ficha da pessoa.")
    justificativa = ""
    if not admin and escolhido != "COLABORADOR":
        st.html('<div class="crh-incluso"><p class="n" style="margin:0">A conta nasce Colaborador, e o pedido de '
                f'{html.escape(PERFIS[escolhido])} vai para o Admin aprovar.</p></div>')
        justificativa = st.text_area("Justificativa para o Admin", max_chars=1000, height=80, key="acesso_justificativa", help=_AJUDA_PEDIDO)
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="acesso_cancelar"):
            fechar()
            st.rerun()
        if st.button("Criar usuário", type="primary", key="acesso_ok"):
            erro_campo = validar_novo_usuario(colab, email)
            if not erro_campo and not admin and escolhido != "COLABORADOR":
                erro_campo = validar_pedido_acesso("COLABORADOR", escolhido, justificativa)
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
            novo_usuario = (resposta.get("usuario") or {}).get("id")
            if escolhido != "COLABORADOR" and admin:
                try:
                    trocar_perfil(st.session_state.token, novo_usuario, escolhido)
                    aviso += f" Perfil: {PERFIS[escolhido]}."
                except ApiError as erro:
                    aviso += f" O perfil continuou Colaborador: {erro.message}"
            elif escolhido != "COLABORADOR":
                try:
                    pedir_acesso(st.session_state.token, novo_usuario, escolhido, justificativa.strip())
                    aviso += f" O pedido de acesso {PERFIS[escolhido]} foi para o Admin."
                except ApiError as erro:
                    aviso += f" O pedido de acesso {PERFIS[escolhido]} não foi enviado ({erro.message}); peça pela ficha."
            if resposta.get("email_enviado") is False:
                aviso += ' O e-mail com a senha não saiu: peça à pessoa para usar "Esqueci minha senha" na tela Entrar.'
            else:
                aviso += " A senha temporária foi por e-mail."
            for chave in ("acesso_dep", "acesso_colab", "acesso_email", "acesso_perfil", "acesso_justificativa"):
                st.session_state.pop(chave, None)
            concluir(aviso)


@st.dialog("Tipo de acesso", width="small", on_dismiss=fechar)
def _modal_acesso(colab: dict, conta: dict, pendente: dict | None) -> None:
    """Admin: troca o perfil na hora. RH: pede ao Admin, com justificativa (change pedido-de-acesso)."""
    admin = perfil(st.session_state.usuario.get("perfil")) == "ADMIN"
    atual = perfil(conta.get("perfil"))
    st.html('<div class="crh-campos crh-campos-direita">'
            f'<p class="r">Pessoa</p><p class="v">{html.escape(colab.get("nome") or "")}</p>'
            f'<p class="r">Acesso atual</p><p class="v">{html.escape(PERFIS.get(atual, atual.capitalize() or "—"))}</p></div>')
    if pendente:
        st.html(f'<p class="crh-nota-ambar">Pedido pendente do RH: {html.escape(pendente["de"])} → {html.escape(pendente["para"])}, '
                f'enviado por {html.escape(pendente["pedido_por"])} em {html.escape(pendente["quando"])}.'
                + (" Ele continua pendente: decida em Usuários e perfis." if admin else "") + "</p>")
    opcoes = [p for p in PERFIS if p != atual]
    novo = st.radio("Novo tipo de acesso", opcoes, format_func=PERFIS.get, key="ac_novo")
    justificativa = ""
    if not admin:
        justificativa = st.text_area("Justificativa para o Admin", max_chars=1000, height=90, key="ac_justificativa", help=_AJUDA_PEDIDO)
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">'
            + ("A troca vale no próximo login da pessoa e fica na auditoria." if admin else "O Admin recebe o pedido, aprova ou recusa; você é avisado no sino.")
            + "</p></div>")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="ac_cancelar"):
            fechar()
            st.rerun()
        if st.button("Alterar acesso" if admin else "Enviar pedido ao Admin", type="primary", key="ac_ok"):
            erro_campo = None if admin else validar_pedido_acesso(atual, novo, justificativa)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                if admin:
                    trocar_perfil(st.session_state.token, conta.get("id"), novo)
                else:
                    pedir_acesso(st.session_state.token, conta.get("id"), novo, justificativa.strip())
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            for chave in ("ac_novo", "ac_justificativa"):
                st.session_state.pop(chave, None)
            nome = colab.get("nome") or ""
            concluir(f"Acesso de {nome} alterado para {PERFIS[novo]}." if admin else f"Pedido de acesso {PERFIS[novo]} para {nome} enviado ao Admin.")


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


@st.dialog("Superior direto", width="small", on_dismiss=fechar)
def _modal_superior(colab: dict, colabs: list[dict], deps: dict) -> None:
    candidatos = {c.get("id"): c for c in candidatos_superior(colabs, colab.get("id"))}
    opcoes = [None] + list(candidatos)
    atual = colab.get("superior_colaborador_id")
    escolhido = st.selectbox(
        f"Superior direto de {colab.get('nome')}", opcoes, index=opcoes.index(atual) if atual in opcoes else 0,
        format_func=lambda i: "Sem superior (vale o gestor do departamento)" if i is None else f"{candidatos[i].get('nome')} — {deps.get(candidatos[i].get('departamento_id')) or '—'}",
        key="col_sup_escolha",
    )
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="col_sup_cancelar"):
            fechar()
            st.rerun()
        if st.button("Salvar", type="primary", key="col_sup_ok"):
            try:
                definir_superior(st.session_state.token, colab.get("id"), escolhido)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            st.session_state.pop("col_sup_escolha", None)
            concluir(f"Superior direto de {colab.get('nome')} atualizado.")


def _documentos_rh(token: str) -> list[dict] | str:
    """Todos os documentos (`documentos`, RH e Admin), guardados por 60 s; carregados só quando uma ficha é aberta."""
    guardado = st.session_state.get("col_docs_cache")
    if guardado and time.time() - guardado["em"] < 60:
        return guardado["dados"]
    try:
        docs = documentos_rh(token).get("documentos") or []
    except ApiError as erro:
        return erro.message
    st.session_state.col_docs_cache = {"em": time.time(), "dados": docs}
    return docs


def _bloco(titulo: str, campos: list[tuple[str, str]]) -> None:
    linhas = "".join(f'<p class="r">{html.escape(r)}</p><p class="v">{html.escape(v)}</p>' for r, v in campos)
    st.html(f'<p class="crh-bloco-titulo" style="margin:0 0 4px">{html.escape(titulo)}</p><div class="crh-campos crh-campos-direita">{linhas}</div>')


def _ficha(colab: dict, dados: dict) -> None:
    """Ficha da pessoa (pedido do usuário em 13/10/2026): dados cadastrais, documentos enviados (com a seta de dados e
    arquivo da Conferência) e o PDF da ficha. Sem salário; conta bancária mascarada."""
    token = st.session_state.token
    partes = secoes(colab, dados["organograma"], dados["usuarios"], dados["colaboradores"])
    docs = _documentos_rh(token)
    linhas_docs = documentos_da_pessoa(docs, colab.get("id")) if isinstance(docs, list) else []
    with st.container(key="col_ficha_card"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html(f'<p class="crh-cfg-titulo">Ficha — {html.escape(colab.get("nome") or "")}</p>', width="stretch")
            agora = datetime.now()
            st.download_button("Baixar ficha em PDF", ficha_pdf(colab.get("nome") or "", partes, linhas_docs, st.session_state.usuario.get("nome") or "RH", agora),
                               file_name=nome_arquivo_ficha(colab.get("nome")), mime="application/pdf", key="col_ficha_pdf",
                               help="A ficha com os dados e os documentos enviados. Tem dados pessoais: guarde só o necessário.")
        for linha in (partes[:2], partes[2:]):
            for coluna, (titulo, campos) in zip(st.columns(2), linha):
                with coluna:
                    _bloco(titulo, campos)
        conta = conta_do_colaborador(colab, dados["usuarios"])
        admin = perfil(st.session_state.usuario.get("perfil")) == "ADMIN"
        pendente = None
        if conta:
            pedidos = pedidos_acesso(token)
            da_conta = pedidos_da_conta(pedidos, conta.get("id")) if isinstance(pedidos, list) else []
            pendente = next((p for p in da_conta if p["pendente"]), None)
            atual = perfil(conta.get("perfil"))
            texto = f"Tipo de acesso: {PERFIS.get(atual, atual.capitalize() or '—')}"
            if pendente:
                texto += f" · pedido pendente para {pendente['para']} ({pendente['quando']})"
            elif da_conta:
                texto += f" · último pedido: {da_conta[0]['para']}, {da_conta[0]['situacao'][0].lower()}"
            st.html(f'<p class="crh-meta" style="margin:8px 0 0">{html.escape(texto)}</p>')
            if isinstance(pedidos, str):
                st.html(f'<p class="crh-meta">Os pedidos de acesso não carregaram agora: {html.escape(pedidos)}</p>')
        with st.container(horizontal=True, vertical_alignment="center", gap="small"):
            st.space("stretch")
            if conta and conta.get("id") != st.session_state.usuario.get("id"):
                if admin and st.button("Alterar acesso", key="col_alterar_acesso"):
                    st.session_state.modal_cadastro = ("tipo_acesso", colab.get("id"))
                    st.rerun()
                if not admin and st.button("Solicitar alteração de acesso", key="col_pedir_acesso", disabled=pendente is not None,
                                           help="Já há um pedido pendente para esta conta." if pendente else None):
                    st.session_state.modal_cadastro = ("tipo_acesso", colab.get("id"))
                    st.rerun()
            if st.button("Definir superior", key="col_definir_superior"):
                st.session_state.modal_cadastro = ("superior", colab.get("id"))
                st.rerun()
            if not colab.get("user_id") and str(colab.get("status") or "").upper() != "DESLIGADO":
                if st.button("Criar acesso", type="primary", key="col_criar_acesso"):
                    st.session_state.modal_cadastro = ("acesso", colab.get("id"))
                    st.rerun()

        st.html(f'<p class="crh-bloco-titulo" style="margin:12px 0 4px">Documentos enviados ({len(linhas_docs)})</p>')
        if isinstance(docs, str):
            alerta(st.empty(), "erro", f"Os documentos não carregaram agora: {docs}")
        elif not linhas_docs:
            st.html('<p class="crh-meta">Esta pessoa ainda não enviou documentos.</p>')
        for l in linhas_docs:
            with st.container(horizontal=True, vertical_alignment="center", key=f"col_doc_{l['id']}"):
                st.html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["documento"])}</p>'
                        f'<p class="d">Enviado em {html.escape(l["enviado"])} · validade {html.escape(l["validade"])}</p></div>', width="stretch")
                st.html(f'<span class="crh-selo {l["situacao"][1]}">{html.escape(l["situacao"][0])}</span>', width="content")
            detalhes_documento(l)


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

    if erro_org := dados["erros"].get("organograma"):
        with st.container(horizontal=True, vertical_alignment="center"):
            alerta(st.empty(), "atencao", f"{_SEM_ORGANOGRAMA} (departamento e cargo aparecem como —): {erro_org}")
            if st.button("Tentar de novo", key="col_recarregar"):
                recarregar()
    _tabela(linhas_colaboradores(colabs, org, busca, dep, situacao))

    selecionado = next((c for c in colabs if c.get("id") == st.session_state.get("col_ficha")), None)
    if selecionado:
        _ficha(selecionado, dados)

    modal = st.session_state.get("modal_cadastro")
    if not modal:
        return
    acao, alvo = modal
    if acao == "admitir" and meu_perfil == "RH":
        _modal_admitir(org, dados["erros"].get("organograma"))
    elif acao == "acesso":
        modal_criar_acesso(colabs, deps, alvo)
    elif acao == "tipo_acesso":
        alvo_colab = next((c for c in colabs if c.get("id") == alvo), None)
        conta = conta_do_colaborador(alvo_colab, dados["usuarios"]) if alvo_colab else None
        if conta is None:
            fechar()
        else:
            pedidos = pedidos_acesso(token)
            pendente = next((p for p in pedidos_da_conta(pedidos, conta.get("id")) if p["pendente"]), None) if isinstance(pedidos, list) else None
            _modal_acesso(alvo_colab, conta, pendente)
    elif acao == "superior":
        alvo_colab = next((c for c in colabs if c.get("id") == alvo), None)
        if alvo_colab is None:
            fechar()
        else:
            _modal_superior(alvo_colab, colabs, deps)
    else:
        fechar()
