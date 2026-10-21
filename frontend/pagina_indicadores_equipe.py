"""F18 parcial: valores registrados e banco corrente, sem consultas administrativas."""

import html

import streamlit as st

from api_client import ApiError
from indicadores_equipe_dados import carregar, invalidar
from indicadores_equipe_modelo import PERIODO, ausencias_por_tipo, meses, motivo_cobertura, serie_mensal, total_banco
from ponto_modelo import hoje_brasilia, saldo
from theme import alerta, render_barras_indicadores, render_hero, render_horas_mensais, render_indicadores, render_topbar


def _nota(texto: str) -> None:
    st.html(f'<p class="crh-meta">{html.escape(texto)}</p>')


def pagina_indicadores_equipe() -> None:
    usuario = st.session_state.usuario
    render_topbar(usuario.get("nome") or "")
    if str(usuario.get("perfil") or "").strip().upper() != "GESTOR":
        render_hero("Indicadores da equipe", "Acompanhe os dados disponíveis da equipe")
        with st.container(border=True):
            alerta(st.empty(), "erro", "Você não tem permissão para acessar esta tela.")
        return
    hoje = hoje_brasilia()
    try:
        with st.spinner("Carregando indicadores..."):
            dados = carregar(st.session_state.token, usuario, hoje)
    except ApiError as erro:
        if erro.status_code != 401:
            render_hero("Indicadores da equipe", "Dados indisponíveis")
            with st.container(border=True):
                alerta(st.empty(), "erro", erro.message)
        return
    banco, folha = dados["banco"], dados["folha"]
    departamento = banco["nome"] if banco else "Departamento não disponível"
    render_hero("Indicadores da equipe", f"{departamento} · últimos 6 meses")
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        if st.button("Atualizar", type="tertiary", key="ie_atualizar"):
            invalidar()
            st.rerun()
        st.space("stretch")
        st.selectbox("Período", [PERIODO], key="ie_periodo", width=220, label_visibility="collapsed")
        st.button("Exportar CSV", disabled=True, help="A exportação auditada ainda não está disponível para o Gestor.", key="ie_csv")
    _nota("Exportação indisponível: esta versão não oferece exportação auditada para o Gestor.")
    if dados["erros"]:
        negadas = any(c == 403 for c in dados["erros"].values())
        with st.container(border=True):
            alerta(st.empty(), "atencao", "Algumas fontes não puderam ser consultadas" +
                   (" por falta de permissão ou indisponibilidade." if negadas else ". Os demais dados disponíveis continuam abaixo."))
    ids_folha = folha["ids"] if folha is not None else None
    ids_banco = banco["ids"] if banco is not None else None
    serie = serie_mensal(dados["meses"], ids_folha, hoje)
    extras = serie[-1]["valor"]
    corrente = total_banco(dados["saldos"], ids_banco)
    render_indicadores([("Absenteísmo", "—", ""), ("Horas extras no mês", saldo(extras)[0] if extras is not None else "—", "ambar"),
                         ("Banco de horas da equipe", saldo(corrente)[0] if corrente is not None else "—", ""), ("Clima (eNPS)", "—", "")])
    inicio = meses(hoje)[0]
    _nota(f"Folha: {len(ids_folha) if ids_folha is not None else 'quantidade não disponível'} pessoas visíveis, exceto você e desligados. "
          f"Período: 01/{inicio[1]:02d}/{inicio[0]} a {hoje:%d/%m/%Y}. Não representa necessariamente todo o departamento.")
    _nota(f"Banco: {len(ids_banco) if ids_banco is not None else 'quantidade não disponível'} pessoas do departamento gerenciado, exceto você. "
          "Saldo corrente, sem filtro de período. O recorte pode diferir da folha.")
    motivos = [m for m in (motivo_cobertura(ids_folha), motivo_cobertura(ids_banco)) if m]
    if motivos:
        _nota(" · ".join(dict.fromkeys(motivos)) + ". Agregados de grupos com menos de 5 pessoas não são exibidos.")
    _nota("Absenteísmo indisponível: falta cobertura histórica adequada para essa métrica.")
    esquerda, direita = st.columns(2, gap="medium")
    with esquerda:
        render_horas_mensais(serie)
        _nota("Soma de horas extras registradas no recorte da folha; não indica fechamento do mês. — significa ausência de cobertura.")
    with direita:
        ausencias, motivo = ausencias_por_tipo(dados["meses"], ids_folha, hoje)
        render_barras_indicadores("Ausências por tipo", ausencias, motivo)
        _nota("Contagem única por solicitação aprovada ou registrada que toca o período. Não mede dias ou pessoas e não inclui férias.")
        st.html('<div class="crh-painel crh-bloco"><p class="crh-bloco-titulo">Clima</p>'
                '<p class="crh-meta">O resultado do clima só aparece para grupos com 5 pessoas ou mais.</p>'
                '<p class="crh-meta">Nesta versão, o resultado não está disponível para o Gestor.</p></div>')
