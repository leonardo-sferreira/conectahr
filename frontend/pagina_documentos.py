"""
Página "Documentos" (tarefas 26 a 28, 62 e 68 da change concluir-frontend-streamlit).

- Documentos pendentes (Figma 309:1249): aparece no topo enquanto o RH tiver pedido documentos
  que ainda faltam. Tabela com os já enviados ("Ver") e os que faltam ("Enviar →").
- Documentos cadastrais (Figma 41:26): todos os documentos da pessoa, com o selo do status.
- Modal "Enviar documento" (Figma 309:1591).

Endpoints: `meus_documentos`, `minhas_pendencias_documento`, `documentos` (POST) e
`documentos/{id}/arquivo` (abre o arquivo; só dono, RH e Admin; cada abertura é auditada). A tela
não tem opção de excluir: o backend recusa a exclusão física e só o RH arquiva (tarefa 28).

Anexo (change anexo-de-arquivos): o modal recebe o arquivo (PDF, JPG ou PNG, até 10 MB). O plano do Xano
não recebe arquivo, então a tela pede a `documentos/envio_arquivo` um endereço de envio de uso único, manda o
arquivo para o armazenamento privado (Supabase) e cadastra o documento com o `arquivo_url` devolvido.

Campos por tipo (change campos-por-tipo-de-documento): ao escolher o tipo, o modal mostra só os campos dele
(`documentos_modelo.CAMPOS`), validados na tela e de novo no backend.
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import (ApiError, abrir_arquivo_documento, enviar_documento, meus_documentos, minhas_pendencias_documento,
                        preparar_envio_arquivo, subir_arquivo)
from documentos_modelo import (TIPOS_ARQUIVO, TIPOS_ENVIO, campos, extensao, linhas_pendentes, lista_documentos, montar_campos,
                               rotulo_tipo, tem_pendencia_aberta, validar_envio)
from onboarding_dados import invalidar_cache as invalidar_onboarding
from theme import alerta, render_hero, render_lista_documentos, render_topbar

_CACHE = "documentos_cache"
_VALIDADE_CACHE_S = 20


def _carregar(token: str) -> dict:
    """{'documentos': list, 'pendencias': list} guardado por 20 s. Erro de `meus_documentos` sobe;
    sem as pendências, a tela segue só com a lista."""
    cache = st.session_state.get(_CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    documentos = meus_documentos(token).get("documentos") or []
    try:
        pendencias = minhas_pendencias_documento(token).get("pendencias") or []
    except ApiError:
        pendencias = []
    dados = {"documentos": documentos, "pendencias": pendencias}
    st.session_state[_CACHE] = {"em": time.time(), "dados": dados}
    return dados


def _invalidar() -> None:
    st.session_state.pop(_CACHE, None)
    invalidar_onboarding()


def _fechar_modal() -> None:
    st.session_state.pop("modal_documento", None)


def _campos_do_tipo(tipo: str | None) -> dict:
    """Os campos do tipo escolhido (`documentos_modelo.CAMPOS`), dois por linha; devolve chave -> valor. A chave do
    widget leva o tipo, então trocar o tipo começa os campos do zero."""
    valores = {}
    lista = campos(tipo)
    for inicio in range(0, len(lista), 2):
        for coluna, campo in zip(st.columns(2), lista[inicio:inicio + 2]):
            with coluna:
                valores[campo["chave"]] = _widget(tipo, campo)
    return valores


def _widget(tipo: str, campo: dict):
    rotulo = campo["rotulo"] + ("" if campo["obrigatorio"] else " (opcional)")
    chave = f"env_c_{tipo}_{campo['chave']}"
    if campo["tipo"] in ("data", "validade"):
        hoje = date.today()
        maximo = date(hoje.year + 30, 12, 31) if campo["tipo"] == "validade" else hoje
        return st.date_input(rotulo, value=None, min_value=date(1940, 1, 1), max_value=maximo, format="DD/MM/YYYY", key=chave, help=campo["ajuda"])
    if campo["tipo"] == "opcao":
        opcoes = campo["opcoes"]
        return st.selectbox(rotulo, list(opcoes), index=None, format_func=lambda v: opcoes[v], placeholder="Escolha", key=chave, help=campo["ajuda"])
    return st.text_input(rotulo, max_chars=14 if campo["tipo"] == "cpf" else 100, key=chave, help=campo["ajuda"],
                         placeholder="000.000.000-00" if campo["tipo"] == "cpf" else None)


@st.dialog("Enviar documento", width="small", on_dismiss=_fechar_modal)
def _modal_enviar() -> None:
    # O tipo inicial (vindo de "Enviar →") já está em st.session_state.env_tipo (_abrir_modal).
    tipo = st.selectbox(
        "Tipo de documento", TIPOS_ENVIO, index=None, format_func=rotulo_tipo, placeholder="Escolha o tipo", key="env_tipo"
    )
    valores = _campos_do_tipo(tipo)
    arquivo = st.file_uploader(
        "Arquivo",
        type=list(TIPOS_ARQUIVO),
        key="env_arquivo",
        help="PDF ou foto do documento (JPG ou PNG), até 10 MB. No celular, dá para tirar a foto na hora.",
    )
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="btn_env_cancelar"):
            _fechar_modal()
            st.rerun()
        if st.button("Enviar para o RH", type="primary", key="btn_env_enviar"):
            erro_campo = validar_envio(tipo, arquivo.name if arquivo else None, arquivo.size if arquivo else None, valores, date.today())
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            token = st.session_state.token
            colaborador_id = st.session_state.usuario.get("colaborador_id")
            ext = extensao(arquivo.name)
            try:
                with st.spinner("Enviando o arquivo..."):
                    envio = preparar_envio_arquivo(token, colaborador_id, ext)
                    subir_arquivo(envio["upload_url"], arquivo.getvalue(), TIPOS_ARQUIVO[ext])
                    enviar_documento(
                        token,
                        {"colaborador_id": colaborador_id, "tipo": tipo, **montar_campos(tipo, valores), "arquivo_url": envio["arquivo_url"]},
                    )
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _invalidar()
            _fechar_modal()
            for chave in [k for k in st.session_state if str(k).startswith("env_")]:
                st.session_state.pop(chave, None)
            st.session_state.aviso_toast = "Documento enviado. O RH vai conferir."
            st.rerun()


def _abrir_modal(tipo: str | None) -> None:
    """Abre "Enviar documento", já com o tipo quando vem de uma pendência ("Enviar →")."""
    st.session_state.modal_documento = tipo
    st.session_state.env_tipo = tipo


def _abrir_arquivo(token: str, documento_id: int) -> None:
    try:
        resposta = abrir_arquivo_documento(token, documento_id)
        st.session_state.doc_link_aberto = resposta.get("arquivo_url")
        st.session_state.pop("doc_link_erro", None)
    except ApiError as erro:
        st.session_state.doc_link_erro = erro.message
        st.session_state.pop("doc_link_aberto", None)


def _tabela_pendentes(token: str, linhas: list[dict]) -> None:
    if link := st.session_state.get("doc_link_aberto"):
        with st.container(horizontal=True):
            st.html('<p class="crh-meta">Link do arquivo pronto (vale por 5 minutos).</p>', width="content")
            st.link_button("Abrir arquivo", link)
    if erro := st.session_state.pop("doc_link_erro", None):
        alerta(st.empty(), "erro", erro)

    pesos = [5, 1.6, 1.8, 1.2]
    with st.container(key="doc_pendentes"):
        with st.container(key="doc_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ("Documento", "Prazo", "Situação", "")):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        for i, linha in enumerate(linhas):
            chave = f"doc_linf_{i}" if linha["acao"] == "enviar" else f"doc_lin_{i}"
            with st.container(key=chave):
                c_doc, c_prazo, c_sit, c_acao = st.columns(pesos, vertical_alignment="center")
                c_doc.html(
                    f'<div class="crh-doc-cel"><p class="t">{html.escape(linha["titulo"])}</p>'
                    f'<p class="d">{html.escape(linha["detalhe"] or "")}</p></div>'
                )
                c_prazo.html(f'<p class="crh-doc-prazo">{html.escape(linha["prazo"])}</p>')
                c_sit.html(
                    f'<span class="crh-selo {linha["tipo"]}">{html.escape(linha["badge"])}</span>', width="content"
                )
                with c_acao:
                    if linha["acao"] == "enviar":
                        if st.button("Enviar →", type="tertiary", key=f"btn_doc_enviar_{i}"):
                            _abrir_modal(linha["tipo_documento"])
                    elif linha["acao"] == "ver" and linha["documento_id"]:
                        if st.button("Ver", type="tertiary", key=f"btn_doc_ver_{i}"):
                            _abrir_arquivo(token, linha["documento_id"])
                            st.rerun()


def pagina_documentos() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)

    # Carregando
    with st.spinner("Carregando seus documentos..."):
        try:
            dados, erro = _carregar(token), None
        except ApiError as falha:
            dados, erro = None, falha

    # Sem colaborador (conta de RH ou Admin), desligado (403) ou outro erro
    if erro is not None:
        render_hero("Documentos", "Envie e acompanhe seus documentos obrigatórios")
        if erro.status_code == 404:
            st.html(
                '<div class="crh-painel crh-bloco"><p class="crh-bloco-titulo">Nenhum documento por aqui</p>'
                '<p class="crh-meta">Sua conta não tem cadastro de colaborador, então não há documentos para enviar.</p></div>'
            )
        else:
            alerta(st.empty(), "erro", erro.message)
        return

    pendentes = linhas_pendentes(dados["pendencias"], dados["documentos"]) if tem_pendencia_aberta(dados["pendencias"]) else []
    render_hero(
        "Documentos",
        "Documentos obrigatórios da sua admissão" if pendentes else "Envie e acompanhe seus documentos obrigatórios",
    )
    if pendentes:
        _tabela_pendentes(token, pendentes)

    with st.container(horizontal=True, key="doc_topo"):
        st.html('<p class="crh-bloco-titulo">Documentos cadastrais</p>', width="content")
        if st.button("Enviar documento", type="primary", key="btn_doc_novo"):
            _abrir_modal(None)

    if not dados["documentos"]:
        st.html('<p class="crh-meta">Você ainda não enviou nenhum documento.</p>')
    else:
        render_lista_documentos(lista_documentos(dados["documentos"]))

    # O modal fica aberto enquanto a marca estiver na sessão (continua na tela se o app rodar de novo).
    if "modal_documento" in st.session_state:
        _modal_enviar()
