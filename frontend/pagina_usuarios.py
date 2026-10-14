"""
Página "Usuários e perfis" do Admin (Figma 246:612; modais 246:1245 "Novo usuário", 246:1280 "Trocar
perfil" e 440:1203 "Vincular ficha"; tarefa 50 da change concluir-frontend-streamlit).

Quem acessa o ConectaRH e com qual perfil. "Vincular ficha" liga uma conta que não tem cadastro de
colaborador (por exemplo, a de RH ou Admin criada antes da ficha) a uma ficha sem conta: sem ficha, a
pessoa não marca ponto nem pede férias. Endpoints: `usuarios`, `usuarios/{id}/perfil|status|
vincular_colaborador`, `colaboradores` e `organograma`. Ninguém troca o próprio perfil, desativa nem
vincula a própria conta (o backend recusa e a tela não oferece).
"""

import html

import streamlit as st

from api_client import ApiError, alterar_status_usuario, aprovar_pedido_acesso, recusar_pedido_acesso, trocar_perfil, vincular_colaborador
from cadastro_modelo import (PERFIS, SITUACOES_USUARIO, fichas_sem_conta, linhas_pedidos_acesso, linhas_usuarios, perfil, resumo_usuarios,
                             validar_recusa_acesso)
from pagina_colaboradores import carregar, concluir, fechar, modal_criar_acesso, pedidos_acesso
from theme import alerta, render_hero, render_indicadores, render_topbar


def _campos(linhas: list[tuple[str, str]]) -> None:
    campos = "".join(f'<p class="r">{html.escape(r)}</p><p class="v">{html.escape(v)}</p>' for r, v in linhas)
    st.html(f'<div class="crh-campos crh-campos-direita">{campos}</div>')


def _botoes(rotulo: str, chave: str) -> bool:
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key=f"{chave}_cancelar"):
            fechar()
            st.rerun()
        return st.button(rotulo, type="primary", key=chave)


@st.dialog("Trocar perfil", width="small", on_dismiss=fechar)
def _modal_perfil(linha: dict) -> None:
    _campos([("Usuário", linha["nome"]), ("Perfil atual", linha["perfil_rotulo"])])
    opcoes = [p for p in PERFIS if p != linha["perfil"]]
    novo = st.radio("Novo perfil", opcoes, format_func=PERFIS.get, key="usr_perfil_novo")
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">A troca fica registrada na auditoria, com quem fez. Ninguém troca o próprio perfil.</p></div>')
    slot = st.empty()
    if _botoes("Trocar perfil", "usr_perfil_ok"):
        try:
            trocar_perfil(st.session_state.token, linha["id"], novo)
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        st.session_state.pop("usr_perfil_novo", None)
        concluir(f"Perfil de {linha['nome']} agora é {PERFIS[novo]}.")


@st.dialog("Vincular ficha", width="small", on_dismiss=fechar)
def _modal_vincular(linha: dict, colabs: list[dict], deps: dict) -> None:
    _campos([("Conta", f"{linha['email']} · {linha['perfil_rotulo']}")])
    livres = {c.get("id"): c for c in fichas_sem_conta(colabs)}
    ids = list(livres)
    # Sugere a ficha com o mesmo nome da conta, quando houver.
    sugestao = next((i for i in ids if str(livres[i].get("nome") or "").casefold() == linha["nome"].casefold()), None)
    escolhida = st.selectbox(
        "Ficha do colaborador", ids, index=ids.index(sugestao) if sugestao in ids else None,
        format_func=lambda i: f"{livres[i].get('nome')} — {deps.get(livres[i].get('departamento_id')) or '—'}",
        placeholder="Escolha a ficha" if ids else "Nenhuma ficha sem conta: admita a pessoa em Colaboradores", key="usr_vinc_colab",
    )
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">Só aparecem fichas sem conta, de colaboradores não desligados. Ninguém vincula a própria conta. O vínculo fica na auditoria, e a pessoa passa a marcar ponto e pedir férias.</p></div>')
    slot = st.empty()
    if _botoes("Vincular", "usr_vinc_ok"):
        if not escolhida:
            alerta(slot, "erro", "Escolha a ficha do colaborador.")
            return
        try:
            vincular_colaborador(st.session_state.token, linha["id"], escolhida)
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        st.session_state.pop("usr_vinc_colab", None)
        concluir(f"Conta de {linha['nome']} vinculada à ficha. A pessoa já pode marcar ponto.")


@st.dialog("Desativar usuário", width="small", on_dismiss=fechar)
def _modal_desativar(linha: dict) -> None:
    _campos([("Usuário", linha["nome"]), ("Perfil", linha["perfil_rotulo"])])
    st.html('<p class="crh-nota-ambar">A pessoa deixa de entrar no ConectaRH.</p>')
    slot = st.empty()
    if _botoes("Desativar", "usr_desat_ok"):
        try:
            alterar_status_usuario(st.session_state.token, linha["id"], False)
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        concluir(f"Conta de {linha['nome']} desativada.")


@st.dialog("Aprovar pedido de acesso", width="small", on_dismiss=fechar)
def _modal_aprovar_acesso(linha: dict) -> None:
    _campos([("Conta", f"{linha['nome']} · {linha['email']}"), ("De → para", f"{linha['de']} → {linha['para']}"),
             ("Pedido por", f"{linha['pedido_por']} em {linha['quando']}"), ("Justificativa", linha["justificativa"])])
    if linha["mudou"]:
        st.html('<p class="crh-nota-ambar">O perfil da conta mudou depois do pedido. Aprovar troca para o perfil pedido mesmo assim.</p>')
    st.html('<div class="crh-incluso"><p class="n" style="margin:0">O perfil é trocado na hora e vale no próximo login. O RH e a pessoa são avisados.</p></div>')
    slot = st.empty()
    if _botoes("Aprovar e trocar o perfil", "usr_ap_ok"):
        try:
            aprovar_pedido_acesso(st.session_state.token, linha["id"])
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        concluir(f"Acesso de {linha['nome']} alterado para {linha['para']}.")


@st.dialog("Recusar pedido de acesso", width="small", on_dismiss=fechar)
def _modal_recusar_acesso(linha: dict) -> None:
    _campos([("Conta", linha["nome"]), ("Pedido", f"{linha['de']} → {linha['para']}"), ("Justificativa", linha["justificativa"])])
    motivo = st.text_area("Motivo da recusa", max_chars=1000, height=80, key="usr_rec_motivo", help="Vai para o RH que pediu.")
    slot = st.empty()
    if _botoes("Recusar", "usr_rec_ok"):
        if erro_campo := validar_recusa_acesso(motivo):
            alerta(slot, "erro", erro_campo)
            return
        try:
            recusar_pedido_acesso(st.session_state.token, linha["id"], motivo.strip())
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        st.session_state.pop("usr_rec_motivo", None)
        concluir(f"Pedido de acesso de {linha['nome']} recusado.")


def _pedidos(linhas: list[dict], meu_id) -> None:
    """Pedidos de alteração de acesso do RH (change pedido-de-acesso): os pendentes com Aprovar e Recusar; o resto no histórico."""
    pendentes = [l for l in linhas if l["pendente"]]
    st.html(f'<p class="crh-bloco-titulo">Pedidos de alteração de acesso ({len(pendentes)})</p>')
    if not pendentes:
        st.html('<p class="crh-meta">Nenhum pedido pendente do RH.</p>')
    for l in pendentes:
        with st.container(horizontal=True, vertical_alignment="center", key=f"usr_ped_{l['id']}"):
            st.html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["nome"])}: {html.escape(l["de"])} → {html.escape(l["para"])}</p>'
                    f'<p class="d">{html.escape(l["pedido_por"])} em {html.escape(l["quando"])} · {html.escape(l["justificativa"])}</p></div>', width="stretch")
            if l["usuario_id"] == meu_id:
                st.html('<p class="crh-meta">Sua conta: outro Admin decide</p>', width="content")
                continue
            if st.button("Aprovar", type="tertiary", key=f"usr_ped_ap_{l['id']}"):
                st.session_state.modal_cadastro = ("aprovar_acesso", l["id"])
                st.rerun()
            if st.button("Recusar", type="tertiary", key=f"usr_ped_rec_{l['id']}"):
                st.session_state.modal_cadastro = ("recusar_acesso", l["id"])
                st.rerun()
    decididos = [l for l in linhas if not l["pendente"]]
    if decididos:
        with st.expander(f"Histórico de pedidos ({len(decididos)})", key="usr_ped_hist"):
            for l in decididos:
                st.html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["nome"])}: {html.escape(l["de"])} → {html.escape(l["para"])} '
                        f'<span class="crh-selo {l["situacao"][1]}">{html.escape(l["situacao"][0])}</span></p>'
                        f'<p class="d">Pedido por {html.escape(l["pedido_por"])} em {html.escape(l["quando"])} · {html.escape(l["decisao"])}</p></div>')


def _tabela(linhas: list[dict], token: str) -> None:
    pesos = [2.8, 1.1, 1.3, 1.5, 3.3]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Usuário", "Perfil", "Último acesso", "Situação", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Ninguém neste filtro.</p>')
        for i, l in enumerate(linhas):
            destaque = l["situacao"][0] in ("Sem ficha", "Senha temporária")
            with st.container(key=f"rh_linf_{i}" if destaque else f"rh_lin_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["nome"])}{" (você)" if l["proprio"] else ""}</p><p class="d">{html.escape(l["email"])}</p></div>')
                c[1].html(f'<span class="crh-selo {l["selo_perfil"]}">{html.escape(l["perfil_rotulo"])}</span>', width="content")
                c[2].html(f'<p class="crh-doc-prazo">{html.escape(l["ultimo_acesso"])}</p>')
                c[3].html(f'<span class="crh-selo {l["situacao"][1]}">{html.escape(l["situacao"][0])}</span>', width="content")
                with c[4]:
                    if l["proprio"] and l["sem_ficha"]:
                        st.html('<p class="crh-meta">Sua conta: outro Admin vincula a ficha</p>')
                    with st.container(horizontal=True, gap="small"):
                        if "vincular" in l["acoes"] and st.button("Vincular ficha", type="tertiary", key=f"usr_vinc_{l['id']}"):
                            st.session_state.modal_cadastro = ("vincular", l["id"])
                            st.rerun()
                        if "perfil" in l["acoes"] and st.button("Trocar perfil", type="tertiary", key=f"usr_perfil_{l['id']}"):
                            st.session_state.modal_cadastro = ("perfil", l["id"])
                            st.rerun()
                        if "desativar" in l["acoes"] and st.button("Desativar", type="tertiary", key=f"rh_recusar_usr_{l['id']}"):
                            st.session_state.modal_cadastro = ("desativar", l["id"])
                            st.rerun()
                        if "ativar" in l["acoes"] and st.button("Reativar", type="tertiary", key=f"usr_ativar_{l['id']}"):
                            try:
                                alterar_status_usuario(token, l["id"], True)
                            except ApiError as erro:
                                st.session_state.usr_erro = erro.message
                                st.rerun()
                            concluir(f"Conta de {l['nome']} reativada.")


def pagina_usuarios() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Usuários e perfis", "Quem acessa o ConectaRH e com qual perfil")
    meu_perfil = perfil(usuario.get("perfil"))
    if meu_perfil != "ADMIN":
        alerta(st.empty(), "erro", "Esta tela é só do Admin.")
        return

    with st.spinner("Carregando..."):
        try:
            dados, erro = carregar(token), None
        except ApiError as falha:
            dados, erro = None, falha
    if erro is not None:
        alerta(st.empty(), "erro", erro.message)
        return
    lista, colabs = dados["usuarios"], dados["colaboradores"]
    deps = {d.get("id"): d.get("nome") for d in dados["organograma"].get("departamentos") or []}
    numeros = resumo_usuarios(lista, colabs)
    render_indicadores([
        ("Usuários ativos", str(numeros["ativos"]), ""),
        ("Sem ficha de colaborador", str(numeros["sem_ficha"]), "ambar"),
        ("Inativos", str(numeros["inativos"]), ""),
        ("Admins", str(numeros["admins"]), "azul"),
    ])

    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        busca = st.text_input("Busca", placeholder="⌕  Nome ou e-mail", key="usr_busca", label_visibility="collapsed", width=260)
        st.space("stretch")
        filtro = st.selectbox("Perfil", [None] + list(PERFIS), format_func=lambda p: "Perfil: Todos" if p is None else f"Perfil: {PERFIS[p]}", key="usr_filtro_perfil", label_visibility="collapsed", width=170)
        situacao = st.selectbox("Situação", list(SITUACOES_USUARIO), format_func=SITUACOES_USUARIO.get, key="usr_situacao", label_visibility="collapsed", width=230)
        if st.button("Novo usuário", type="primary", key="usr_novo"):
            st.session_state.modal_cadastro = ("acesso", None)
            st.rerun()

    if erro_acao := st.session_state.pop("usr_erro", None):
        alerta(st.empty(), "erro", erro_acao)
    pedidos = pedidos_acesso(token)
    linhas_pedidos = linhas_pedidos_acesso(pedidos) if isinstance(pedidos, list) else []
    if isinstance(pedidos, str):
        alerta(st.empty(), "atencao", f"Os pedidos de acesso não carregaram agora: {pedidos}")
    else:
        _pedidos(linhas_pedidos, usuario.get("id"))
    linhas = linhas_usuarios(lista, colabs, usuario.get("id"), meu_perfil, busca, filtro, situacao)
    _tabela(linhas, token)
    st.html('<p class="crh-meta">Toda troca de perfil, desativação e vínculo fica na auditoria. Ninguém troca o próprio perfil nem vincula a própria conta. Conta sem ficha não marca ponto nem pede férias: use "Vincular ficha".</p>')

    modal = st.session_state.get("modal_cadastro")
    if not modal:
        return
    acao, alvo = modal
    if acao == "acesso":
        modal_criar_acesso(colabs, deps, alvo)
        return
    if acao in ("aprovar_acesso", "recusar_acesso"):
        pedido = next((l for l in linhas_pedidos if l["id"] == alvo and l["pendente"] and l["usuario_id"] != usuario.get("id")), None)
        if pedido is None:
            fechar()
        elif acao == "aprovar_acesso":
            _modal_aprovar_acesso(pedido)
        else:
            _modal_recusar_acesso(pedido)
        return
    linha = next((l for l in linhas_usuarios(lista, colabs, usuario.get("id"), meu_perfil) if l["id"] == alvo), None)
    if linha is None:
        fechar()
        return
    if acao == "vincular" and "vincular" in linha["acoes"]:
        _modal_vincular(linha, colabs, deps)
    elif acao == "perfil" and "perfil" in linha["acoes"]:
        _modal_perfil(linha)
    elif acao == "desativar" and "desativar" in linha["acoes"]:
        _modal_desativar(linha)
    else:
        fechar()
