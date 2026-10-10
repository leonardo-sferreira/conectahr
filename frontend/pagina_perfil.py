"""
Página "Meu Perfil" (Figma seção 6: 202:175; modais 202:342 e 202:509; tarefas 14 a 16 da change
concluir-frontend-streamlit).

Cartões, como no Figma: Pendências, Dados pessoais, Cargo e departamento, Conta bancária e Organograma.
- Dados pessoais e de cargo são só consulta. "Solicitar alteração cadastral" manda um pedido ao RH
  (`solicitacoes`, tipo `alteracao_cadastral`); o RH confere e aplica.
- A conta bancária a própria pessoa edita (`meus_dados_bancarios` PATCH). Nenhum endpoint daqui recebe
  id: a tela só mostra e altera dados do próprio colaborador, qualquer que seja o perfil (inclusive
  Gestor, que nunca vê a conta de outra pessoa).
- O organograma mostra só nome, cargo e departamento (é o que o backend devolve).

Diferença em relação ao Figma: o modal de alteração cadastral não tem "Comprovante (opcional)",
porque o sistema não recebe arquivo; se o RH precisar de comprovante, pede pela tela Documentos.
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import (
    ApiError,
    central_de_tarefas,
    meu_perfil_colaborador,
    minhas_pendencias_documento,
    organograma,
    salvar_dados_bancarios,
    solicitar_alteracao_cadastral,
)
from perfil_modelo import (
    BANCOS,
    CAMPOS_ALTERACAO,
    TIPOS_CONTA,
    cargo_e_departamento,
    conta_bancaria,
    conta_mascarada,
    dados_pessoais,
    descricao_alteracao,
    organograma_pessoal,
    pendencias,
    validar_alteracao,
    validar_bancarios,
)
from theme import alerta, render_hero, render_topbar

_CACHE = "perfil_cache"
_VALIDADE_CACHE_S = 20


def _carregar(token: str) -> dict:
    """{'perfil', 'central', 'docs', 'org'} por 20 s. Erro do perfil sobe (404 = conta sem colaborador);
    sem as outras consultas, os cartões delas ficam vazios."""
    cache = st.session_state.get(_CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = {"perfil": meu_perfil_colaborador(token)}
    for chave, funcao in (("central", central_de_tarefas), ("docs", minhas_pendencias_documento), ("org", organograma)):
        try:
            dados[chave] = funcao(token)
        except ApiError:
            dados[chave] = None
    st.session_state[_CACHE] = {"em": time.time(), "dados": dados}
    return dados


def _invalidar() -> None:
    st.session_state.pop(_CACHE, None)
    st.session_state.pop("perfil_onboarding_cache", None)


def _fechar() -> None:
    st.session_state.pop("modal_perfil", None)


def _campos(pares: list[tuple[str, str]]) -> str:
    return '<div class="crh-campos-grid">' + "".join(
        f'<div><p class="r">{html.escape(r)}</p><p class="v">{html.escape(str(v))}</p></div>' for r, v in pares
    ) + "</div>"


# ---------------------------------------------------------------------------
# Modais
# ---------------------------------------------------------------------------
@st.dialog("Editar dados bancários", width="medium", on_dismiss=_fechar)
def _modal_bancarios(atual: dict) -> None:
    st.html(
        '<p class="crh-cfg-texto">Esses dados são usados só para o pagamento. RH e Admin consultam; seu gestor '
        "não tem acesso.</p>"
    )
    opcoes = BANCOS + ["Outro banco"]
    banco_atual = atual.get("banco") or ""
    indice = opcoes.index(banco_atual) if banco_atual in BANCOS else (len(BANCOS) if banco_atual else None)
    escolha = st.selectbox("Banco", opcoes, index=indice, placeholder="Escolha o banco", key="pf_banco")
    banco = escolha
    if escolha == "Outro banco":
        banco = st.text_input("Nome do banco", value="" if banco_atual in BANCOS else banco_atual, max_chars=100, key="pf_banco_outro")
    c1, c2, c3 = st.columns([1.2, 1.6, 0.8])
    agencia = c1.text_input("Agência", value=atual.get("agencia") or "", max_chars=10, key="pf_agencia")
    conta = c2.text_input("Conta", value=atual.get("conta") or "", max_chars=20, key="pf_conta")
    digito = c3.text_input("Dígito", value=atual.get("digito") or "", max_chars=2, key="pf_digito")
    tipos = list(TIPOS_CONTA)
    tipo = st.radio(
        "Tipo de conta", tipos, format_func=TIPOS_CONTA.get, horizontal=True, key="pf_tipo",
        index=tipos.index(atual["tipo_conta"]) if atual.get("tipo_conta") in tipos else 0,
    )
    st.html(
        f'<div class="crh-incluso"><p class="n" style="margin:0">A alteração fica registrada na auditoria com a conta '
        f"mascarada{(' (' + html.escape(conta_mascarada(conta)) + ')') if conta else ''}.</p></div>"
    )
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="pf_bancarios_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Salvar dados bancários", type="primary", key="pf_bancarios_salvar"):
            erros = validar_bancarios(banco or "", agencia, conta, digito, tipo)
            if erros:
                alerta(slot, "erro", " ".join(erros.values()))
                return
            try:
                salvar_dados_bancarios(st.session_state.token, banco.strip(), agencia.strip(), conta.strip(), digito.strip().upper(), tipo)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _invalidar()
            _fechar()
            for chave in ("pf_banco", "pf_banco_outro", "pf_agencia", "pf_conta", "pf_digito", "pf_tipo"):
                st.session_state.pop(chave, None)
            st.session_state.aviso_toast = "Dados bancários atualizados."
            st.rerun()


@st.dialog("Solicitar alteração cadastral", width="medium", on_dismiss=_fechar)
def _modal_alteracao(valores_atuais: dict) -> None:
    st.html(
        '<p class="crh-cfg-texto">Dados pessoais e de cargo não são editados direto. O pedido vai para o RH, que '
        "confere e aplica no cadastro.</p>"
    )
    campo = st.selectbox("Campo a alterar", CAMPOS_ALTERACAO, index=None, placeholder="Escolha o campo", key="pf_alt_campo")
    atual = valores_atuais.get(campo, "") if campo else ""
    st.text_input("Valor atual", value=atual, disabled=True, key=f"pf_alt_atual_{campo or 'nenhum'}")
    novo = st.text_input("Novo valor", max_chars=1500, key="pf_alt_novo")
    motivo = st.text_area("Motivo", max_chars=400, key="pf_alt_motivo", height=80)
    st.html(
        '<div class="crh-incluso"><p class="n" style="margin:0">Você acompanha o status na Central de Pendências: '
        "recebida → em análise → atendida ou indeferida. Se o RH precisar de comprovante, ele pede pela tela Documentos.</p></div>"
    )
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="pf_alt_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Enviar solicitação", type="primary", key="pf_alt_enviar"):
            erro_campo = validar_alteracao(campo, novo, atual)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                solicitar_alteracao_cadastral(st.session_state.token, descricao_alteracao(campo, atual, novo, motivo))
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _fechar()
            for chave in ("pf_alt_campo", "pf_alt_novo", "pf_alt_motivo"):
                st.session_state.pop(chave, None)
            st.session_state.aviso_toast = "Solicitação enviada ao RH."
            st.rerun()


# ---------------------------------------------------------------------------
def _cartao_pendencias(itens: list[dict]) -> None:
    with st.container(key="perfil_card_pendencias"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html(
                f'<div class="crh-pf-titulo"><span class="crh-pf-contador">{len(itens)}</span>'
                '<p class="crh-cfg-titulo">Pendências</p></div>',
                width="content",
            )
            st.space("stretch")
            if st.button("Ver todas →", type="tertiary", key="pf_ver_pendencias"):
                st.toast("A Central de Pendências ainda está em construção.")
        if not itens:
            st.html('<p class="crh-meta">Nada pendente com você agora.</p>')
            return
        st.html(
            '<div class="crh-pf-lista">' + "".join(
                f'<div class="crh-pf-item"><span class="p"></span><div><p class="t">{html.escape(i["titulo"])}</p>'
                f'<p class="d">{html.escape(i["detalhe"])}</p></div></div>'
                for i in itens
            ) + "</div>"
        )


def _cartao_campos(chave: str, titulo: str, pares, acao=None) -> None:
    with st.container(key=chave):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html(f'<p class="crh-cfg-titulo">{html.escape(titulo)}</p>', width="content")
            st.space("stretch")
            if acao:
                acao()
        st.html(_campos(pares))


def _cartao_organograma(org: dict | None) -> None:
    with st.container(key="perfil_card_org"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html('<p class="crh-cfg-titulo">Organograma</p>', width="content")
            st.space("stretch")
            if st.button("Ver organograma completo →", type="tertiary", key="pf_ver_org"):
                st.toast("O organograma completo ainda está em construção.")
        if org is None or org["voce"] is None:
            st.html('<p class="crh-meta">Não foi possível montar o organograma agora.</p>')
            return

        def cartao(p, destaque=False):
            return (
                f'<div class="crh-org-pessoa{" voce" if destaque else ""}"><span class="a">{html.escape(p["iniciais"])}</span>'
                f'<div><p class="t">{html.escape(p["nome"])}{" (você)" if destaque else ""}</p><p class="d">{html.escape(p["detalhe"])}</p></div></div>'
            )

        partes = []
        if org["gestor"]:
            partes += [cartao(org["gestor"]), '<p class="crh-org-seta">↓</p>']
        partes.append(cartao(org["voce"], destaque=True))
        if org["colegas"]:
            partes.append('<p class="crh-org-seta">↓ colegas de equipe</p>')
            partes.append('<div class="crh-org-linha">' + "".join(cartao(c) for c in org["colegas"]) + "</div>")
            if org["mais"]:
                partes.append(f'<p class="crh-meta">e mais {org["mais"]} colega{"s" if org["mais"] > 1 else ""}</p>')
        st.html('<div class="crh-org">' + "".join(partes) + "</div>")


def pagina_perfil() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Meu Perfil", "Dados pessoais, cargo, conta bancária e hierarquia")

    with st.spinner("Carregando seu perfil..."):
        try:
            dados, erro = _carregar(token), None
        except ApiError as falha:
            dados, erro = None, falha
    if erro is not None:
        if erro.status_code == 404:
            st.html(
                '<div class="crh-painel crh-bloco"><p class="crh-bloco-titulo">Sem cadastro de colaborador</p>'
                '<p class="crh-meta">Sua conta não tem cadastro de colaborador, então não há dados pessoais, cargo nem conta bancária para mostrar.</p></div>'
            )
        else:
            alerta(st.empty(), "erro", erro.message)
        return

    perfil = dados["perfil"]
    colaborador = perfil.get("colaborador") or {}
    org_bruto = dados["org"] or {}
    departamento = perfil.get("departamento") or {}
    org = organograma_pessoal(org_bruto, colaborador.get("id"), departamento) if dados["org"] else None
    nome_gestor = org["gestor"]["nome"] if org and org["gestor"] else None

    _cartao_pendencias(pendencias(dados["central"], (dados["docs"] or {}).get("pendencias") or [], date.today()))

    pessoais = dados_pessoais(perfil, usuario.get("email"))

    def acao_alteracao():
        if st.button("Solicitar alteração cadastral", type="tertiary", key="pf_btn_alteracao"):
            st.session_state.modal_perfil = "alteracao"

    _cartao_campos("perfil_card_pessoais", "Dados pessoais", pessoais, acao_alteracao)
    _cartao_campos("perfil_card_cargo", "Cargo e departamento", cargo_e_departamento(perfil, nome_gestor))

    conta = conta_bancaria(perfil)

    def acao_bancarios():
        if st.button("Editar dados bancários" if conta else "Cadastrar dados bancários", type="primary", key="pf_btn_bancarios"):
            st.session_state.modal_perfil = "bancarios"

    with st.container(key="perfil_card_banco"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html('<p class="crh-cfg-titulo">Conta bancária</p>', width="content")
            st.space("stretch")
            acao_bancarios()
        if conta:
            st.html(_campos(conta))
        else:
            st.html('<p class="crh-meta">Nenhuma conta cadastrada. Cadastre para receber o pagamento.</p>')
        st.html('<p class="crh-cfg-nota">Visível para RH e Admin apenas para fins de pagamento — seu gestor não tem acesso a estes dados.</p>')

    _cartao_organograma(org)

    modal = st.session_state.get("modal_perfil")
    if modal == "bancarios":
        _modal_bancarios(colaborador)
    elif modal == "alteracao":
        valores = dict(pessoais)
        valores["E-mail pessoal"] = colaborador.get("email_pessoal") or "—"
        _modal_alteracao(valores)

