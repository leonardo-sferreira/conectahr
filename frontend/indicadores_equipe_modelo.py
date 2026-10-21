"""Agregados do F18: recortes separados, sem recriar regras de jornada ou autorização."""

import math
from datetime import date

from pagamento_modelo import MESES
from ponto_modelo import TIPOS_AUSENCIA, saldo

MINIMO_PESSOAS = 5  # Piso padrão da spec Indicadores sem identificação de pessoas.
PERIODO = "Últimos 6 meses"


def id_valido(valor) -> bool:
    return type(valor) is int and valor > 0


def numero(valor) -> float | None:
    try:
        return float(valor) if type(valor) in (int, float) and math.isfinite(valor) else None
    except (OverflowError, ValueError):
        return None


def dia(valor) -> date | None:
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        return None


def meses(hoje: date) -> list[tuple[int, int]]:
    indice = hoje.year * 12 + hoje.month - 1
    return [(i // 12, i % 12 + 1) for i in range(indice - 5, indice + 1)]


def recorte_folha(resposta: dict) -> dict:
    pessoas = resposta.get("pessoas")
    if not isinstance(pessoas, list) or any(not isinstance(p, dict) or not id_valido(p.get("id"))
            or type(p.get("e_voce")) is not bool or p.get("status") not in ("Ativo", "Ferias", "Afastado", "Desligado") for p in pessoas):
        raise ValueError("Lista de pessoas incompleta")
    if len({p["id"] for p in pessoas}) != len(pessoas):
        raise ValueError("Pessoas duplicadas")
    proprios = [p["id"] for p in pessoas if p["e_voce"]]
    if pessoas and len(proprios) != 1:
        raise ValueError("Não foi possível identificar a própria ficha")
    return {"gestor_id": proprios[0] if proprios else None,
            "ids": [p["id"] for p in pessoas if not p["e_voce"] and p["status"] != "Desligado"]}


def recorte_banco(org: dict, colaborador_id) -> dict:
    departamentos, pessoas = org.get("departamentos"), org.get("colaboradores")
    if not isinstance(departamentos, list) or not isinstance(pessoas, list) or not id_valido(colaborador_id):
        raise ValueError("Estrutura indisponível")
    if any(not isinstance(d, dict) or not id_valido(d.get("id")) or "gestor_colaborador_id" not in d for d in departamentos):
        raise ValueError("Departamentos incompletos")
    geridos = [d for d in departamentos if isinstance(d, dict) and d.get("gestor_colaborador_id") == colaborador_id]
    if len(geridos) != 1 or not id_valido(geridos[0].get("id")):
        raise ValueError("Departamento gerenciado não identificado de forma única")
    departamento = geridos[0]
    if any(not isinstance(p, dict) or not id_valido(p.get("id")) or "departamento_id" not in p
           or (p["departamento_id"] is not None and not id_valido(p["departamento_id"])) for p in pessoas):
        raise ValueError("Estrutura incompleta")
    if len({p["id"] for p in pessoas}) != len(pessoas):
        raise ValueError("Pessoas duplicadas")
    return {"nome": departamento.get("nome") if isinstance(departamento.get("nome"), str) else "Departamento não disponível",
            "ids": [p["id"] for p in pessoas if p["departamento_id"] == departamento["id"]
                    and p["id"] != colaborador_id and p.get("status") != "Desligado"]}


def motivo_cobertura(ids: list[int] | None) -> str:
    if ids is None:
        return "Fonte indisponível"
    if not ids:
        return "Sem pessoas neste recorte"
    return "Grupo com menos de 5 pessoas" if len(ids) < MINIMO_PESSOAS else ""


def extras_do_mes(registros, ids: list[int] | None, ano: int, mes: int, hoje: date) -> tuple[float | None, str]:
    if motivo := motivo_cobertura(ids):
        return None, motivo
    if not isinstance(registros, list):
        return None, "Fonte indisponível"
    encontrados, vistos, dias, total = set(), {}, set(), 0.0
    for r in registros:
        if not isinstance(r, dict) or not id_valido(r.get("colaborador_id")):
            return None, "Dados incompletos"
        if r.get("colaborador_id") not in ids:
            continue
        d = dia(r.get("data"))
        if d is None or not id_valido(r.get("id")):
            return None, "Dados incompletos"
        if (d.year, d.month) != (ano, mes) or d > hoje:
            continue
        valor = numero(r.get("horas_extras"))
        if valor is None or valor < 0:
            return None, "Valor não disponível"
        if r["id"] in vistos:
            if vistos[r["id"]] != r:
                return None, "Dados conflitantes"
            continue
        vistos[r["id"]] = r
        if (r["colaborador_id"], d) in dias:
            return None, "Dados conflitantes"
        dias.add((r["colaborador_id"], d))
        encontrados.add(r["colaborador_id"])
        total += valor
    if not encontrados:
        return None, "Sem registros"
    if encontrados != set(ids):
        return None, "Cobertura incompleta"
    return (total, "Valores registrados") if numero(total) is not None else (None, "Valor não disponível")


def serie_mensal(consultas: dict, ids: list[int] | None, hoje: date) -> list[dict]:
    saida = []
    for ano, mes in meses(hoje):
        dados = consultas.get((ano, mes)) or {}
        valor, situacao = extras_do_mes(dados.get("registros"), ids, ano, mes, hoje)
        saida.append({"rotulo": f"{MESES[mes - 1][:3].lower()}/{str(ano)[2:]}", "valor": valor,
                      "texto": saldo(valor)[0] if valor is not None else "—", "situacao": situacao})
    return saida


def ausencias_por_tipo(consultas: dict, ids: list[int] | None, hoje: date) -> tuple[list[tuple[str, int]] | None, str]:
    if motivo := motivo_cobertura(ids):
        return None, motivo
    inicio = date(*meses(hoje)[0], 1)
    unicas = {}
    for chave in meses(hoje):
        registros = (consultas.get(chave) or {}).get("ausencias")
        if not isinstance(registros, list):
            return None, "Período sem cobertura completa"
        for a in registros:
            if not isinstance(a, dict) or not id_valido(a.get("colaborador_id")):
                return None, "Dados incompletos"
            if a.get("colaborador_id") not in ids:
                continue
            if a.get("status") in ("Pendente", "Rejeitada"):
                continue
            de, ate = dia(a.get("data_inicio")), dia(a.get("data_fim"))
            if not id_valido(a.get("id")) or not de or not ate or ate < de or a.get("tipo") not in TIPOS_AUSENCIA or a.get("status") not in ("Aprovada", "Registrado"):
                return None, "Dados incompletos"
            if de > hoje or ate < inicio:
                continue
            if a["id"] in unicas and unicas[a["id"]] != a:
                return None, "Dados conflitantes"
            unicas[a["id"]] = a
    contagens = {}
    for a in unicas.values():
        nome = TIPOS_AUSENCIA[a["tipo"]]
        contagens[nome] = contagens.get(nome, 0) + 1
    return sorted(contagens.items(), key=lambda x: (-x[1], x[0])), "Solicitações aprovadas ou registradas"


def total_banco(saldos: dict, ids: list[int] | None) -> float | None:
    if motivo_cobertura(ids) or any(numero(saldos.get(pid)) is None for pid in ids):
        return None
    return numero(sum(saldos[pid] for pid in ids))
