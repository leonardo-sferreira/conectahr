"""
Página "Início" — fiel ao nó 62:38 do protótipo Figma: saudação, quatro
indicadores, comunicados internos, aniversariantes do mês e atalho para o FAQ.

Dados reais do backend (cada bloco falha isolado, mostrando "—" em vez de
derrubar a tela inteira):
- Pendências: central_de_tarefas (pendências pessoais + filas de decisão do perfil).
- Banco de horas: meu_banco_horas (saldo = créditos - débitos).
- Aniversariantes: colaboradores/aniversariantes.
- Comunicados: meus_comunicados (já filtrados por vigência e público-alvo).
- Dias de férias: ainda não existe endpoint de saldo de férias no backend,
  então o card mostra "—" até ele existir.
- Termômetro de humor (Figma 563:932 e 563:971; change termometro-de-humor): humor (GET e POST). O cartão aparece
  enquanto a pessoa não respondeu o ciclo de 10 dias; "Agora não" esconde até a próxima sessão. Respondido o ciclo,
  a rota não é chamada de novo nesta sessão.
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import ApiError, aniversariantes, central_de_tarefas, meu_banco_horas, meu_humor, meus_comunicados, responder_humor
from humor_modelo import MOTIVOS, OPCOES, periodo, proximo, validar_resposta
from onboarding_dados import carregar as carregar_onboarding
from onboarding_modelo import card_inicio
from theme import alerta, render_barra_progresso, render_linhas_onboarding, render_titulo_cartao, render_topbar

_DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
_MESES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]
_PUBLICO_ALVO = {"todos": "todos os colaboradores", "departamento": "seu departamento"}


def _consultar(funcao, token: str) -> dict | None:
    try:
        return funcao(token)
    except ApiError:
        return None


def _data_extenso(hoje: date) -> str:
    return f"{_DIAS_SEMANA[hoje.weekday()]}, {hoje.day:02d} de {_MESES[hoje.month - 1]} de {hoje.year}"


def _total_pendencias(central: dict) -> int:
    total = int(bool(central.get("minha_senha_primeiro_acesso"))) + int(bool(central.get("meu_cadastro_incompleto")))
    for chave in ("minhas_ferias_pendentes", "fila_ferias_pendentes", "fila_documentos_pendentes", "fila_desligamentos_pendentes"):
        total += len(central.get(chave) or [])
    return total


def _formatar_saldo(horas: float) -> tuple[str, str]:
    """Saldo decimal (ex.: 3.3333) -> ("+3h20", classe CSS de cor)."""
    minutos = round(abs(horas) * 60)
    sinal = "+" if horas > 0 else "-" if horas < 0 else ""
    classe = "positivo" if horas > 0 else "negativo" if horas < 0 else ""
    return f"{sinal}{minutos // 60}h{minutos % 60:02d}", classe


def _meta_comunicado(comunicado: dict) -> str:
    publico = comunicado.get("publico_alvo")
    alvo = comunicado.get("perfil_alvo") if publico == "perfil" else _PUBLICO_ALVO.get(publico, "")
    partes = [alvo] if alvo else []
    if comunicado.get("data_fim"):
        partes.append("vigente até " + date.fromisoformat(comunicado["data_fim"][:10]).strftime("%d/%m/%Y"))
    return " · ".join(partes)


def _card_onboarding(token: str, usuario: dict) -> None:
    """Card "Seu onboarding: N de 13 etapas" no topo do Início enquanto o onboarding não termina
    (Figma 309:1446). Falha de rede ou ausência de onboarding: o card simplesmente não aparece."""
    try:
        dados = carregar_onboarding(token, usuario.get("colaborador_id"), usar_cache=True)
    except ApiError:
        return
    card = card_inicio(dados["itens"], dados["onboarding"], dados["docs"]) if dados else None
    if not card:
        return
    esquerda, direita = st.columns([664, 420], gap="medium")
    with esquerda:
        with st.container(key="onb_inicio"):
            render_titulo_cartao(card["titulo"])
            render_barra_progresso("Progresso", card["percentual"])
            render_linhas_onboarding([card["proxima"]])
            if st.button("Continuar onboarding →", type="primary", key="btn_continuar_onb"):
                st.session_state.ir_meu_onboarding = True
                st.rerun()
    with direita:
        with st.container(key="onb_pendencias"):
            render_titulo_cartao("Pendências")
            if card["pendencias"]:
                render_linhas_onboarding(
                    [{"titulo": p["titulo"], "detalhe": p["detalhe"], "badge": p["badge"], "tipo": "amb"} for p in card["pendencias"]]
                )
            else:
                st.html('<p class="crh-meta">Nenhuma pendência de documento.</p>')


_HUMOR_CACHE_S = 60


def _card_humor(token: str, usuario: dict) -> None:
    """Termômetro de humor: a pergunta do ciclo de 10 dias, enquanto a pessoa não respondeu."""
    if not usuario.get("colaborador_id") or st.session_state.get("hm_oculto"):
        return
    if obrigado := st.session_state.get("hm_obrigado"):
        st.html('<div class="crh-hm-ok"><div class="bola"></div><div><p class="t">Obrigado! Sua resposta entrou no termômetro deste ciclo.</p>'
                f'<p class="s">O próximo abre em {html.escape(obrigado)}. Se precisar conversar, use o Canal de denúncias ou fale com o RH.</p></div></div>')
        return
    estado = st.session_state.get("hm_estado")
    if estado is None or (not estado["respondeu"] and time.time() - estado["em"] > _HUMOR_CACHE_S):
        try:
            dados = meu_humor(token)
        except ApiError:
            return
        estado = {"em": time.time(), "ciclo": int(dados.get("ciclo") or 0), "respondeu": bool(dados.get("respondeu"))}
        st.session_state.hm_estado = estado
    if estado["respondeu"]:
        return
    rotulos = {n: r for n, r, _ in OPCOES}
    with st.container(key="cfg_card_hm"):
        st.html(f'<div class="crh-hm-topo"><div><p class="crh-cfg-titulo">Como você está se sentindo no trabalho?</p>'
                '<p class="crh-meta">Termômetro de humor · anônimo · leva 5 segundos. Ninguém vê sua resposta: o RH e o gestor só veem a média do setor.</p></div>'
                f'<p class="crh-hm-ciclo">Ciclo de {html.escape(periodo(estado["ciclo"]))}</p></div>')
        nota = st.segmented_control("Como você está", list(rotulos), format_func=rotulos.get, key="hm_nota", label_visibility="collapsed",
                                  width="stretch")
        with st.container(horizontal=True, vertical_alignment="bottom"):
            motivo = st.selectbox("O que mais pesou? (opcional)", list(MOTIVOS), index=None, format_func=MOTIVOS.get, placeholder="Escolha, se quiser",
                                  key="hm_motivo")
            if st.button("Agora não", key="hm_agora"):
                st.session_state.hm_oculto = True
                st.rerun()
            enviar = st.button("Enviar", type="primary", key="hm_enviar")
        slot = st.empty()
        if enviar:
            erro = validar_resposta(nota, motivo)
            if erro:
                alerta(slot, "erro", erro)
                return
            try:
                responder_humor(token, nota, motivo)
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            st.session_state.hm_estado = dict(estado, respondeu=True)
            st.session_state.hm_obrigado = proximo(estado["ciclo"])
            for chave in ("hm_nota", "hm_motivo"):
                st.session_state.pop(chave, None)
            st.rerun()


def pagina_inicio() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    primeiro_nome = usuario["nome"].split()[0]

    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)

    with st.spinner("Carregando..."):
        central = _consultar(central_de_tarefas, token)
        banco = _consultar(meu_banco_horas, token)
        aniv = _consultar(aniversariantes, token)
        comunicados = _consultar(meus_comunicados, token)

    st.html(
        f"""
        <div class="crh-hero">
          <div class="crh-hero-titulo">
            <div class="crh-hero-barra"></div>
            <p>Olá, {html.escape(primeiro_nome)}</p>
          </div>
          <p class="crh-hero-sub">{_data_extenso(date.today())} — bem-vindo de volta ao ConectaRH</p>
        </div>
        """
    )

    _card_onboarding(token, usuario)
    _card_humor(token, usuario)

    lista_aniv = aniv.get("aniversariantes", []) if aniv else []
    pendencias = str(_total_pendencias(central)) if central else "—"
    saldo, classe_saldo = _formatar_saldo(float(banco.get("saldo_horas") or 0)) if banco else ("—", "")
    total_aniv = str(len(lista_aniv)) if aniv else "—"

    stats = [
        ("Pendências", pendencias, ""),
        ("Dias de férias", "—", ""),
        ("Banco de horas", saldo, classe_saldo),
        ("Aniversariantes no mês", total_aniv, ""),
    ]
    st.html(
        '<div class="crh-linha">'
        + "".join(
            f'<div class="crh-painel crh-stat"><p class="crh-stat-rotulo">{rotulo}</p>'
            f'<p class="crh-stat-valor {classe}">{valor}</p></div>'
            for rotulo, valor, classe in stats
        )
        + "</div>"
    )

    if comunicados is None:
        itens_comunicados = '<p class="crh-meta">Não foi possível carregar os comunicados.</p>'
    elif not comunicados.get("comunicados"):
        itens_comunicados = '<p class="crh-meta">Nenhum comunicado no momento.</p>'
    else:
        itens_comunicados = "".join(
            f'<div class="crh-comunicado"><p class="crh-com-titulo">{html.escape(c["titulo"])}</p>'
            f'<p class="crh-meta">{html.escape(_meta_comunicado(c))}</p></div>'
            for c in comunicados["comunicados"]
        )

    if aniv is None:
        itens_aniv = '<p class="crh-meta">Não foi possível carregar os aniversariantes.</p>'
    elif not lista_aniv:
        itens_aniv = '<p class="crh-meta">Nenhum aniversariante este mês.</p>'
    else:
        itens_aniv = "".join(
            f'<div class="crh-aniv"><div class="crh-aniv-icone">🎂</div>'
            f'<p class="crh-aniv-nome">{html.escape(a["nome"])}</p>'
            f'<p class="crh-meta">{html.escape(a["aniversario"])}</p></div>'
            for a in lista_aniv
        )

    st.html(
        f"""
        <div class="crh-linha">
          <div class="crh-painel crh-bloco flex">
            <p class="crh-bloco-titulo">Comunicados internos</p>
            {itens_comunicados}
          </div>
          <div class="crh-painel crh-bloco fixo">
            <p class="crh-bloco-titulo">Aniversariantes do mês</p>
            {itens_aniv}
          </div>
        </div>
        """
    )

    with st.container(horizontal=True, vertical_alignment="center", key="inicio_faq"):
        st.html('<div class="crh-faq" style="padding:0"><div><p class="crh-faq-titulo">Dúvidas sobre férias, ponto ou documentos?</p>'
                '<p class="crh-meta">Consulte a base de conhecimento do RH</p></div></div>', width="stretch")
        if st.button("Ver FAQ →", type="tertiary", key="inicio_ver_faq"):
            st.session_state.ir_faq = True
            st.rerun()
