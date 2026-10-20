"""
Regras das telas de desligamento (Figma "Pedir desligamento" 224:4056 e "RH — Desligamentos" 249:3075; change
fluxo-de-desligamento). Funções puras, sem Streamlit.

Fluxo do backend: pendente → (RH assume) em análise → aprovado (aviso prévio: agendado para a data efetiva; imediato:
concluído na hora) ou rejeitado; pendente → cancelado (por quem pediu); agendado → concluído (na data efetiva, com o
checklist de saída completo). Ninguém decide o próprio pedido; as decisões são do RH.
"""

from datetime import date

from onboarding_modelo import data_br

MOTIVOS = ["Nova oportunidade de trabalho", "Mudança de cidade", "Questões pessoais ou de saúde", "Estudos", "Insatisfação com o trabalho", "Outro"]
ABAS = {"Pendentes": ("pendente",), "Em análise": ("em_analise",), "Agendados": ("agendado",), "Concluídos": ("concluido", "rejeitada", "cancelada")}
ORIGENS = {"funcionario": "Colaborador", "gestor": "Gestor"}
_STATUS = {"pendente": ("Pendente", "amb"), "em_analise": ("Em análise", "azul"), "agendado": ("Agendado", "neu"), "concluido": ("Concluído", "ok"),
           "rejeitada": ("Rejeitado", "err"), "cancelada": ("Cancelado", "neu")}
ATIVOS = ("pendente", "em_analise", "agendado")
COMO_FUNCIONA = [("Você envia o pedido", "Pode cancelar enquanto estiver pendente."), ("O RH analisa", "Você recebe uma notificação com a resposta."),
                 ("Checklist de saída", "Equipamentos, documentos e acertos."), ("Acesso encerrado", "No último dia combinado.")]
ETAPAS = ("Pendente → Em análise (RH assume) → Aprovado (com data efetiva) ou Rejeitado → Agendado → Concluído. O gestor só pede desligamento "
          "de quem é do departamento dele.")


def _data(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def situacao(status) -> tuple[str, str]:
    return _STATUS.get(status, (str(status or "—").capitalize(), "neu"))


def validar_pedido(data_prevista: date | None, hoje: date, confirmado: bool, comentario: str = "") -> str | None:
    if data_prevista is None:
        return "Informe o último dia de trabalho desejado."
    if data_prevista < hoje:
        return "O último dia não pode ser no passado."
    if len((comentario or "").strip()) > 900:
        return "O comentário pode ter no máximo 900 caracteres."
    if not confirmado:
        return "Marque que entende que o aviso prévio, os equipamentos e o último acesso serão combinados com o RH."
    return None


def montar_pedido(data_prevista: date, hoje: date, motivo: str | None, comentario: str) -> tuple[str, int, str]:
    """(tipo, dias de aviso, motivo para o backend). Data de hoje = imediato; depois = aviso prévio com os dias até ela.
    O backend exige um motivo de 5 caracteres ou mais: o formulário tem motivo e comentário opcionais."""
    dias = (data_prevista - hoje).days
    partes = [p for p in (motivo, (comentario or "").strip()) if p]
    texto = " — ".join(partes) if partes else "Motivo não informado"
    return ("imediato", 0, texto) if dias <= 0 else ("aviso_previo", dias, texto)


def tipo_legivel(s: dict) -> str:
    if s.get("tipo_desligamento") == "imediato":
        return "Imediato"
    dias = s.get("dias_aviso")
    return f"Aviso prévio · {dias} dias" if dias else "Aviso prévio"


def linhas_meus(solicitacoes: list[dict]) -> list[dict]:
    """Os pedidos da própria pessoa, do mais recente: último dia, situação e o que dá para fazer."""
    saida = []
    for s in sorted(solicitacoes or [], key=lambda x: str(x.get("created_at") or ""), reverse=True):
        badge, tom = situacao(s.get("status"))
        ultimo = data_br(s.get("data_efetiva") or s.get("data_prevista")) or "—"
        detalhe = [f"Pedido em {data_br(s.get('created_at')) or '—'}", tipo_legivel(s)]
        if s.get("origem") == "gestor":
            detalhe.append("pedido pelo gestor")
        if s.get("status") == "rejeitada" and s.get("motivo_decisao"):
            detalhe.append(f"Motivo do RH: {s['motivo_decisao']}")
        saida.append({"id": s.get("id"), "titulo": f"Último dia: {ultimo}", "detalhe": " · ".join(detalhe), "badge": badge, "tom": tom,
                      "pode_cancelar": s.get("status") == "pendente"})
    return saida


def pedido_em_andamento(solicitacoes: list[dict], colaborador_id) -> dict | None:
    return next((s for s in solicitacoes or [] if s.get("colaborador_id") == colaborador_id and s.get("status") in ATIVOS), None)


def indicadores(contagens: dict) -> list[tuple[str, str, str]]:
    c = contagens or {}
    return [("Pendentes", str(c.get("pendente") or 0), "ambar"), ("Em análise", str(c.get("em_analise") or 0), "azul"),
            ("Agendados", str(c.get("agendado") or 0), ""), ("Concluídos no ano", str(c.get("concluido_no_ano") or 0), "verde")]


def linhas_rh(solicitacoes: list[dict], aba: str, origem: str | None = None) -> list[dict]:
    status = ABAS.get(aba, ())
    saida = []
    for s in solicitacoes or []:
        if s.get("status") not in status or (origem and s.get("origem") != origem):
            continue
        badge, tom = situacao(s.get("status"))
        sub = " — ".join(p for p in (s.get("departamento"), s.get("cargo")) if p) or "—"
        saida.append({"id": s.get("id"), "pessoa": s.get("colaborador_nome") or "—", "sub": sub, "origem": ORIGENS.get(s.get("origem"), "—"),
                      "tipo": tipo_legivel(s), "data": data_br(s.get("data_efetiva") or s.get("data_prevista")) or "—",
                      "responsavel": s.get("responsavel_rh_nome") or "—", "status": s.get("status"), "badge": badge, "tom": tom,
                      "colaborador_user_id": s.get("colaborador_user_id"), "data_efetiva": s.get("data_efetiva"), "data_prevista": s.get("data_prevista"),
                      "tipo_desligamento": s.get("tipo_desligamento")})
    return saida


def acoes_rh(linha: dict, meu_user_id, hoje: date) -> dict:
    """{acao: motivo_de_estar_desligado_ou_None}."""
    if linha.get("colaborador_user_id") == meu_user_id and linha.get("status") in ATIVOS:
        motivo = "Outra pessoa do RH decide o seu desligamento"
        return {"assumir": motivo} if linha["status"] == "pendente" else {"rejeitar": motivo, "aprovar": motivo} if linha["status"] == "em_analise" else {"concluir": motivo}
    if linha.get("status") == "pendente":
        return {"assumir": None}
    if linha.get("status") == "em_analise":
        return {"rejeitar": None, "aprovar": None}
    if linha.get("status") == "agendado":
        efetiva = _data(linha.get("data_efetiva"))
        return {"concluir": f"Só a partir de {data_br(linha['data_efetiva'])}" if efetiva and efetiva > hoje else None}
    return {}


def validar_aprovacao(data_efetiva: date | None, hoje: date, motivo: str) -> str | None:
    if data_efetiva is None:
        return "Informe a data efetiva (o último dia)."
    if data_efetiva < hoje:
        return "A data efetiva não pode ser no passado."
    if len((motivo or "").strip()) < 5:
        return "Escreva a justificativa da decisão (pelo menos 5 caracteres)."
    return None


def linhas_checklist(itens: list[dict]) -> list[dict]:
    return [{"id": i.get("id"), "titulo": i.get("titulo") or "—", "detalhe": f"Responsável: {i.get('responsavel') or '—'}",
             "badge": "Feito" if i.get("feito") else "Pendente", "tom": "ok" if i.get("feito") else "amb", "feito": bool(i.get("feito"))}
            for i in sorted(itens or [], key=lambda x: x.get("ordem") or 0)]


def faltam(itens: list[dict]) -> int:
    return sum(1 for i in itens or [] if not i.get("feito"))
