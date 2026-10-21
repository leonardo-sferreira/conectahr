"""Apresentação do F15 a partir das atribuições do avaliador, sem ampliar seu escopo."""

from avaliacao_ciclo_modelo import situacao_avaliacao
from trajetoria_modelo import nota_br


def atribuida(avaliacao: dict, usuario_id) -> bool:
    return (usuario_id is not None and avaliacao.get("user_id") == usuario_id
            and avaliacao.get("relacao_avaliador") == "gestor")


def atribuicoes(avaliacoes: list[dict], usuario_id) -> list[dict]:
    return [a for a in avaliacoes if a.get("id") is not None and atribuida(a, usuario_id)]


def editavel(avaliacao: dict) -> bool:
    return avaliacao.get("status") in ("pendente", "em_andamento")


def ciclos_disponiveis(ciclos: list[dict], avaliacoes: list[dict]) -> list[dict]:
    por_id = {c["id"]: {"id": c["id"], "nome": c.get("nome") or f'Ciclo #{c["id"]}',
                       "status": c.get("status")} for c in ciclos if c.get("id") is not None}
    for a in avaliacoes:
        cid = a.get("ciclo_avaliacao_id")
        if cid is not None and cid not in por_id:
            por_id[cid] = {"id": cid, "nome": f"Ciclo #{cid}", "status": None}
    return sorted(por_id.values(), key=lambda c: (c.get("status") != "em_andamento", -c["id"]))


def indicadores(avaliacoes: list[dict]) -> list[tuple[str, str, str]]:
    ativas = [a for a in avaliacoes if a.get("status") != "cancelada"]
    return [("Liderados no ciclo", str(len({a["colaborador_id"] for a in ativas if a.get("colaborador_id") is not None})), ""),
            ("Avaliações enviadas", str(sum(a.get("status") == "enviada" for a in avaliacoes)), "verde"),
            ("A fazer", str(sum(editavel(a) for a in avaliacoes)), "ambar"),
            ("Contestações abertas", "—", "")]


def linhas(avaliacoes: list[dict], org: dict) -> list[dict]:
    pessoas = {p.get("id"): p for p in org.get("colaboradores") or []}
    cargos = {c.get("id"): c for c in org.get("cargos") or []}
    resultado = []
    for a in avaliacoes:
        p = pessoas.get(a.get("colaborador_id")) or {}
        cargo = cargos.get(p.get("cargo_id")) or {}
        # O nível da pessoa é o nível de carreira (l1…l5), não o nível hierárquico do cargo.
        detalhe = " — ".join(str(v) for v in (cargo.get("nome"), str(p["nivel"]).upper() if p.get("nivel") else None) if v)
        rotulo, tom = ("A fazer", "amb") if a.get("status") == "pendente" else situacao_avaliacao(a.get("status"))
        resultado.append({"id": a["id"], "nome": p.get("nome") or f'Colaborador #{a.get("colaborador_id")}',
                          "detalhe": detalhe or "—", "autoavaliacao": "—", "situacao": rotulo, "tom": tom,
                          "nota": (nota_br(a.get("nota")) or "—") if a.get("status") == "enviada" else "—",
                          "editavel": editavel(a)})
    return sorted(resultado, key=lambda l: (l["nome"].casefold(), l["id"]))
