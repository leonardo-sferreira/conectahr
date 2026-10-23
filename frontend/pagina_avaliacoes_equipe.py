"""F15 do Gestor (248:744 e 248:1019), limitado aos contratos atuais de avaliação."""

import html

import streamlit as st

from api_client import ApiError
from avaliacoes_equipe_dados import carregar, formulario, gravar, invalidar
from avaliacoes_equipe_modelo import ciclos_disponiveis, editavel, indicadores, linhas
from campos import campos_invalidos
from theme import alerta, render_hero, render_indicadores, render_topbar
from trajetoria_modelo import NOTAS, validar_envio


def fechar() -> None:
    st.session_state.pop("ae_modal", None)
    st.session_state.pop("ae_form", None)


def _abrir(alvo: dict, ciclo: dict) -> None:
    for chave in list(st.session_state):
        if str(chave).startswith("ae_campo_"):
            st.session_state.pop(chave, None)
    fechar()
    st.session_state.ae_modal = {"alvo": alvo, "ciclo": ciclo}
    st.rerun()


def _conteudo_avaliacao(alvo: dict, ciclo: dict) -> None:
    usuario_id = st.session_state.usuario.get("id")
    token = st.session_state.token
    try:
        if "ae_form" not in st.session_state:
            with st.spinner("Carregando competências..."):
                st.session_state.ae_form = formulario(token, usuario_id, alvo)
        form = st.session_state.ae_form
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    st.html(f'<p class="crh-meta">{html.escape(form.get("avaliado_nome") or "liderado")}</p>'
            f'<div class="crh-incluso"><p class="crh-meta">Ciclo: {html.escape(ciclo["nome"])}</p>'
            '<p class="crh-meta">Autoavaliação: Não disponível</p></div>')
    if not editavel(form):
        alerta(st.empty(), "atencao", "Esta avaliação já foi enviada ou cancelada e não pode ser alterada.")
        return
    competencias = form.get("competencias") or []
    if not competencias:
        alerta(st.empty(), "atencao", validar_envio([], {}) or "Não há competências disponíveis.")
        return
    salvas = {r.get("competencia_avaliacao_id"): r for r in form.get("respostas") or []}
    notas, comentarios = {}, {}
    for c in competencias:
        cid = c["id"]
        salva = salvas.get(cid) or {}
        st.html(f'<p class="crh-bloco-titulo">{html.escape(c.get("nome") or "")}</p>')
        opcoes = list(NOTAS)
        notas[cid] = st.segmented_control("Nota", opcoes, label_visibility="collapsed", width="stretch",
                                          default=salva["nota"] if salva.get("nota") in opcoes else None,
                                          key=f"ae_campo_nota_{alvo['id']}_{cid}")
        comentarios[cid] = st.text_input("Comentário por competência (opcional)", value=salva.get("comentario") or "",
                                         max_chars=2000, key=f"ae_campo_com_{alvo['id']}_{cid}")
    geral = st.text_area("Comentário para o liderado", max_chars=2000, height=80, key=f"ae_campo_geral_{alvo['id']}",
                         help="Este comentário só é salvo ao enviar a avaliação. O rascunho guarda as notas e os comentários por competência.")
    confirmar = st.checkbox("Entendo que, depois de enviada, a avaliação não pode mais ser alterada.",
                            key=f"ae_campo_confirma_{alvo['id']}")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="ae_cancelar"):
            fechar()
            st.rerun()
        salvar = st.button("Salvar rascunho", key="ae_salvar")
        enviar = st.button("Enviar avaliação", type="primary", key="ae_enviar")
    if not (salvar or enviar):
        return
    erro_campo = " ".join(campos_invalidos())
    if enviar:
        erro_campo = erro_campo or validar_envio(competencias, notas) or (None if confirmar else "Marque a confirmação para enviar.")
    elif not any(n is not None for n in notas.values()):
        erro_campo = erro_campo or "Dê uma nota a pelo menos uma competência para salvar o rascunho."
    if erro_campo:
        alerta(slot, "erro", erro_campo)
        return
    try:
        with st.spinner("Salvando..."):
            gravar(token, usuario_id, alvo, form, notas, comentarios, geral, enviar)
    except ApiError as erro:
        mensagem = erro.message
        if erro.status_code not in (401, 403, 409):
            mensagem += " Algumas respostas podem ter sido salvas. Confira antes de tentar novamente."
        alerta(slot, "erro", mensagem)
        return
    st.session_state.ae_aviso = "Avaliação enviada." if enviar else "Rascunho salvo: notas e comentários por competência."
    fechar()
    st.rerun()


def _tabela(avaliacoes: list[dict], org: dict, ciclo: dict) -> None:
    pesos = [3, 1.2, 1.3, .6, 1.2]
    alvos = {a["id"]: a for a in avaliacoes}
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for col, nome in zip(st.columns(pesos), ("Pessoa", "Autoavaliação", "Minha avaliação", "Nota", "")):
                col.html(f'<p class="crh-doc-cab">{nome}</p>')
        if not avaliacoes:
            st.html('<p class="crh-meta">Nenhuma avaliação atribuída a você neste ciclo.</p>')
        for l in linhas(avaliacoes, org):
            with st.container(key=f"rh_linf_ae_{l['id']}" if l["editavel"] else f"rh_lin_ae_{l['id']}"):
                cols = st.columns(pesos, vertical_alignment="center")
                cols[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["nome"])}</p>'
                             f'<p class="d">{html.escape(l["detalhe"])}</p></div>')
                cols[1].html('<p class="crh-doc-prazo">—</p>')
                cols[2].html(f'<span class="crh-selo {l["tom"]}">{html.escape(l["situacao"])}</span>')
                cols[3].html(f'<p class="crh-doc-prazo">{html.escape(l["nota"])}</p>')
                if l["editavel"]:
                    with cols[4]:
                        if st.button("Avaliar →", type="tertiary", key=f"ae_avaliar_{l['id']}"):
                            _abrir(alvos[l["id"]], ciclo)


def pagina_avaliacoes_equipe() -> None:
    usuario = st.session_state.usuario
    render_topbar(usuario.get("nome") or "")
    if str(usuario.get("perfil") or "").strip().upper() != "GESTOR":
        render_hero("Avaliações da equipe", "")
        alerta(st.empty(), "erro", "Você não tem permissão para acessar esta tela.")
        return
    try:
        with st.spinner("Carregando..."):
            dados = carregar(st.session_state.token, usuario.get("id"))
    except ApiError as erro:
        render_hero("Avaliações da equipe", "")
        if erro.status_code != 401:
            alerta(st.empty(), "erro", erro.message)
            if st.button("Tentar novamente", key="ae_repetir"):
                invalidar()
                st.rerun()
        return
    ciclos = ciclos_disponiveis(dados["ciclos"], dados["avaliacoes"])
    ids = [c["id"] for c in ciclos]
    if st.session_state.get("ae_ciclo") not in ids:
        st.session_state.ae_ciclo = ids[0] if ids else None
    ciclo = next((c for c in ciclos if c["id"] == st.session_state.ae_ciclo), None)
    render_hero("Avaliações da equipe", f'Ciclo {ciclo["nome"]}' if ciclo else "Nenhum ciclo disponível")
    if aviso := st.session_state.pop("ae_aviso", None):
        alerta(st.empty(), "sucesso", aviso)
    if dados["erros"]:
        alerta(st.empty(), "atencao", "Algumas informações não estão disponíveis. As avaliações atribuídas continuam acessíveis.")
    avaliacoes = [a for a in dados["avaliacoes"] if ciclo and a.get("ciclo_avaliacao_id") == ciclo["id"]]
    render_indicadores(indicadores(avaliacoes))
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        aba = st.segmented_control("Área", ["Avaliações", "Contestações"], default="Avaliações", key="ae_aba", label_visibility="collapsed")
        st.space("stretch")
        st.selectbox("Ciclo", ids, format_func=lambda cid: "Ciclo: " + next(c["nome"] for c in ciclos if c["id"] == cid),
                     key="ae_ciclo", label_visibility="collapsed", placeholder="Nenhum ciclo", disabled=not ids, width=200)
        if st.button("Atualizar", key="ae_atualizar", type="tertiary"):
            invalidar()
            fechar()
            st.rerun()
    if aba == "Contestações":
        with st.container(border=True):
            st.html('<p class="crh-bloco-titulo">Contestações</p>')
            alerta(st.empty(), "atencao", "Não disponível para o perfil Gestor. As contestações são revisadas pelo RH ou Admin; a revisão não altera a nota original.")
        return
    if ciclo:
        _tabela(avaliacoes, dados["organograma"], ciclo)
    else:
        st.html('<p class="crh-meta">Nenhuma avaliação atribuída a você.</p>')
    st.html('<p class="crh-meta">Indicadores referentes às avaliações atribuídas a você como gestor. '
            'Autoavaliação, prazo específico do gestor e contestações não estão disponíveis para consulta nesta tela.</p>'
            '<p class="crh-meta">Nenhuma promoção ou desligamento é decidido automaticamente pela nota.</p>')
    if modal := st.session_state.get("ae_modal"):
        # O alvo precisa continuar entre as atribuições da sessão; o backend confirma novamente a cada operação.
        alvo = next((a for a in avaliacoes if a["id"] == modal["alvo"].get("id")), None)

        if alvo and editavel(alvo):
            pessoa = linhas([alvo], dados["organograma"])[0]["nome"]

            @st.dialog(f"Avaliar {pessoa}", width="small", on_dismiss=fechar)
            def _modal_avaliacao() -> None:
                _conteudo_avaliacao(alvo, ciclo)

            _modal_avaliacao()

        else:
            fechar()
            alerta(st.empty(), "atencao", "Esta avaliação não está disponível para edição.")