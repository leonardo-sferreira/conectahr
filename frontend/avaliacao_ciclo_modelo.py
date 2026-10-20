"""
Regras das abas de avaliação de desempenho da tela "Ciclos de avaliação" (change pesquisa-clima-e-avaliacao-360, D5 a D7).
Funções puras, sem Streamlit.

Ciclo: planejamento → (iniciar) em andamento → (fechamento) fechamento → (concluir) concluído; ou cancelado a partir de
qualquer um desses. Só com o ciclo em andamento o RH atribui avaliações (autoavaliação, gestor, par, subordinado, RH).
Ao concluir ou cancelar, as avaliações ainda em aberto ficam canceladas.
"""

from datetime import date

from onboarding_modelo import data_br

# Rótulos do Figma F27 (249:5068): "Aberto" e "Fechado".
STATUS = {"planejamento": ("Planejamento", "neu"), "em_andamento": ("Aberto", "azul"), "fechamento": ("Em fechamento", "amb"),
          "concluido": ("Fechado", "neu"), "cancelado": ("Cancelado", "err")}
DESCRICAO_PADRAO = "Avaliação 360 — todos os ativos"
_PROXIMOS = {"planejamento": [("em_andamento", "Iniciar ciclo")], "em_andamento": [("fechamento", "Iniciar fechamento")], "fechamento": [("concluido", "Concluir")]}
_CONFIRMACAO = {
    "em_andamento": "Com o ciclo em andamento, você já pode atribuir as avaliações.",
    "fechamento": "No fechamento, quem ainda não enviou deve terminar; o RH revisa as contestações.",
    "concluido": "Ao concluir, as avaliações que não foram enviadas ficam canceladas. Isso não volta atrás.",
    "cancelado": "Ao cancelar, as avaliações que não foram enviadas ficam canceladas. Isso não volta atrás.",
}
RELACOES = {"autoavaliacao": "Autoavaliação", "gestor": "Gestor", "par": "Par", "subordinado": "Subordinado", "rh": "RH"}
STATUS_AVALIACAO = {"pendente": ("Pendente", "amb"), "em_andamento": ("Em andamento", "azul"), "enviada": ("Enviada", "ok"), "cancelada": ("Cancelada", "neu")}


def situacao(status) -> tuple[str, str]:
    return STATUS.get(status, (str(status or "—"), "neu"))


def situacao_avaliacao(status) -> tuple[str, str]:
    return STATUS_AVALIACAO.get(status, (str(status or "—"), "neu"))


def acoes(status) -> list[tuple[str, str]]:
    """Botões de mudança de situação: [(status de destino, rótulo)]. Cancelar vale até o ciclo ser concluído."""
    seguintes = list(_PROXIMOS.get(status, []))
    if status in _PROXIMOS:
        seguintes.append(("cancelado", "Cancelar ciclo"))
    return seguintes


def confirmacao(destino: str) -> str:
    return _CONFIRMACAO.get(destino, "")


def pode_atribuir(ciclo: dict) -> bool:
    return ciclo.get("status") == "em_andamento"


def periodo(ciclo: dict) -> str:
    if not ciclo.get("data_inicio") and not ciclo.get("data_fim"):
        return "—"
    return f"{data_br(ciclo.get('data_inicio'))} a {data_br(ciclo.get('data_fim'))}"


def progresso(ciclo: dict) -> str:
    c = ciclo.get("contagens") or {}
    validas = (c.get("total") or 0) - (c.get("canceladas") or 0)
    return f"{c.get('enviadas') or 0} de {validas} enviadas" if validas else "Nenhuma atribuída"


def pct_relacao(ciclo: dict, relacao: str) -> int | None:
    """% enviado das autoavaliações ("auto") ou das avaliações do gestor ("gestor"), sem as canceladas; None sem nenhuma."""
    c = ciclo.get("contagens") or {}
    total = c.get(f"{relacao}_total") or 0
    return round((c.get(f"{relacao}_enviadas") or 0) / total * 100) if total else None


def ano(ciclo: dict) -> int | None:
    for campo in ("data_inicio", "data_fim"):
        try:
            return date.fromisoformat(str(ciclo.get(campo))[:10]).year
        except ValueError:
            continue
    return None


def anos(ciclos: list[dict]) -> list[int]:
    return sorted({a for a in (ano(c) for c in ciclos) if a}, reverse=True)


def do_ano(ciclos: list[dict], ano_escolhido: int | None) -> list[dict]:
    return [c for c in ciclos if ano_escolhido is None or ano(c) == ano_escolhido]


def em_foco(ciclos: list[dict], escolhido=None) -> dict | None:
    """O ciclo dos cartões de baixo: o escolhido; senão o primeiro aberto ou em fechamento; senão o primeiro."""
    por_id = {c["id"]: c for c in ciclos}
    if escolhido in por_id:
        return por_id[escolhido]
    return next((c for c in ciclos if c.get("status") in ("em_andamento", "fechamento")), ciclos[0] if ciclos else None)


def andamento_departamentos(avaliacoes: list[dict]) -> list[tuple[str, int]]:
    """[(departamento, % enviado)], sem as canceladas, em ordem alfabética."""
    grupos: dict[str, list[int]] = {}
    for a in avaliacoes:
        if a.get("status") == "cancelada":
            continue
        g = grupos.setdefault(a.get("departamento") or "Sem departamento", [0, 0])
        g[1] += 1
        g[0] += a.get("status") == "enviada"
    return [(nome, round(env / tot * 100)) for nome, (env, tot) in sorted(grupos.items())]


def contestacoes_do_ciclo(contestacoes: list[dict], ciclo_id) -> list[dict]:
    return [c for c in contestacoes if c.get("ciclo_avaliacao_id") == ciclo_id]


def linha_contestacao(c: dict) -> tuple[str, str]:
    """("Leonardo dos Santos → Ana Ribeiro", "Aberta em 26/09")."""
    criada = data_br(c.get("criada_em"))[:5] if c.get("criada_em") else "—"
    return f'{c.get("avaliado_nome") or "—"} → {c.get("avaliador_nome") or "—"}', f"Aberta em {criada}"


def validar_ciclo(nome: str, inicio: date | None, fim: date | None, autoavaliacao: bool = True, gestor: bool = True) -> str | None:
    if len((nome or "").strip()) < 3:
        return "Dê um nome ao ciclo (pelo menos 3 caracteres)."
    if inicio is None or fim is None:
        return "Informe o início e o fim do ciclo."
    if fim < inicio:
        return "O fim não pode ser antes do início."
    if not autoavaliacao and not gestor:
        return "Escolha pelo menos um tipo de avaliação."
    return None


def validar_avulsa(avaliado: dict | None, avaliador: dict | None, relacao: str | None) -> str | None:
    if not avaliado or not avaliador or not relacao:
        return "Escolha quem é avaliado, quem avalia e a relação."
    if not avaliador.get("user_id"):
        return "Quem avalia precisa ter conta no sistema."
    mesmo = avaliado.get("id") == avaliador.get("id")
    if relacao == "autoavaliacao" and not mesmo:
        return "Na autoavaliação, quem avalia é a própria pessoa."
    if relacao != "autoavaliacao" and mesmo:
        return "Para a pessoa avaliar a si mesma, use a relação Autoavaliação."
    return None


def resumo_lote(r: dict) -> str:
    partes = [f"{r.get('criadas') or 0} avaliações atribuídas"]
    if r.get("puladas"):
        partes.append(f"{r['puladas']} já existiam")
    if r.get("sem_gestor"):
        partes.append(f"{r['sem_gestor']} pessoas sem gestor definido")
    return "; ".join(partes) + "."


def filtrar_avaliacoes(avaliacoes: list[dict], status: str | None, departamento_id, busca: str) -> list[dict]:
    termo = (busca or "").strip().lower()
    return [a for a in avaliacoes
            if (not status or a.get("status") == status)
            and (departamento_id is None or a.get("departamento_id") == departamento_id)
            and (not termo or termo in (a.get("avaliado_nome") or "").lower() or termo in (a.get("avaliador_nome") or "").lower())]


def nota_legivel(nota) -> str:
    if nota is None:
        return "—"
    return f"{float(nota):.1f}".replace(".", ",")
