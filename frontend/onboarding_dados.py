"""
Carrega do backend o que as telas de Onboarding precisam e guarda o resultado por alguns
segundos em `st.session_state`, para o Início não repetir as mesmas consultas a cada
interação (o plano gratuito do Xano limita a 10 requisições a cada 20 segundos).

Endpoints: `colaboradores/{id}/onboarding`, `onboarding_item/{id}/concluir`,
`minhas_pendencias_documento`, `meu_perfil_colaborador` e `organograma` (nome do gestor).
As regras de apresentação ficam em `onboarding_modelo.py`.
"""

import time

import streamlit as st

from api_client import (
    ApiError,
    concluir_item_onboarding,
    meu_perfil_colaborador,
    minhas_pendencias_documento,
    onboarding,
    organograma,
)
from onboarding_modelo import resumo_documentos

_VALIDADE_CACHE_S = 20
_CHAVE_CACHE = "onboarding_cache"


def invalidar_cache() -> None:
    st.session_state.pop(_CHAVE_CACHE, None)


def _cache_valido() -> dict | None:
    cache = st.session_state.get(_CHAVE_CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache
    return None


def carregar(token: str, colaborador_id: int | None, *, concluir_troca_de_senha: bool = False, usar_cache: bool = False) -> dict | None:
    """{'onboarding', 'itens', 'docs'} ou None quando a pessoa não tem onboarding (sem colaborador ou 404).

    `concluir_troca_de_senha`: logo depois da troca da senha temporária, marca o item "Trocar senha
    temporária" como concluído (a própria pessoa é a responsável por ele). Erros do backend que não
    sejam "não tem onboarding" sobem como ApiError."""
    if not colaborador_id:
        return None
    if usar_cache and (cache := _cache_valido()) is not None:
        return cache["dados"]

    try:
        dados = onboarding(token, colaborador_id)
    except ApiError as erro:
        if erro.status_code == 404:
            return None
        raise

    if concluir_troca_de_senha:
        pendente = next((i for i in dados["itens"] if i["categoria"] == "troca_senha" and not i["concluido"]), None)
        if pendente:
            try:
                concluir_item_onboarding(token, pendente["id"])
                dados = onboarding(token, colaborador_id)
            except ApiError:
                pass  # O checklist continua útil mesmo sem esse registro; o RH pode concluir o item.

    try:
        docs = resumo_documentos(minhas_pendencias_documento(token).get("pendencias") or [])
    except ApiError:
        docs = None  # As etapas aparecem sem a contagem de documentos.

    resultado = {"onboarding": dados.get("onboarding") or {}, "itens": dados["itens"], "docs": docs}
    st.session_state[_CHAVE_CACHE] = {"em": time.time(), "dados": resultado}
    return resultado


def resumo_do_perfil(token: str, usar_cache: bool = False) -> dict:
    """{'gestor', 'departamento', 'contrato', 'carga'} (valores ausentes ficam None)."""
    cache = st.session_state.get("perfil_onboarding_cache")
    if usar_cache and cache and time.time() - cache["em"] < 120:
        return cache["dados"]
    perfil = _resumo_do_perfil(token)
    st.session_state["perfil_onboarding_cache"] = {"em": time.time(), "dados": perfil}
    return perfil


def _resumo_do_perfil(token: str) -> dict:
    try:
        perfil = meu_perfil_colaborador(token)
    except ApiError:
        return {"gestor": None, "departamento": None, "contrato": None, "carga": None}
    colaborador = perfil.get("colaborador") or {}
    departamento = perfil.get("departamento") or {}
    gestor = None
    try:
        gestor_id = departamento.get("gestor_colaborador_id")
        gestor = next((c["nome"] for c in organograma(token).get("colaboradores", []) if c.get("id") == gestor_id), None)
    except ApiError:
        pass
    carga = colaborador.get("carga_horaria_semanal")
    return {
        "gestor": gestor,
        "departamento": departamento.get("nome"),
        "contrato": str(colaborador["tipo_contrato"]) if colaborador.get("tipo_contrato") else None,
        "carga": f"{float(carga):g}h/semana" if carga else None,
    }


def texto_resumo(perfil: dict) -> str:
    """"Gestor: Ana Ribeiro · Departamento: TI · CLT · 44h/semana"."""
    partes = []
    if perfil["gestor"]:
        partes.append(f"Gestor: {perfil['gestor']}")
    if perfil["departamento"]:
        partes.append(f"Departamento: {perfil['departamento']}")
    partes += [p for p in (perfil["contrato"], perfil["carga"]) if p]
    return " · ".join(partes)
