"""
Peças de tela do ponto no REP-P usadas pelo colaborador (`pagina_ponto.py`) e pela folha da equipe
(`pagina_folha_ponto.py`): a planilha do mês em `st.dataframe` (design D8, Figma 464:826), o cabeçalho do
art. 84 e o formulário de correção (Figma 465:856 e 465:894). As regras ficam em `ponto_mensal_modelo.py`.
"""

import html

import pandas as pd
import streamlit as st

from ponto_mensal_modelo import COLUNA_AJUSTE, colunas_planilha, desconsideraveis, dia_longo, linha_selecionada, linhas_planilha, marcacoes_texto, pares_do_mes, situacao_curta, tem_saldo, texto_opcao_marcacao, valores_ajuste, chave_marcacao, alvo_da_chave
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


def render_planilha(linhas: list[dict], chave: str, ajustavel=None) -> dict | None:
    """A planilha do mês, uma linha por dia. Com `ajustavel` (função que diz se o dia aceita ajuste), cada dia ganha a
    caixa "Ajuste" no fim da linha (`st.data_editor`, só essa coluna editável): marcar devolve o dia, para abrir o pedido
    ou o ajuste na hora. Sem `ajustavel`, só consulta. Devolve o dia marcado ou None."""
    pares = pares_do_mes(linhas)
    tabela = pd.DataFrame(linhas_planilha(linhas, pares), columns=colunas_planilha(pares, tem_saldo(linhas)))
    altura = 38 + 35 * len(linhas)  # sem rolagem interna: o mês inteiro à vista, como no Figma
    if ajustavel is None:
        st.dataframe(estilo_planilha_ponto(tabela, [l["tom"] for l in linhas]), hide_index=True, width="stretch", height=altura, key=chave)
        return None
    tabela[COLUNA_AJUSTE] = valores_ajuste(linhas, ajustavel)
    editada = st.data_editor(
        estilo_planilha_ponto(tabela, [l["tom"] for l in linhas]), hide_index=True, width="stretch", height=altura,
        key=f"{chave}_v{st.session_state.get(f'{chave}_versao', 0)}",
        disabled=[c for c in tabela.columns if c != COLUNA_AJUSTE], num_rows="fixed",
        column_config={COLUNA_AJUSTE: st.column_config.CheckboxColumn(COLUNA_AJUSTE, help="Marque para ajustar o dia", width="small")},
    )
    return linha_selecionada(linhas, [i for i, v in enumerate(editada[COLUNA_AJUSTE]) if v is True])


def desmarcar_planilha(chave: str) -> None:
    """Tira a marca da caixa "Ajuste" para o dia não abrir de novo. Apagar o estado não basta: o `st.data_editor` guarda
    a edição no navegador e a manda de novo na rodada seguinte (Cancelar reabria o pedido). Uma versão nova na chave
    recria a planilha sem a marca."""
    versao = f"{chave}_versao"
    st.session_state.pop(f"{chave}_v{st.session_state.get(versao, 0)}", None)
    st.session_state[versao] = st.session_state.get(versao, 0) + 1


def resumo_do_dia(linha: dict) -> None:
    """O quadro com dia, marcações e situação, no topo do pedido e do ajuste."""
    st.html(
        '<div class="crh-campos crh-campos-direita">'
        f'<p class="r">Dia</p><p class="v">{html.escape(dia_longo(linha["data"]))}</p>'
        f'<p class="r">Marcações</p><p class="v">{html.escape(marcacoes_texto(linha))}</p>'
        f'<p class="r">Situação</p><p class="v"><span class="crh-ponto-status {linha["tom"]}">{html.escape(situacao_curta(linha))}</span></p></div>'
    )


def formulario_pedido(linha: dict, prefixo: str) -> tuple:
    """Campos do pedido (ou do ajuste): (tipo, horário, alvo, motivo); `alvo` é {'marcacao_id', 'tratamento_id'} da
    marcação escolhida, ou None. Corrigir o horário e desconsiderar oferecem todas as marcações do dia que ainda não
    estão em análise, originais e incluídas, com o papel no dia; sem nenhuma, só a inclusão."""
    opcoes = desconsideraveis(linha)
    tipos = list(TIPOS_PEDIDO) if opcoes else ["inclusao"]
    tipo = st.radio("O que precisa ser corrigido?", tipos, format_func=TIPOS_PEDIDO.get, key=f"{prefixo}_tipo")
    horario = alvo = None
    if tipo != "inclusao":
        por_chave = {chave_marcacao(b): b for b in opcoes}
        rotulo = "Marcação a corrigir" if tipo == "alteracao" else "Marcação a desconsiderar"
        chave = st.selectbox(rotulo, list(por_chave), index=None, placeholder="Escolha a marcação", key=f"{prefixo}_marcacao",
                             format_func=lambda c: texto_opcao_marcacao(linha, por_chave[c]))
        alvo = alvo_da_chave(chave)
    if tipo != "desconsideracao":
        rotulo = "Horário certo" if tipo == "alteracao" else "Horário da marcação que faltou"
        horario = st.time_input(rotulo, value=None, step=60, key=f"{prefixo}_hora")
    motivo = st.text_area("Motivo", max_chars=150, key=f"{prefixo}_motivo", height=80)
    return tipo, horario, alvo, motivo


def limpar_formulario(prefixo: str) -> None:
    for sufixo in ("tipo", "hora", "marcacao", "motivo"):
        st.session_state.pop(f"{prefixo}_{sufixo}", None)
