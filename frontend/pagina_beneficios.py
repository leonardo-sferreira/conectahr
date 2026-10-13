"""
Página "Benefícios" (tarefa 82 da change concluir-frontend-streamlit). A conferir com o Figma, que estava fora do ar.

- Todos: "Meus benefícios" — o número de ativos e, para cada um, um item que abre (formato da FAQ) com a operadora, a
  descrição, os links e os materiais (`meus_beneficios`, `beneficio_arquivos/{id}/abrir`); sem valores nem histórico
  (change apresentacao-de-beneficios, pedido do usuário em 13/10/2026).
- RH e Admin, também:
  - "Catálogo": cadastrar benefício (`beneficios` POST), editar a apresentação (`beneficios/{id}` PATCH, com links;
    materiais em `beneficios/{id}/arquivos` e `beneficio_arquivos/{id}/remover`, no Supabase) e ativar ou desativar
    (`beneficios/{id}/status`);
  - "Por colaborador": os benefícios da pessoa (`colaboradores/{id}/beneficios`), vincular um do catálogo e encerrar
    (`colaborador_beneficios/{id}/encerrar`), sem apagar.
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import (
    ApiError,
    abrir_material_beneficio,
    beneficios_catalogo,
    beneficios_da_pessoa,
    cadastrar_beneficio,
    colaboradores,
    editar_beneficio,
    encerrar_beneficio,
    meus_beneficios,
    organograma,
    preparar_material_beneficio,
    registrar_material_beneficio,
    remover_material_beneficio,
    status_beneficio,
    subir_arquivo,
    vincular_beneficio,
)
from beneficios_modelo import (MAX_LINKS, TIPOS, apresentacao, ler_links, linhas, links_texto, moeda, validar_beneficio, validar_material,
                               validar_vinculo)
from documentos_modelo import TIPOS_ARQUIVO, extensao
from cadastro_modelo import perfil
from theme import alerta, render_hero, render_indicadores, render_topbar

_VALIDADE_CACHE_S = 20


def _cache(chave: str, carregar):
    guardado = st.session_state.get("beneficios_cache") or {}
    item = guardado.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = carregar()
    guardado[chave] = {"em": time.time(), "dados": dados}
    st.session_state.beneficios_cache = guardado
    return dados


def _fechar() -> None:
    st.session_state.pop("modal_beneficio", None)


def _concluir(aviso: str) -> None:
    st.session_state.pop("beneficios_cache", None)
    _fechar()
    st.session_state.aviso_toast = aviso
    st.rerun()


def _cartoes(itens: list[dict], encerrados: bool = False) -> None:
    for l in itens:
        operadora = f" · {html.escape(l['operadora'])}" if l["operadora"] else ""
        vigencia = f"De {l['desde']} a {l['ate']}" if l["ate"] else f"Desde {l['desde']}"
        obs = f'<p class="d">{html.escape(l["observacao"])}</p>' if l["observacao"] else ""
        selo = '<span class="crh-selo neu">Encerrado</span>' if encerrados else '<span class="crh-selo ok">Ativo</span>'
        st.html(
            f'<div class="crh-linha-onb"><div class="txt"><p class="t">{html.escape(l["nome"])}</p>'
            f'<p class="d">{html.escape(l["tipo"])}{operadora} · {html.escape(vigencia)}</p>'
            f'<p class="d">Empresa paga {html.escape(l["valor_empresa"])} · Desconto {html.escape(l["desconto"])}</p>{obs}</div>{selo}</div>'
        )


def _meus(token: str) -> None:
    with st.spinner("Carregando..."):
        try:
            dados, erro = _cache("meus", lambda: meus_beneficios(token).get("beneficios") or []), None
        except ApiError as falha:
            dados, erro = None, falha
    if erro is not None:
        if erro.status_code == 404:
            st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">Sua conta ainda não está ligada a um cadastro de funcionário, então não há benefícios.</p></div>')
        else:
            alerta(st.empty(), "erro", erro.message)
        return
    itens = apresentacao(dados, date.today())
    render_indicadores([("Benefícios ativos", str(len(itens)), "verde")])
    if not itens:
        st.html('<p class="crh-meta">Você ainda não tem benefício ativo. Dúvidas: fale com o RH.</p>')
    for b in itens:
        _apresentacao(token, b)
    if erro_material := st.session_state.pop("ben_mat_erro", None):
        alerta(st.empty(), "erro", erro_material)


def _apresentacao(token: str, b: dict) -> None:
    """Um benefício como item que abre (formato da FAQ): operadora, descrição, links e materiais."""
    with st.expander(f"{b['nome']} · {b['tipo']}"):
        if b["operadora"]:
            st.html(f'<p class="crh-meta" style="margin:0">Operadora: {html.escape(b["operadora"])}</p>')
        if b["descricao"]:
            st.html(f'<p class="crh-cfg-texto" style="white-space:pre-wrap;margin:0">{html.escape(b["descricao"])}</p>')
        if b["links"]:
            st.html('<p class="crh-cfg-titulo" style="margin:8px 0 0">Links úteis</p>')
            with st.container(horizontal=True, gap="small"):
                for i, link in enumerate(b["links"]):
                    st.link_button(link["titulo"], link["url"], key=f"ben_link_{b['beneficio_id']}_{i}")
        if b["arquivos"]:
            st.html('<p class="crh-cfg-titulo" style="margin:8px 0 0">Materiais</p>')
            for m in b["arquivos"]:
                with st.container(horizontal=True, vertical_alignment="center"):
                    st.html(f'<p class="crh-cfg-texto" style="margin:0">{html.escape(m.get("nome") or "Material")}</p>', width="stretch")
                    aberto = st.session_state.get("ben_mat_aberto")
                    if aberto and aberto[0] == m["id"]:
                        st.link_button("Abrir arquivo", aberto[1], type="primary", key=f"ben_mat_link_{m['id']}")
                    elif st.button("Abrir", type="tertiary", key=f"ben_mat_{m['id']}"):
                        try:
                            st.session_state.ben_mat_aberto = (m["id"], abrir_material_beneficio(token, m["id"]).get("arquivo_url"))
                        except ApiError as erro:
                            st.session_state.ben_mat_erro = erro.message
                        st.rerun()
        if not (b["operadora"] or b["descricao"] or b["links"] or b["arquivos"]):
            st.html('<p class="crh-meta" style="margin:0">O RH ainda não cadastrou a apresentação deste benefício.</p>')


# ---------------------------------------------------------------------------
# RH e Admin
# ---------------------------------------------------------------------------
@st.dialog("Novo benefício", width="small", on_dismiss=_fechar)
def _modal_novo() -> None:
    nome = st.text_input("Nome", max_chars=100, placeholder="Ex.: Plano de saúde Unimed", key="ben_nome")
    tipo = st.selectbox("Tipo", list(TIPOS), format_func=TIPOS.get, index=None, placeholder="Escolha", key="ben_tipo")
    operadora = st.text_input("Operadora ou fornecedor (opcional)", max_chars=100, key="ben_operadora")
    descricao = st.text_area("Descrição (opcional)", max_chars=500, key="ben_descricao", height=70)
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="ben_novo_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Cadastrar", type="primary", key="ben_novo_ok"):
            erro_campo = validar_beneficio(nome, tipo)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                cadastrar_beneficio(st.session_state.token, nome.strip(), tipo, operadora.strip() or None, descricao.strip() or None)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            for chave in ("ben_nome", "ben_tipo", "ben_operadora", "ben_descricao"):
                st.session_state.pop(chave, None)
            _concluir(f"Benefício {nome.strip()} cadastrado.")


def _abrir_edicao(b: dict) -> None:
    """Abre "Editar benefício" com os dados atuais nos campos."""
    st.session_state.modal_beneficio = ("editar", b["id"])
    st.session_state.ben_ed_nome = b.get("nome") or ""
    st.session_state.ben_ed_tipo = b.get("tipo") if b.get("tipo") in TIPOS else "outro"
    st.session_state.ben_ed_operadora = b.get("operadora") or ""
    st.session_state.ben_ed_descricao = b.get("descricao") or ""
    st.session_state.ben_ed_links = links_texto(b.get("links"))


@st.dialog("Editar benefício", width="medium", on_dismiss=_fechar)
def _modal_editar(b: dict) -> None:
    """Dados e apresentação do benefício (change apresentacao-de-beneficios, D5). Salvar avisa quem tem o benefício;
    anexar e remover material são ações à parte."""
    c1, c2 = st.columns(2)
    nome = c1.text_input("Nome", max_chars=100, key="ben_ed_nome")
    tipo = c2.selectbox("Tipo", list(TIPOS), format_func=TIPOS.get, key="ben_ed_tipo")
    operadora = st.text_input("Operadora ou fornecedor (opcional)", max_chars=100, key="ben_ed_operadora")
    descricao = st.text_area("O que é o benefício", max_chars=2000, key="ben_ed_descricao", height=120,
                             help="Texto que o colaborador lê ao abrir o benefício: o que cobre, como usar, a quem procurar.")
    links_txt = st.text_area("Links úteis (opcional)", key="ben_ed_links", height=80, placeholder="Site da operadora | https://www.exemplo.com.br",
                             help=f"Um por linha, no formato Título | https://endereço. Até {MAX_LINKS}.")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="ben_ed_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Salvar", type="primary", key="ben_ed_ok"):
            links, erro_links = ler_links(links_txt)
            erro_campo = validar_beneficio(nome, tipo) or erro_links
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                editar_beneficio(st.session_state.token, b["id"], nome.strip(), tipo, operadora.strip() or None, descricao.strip() or None, links)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _concluir(f"Benefício {nome.strip()} atualizado. Quem tem o benefício recebe o aviso.")

    st.html('<p class="crh-cfg-titulo" style="margin:12px 0 0">Materiais</p>')
    for m in b.get("arquivos") or []:
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html(f'<p class="crh-cfg-texto" style="margin:0">{html.escape(m.get("nome") or "Material")}</p>', width="stretch")
            if st.button("Remover", type="tertiary", key=f"ben_ed_rm_{m['id']}"):
                try:
                    remover_material_beneficio(st.session_state.token, m["id"])
                except ApiError as erro:
                    alerta(slot, "erro", erro.message)
                    return
                st.session_state.pop("beneficios_cache", None)
                st.rerun()
    if not b.get("arquivos"):
        st.html('<p class="crh-meta" style="margin:0">Nenhum material. Anexe guias, tabelas ou regulamentos para o colaborador ler.</p>')
    c3, c4 = st.columns([1, 1.4])
    nome_material = c3.text_input("Nome do material", max_chars=100, placeholder="Ex.: Guia do plano", key="ben_ed_mat_nome")
    with c4:
        arquivo = st.file_uploader("Arquivo", type=list(TIPOS_ARQUIVO), key="ben_ed_mat_arquivo", help="PDF, JPG ou PNG, até 10 MB.")
    slot_material = st.empty()
    if st.button("Anexar material", key="ben_ed_mat_ok"):
        erro_campo = validar_material(nome_material, arquivo.name if arquivo else None, arquivo.size if arquivo else None)
        if erro_campo:
            alerta(slot_material, "erro", erro_campo)
            return
        ext = extensao(arquivo.name)
        try:
            with st.spinner("Enviando o material..."):
                envio = preparar_material_beneficio(st.session_state.token, b["id"], ext)
                subir_arquivo(envio["upload_url"], arquivo.getvalue(), TIPOS_ARQUIVO[ext])
                registrar_material_beneficio(st.session_state.token, b["id"], nome_material.strip(), envio["caminho"])
        except ApiError as erro:
            alerta(slot_material, "erro", erro.message)
            return
        for chave in ("ben_ed_mat_nome", "ben_ed_mat_arquivo"):
            st.session_state.pop(chave, None)
        st.session_state.pop("beneficios_cache", None)
        st.toast(f"Material {nome_material.strip()} anexado.")
        st.rerun()


@st.dialog("Vincular benefício", width="small", on_dismiss=_fechar)
def _modal_vincular(pessoa: dict, catalogo: list[dict]) -> None:
    ativos = {b["id"]: b for b in catalogo if b.get("ativo", True)}
    st.html(f'<p class="crh-meta" style="margin:0">Para {html.escape(pessoa.get("nome") or "")}</p>')
    bid = st.selectbox("Benefício", list(ativos), format_func=lambda i: f"{ativos[i].get('nome')} — {TIPOS.get(ativos[i].get('tipo'), 'Outro')}", index=None,
                       placeholder="Escolha do catálogo" if ativos else "Cadastre um benefício no Catálogo antes", key="ben_v_id")
    c1, c2 = st.columns(2)
    valor = c1.number_input("A empresa paga (R$/mês)", min_value=0.0, value=0.0, step=10.0, format="%.2f", key="ben_v_valor")
    desconto = c2.number_input("Desconto do colaborador (R$/mês)", min_value=0.0, value=0.0, step=10.0, format="%.2f", key="ben_v_desc")
    c3, c4 = st.columns(2)
    inicio = c3.date_input("Início", value=date.today(), format="DD/MM/YYYY", key="ben_v_inicio")
    fim = c4.date_input("Fim (opcional)", value=None, format="DD/MM/YYYY", key="ben_v_fim")
    obs = st.text_input("Observação (opcional)", max_chars=500, key="ben_v_obs")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="ben_v_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Vincular", type="primary", key="ben_v_ok"):
            erro_campo = validar_vinculo(bid, valor, desconto, inicio, fim)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            dados = {"beneficio_id": bid, "valor_empresa": float(valor), "desconto_colaborador": float(desconto), "data_inicio": inicio.isoformat(),
                     "data_fim": fim.isoformat() if fim else None, "observacao": obs.strip() or None}
            try:
                vincular_beneficio(st.session_state.token, pessoa["id"], dados)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            for chave in ("ben_v_id", "ben_v_valor", "ben_v_desc", "ben_v_inicio", "ben_v_fim", "ben_v_obs"):
                st.session_state.pop(chave, None)
            _concluir(f"{ativos[bid].get('nome')} vinculado a {pessoa.get('nome')}.")


@st.dialog("Encerrar benefício", width="small", on_dismiss=_fechar)
def _modal_encerrar(pessoa: dict, linha: dict) -> None:
    st.html(f'<p class="crh-meta" style="margin:0">{html.escape(linha["nome"])} de {html.escape(pessoa.get("nome") or "")}, desde {html.escape(linha["desde"])}</p>')
    fim = st.date_input("Último dia", value=date.today(), format="DD/MM/YYYY", key="ben_e_fim")
    obs = st.text_input("Motivo (opcional)", max_chars=500, key="ben_e_obs")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="ben_e_voltar"):
            _fechar()
            st.rerun()
        if st.button("Encerrar", type="primary", key="ben_e_ok"):
            try:
                encerrar_beneficio(st.session_state.token, linha["id"], fim.isoformat(), obs.strip() or None)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            for chave in ("ben_e_fim", "ben_e_obs"):
                st.session_state.pop(chave, None)
            _concluir(f"{linha['nome']} de {pessoa.get('nome')} encerrado.")


def _catalogo(token: str) -> None:
    try:
        catalogo = _cache("catalogo", lambda: beneficios_catalogo(token).get("beneficios") or [])
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        st.html('<p class="crh-meta">O catálogo é a lista de benefícios que a empresa oferece. Benefício desativado não aceita novos vínculos; os atuais continuam.</p>', width="stretch")
        if st.button("Novo benefício", type="primary", key="ben_novo"):
            st.session_state.modal_beneficio = ("novo", None)
            st.rerun()
    pesos = [3, 2, 2.2, 1.2, 1, 1.4]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Benefício", "Tipo", "Operadora", "Situação", "", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not catalogo:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhum benefício cadastrado. Use "Novo benefício".</p>')
        for i, b in enumerate(catalogo):
            with st.container(key=f"rh_lin_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(b.get("nome") or "")}</p><p class="d">{html.escape(b.get("descricao") or "")}</p></div>')
                c[1].html(f'<p class="crh-doc-prazo">{html.escape(TIPOS.get(b.get("tipo"), "Outro"))}</p>')
                c[2].html(f'<p class="crh-doc-prazo">{html.escape(b.get("operadora") or "—")}</p>')
                ativo = b.get("ativo", True)
                c[3].html(f'<span class="crh-selo {"ok" if ativo else "neu"}">{"Ativo" if ativo else "Desativado"}</span>', width="content")
                with c[4]:
                    if st.button("Editar", type="tertiary", key=f"ben_editar_{b['id']}"):
                        _abrir_edicao(b)
                        st.rerun()
                with c[5]:
                    if st.button("Desativar" if ativo else "Reativar", type="tertiary", key=f"ben_status_{b['id']}"):
                        try:
                            status_beneficio(token, b["id"], not ativo)
                        except ApiError as erro:
                            st.session_state.ben_erro = erro.message
                            st.rerun()
                        _concluir(f"{b.get('nome')} {'desativado' if ativo else 'reativado'}.")
    if erro := st.session_state.pop("ben_erro", None):
        alerta(st.empty(), "erro", erro)
    modal = st.session_state.get("modal_beneficio")
    if modal and modal[0] == "editar":
        b = next((x for x in catalogo if x.get("id") == modal[1]), None)
        if b is None:
            _fechar()
        else:
            _modal_editar(b)


def _por_colaborador(token: str) -> None:
    try:
        base = _cache("base", lambda: {"colabs": colaboradores(token).get("colaboradores") or [], "org": organograma(token)})
        catalogo = _cache("catalogo", lambda: beneficios_catalogo(token).get("beneficios") or [])
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    deps = {d.get("id"): d.get("nome") for d in base["org"].get("departamentos") or []}
    pessoas = {c["id"]: c for c in sorted(base["colabs"], key=lambda c: (c.get("nome") or "").casefold()) if str(c.get("status") or "").upper() != "DESLIGADO"}
    if not pessoas:
        st.html('<p class="crh-meta">Nenhum colaborador ativo.</p>')
        return
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        pid = st.selectbox("Pessoa", list(pessoas), format_func=lambda i: f"{pessoas[i].get('nome')} — {deps.get(pessoas[i].get('departamento_id')) or '—'}",
                           key="ben_pessoa", label_visibility="collapsed", width=360)
        st.space("stretch")
        if st.button("Vincular benefício", type="primary", key="ben_vincular"):
            st.session_state.modal_beneficio = ("vincular", pid)
            st.rerun()
    pessoa = pessoas[pid]
    try:
        vinculos = _cache(f"pessoa-{pid}", lambda: beneficios_da_pessoa(token, pid).get("beneficios") or [])
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    visao = linhas(vinculos, date.today())
    render_indicadores([
        ("Benefícios ativos", str(len(visao["ativos"])), "verde"),
        ("A empresa paga por mês", visao["total_empresa"], ""),
        ("Desconto do colaborador", visao["total_desconto"], "ambar"),
        ("Encerrados", str(len(visao["encerrados"])), ""),
    ])
    if not visao["ativos"] and not visao["encerrados"]:
        st.html('<p class="crh-meta">Esta pessoa ainda não tem benefício. Use "Vincular benefício".</p>')
    for l in visao["ativos"]:
        with st.container(horizontal=True, vertical_alignment="center", key=f"ben_lin_{l['id']}"):
            _cartoes([l])
            if st.button("Encerrar", type="tertiary", key=f"rh_recusar_ben_{l['id']}"):
                st.session_state.modal_beneficio = ("encerrar", (pid, l["id"]))
                st.rerun()
    if visao["encerrados"]:
        st.html('<p class="crh-bloco-titulo">Histórico</p>')
        _cartoes(visao["encerrados"], encerrados=True)

    modal = st.session_state.get("modal_beneficio")
    if modal and modal[0] == "vincular" and modal[1] == pid:
        _modal_vincular(pessoa, catalogo)
    elif modal and modal[0] == "encerrar" and modal[1][0] == pid:
        linha = next((l for l in visao["ativos"] if l["id"] == modal[1][1]), None)
        if linha is None:
            _fechar()
        else:
            _modal_encerrar(pessoa, linha)


def pagina_beneficios() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    rh = perfil(usuario.get("perfil")) in ("RH", "ADMIN")
    render_hero("Benefícios", "Os benefícios da empresa: valores, descontos e vigência" if rh else "Seus benefícios e como usar cada um")
    if not rh:
        _meus(token)
        return
    abas = ["Meus benefícios", "Catálogo", "Por colaborador"]
    with st.container(key="cfg_abas", width="content"):
        aba = st.segmented_control("Aba", abas, default=abas[0], required=True, key="ben_aba", label_visibility="collapsed")
    if aba == "Meus benefícios":
        _meus(token)
    elif aba == "Catálogo":
        _catalogo(token)
        if (st.session_state.get("modal_beneficio") or (None,))[0] == "novo":
            _modal_novo()
    else:
        _por_colaborador(token)
