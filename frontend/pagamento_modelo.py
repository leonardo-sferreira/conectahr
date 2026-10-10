"""
Regras de apresentação de Pagamento (Figma 70:46 para o colaborador; seção 9, 236:357 e 236:594, para o
RH e o Admin; modais 237:363, 237:402 e 237:441; tarefas 29 e 30 da change concluir-frontend-streamlit).
Funções puras, sem Streamlit.

Holerite e informe de rendimentos são documentos (`tipo` = "holerite" ou "informe_rendimentos") que só
RH e Admin lançam; nascem aprovados e não vencem. O backend não tem campo de competência: a tela grava a
competência no nome do documento ("Holerite — Agosto/2026", "Informe de rendimentos 2025") e, se o nome
não seguir esse padrão, usa a data de emissão (holerite: mês anterior; informe: ano anterior).
"""

import re
from datetime import date

from onboarding_modelo import data_br

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
TIPOS_PAGAMENTO = ("holerite", "informe_rendimentos")
_RE_HOLERITE = re.compile(r"(" + "|".join(MESES) + r")/(\d{4})", re.I)
_RE_ANO = re.compile(r"(\d{4})")


def rotulo_competencia(tipo: str, competencia) -> str:
    if tipo == "holerite":
        ano, mes = competencia
        return f"{MESES[mes - 1]}/{ano}"
    return str(competencia)


def nome_documento(tipo: str, competencia) -> str:
    if tipo == "holerite":
        return f"Holerite — {rotulo_competencia(tipo, competencia)}"
    return f"Informe de rendimentos {competencia}"


def competencia_de(documento: dict):
    """(ano, mês) do holerite ou o ano-calendário do informe; None se não der para saber."""
    tipo = documento.get("tipo")
    nome = documento.get("nome_documento") or ""
    emissao = None
    try:
        emissao = date.fromisoformat(str(documento.get("data_emissao"))[:10])
    except ValueError:
        pass
    if tipo == "holerite":
        if m := _RE_HOLERITE.search(nome):
            mes = next(i for i, n in enumerate(MESES, 1) if n.lower() == m.group(1).lower())
            return int(m.group(2)), mes
        if emissao:
            return (emissao.year, emissao.month - 1) if emissao.month > 1 else (emissao.year - 1, 12)
        return None
    if tipo == "informe_rendimentos":
        if m := _RE_ANO.search(nome):
            return int(m.group(1))
        return emissao.year - 1 if emissao else None
    return None


def _vigentes(documentos: list[dict], tipo: str) -> list[dict]:
    """Os documentos aprovados do tipo. O substituído some: o colaborador vê só a versão nova."""
    return [d for d in documentos if d.get("tipo") == tipo and d.get("status") == "aprovado" and competencia_de(d) is not None]


def do_colaborador(documentos: list[dict]) -> dict:
    """Visão do colaborador (Figma 70:46): {'anos', 'holerites': {ano: [linhas]}, 'informes': [linhas]}.
    Cada linha: {'id', 'titulo', 'detalhe', 'badge', 'tipo'}."""
    holerites: dict[int, list] = {}
    for d in sorted(_vigentes(documentos, "holerite"), key=competencia_de, reverse=True):
        ano, mes = competencia_de(d)
        holerites.setdefault(ano, []).append({
            "id": d.get("id"), "titulo": f"Holerite — {MESES[mes - 1]}/{ano}",
            "detalhe": f"Emitido em {data_br(d.get('data_emissao'))}" if d.get("data_emissao") else "Emitido no início do mês seguinte",
            "badge": "Disponível", "tipo": "ok",
        })
    informes = [
        {"id": d.get("id"), "titulo": f"Informe de rendimentos {competencia_de(d)}",
         "detalhe": (f"Emitido em {data_br(d.get('data_emissao'))} · " if d.get("data_emissao") else "") + "para declaração do IR",
         "badge": "Disponível", "tipo": "ok"}
        for d in sorted(_vigentes(documentos, "informe_rendimentos"), key=competencia_de, reverse=True)
    ]
    return {"anos": sorted(holerites, reverse=True), "holerites": holerites, "informes": informes}


def competencias_recentes(hoje: date, quantidade: int = 12) -> list[tuple[int, int]]:
    """Os últimos meses fechados, do mais recente ao mais antigo (o holerite sai no mês seguinte)."""
    ano, mes = hoje.year, hoje.month
    lista = []
    for _ in range(quantidade):
        mes -= 1
        if mes == 0:
            ano, mes = ano - 1, 12
        lista.append((ano, mes))
    return lista


def anos_recentes(hoje: date, quantidade: int = 5) -> list[int]:
    return [hoje.year - n for n in range(1, quantidade + 1)]


def linhas_rh(org: dict, documentos: list[dict], tipo: str, competencia, departamento_id=None) -> dict:
    """Visão do RH (Figma 236:357 e 236:594): uma linha por colaborador ativo, com o documento da
    competência, se já foi lançado. {'linhas', 'ativos', 'lancados', 'faltando'}."""
    deps = {d.get("id"): d.get("nome") for d in org.get("departamentos") or []}
    cargos = {c.get("id"): c.get("nome") for c in org.get("cargos") or []}
    por_colaborador: dict = {}
    for d in _vigentes(documentos, tipo):
        if competencia_de(d) == competencia:
            atual = por_colaborador.get(d.get("colaborador_id"))
            if atual is None or str(d.get("created_at") or "") > str(atual.get("created_at") or ""):
                por_colaborador[d.get("colaborador_id")] = d
    linhas = []
    for c in sorted(org.get("colaboradores") or [], key=lambda c: c.get("nome") or ""):
        if departamento_id and c.get("departamento_id") != departamento_id:
            continue
        doc = por_colaborador.get(c.get("id"))
        linhas.append({
            "colaborador_id": c.get("id"),
            "nome": c.get("nome") or "Colaborador",
            "detalhe": cargos.get(c.get("cargo_id")) or "—",
            "departamento": deps.get(c.get("departamento_id")) or "—",
            "competencia": rotulo_competencia(tipo, competencia),
            "lancado_em": data_br((doc or {}).get("created_at") or (doc or {}).get("data_emissao")) or "—",
            "situacao": ("Lançado", "ok") if doc else ("Faltando", "amb"),
            "documento": doc,
        })
    lancados = sum(1 for l in linhas if l["documento"])
    linhas.sort(key=lambda l: (l["documento"] is not None, l["nome"]))  # quem falta aparece primeiro
    return {"linhas": linhas, "ativos": len(linhas), "lancados": lancados, "faltando": len(linhas) - lancados}


def validar_lancamento(colaborador_id, data_emissao: date | None, link: str, hoje: date) -> str | None:
    if not colaborador_id:
        return "Escolha o colaborador."
    if not data_emissao:
        return "Informe a data de emissão."
    if data_emissao > hoje:
        return "A data de emissão não pode ser futura."
    link = (link or "").strip()
    if not link:
        return "Informe o link do arquivo."
    if not link.lower().startswith("https://"):
        return "O link do arquivo precisa começar com https://."
    return None


def validar_substituicao(link: str, motivo: str) -> str | None:
    link = (link or "").strip()
    if not link:
        return "Informe o link do arquivo corrigido."
    if not link.lower().startswith("https://"):
        return "O link do arquivo precisa começar com https://."
    if len((motivo or "").strip()) < 5:
        return "Explique o motivo da correção em pelo menos 5 caracteres."
    return None
