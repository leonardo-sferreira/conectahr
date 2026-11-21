"""
Regras da tela "Sessões ativas" do Admin (Figma 249:6819; tarefa 65 da change concluir-frontend-streamlit). Funções
puras, sem Streamlit. Os dados vêm de `admin/sessoes_ativas` GET: nome e perfil da conta, navegador e início, sem IP.
"""

import unicodedata
from datetime import date

from ponto_modelo import para_brasilia

PERFIS = {"ADMIN": "Admin", "RH": "RH", "GESTOR": "Gestor", "COLABORADOR": "Colaborador"}


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto or "") if unicodedata.category(c) != "Mn").lower()


def inicio(valor, hoje: date) -> str:
    momento = para_brasilia(valor)
    if not momento:
        return "—"
    if momento.date() == hoje:
        return f"Hoje, {momento:%H:%M}"
    return f"{momento:%d/%m/%Y}, {momento:%H:%M}"


def linhas(sessoes: list[dict], hoje: date, busca: str = "", perfil: str | None = None) -> list[dict]:
    """Sessões filtradas por nome e perfil, as mais recentes primeiro; a do próprio Admin vem marcada."""
    termo = _sem_acento(busca.strip())
    saida = []
    for s in sessoes or []:
        p = str(s.get("perfil") or "").upper()
        if perfil and p != perfil:
            continue
        nome = s.get("nome") or "Conta sem nome"
        if termo and termo not in _sem_acento(nome):
            continue
        saida.append({"id": s.get("id"), "nome": nome, "perfil": PERFIS.get(p, p.title() or "—"),
                      "dispositivo": s.get("dispositivo") or "Navegador não identificado",
                      "inicio": inicio(s.get("created_at"), hoje), "atual": bool(s.get("atual")),
                      "_ordem": para_brasilia(s.get("created_at"))})
    saida.sort(key=lambda l: (l["_ordem"] is None, -(l["_ordem"].timestamp() if l["_ordem"] else 0)))
    for l in saida:
        l.pop("_ordem")
    return saida


def contas(sessoes: list[dict]) -> int:
    return len({s.get("user_id") for s in sessoes or []})
