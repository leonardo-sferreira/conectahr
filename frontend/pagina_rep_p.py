"""
Página "Ponto eletrônico (REP-P)" do grupo RH (Figma 467:834; change ponto-rep-p-e-ferias-clt, tarefa 5.3). Só RH e Admin.

Quatro cartões:
- Empregador: tipo de identificador, CNPJ ou CPF, CNO ou CAEPF, razão social e local da prestação de serviço. Mudar o
  empregador grava um registro tipo 2 no AFD com o CPF de quem salvou (o backend decide e audita).
- Programa (REP-P) e tratamento (PTRP): registro no INPI, desenvolvedor, nome e versão do PTRP (AFD tipo 1, AEJ tipo 08).
  Os dois cartões gravam pelo mesmo `PUT empregador`, que recebe tudo junto.
- Disponibilidade do serviço de ponto: registra a indisponibilidade (08) e a volta (07) no AFD (tipo 6).
- Arquivos para a fiscalização: período e os botões "Gerar AFD" e "Gerar AEJ". O backend (`rep/afd` e `rep/aej`, ambos
  auditados) entrega os registros; o arquivo é montado aqui (`rep_modelo`) com o nome do leiaute e baixado. O AFD gerado
  passa pela conferência (`conferir_afd`) antes de ir para o botão de baixar.

Diferenças do Figma: a disponibilidade mostra só o estado atual (o backend não guarda desde quando), e a lista de
arquivos gerados é a da sessão (o histórico completo fica na auditoria).
"""

import html
from datetime import date, datetime, timedelta

import streamlit as st

import rep_modelo as rm
from api_client import ApiError, dados_aej, dados_afd, empregador_rep, evento_rep, salvar_empregador_rep
from campos import campo
from theme import alerta, render_hero, render_topbar

TIPOS_ID = {"cnpj": "CNPJ", "cpf": "CPF"}
AVISO_ASSINATURA = ('Os arquivos saem sem a assinatura eletrônica ICP-Brasil (.p7s), que este projeto não faz. A última linha traz o '
                    'texto "ASSINATURA_DIGITAL_EM_ARQUIVO_P7S", como pede o leiaute.')
# Campo do formulário -> chave do widget.
CAMPOS = {
    "tipo_identificador": "rep_tipo", "identificador": "rep_identificador", "cno_caepf": "rep_cno",
    "razao_social": "rep_razao", "local_prestacao": "rep_local", "inpi_registro": "rep_inpi",
    "desenvolvedor_identificador": "rep_dev_id", "desenvolvedor_nome": "rep_dev_nome", "desenvolvedor_email": "rep_dev_email",
    "ptrp_nome": "rep_ptrp_nome", "ptrp_versao": "rep_ptrp_versao",
}


def _cabecalho(titulo: str, nota: str) -> None:
    st.html(f'<div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap">'
            f'<p class="crh-cfg-titulo">{html.escape(titulo)}</p><p class="crh-cfg-nota">{html.escape(nota)}</p></div>')


def _carregar(token: str) -> dict | None:
    if "rep_empregador" not in st.session_state:
        empregador = empregador_rep(token).get("empregador")
        st.session_state.rep_empregador = empregador
        for campo_api, chave in CAMPOS.items():
            valor = (empregador or {}).get(campo_api)
            st.session_state[chave] = (valor or "cnpj") if campo_api == "tipo_identificador" else (valor or "")
    return st.session_state.rep_empregador


def _formulario() -> dict:
    dados = {campo_api: st.session_state.get(chave) for campo_api, chave in CAMPOS.items()}
    for chave in ("identificador", "cno_caepf", "desenvolvedor_identificador"):
        dados[chave] = rm._digitos(dados[chave])
    dados["desenvolvedor_tipo_identificador"] = "cpf" if len(dados["desenvolvedor_identificador"]) == 11 else "cnpj"
    return {k: (v.strip() if isinstance(v, str) else v) for k, v in dados.items()}


def _salvar(slot, aviso: str) -> None:
    dados = _formulario()
    if erro := rm.validar_empregador(dados):
        alerta(slot, "erro", erro)
        return
    try:
        resposta = salvar_empregador_rep(st.session_state.token, dados)
    except ApiError as erro_api:
        alerta(slot, "erro", erro_api.message)
        return
    st.session_state.pop("rep_empregador", None)
    st.session_state.aviso_toast = aviso + (" O AFD recebeu o registro de alteração (tipo 2)." if resposta.get("registro_tipo_2") else "")
    st.rerun()


def _cartao_empregador() -> None:
    with st.container(key="cfg_card_rep_emp"):
        _cabecalho("Empregador", "Usado no comprovante, no espelho, no AFD e no AEJ")
        c1, c2, c3 = st.columns(3)
        c1.selectbox("Tipo de identificador", list(TIPOS_ID), format_func=TIPOS_ID.get, key="rep_tipo")
        rotulo = TIPOS_ID.get(st.session_state.get("rep_tipo"), "CNPJ")
        campo(c2, rotulo, "numero", "rep_identificador", max_chars=14, placeholder="só números")
        campo(c3, "CNO ou CAEPF (opcional)", "numero", "rep_cno", max_chars=14, placeholder="—")
        campo(st, "Razão social", "texto", "rep_razao", max_chars=150)
        campo(st, "Local da prestação de serviço", "endereco", "rep_local", max_chars=100)
        slot = st.empty()
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html('<p class="crh-cfg-nota">Cada alteração entra no AFD (registro tipo 2) com o seu CPF e fica na auditoria.</p>')
            if st.button("Salvar empregador", type="primary", key="rep_salvar_emp"):
                _salvar(slot, "Empregador salvo.")


def _cartao_programa() -> None:
    with st.container(key="cfg_card_rep_prog"):
        _cabecalho("Programa (REP-P) e tratamento (PTRP)", "Usado no comprovante, no AFD (tipo 1) e no AEJ (tipo 08)")
        c1, c2 = st.columns(2)
        campo(c1, "Registro do programa no INPI", "texto", "rep_inpi", max_chars=17, placeholder="BR512026000000-0")
        campo(c2, "Desenvolvedor (CNPJ ou CPF)", "numero", "rep_dev_id", max_chars=14, placeholder="só números")
        campo(c1, "Nome do desenvolvedor", "texto", "rep_dev_nome", max_chars=150)
        campo(c2, "E-mail do desenvolvedor", "email", "rep_dev_email", max_chars=50)
        campo(c1, "Nome do PTRP", "texto", "rep_ptrp_nome", max_chars=150, placeholder="ConectaRH Ponto")
        campo(c2, "Versão", "texto", "rep_ptrp_versao", max_chars=8, placeholder="1.0")
        slot = st.empty()
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Salvar programa", type="primary", key="rep_salvar_prog"):
                _salvar(slot, "Programa salvo.")


def _cartao_disponibilidade(empregador: dict | None) -> None:
    with st.container(key="cfg_card_rep_disp"):
        st.html('<p class="crh-cfg-titulo">Disponibilidade do serviço de ponto</p>')
        disponivel = bool(empregador and empregador.get("servico_disponivel", True))
        slot = st.empty()
        with st.container(horizontal=True, vertical_alignment="center"):
            if not empregador:
                st.html('<span class="crh-selo neu">Bloqueado: cadastre o empregador</span>')
            elif disponivel:
                st.html('<span class="crh-selo ok">Disponível</span>')
            else:
                st.html('<span class="crh-selo err">Indisponível</span>')
            st.space("stretch")
            rotulo = "Registrar indisponibilidade" if disponivel or not empregador else "Registrar volta do serviço"
            if st.button(rotulo, key="rep_evento", disabled=not empregador):
                try:
                    evento_rep(st.session_state.token, "08" if disponivel else "07")
                except ApiError as erro:
                    alerta(slot, "erro", erro.message)
                    return
                st.session_state.pop("rep_empregador", None)
                st.session_state.aviso_toast = "Indisponibilidade registrada no AFD (código 08)." if disponivel else "Volta do serviço registrada no AFD (código 07)."
                st.rerun()
        st.html('<p class="crh-cfg-nota">Registra no AFD (tipo 6) a indisponibilidade (código 08) e a volta (código 07), com data e hora.</p>')


def _mes_anterior() -> tuple[date, date]:
    primeiro = date.today().replace(day=1)
    fim = primeiro - timedelta(days=1)
    return fim.replace(day=1), fim


def _contar(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _gerar(tipo: str, inicio: date, fim: date, slot) -> None:
    de, ate = inicio.isoformat(), fim.isoformat()
    token = st.session_state.token
    try:
        if tipo == "AFD":
            resposta = dados_afd(token, de, ate)
            conteudo = rm.gerar_afd(resposta.get("empregador") or {}, resposta.get("registros") or [], de, ate)
            nome = rm.nome_afd(resposta.get("empregador") or {})
            quantidade = _contar(len(resposta.get("registros") or []), "registro", "registros")
            if problemas := rm.conferir_afd(conteudo):
                alerta(slot, "erro", "O AFD gerado não passou na conferência: " + "; ".join(problemas[:3]))
                return
        else:
            dados = rm.preparar_aej(dados_aej(token, de, ate), de, ate)
            conteudo = rm.gerar_aej(dados, de, ate)
            nome = rm.nome_aej(dados["empregador"])
            quantidade = _contar(len(dados["vinculos"]), "vínculo", "vínculos")
    except ApiError as erro:
        alerta(slot, "erro", erro.message)
        return
    gerados = st.session_state.setdefault("rep_gerados", [])
    gerados.insert(0, {"tipo": tipo, "nome": nome, "conteudo": conteudo, "periodo": f"{inicio:%d/%m} a {fim:%d/%m/%Y}",
                       "quantidade": quantidade, "em": datetime.now().strftime("%d/%m/%Y %H:%M")})


def _cartao_arquivos(empregador: dict | None) -> None:
    with st.container(key="cfg_card_rep_arq"):
        _cabecalho("Arquivos para a fiscalização", "Leiautes do MTE de 31/07/2026 · AFD 004 · AEJ 002")
        padrao_de, padrao_ate = _mes_anterior()
        c1, c2, c3, c4 = st.columns([3, 3, 1.2, 1.2], vertical_alignment="bottom")
        inicio = c1.date_input("De", value=padrao_de, format="DD/MM/YYYY", key="rep_de")
        fim = c2.date_input("Até", value=padrao_ate, format="DD/MM/YYYY", key="rep_ate")
        slot = st.empty()
        clicou = None
        if c3.button("Gerar AFD", type="primary", key="rep_gerar_afd", disabled=not empregador, width="stretch"):
            clicou = "AFD"
        if c4.button("Gerar AEJ", key="rep_gerar_aej", disabled=not empregador, width="stretch"):
            clicou = "AEJ"
        if clicou:
            if not inicio or not fim or fim < inicio:
                alerta(slot, "erro", "A data final deve ser igual ou posterior à inicial.")
            else:
                _gerar(clicou, inicio, fim, slot)
        if empregador:
            st.html(f'<div class="crh-incluso"><p class="n" style="margin:0">Nome do arquivo: {html.escape(rm.nome_afd(empregador))} · '
                    'texto ISO 8859-1, uma linha por registro, em ordem de NSR.</p></div>')
        else:
            alerta(st.empty(), "atencao", "Cadastre o empregador para gerar os arquivos.")
        alerta(st.empty(), "atencao", AVISO_ASSINATURA)
        for i, g in enumerate(st.session_state.get("rep_gerados") or []):
            with st.container(horizontal=True, vertical_alignment="center", key=f"rep_gerado_{i}"):
                st.html(f'<p class="crh-doc-prazo"><b>{g["tipo"]} · {html.escape(g["periodo"])} · {html.escape(g["quantidade"])}</b>'
                        f' <span class="crh-meta">· gerado em {g["em"]}</span></p>')
                st.space("stretch")
                st.download_button(f"Baixar {g['nome']}", g["conteudo"], file_name=g["nome"], mime="text/plain", key=f"rep_baixar_{i}", type="tertiary")


def pagina_rep_p() -> None:
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Ponto eletrônico (REP-P)",
                "Dados do empregador e do programa, disponibilidade do serviço e os arquivos AFD e AEJ (Portaria MTP nº 671/2021)")
    if str(usuario.get("perfil", "")).upper() not in ("RH", "ADMIN"):
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return
    try:
        with st.spinner("Carregando..."):
            empregador = _carregar(st.session_state.token)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    _cartao_empregador()
    _cartao_programa()
    _cartao_disponibilidade(empregador)
    _cartao_arquivos(empregador)
