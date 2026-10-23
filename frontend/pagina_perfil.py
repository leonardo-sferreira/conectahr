"""
Página "Meu Perfil" (Figma seção 6: 202:175; modais 202:342 e 202:509; tarefas 14 a 16 da change
concluir-frontend-streamlit).

Cartões, como no Figma: Pendências, Dados pessoais, Contato e endereço, Cargo e departamento, Conta bancária
e Organograma.
- Telefone, e-mail pessoal e endereço a própria pessoa edita, sem pedido ao RH (`meu_perfil_colaborador`
  PATCH; tarefa 72, Figma 459:1152).
- Nome, CPF, data de nascimento e cargo são só consulta. "Solicitar alteração cadastral" manda um pedido ao RH
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
    preparar_envio_foto,
    remover_minha_foto,
    salvar_contato_endereco,
    salvar_dados_bancarios,
    salvar_minha_foto,
    solicitar_alteracao_cadastral,
    subir_arquivo,
)
from cep import CepErro
from cep import consultar as consultar_cep
from perfil_modelo import (
    BANCOS,
    CAMPOS_ALTERACAO,
    TIPOS_CONTA,
    UFS,
    cargo_e_departamento,
    conta_bancaria,
    contato_e_endereco,
    dados_pessoais,
    descricao_alteracao,
    organograma_pessoal,
    pendencias,
    validar_alteracao,
    validar_bancarios,
    validar_contato,
)
from campos import campo, limpar
from foto_modelo import EXTENSOES, avatar_html, tratar, validar_arquivo
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
    for chave in _CHAVES_CONTATO + _CHAVES_BANCO:  # o próximo "Editar" abre com os dados salvos, não com o que ficou digitado
        st.session_state.pop(chave, None)


def _campos(pares: list[tuple[str, str]]) -> str:
    return '<div class="crh-campos-grid">' + "".join(
        f'<div><p class="r">{html.escape(r)}</p><p class="v">{html.escape(str(v))}</p></div>' for r, v in pares
    ) + "</div>"


# ---------------------------------------------------------------------------
# Modais
# ---------------------------------------------------------------------------
@st.dialog("Editar dados bancários", width="medium", on_dismiss=_fechar)
def _modal_bancarios(atual: dict) -> None:
    opcoes = BANCOS + ["Outro banco"]
    banco_atual = atual.get("banco") or ""
    indice = opcoes.index(banco_atual) if banco_atual in BANCOS else (len(BANCOS) if banco_atual else None)
    escolha = st.selectbox("Banco", opcoes, index=indice, placeholder="Escolha o banco", key="pf_banco")
    banco = escolha
    if escolha == "Outro banco":
        st.session_state.setdefault("pf_banco_outro", "" if banco_atual in BANCOS else banco_atual)
        banco = campo(st, "Nome do banco", "texto", "pf_banco_outro", max_chars=100)
    # Valores atuais pela sessão; agência e conta só números, e o dígito aceita X.
    for chave, valor in (("pf_agencia", atual.get("agencia")), ("pf_conta", atual.get("conta")), ("pf_digito", atual.get("digito"))):
        st.session_state.setdefault(chave, valor or "")
    c1, c2, c3 = st.columns([1.2, 1.6, 0.8])
    agencia = campo(c1, "Agência", "numero", "pf_agencia", max_chars=10)
    conta = campo(c2, "Conta", "numero", "pf_conta", max_chars=20)
    digito = campo(c3, "Dígito", "codigo", "pf_digito", max_chars=2)
    tipos = list(TIPOS_CONTA)
    tipo = st.radio(
        "Tipo de conta", tipos, format_func=TIPOS_CONTA.get, horizontal=True, key="pf_tipo",
        index=tipos.index(atual["tipo_conta"]) if atual.get("tipo_conta") in tipos else 0,
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


_CHAVES_BANCO = ("pf_banco_outro", "pf_agencia", "pf_conta", "pf_digito")
_CHAVES_CONTATO = ("pf_ct_telefone", "pf_ct_email", "pf_ct_cep", "pf_ct_logradouro", "pf_ct_numero", "pf_ct_complemento",
                   "pf_ct_bairro", "pf_ct_cidade", "pf_ct_estado", "pf_ct_cep_msg")


def _buscar_cep() -> None:
    """Ao informar o CEP, preenche logradouro, bairro, cidade e UF (`cep.consultar`: BrasilAPI e, se falhar, ViaCEP).
    Só troca o campo que a busca trouxe; número e complemento ficam com a pessoa. Sem CEP achado, avisa e deixa digitar."""
    try:
        achado = consultar_cep(st.session_state.get("pf_ct_cep"))
    except CepErro as erro:
        st.session_state.pf_ct_cep_msg = ("atencao", str(erro))
        return
    st.session_state.pf_ct_cep = limpar(st.session_state.get("pf_ct_cep"), "numero")[0]  # só os 8 números, como o campo aceita
    for campo in ("logradouro", "bairro", "cidade"):
        if achado[campo]:
            st.session_state[f"pf_ct_{campo}"] = achado[campo]
    if achado["estado"]:
        st.session_state.pf_ct_estado = achado["estado"]
    falta = "o número" if achado["logradouro"] else "a rua, o bairro e o número"
    st.session_state.pf_ct_cep_msg = ("sucesso", f"Endereço encontrado pelo CEP. Confira e informe {falta}.")


@st.dialog("Editar contato e endereço", width="medium", on_dismiss=_fechar)
def _modal_contato(atual: dict) -> None:
    # Valores atuais vão para a sessão uma vez; os campos não recebem `value=`, porque a busca do CEP também escreve
    # neles pela sessão (os dois juntos fazem o Streamlit mostrar um aviso na tela).
    uf = (atual.get("estado") or "").upper()
    # Telefone e CEP já gravados com máscara vêm só com os números (o backend passou a aceitar só números, 20/10/2026).
    for chave, valor in (("pf_ct_telefone", limpar(atual.get("telefone"), "numero")[0]), ("pf_ct_email", atual.get("email_pessoal")),
                         ("pf_ct_cep", limpar(atual.get("cep"), "numero")[0]),
                         ("pf_ct_logradouro", atual.get("logradouro")), ("pf_ct_numero", atual.get("numero")), ("pf_ct_complemento", atual.get("complemento")),
                         ("pf_ct_bairro", atual.get("bairro")), ("pf_ct_cidade", atual.get("cidade"))):
        st.session_state.setdefault(chave, valor or "")
    st.session_state.setdefault("pf_ct_estado", uf if uf in UFS else None)
    d = {}
    c1, c2 = st.columns([1, 1.6])
    d["telefone"] = campo(c1, "Telefone", "numero", "pf_ct_telefone", max_chars=11, placeholder="DDD + número, só números")
    d["email_pessoal"] = campo(c2, "E-mail pessoal", "email", "pf_ct_email", max_chars=255)
    c1, c2 = st.columns([1, 2.6])
    d["cep"] = campo(c1, "CEP", "numero", "pf_ct_cep", max_chars=8, placeholder="Só os 8 números", on_change=_buscar_cep,
                             help="Digite o CEP e aperte Enter: o endereço é preenchido sozinho.")
    d["logradouro"] = campo(c2, "Logradouro", "endereco", "pf_ct_logradouro", max_chars=150)
    c1, c2 = st.columns([1, 2.6])
    d["numero"] = campo(c1, "Número", "numero", "pf_ct_numero", max_chars=10, placeholder="Só números")
    d["complemento"] = campo(c2, "Complemento (opcional)", "endereco", "pf_ct_complemento", max_chars=100, placeholder="Ex.: casa B, apto 12")
    if msg := st.session_state.get("pf_ct_cep_msg"):
        alerta(st.empty(), msg[0], msg[1])
    d["bairro"] = campo(st, "Bairro", "endereco", "pf_ct_bairro", max_chars=100)
    c1, c2 = st.columns([2.6, 1])
    d["cidade"] = campo(c1, "Cidade", "endereco", "pf_ct_cidade", max_chars=100)
    d["estado"] = c2.selectbox("Estado (UF)", UFS, placeholder="UF", key="pf_ct_estado")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="pf_contato_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Salvar contato e endereço", type="primary", key="pf_contato_salvar"):
            erros = validar_contato(d)
            if erros:
                alerta(slot, "erro", " ".join(erros.values()))
                return
            corpo = {k: (v or "").strip() for k, v in d.items()}
            corpo["estado"] = corpo["estado"].upper()
            try:
                salvar_contato_endereco(st.session_state.token, corpo)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _invalidar()
            _fechar()
            for chave in _CHAVES_CONTATO:
                st.session_state.pop(chave, None)
            st.session_state.aviso_toast = "Contato e endereço atualizados."
            st.rerun()


@st.dialog("Solicitar alteração cadastral", width="medium", on_dismiss=_fechar)
def _modal_alteracao(valores_atuais: dict) -> None:
    campo = st.selectbox("Campo a alterar", CAMPOS_ALTERACAO, index=None, placeholder="Escolha o campo", key="pf_alt_campo")
    atual = valores_atuais.get(campo, "") if campo else ""
    st.text_input("Valor atual", value=atual, disabled=True, key=f"pf_alt_atual_{campo or 'nenhum'}")
    novo = st.text_input("Novo valor", max_chars=1500, key="pf_alt_novo")
    motivo = st.text_area("Motivo", max_chars=400, key="pf_alt_motivo", height=80)
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
                st.session_state.ir_central = True
                st.rerun()
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


def _atualizar_foto_da_conta(url: str | None) -> None:
    """O menu da conta passa a mostrar a foto nova (ou as iniciais) sem esperar o cache de 8 minutos."""
    st.session_state.usuario = dict(st.session_state.usuario, tem_foto=bool(url))
    st.session_state.minha_foto = {"em": time.time(), "url": url}
    st.session_state.pop("pf_foto_arquivo", None)
    _invalidar()
    st.session_state.pop("org_cache", None)


def _cartao_foto(token: str, nome: str, foto_url: str | None) -> None:
    """Foto de perfil (Figma 571:1042; change foto-de-perfil): opcional, tratada no servidor do app (256 × 256 WebP, sem
    metadados) e enviada direto ao armazenamento privado."""
    with st.container(key="cfg_card_pf_foto"):
        with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
            st.html(avatar_html(nome, foto_url, 96, "crh-pf-avatar"), width="content")
            with st.container():
                st.html('<p class="crh-cfg-titulo">Foto de perfil</p><p class="crh-meta">Opcional. Aparece no seu perfil, no organograma e no menu '
                        'da conta. JPG, PNG ou WebP de até 2 MB; a foto é recortada quadrada.</p>')
                arquivo = st.file_uploader("Escolher a foto", type=list(EXTENSOES), key="pf_foto_arquivo", label_visibility="collapsed")
                slot = st.empty()
                with st.container(horizontal=True):
                    enviar = st.button("Trocar foto" if foto_url else "Enviar foto", type="primary", key="pf_foto_enviar", disabled=arquivo is None)
                    remover = st.button("Remover foto", key="pf_foto_remover") if foto_url else False
    if enviar and arquivo is not None:
        erro = validar_arquivo(arquivo.name, arquivo.size, arquivo.type)
        if erro:
            alerta(slot, "erro", erro)
            return
        try:
            conteudo = tratar(arquivo.getvalue())
            envio = preparar_envio_foto(token)
            subir_arquivo(envio["upload_url"], conteudo, "image/webp")
            r = salvar_minha_foto(token, envio["caminho"])
        except ValueError as erro_imagem:
            alerta(slot, "erro", str(erro_imagem))
            return
        except ApiError as erro_api:
            alerta(slot, "erro", erro_api.message)
            return
        _atualizar_foto_da_conta(r.get("foto_url"))
        st.session_state.aviso_toast = "Foto atualizada."
        st.rerun()
    if remover:
        try:
            remover_minha_foto(token)
        except ApiError as erro_api:
            alerta(slot, "erro", erro_api.message)
            return
        _atualizar_foto_da_conta(None)
        st.session_state.aviso_toast = "Foto removida. Agora aparecem as suas iniciais."
        st.rerun()


def _cartao_organograma(org: dict | None) -> None:
    with st.container(key="perfil_card_org"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html('<p class="crh-cfg-titulo">Organograma</p>', width="content")
            st.space("stretch")
            if st.button("Ver organograma completo →", type="tertiary", key="pf_ver_org"):
                st.session_state.ir_organograma = True
                st.rerun()
        if org is None or org["voce"] is None:
            st.html('<p class="crh-meta">Não foi possível montar o organograma agora.</p>')
            return

        def cartao(p, destaque=False):
            return (
                f'<div class="crh-org-pessoa{" voce" if destaque else ""}">{avatar_html(p["nome"], p.get("foto_url"), 30)}'
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

    _cartao_foto(token, usuario["nome"], perfil.get("foto_url"))

    _cartao_pendencias(pendencias(dados["central"], (dados["docs"] or {}).get("pendencias") or [], date.today()))

    pessoais = dados_pessoais(perfil, usuario.get("email"))

    def acao_alteracao():
        if st.button("Solicitar alteração cadastral", type="tertiary", key="pf_btn_alteracao"):
            st.session_state.modal_perfil = "alteracao"

    _cartao_campos("perfil_card_pessoais", "Dados pessoais", pessoais, acao_alteracao)

    with st.container(key="perfil_card_contato"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html('<p class="crh-cfg-titulo">Contato e endereço</p>', width="content")
            st.space("stretch")
            if st.button("Editar contato e endereço", type="primary", key="pf_btn_contato"):
                st.session_state.modal_perfil = "contato"
        st.html(_campos(contato_e_endereco(perfil)))
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

    _cartao_organograma(org)
    # Caminho para pedir o desligamento (change fluxo-de-desligamento; o menu do Figma não tem o item).
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Pedir desligamento →", type="tertiary", key="pf_pedir_desligamento"):
            st.session_state.ir_pedir_desligamento = True
            st.rerun()

    modal = st.session_state.get("modal_perfil")
    if modal == "bancarios":
        _modal_bancarios(colaborador)
    elif modal == "contato":
        _modal_contato(colaborador)
    elif modal == "alteracao":
        _modal_alteracao(dict(pessoais))

