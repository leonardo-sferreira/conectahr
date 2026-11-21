"""
Regras das ações da ficha em "Colaboradores" (tarefa 53 da change concluir-frontend-streamlit): "Mudar cargo ou
salário" (`colaboradores/{id}/vinculo` PATCH), a linha do tempo (`colaboradores/{id}/timeline` GET) e o cartão de
onboarding (`colaboradores/{id}/onboarding` GET). Funções puras, sem Streamlit.

A linha do tempo não mostra salário: a ficha não mostra salário (pedido do usuário em 13/10/2026).
"""

from datetime import date

from onboarding_modelo import contagem

TIPOS_ALTERACAO = {"promocao": "Promoção", "alteracao_cargo": "Mudança de cargo", "alteracao_departamento": "Mudança de departamento",
                   "alteracao_salarial": "Alteração salarial", "alteracao_contratual": "Alteração contratual"}
_TITULO_EVENTO = dict(TIPOS_ALTERACAO, admissao="Admissão", desligamento="Desligamento")


def _dia(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10]) if valor else None
    except ValueError:
        return None


def _br(d: date | None) -> str:
    return f"{d:%d/%m/%Y}" if d else "—"


def vinculo_atual(colab: dict) -> dict:
    """Os valores de hoje da ficha, para começar o formulário (o salário entra só no campo, nunca na tela)."""
    return {"cargo_id": colab.get("cargo_id"), "departamento_id": colab.get("departamento_id"), "tipo_contrato": colab.get("tipo_contrato") or "CLT",
            "nivel": colab.get("nivel") or "l1", "salario": float(colab.get("salario") or 0), "carga_horaria_semanal": float(colab.get("carga_horaria_semanal") or 44)}


def tipo_sugerido(atual: dict, novo: dict) -> str:
    """O tipo de alteração que mais combina com o que mudou (o RH pode trocar)."""
    if novo["departamento_id"] != atual["departamento_id"]:
        return "alteracao_departamento"
    if novo["cargo_id"] != atual["cargo_id"]:
        return "promocao" if novo["nivel"] > atual["nivel"] else "alteracao_cargo"
    if novo["salario"] != atual["salario"]:
        return "alteracao_salarial"
    return "alteracao_contratual"


def validar_vinculo(atual: dict, novo: dict, data_inicio: date | None, admissao: date | None, motivo: str) -> str | None:
    if novo == atual:
        return "Nada mudou: altere o cargo, o departamento, o contrato, o nível, o salário ou a jornada."
    if not novo.get("cargo_id") or not novo.get("departamento_id"):
        return "Escolha o cargo e o departamento."
    if novo["salario"] <= 0:
        return "Informe o salário."
    if not 1 <= novo["carga_horaria_semanal"] <= 60:
        return "A jornada semanal vai de 1 a 60 horas."
    if not data_inicio:
        return "Informe a data em que a mudança vale."
    if admissao and data_inicio < admissao:
        return "A mudança não pode valer antes da admissão."
    if len((motivo or "").strip()) < 3:
        return "Explique o motivo (mínimo de 3 caracteres)."
    return None


def linhas_timeline(timeline: dict, cargos: dict, deps: dict) -> list[dict]:
    """Do mais recente ao mais antigo: [{data, titulo, detalhe}]. Sem salário."""
    eventos = []
    for h in (timeline or {}).get("historico") or []:
        inicio = _dia(h.get("data_inicio"))
        partes = [cargos.get(h.get("cargo_id")) or "Cargo não informado", deps.get(h.get("departamento_id")) or "Departamento não informado"]
        if h.get("nivel"):
            partes.append(str(h["nivel"]).upper())
        eventos.append((inicio, {"data": _br(inicio), "titulo": _TITULO_EVENTO.get(h.get("tipo_alteracao"), "Alteração"), "detalhe": " · ".join(partes)}))
    for f in (timeline or {}).get("ferias_concluidas") or []:
        inicio, fim = _dia(f.get("data_inicio")), _dia(f.get("data_fim"))
        eventos.append((inicio, {"data": _br(inicio), "titulo": "Férias", "detalhe": f"{_br(inicio)} a {_br(fim)}"}))
    eventos.sort(key=lambda e: e[0] or date.min, reverse=True)
    return [e for _, e in eventos]


def resumo_onboarding(dados: dict | None) -> dict | None:
    """{percentual, concluidas, total, proxima, situacao} ou None quando não há onboarding."""
    if not dados or not dados.get("onboarding"):
        return None
    c = contagem(dados.get("itens") or [])
    proxima = next((i.get("descricao") for i in dados.get("itens") or [] if not i.get("concluido")), None)
    terminou = c["total"] and c["concluidas"] == c["total"]
    return {"percentual": c["percentual"], "concluidas": c["concluidas"], "total": c["total"], "proxima": proxima,
            "situacao": "Concluído" if terminou or dados["onboarding"].get("status") == "concluido" else "Em andamento"}
