"""Apresentação do F15 a partir das atribuições do avaliador, sem ampliar seu escopo."""

from avaliacao_ciclo_modelo import situacao_avaliacao
from onboarding_modelo import data_br
from trajetoria_modelo import nota_br

# Situação da autoavaliação da pessoa no ciclo, sem notas (change backend-gestor-pendencias, D4).
AUTOAVALIACAO = {"enviada": ("Enviada", "ok"), "em_andamento": ("Em andamento", "azul"), "pendente": ("Pendente", "amb"),
                 "sem_autoavaliacao": ("Sem autoavaliação", "neu")}
DECISOES_GESTOR = {"manter": "Manter a nota", "revisar": "Revisar a nota"}


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


def autoavaliacao(a: dict) -> tuple[str, str]:
    return AUTOAVALIACAO.get(a.get("autoavaliacao_status"), ("—", "neu"))


def prazo(a: dict) -> str:
    return data_br(a.get("prazo")) or "—"


def contestacoes_do_ciclo(contestacoes: list[dict] | None, ciclo_id) -> list[dict] | None:
    if contestacoes is None:
        return None
    return [c for c in contestacoes if c.get("ciclo_avaliacao_id") == ciclo_id]


def situacao_contestacao(c: dict) -> tuple[str, str]:
    if c.get("status") == "revisada":
        return "Fechada pelo RH", "ok"
    if c.get("decisao_gestor"):
        return "Aguardando o RH", "azul"
    return "Aguardando sua resposta", "amb"


def validar_resposta_gestor(decisao: str | None, nota, justificativa: str) -> str | None:
    if decisao not in DECISOES_GESTOR:
        return "Escolha manter ou revisar a nota."
    if decisao == "revisar" and nota not in (1, 2, 3, 4, 5):
        return "Escolha a nova nota, de 1 a 5."
    if len((justificativa or "").strip()) < 5:
        return "Escreva a justificativa (pelo menos 5 caracteres)."
    return None


def indicadores(avaliacoes: list[dict], contestacoes: list[dict] | None = None) -> list[tuple[str, str, str]]:
    ativas = [a for a in avaliacoes if a.get("status") != "cancelada"]
    return [("Liderados no ciclo", str(len({a["colaborador_id"] for a in ativas if a.get("colaborador_id") is not None})), ""),
            ("Avaliações enviadas", str(sum(a.get("status") == "enviada" for a in avaliacoes)), "verde"),
            ("A fazer", str(sum(editavel(a) for a in avaliacoes)), "ambar"),
            ("Contestações abertas", "—" if contestacoes is None else str(sum(c.get("status") == "aberta" for c in contestacoes)), "")]


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
                          "detalhe": detalhe or "—", "autoavaliacao": autoavaliacao(a), "prazo": prazo(a), "situacao": rotulo, "tom": tom,
                          "nota": (nota_br(a.get("nota")) or "—") if a.get("status") == "enviada" else "—",
                          "editavel": editavel(a)})
    return sorted(resultado, key=lambda l: (l["nome"].casefold(), l["id"]))
