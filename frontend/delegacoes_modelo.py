"""Apresentação do F17; vigência usa a mesma data UTC dos consumidores do backend."""

from datetime import date, datetime, timezone

from decisoes_modelo import periodo

ESCOPOS = {"ferias": "Férias", "correcao_ponto": "Correção de ponto", "ausencia": "Ausências",
           "documento": "Documentos", "desligamento": "Desligamento", "solicitacao_rh": "Solicitações ao RH",
           "todas": "Todas as aprovações"}


def hoje_utc() -> date:
    return datetime.now(timezone.utc).date()


def vinculada(d: dict, usuario_id) -> bool:
    return usuario_id is not None and usuario_id in (d.get("titular_user_id"), d.get("substituto_user_id"))


def pode_cancelar(d: dict, usuario_id) -> bool:
    return usuario_id is not None and d.get("titular_user_id") == usuario_id and d.get("cancelada_em") is None


def datas(d: dict) -> tuple[date, date] | None:
    try:
        inicio, fim = date.fromisoformat(d.get("data_inicio")), date.fromisoformat(d.get("data_fim"))
        return (inicio, fim) if inicio <= fim else None
    except (ValueError, TypeError):
        return None


def situacao(d: dict, hoje: date) -> tuple[str, str]:
    if d.get("cancelada_em") is not None:
        return "Cancelada", "neu"
    if not (limites := datas(d)):
        return "Não disponível", "neu"
    inicio, fim = limites
    if hoje < inicio:
        return "Agendada", "azul"
    if hoje > fim:
        return "Encerrada", "neu"
    return "Ativa", "ok"


def linhas(delegacoes: list[dict], usuario_id, hoje: date, nomes: dict | None = None) -> list[dict]:
    resultado = []
    for d in delegacoes:
        if not vinculada(d, usuario_id):
            continue
        concedida = d.get("titular_user_id") == usuario_id
        status, tom = situacao(d, hoje)
        escopo = d.get("escopo")
        nota = ("Férias e correção de ponto." if escopo == "todas" else ""
                if escopo in ("ferias", "correcao_ponto") else "Decisão do RH: sem efeito para o Gestor.")
        outro = d.get("substituto_user_id") if concedida else d.get("titular_user_id")
        nome = (nomes or {}).get(outro)
        resultado.append({"id": d["id"], "pessoa": nome or ("Substituto não disponível" if concedida else "Titular não disponível"),
                          "direcao": "Delegada por mim" if concedida else "Recebida por mim",
                          "periodo": periodo(d.get("data_inicio"), d.get("data_fim")) if datas(d) else "—",
                          "escopo": ESCOPOS.get(escopo, "Não disponível"), "nota_escopo": nota,
                          "motivo": d.get("motivo") or "—", "situacao": status, "tom": tom,
                          "encerrada": status in ("Encerrada", "Cancelada"),
                          "cancelavel": pode_cancelar(d, usuario_id)})
    return resultado


# Criação pelo Gestor (change backend-gestor-pendencias, D3): só o que ele decide; o substituto vem do catálogo do backend.
ESCOPOS_GESTOR = ["ferias", "correcao_ponto", "todas"]


def rotulo_substituto(s: dict) -> str:
    extra = " · outro Gestor" if s.get("motivo") == "gestor" else ""
    return f"{s.get('nome') or 'Sem nome'} ({s.get('setor') or 'sem setor'}){extra}"


def validar_nova(substituto, escopo, inicio: date | None, fim: date | None, motivo: str, hoje: date) -> str | None:
    if not substituto:
        return "Escolha o substituto."
    if escopo not in ESCOPOS:
        return "Escolha o que delegar."
    if inicio is None or fim is None:
        return "Informe o início e o fim."
    if inicio < hoje:
        return "O início não pode ser no passado."
    if fim < inicio:
        return "O fim não pode ser antes do início."
    if len((motivo or "").strip()) < 5:
        return "Escreva o motivo (pelo menos 5 caracteres)."
    return None
