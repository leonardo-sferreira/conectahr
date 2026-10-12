"""
Peças de tela do ponto no REP-P usadas pelo colaborador (`pagina_ponto.py`) e pela folha da equipe
(`pagina_folha_ponto.py`): a planilha do mês em `st.dataframe` (design D8, Figma 464:826), o cabeçalho do
art. 84 e o formulário de correção (Figma 465:856 e 465:894). As regras ficam em `ponto_mensal_modelo.py`.
"""

import html

import pandas as pd
import streamlit as st

from ponto_mensal_modelo import colunas_planilha, desconsideraveis, dia_longo, linha_selecionada, linhas_planilha, marcacoes_texto, pares_do_mes, situacao_curta
from ponto_modelo import TIPOS_PEDIDO
from theme import estilo_planilha_ponto


def render_cabecalho(cabecalho: dict) -> None:
    """Cartão "Espelho de ponto eletrônico" com os campos do art. 84."""
    with st.container(key="ponto_espelho_cab"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html(f'<p class="crh-cfg-titulo">{html.escape(cabecalho["titulo"])}</p>', width="stretch")
            st.html(f'<p class="crh-legenda-ponto">{html.escape(cabecalho["emissao"])}</p>', width="content")
        st.html('<div class="crh-espelho-cab">' + "".join(
            f'<div><p class="r">{html.escape(r)}</p><p class="v">{html.escape(v)}</p></div>' for r, v in cabecalho["campos"]) + "</div>")


def render_planilha(linhas: list[dict], chave: str, selecionavel: bool = True) -> dict | None:
    """A planilha do mês, uma linha por dia. Devolve o dia escolhido (linha da planilha) ou None."""
    pares = pares_do_mes(linhas)
    tabela = pd.DataFrame(linhas_planilha(linhas, pares), columns=colunas_planilha(pares))
    estilo = estilo_planilha_ponto(tabela, [l["tom"] for l in linhas])
    altura = 38 + 35 * len(linhas)  # sem rolagem interna: o mês inteiro à vista, como no Figma
    if not selecionavel:
        st.dataframe(estilo, hide_index=True, width="stretch", height=altura, key=chave)
        return None
    evento = st.dataframe(estilo, hide_index=True, width="stretch", height=altura, key=chave, on_select="rerun", selection_mode="single-row")
    return linha_selecionada(linhas, list(evento.selection.rows) if evento else [])


def resumo_do_dia(linha: dict) -> None:
    """O quadro com dia, marcações e situação, no topo do pedido e do ajuste."""
    st.html(
        '<div class="crh-campos crh-campos-direita">'
        f'<p class="r">Dia</p><p class="v">{html.escape(dia_longo(linha["data"]))}</p>'
        f'<p class="r">Marcações</p><p class="v">{html.escape(marcacoes_texto(linha))}</p>'
        f'<p class="r">Situação</p><p class="v"><span class="crh-ponto-status {linha["tom"]}">{html.escape(situacao_curta(linha))}</span></p></div>'
    )


def formulario_pedido(linha: dict, prefixo: str) -> tuple:
    """Campos do pedido (ou do ajuste): (tipo, horário, marcacao_id, motivo). A desconsideração só oferece as marcações
    originais que ainda não estão em análise; sem nenhuma, só a inclusão."""
    opcoes_desc = desconsideraveis(linha)
    tipos = list(TIPOS_PEDIDO) if opcoes_desc else ["inclusao"]
    tipo = st.radio("O que precisa ser corrigido?", tipos, format_func=TIPOS_PEDIDO.get, key=f"{prefixo}_tipo")
    horario = marcacao_id = None
    if tipo == "inclusao":
        horario = st.time_input("Horário da marcação que faltou", value=None, step=60, key=f"{prefixo}_hora")
    else:
        por_id = {b["marcacao_id"]: b for b in opcoes_desc}
        marcacao_id = st.selectbox("Marcação a desconsiderar", list(por_id), index=None, placeholder="Escolha a marcação", key=f"{prefixo}_marcacao",
                                   format_func=lambda i: f"{por_id[i]['hora']} · NSR {str(por_id[i]['nsr'] or '').rjust(9, '0')}")
    motivo = st.text_area("Motivo", max_chars=150, key=f"{prefixo}_motivo", height=80)
    return tipo, horario, marcacao_id, motivo


def limpar_formulario(prefixo: str) -> None:
    for sufixo in ("tipo", "hora", "marcacao", "motivo"):
        st.session_state.pop(f"{prefixo}_{sufixo}", None)
