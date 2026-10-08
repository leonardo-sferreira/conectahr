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
"""

import html
from datetime import date

import streamlit as st

from api_client import ApiError, aniversariantes, central_de_tarefas, meu_banco_horas, meus_comunicados
from theme import render_topbar

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


def pagina_inicio() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    primeiro_nome = usuario["nome"].split()[0]

    render_topbar(usuario["nome"])

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

    st.html(
        """
        <div class="crh-painel crh-faq">
          <div>
            <p class="crh-faq-titulo">Dúvidas sobre férias, ponto ou documentos?</p>
            <p class="crh-meta">Consulte a base de conhecimento do RH</p>
          </div>
          <p class="crh-faq-link">Ver FAQ →</p>
        </div>
        """
    )
