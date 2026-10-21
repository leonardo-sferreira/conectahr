"""Dados de apresentação de Minha equipe (F14, tarefa 57), sem Streamlit.

Só subordinados diretos; autorização e persistência continuam no backend.
O ponto da semana reutiliza o mesmo espelho da folha, inclusive tratamentos do REP-P.
"""

from datetime import date, timedelta

from folha_modelo import espelho_da_pessoa


def colaborador_do_gestor(pessoas: list[dict]):
    return next((p.get("id") for p in pessoas if p.get("e_voce")), None)


def liderados(pessoas: list[dict]) -> list[dict]:
    gestor_id = colaborador_do_gestor(pessoas)
    if gestor_id is None:
        return []
    return sorted(
        [p for p in pessoas if not p.get("e_voce") and p.get("id") != gestor_id
         and p.get("superior_colaborador_id") == gestor_id
         and str(p.get("status") or "").strip().upper() != "DESLIGADO"],
        key=lambda p: str(p.get("nome") or "").casefold(),
    )


def semana_atual(hoje: date) -> tuple[date, date]:
    inicio = hoje - timedelta(days=hoje.weekday())
    return inicio, inicio + timedelta(days=6)


def meses_da_semana(hoje: date) -> list[tuple[int, int]]:
    inicio, fim = semana_atual(hoje)
    return sorted({(inicio.year, inicio.month), (fim.year, fim.month)})


def ponto_da_semana(pessoa: dict, meses: dict, feriados: list[dict] | None, hoje: date) -> dict | None:
    """None significa consulta incompleta; nunca transformar falha em semana sem pendências."""
    inicio, fim = semana_atual(hoje)
    if feriados is None or any(not isinstance(meses.get(chave), dict)
                              or not any(k in meses[chave] for k in ("registros", "marcacoes"))
                              for chave in meses_da_semana(hoje)):
        return None
    linhas = []
    for ano, mes in meses_da_semana(hoje):
        linhas.extend(l for l in espelho_da_pessoa(pessoa, meses[(ano, mes)], feriados, ano, mes, hoje)
                      if inicio <= l["data"] <= fim)
    dias_passados = [l for l in linhas if l["data"] < hoje and not l["em_branco"]]
    return {
        "dias": linhas,
        "incompletos": sum(l["status"] in ("INCOMPLETO", "SEM REGISTRO", "FALTA INJUSTIFICADA") for l in dias_passados),
        "horas": sum(l["horas"] for l in linhas),
    }


def situacao_ponto(ponto: dict | None) -> tuple[str, str]:
    if ponto is None:
        return "Não disponível", "neu"
    if ponto["incompletos"]:
        return "Incompleto", "err"
    dias = [l for l in ponto["dias"] if not l["em_branco"]]
    if any(l["status"] == "AUSÊNCIA EM ANÁLISE" for l in dias):
        return "Em análise", "amb"
    if any(l["status"] in ("COMPLETO", "AJUSTADO") for l in dias):
        return "Completo", "ok"
    return "—", "neu"


def periodo_ferias(hoje: date) -> tuple[str, str]:
    """90 datas, incluindo hoje; períodos que já começaram podem tocar esta janela."""
    return hoje.isoformat(), (hoje + timedelta(days=89)).isoformat()


def ferias_do_periodo(pessoas: list[dict], resposta: dict | None, hoje: date) -> list[dict] | None:
    if resposta is None or not isinstance(resposta.get("ferias"), list):
        return None
    ids = {p["id"] for p in pessoas}
    inicio, fim = periodo_ferias(hoje)
    ferias = []
    for f in resposta["ferias"]:
        try:
            de = date.fromisoformat(str(f.get("data_inicio")))
            ate = date.fromisoformat(str(f.get("data_fim")))
        except ValueError:
            continue
        if (f.get("colaborador_id") in ids and f.get("status") in ("Aprovada", "Pendente")
                and de <= ate and de.isoformat() <= fim and ate.isoformat() >= inicio):
            ferias.append(f)
    return sorted(ferias, key=lambda f: (f["data_inicio"], f["colaborador_id"], f.get("id", 0)))


def indicadores(pessoas: list[dict], pontos: dict, pendencias: dict, ferias: list[dict] | None, hoje: date) -> list[tuple]:
    def numero(valor):
        return "—" if valor is None else str(valor)

    pedidos = [pendencias[p["id"]]["total"] for p in pessoas]
    ponto = [pontos[p["id"]] for p in pessoas]
    total = sum(pedidos) if all(n is not None for n in pedidos) else None
    incompletos = sum(bool(p["incompletos"]) for p in ponto) if all(p is not None for p in ponto) else None
    em_ferias = sum(bool(ferias_atuais(p["id"], {"ferias": ferias}, hoje)) for p in pessoas) if ferias is not None else None
    return [("Liderados", str(len(pessoas)), ""), ("Pedidos para decidir", numero(total), "ambar"),
            ("Ponto incompleto esta semana", numero(incompletos), "negativo"),
            ("De férias agora", numero(em_ferias), "")]


def rotulo_pendencias(grupo: dict) -> str:
    total = grupo["total"]
    if total is None:
        return "Não disponível"
    if not total:
        return "—"
    if len(grupo["correcoes"]) == total:
        return f"{total} correção" if total == 1 else f"{total} correções"
    return f"{total} pedido" if total == 1 else f"{total} pedidos"


def ferias_atuais(pessoa_id, dados_mes: dict | None, hoje: date) -> list[dict] | None:
    if dados_mes is None:
        return None
    dia = hoje.isoformat()
    return [f for f in dados_mes.get("ferias") or []
            if f.get("colaborador_id") == pessoa_id and f.get("status") == "Aprovada"
            and str(f.get("data_inicio") or "")[:10] <= dia <= str(f.get("data_fim") or "")[:10]]


def pendencias_por_pessoa(pessoas: list[dict], central: dict | None, correcoes: dict | None) -> dict:
    """Só pedidos para decidir, separados por fonte para preservar falhas parciais."""
    grupos = {p["id"]: {"ferias": None, "ausencias": None, "correcoes": None, "total": None} for p in pessoas}
    fontes = (("ferias", None if central is None else central.get("fila_ferias_pendentes") or [], "Pendente"),
              ("ausencias", None if central is None else central.get("fila_ausencias_pendentes") or [], "Pendente"),
              ("correcoes", None if correcoes is None else correcoes.get("correcoes") or [], "pendente"))
    for tipo, itens, status in fontes:
        if itens is None:
            continue
        for grupo in grupos.values():
            grupo[tipo] = []
        for item in itens:
            pid = item.get("colaborador_id")
            if pid in grupos and item.get("status") == status:
                grupos[pid][tipo].append(item)
    for grupo in grupos.values():
        if all(grupo[tipo] is not None for tipo, _, _ in fontes):
            grupo["total"] = sum(len(grupo[tipo]) for tipo, _, _ in fontes)
    return grupos


def filtrar_pessoas(pessoas: list[dict], busca: str = "", situacao: str = "") -> list[dict]:
    termo = busca.strip().casefold()
    return [p for p in pessoas if termo in str(p.get("nome") or "").casefold()
            and (not situacao or str(p.get("status") or "").strip().upper() == situacao.upper())]
