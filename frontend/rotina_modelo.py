"""
Regras da tela "Rotina diária" (Figma 289:900, 289:1190 e 289:1477 e o modal 290:1164; tarefa 64 da change
concluir-frontend-streamlit). Funções puras, sem Streamlit.

As contagens vêm de `ConectaHR/processar_transicoes_diarias`: sem gravar, em `status_operacional` GET
(`rotina_diaria_pendente`), e aplicando, na resposta de `rotinas/processar_diarias` POST (`aplicadas`). As duas têm as
mesmas chaves. `desligados_prazo_cumprido` é uma lista (só aviso: a anonimização é pessoa a pessoa).
"""

from datetime import datetime

from ponto_modelo import para_brasilia

# (chave ou chaves somadas, título, o que acontece)
TRANSICOES = [
    (("desligamentos_concluidos",), "Desligamentos agendados com data efetiva atingida",
     "Concluir o desligamento, gravar o histórico profissional e revogar as sessões"),
    (("ferias_concluidas",), "Férias aprovadas já encerradas", "Passam de Aprovada para Concluída"),
    (("ponto_para_incompleto",), "Ponto aberto de dias anteriores", "Passa de Aberto para Incompleto"),
    (("instrumentos_expirados",), "Instrumentos vigentes com a vigência encerrada", "Passam de Vigente para Expirado"),
    (("colaboradores_para_ferias", "colaboradores_para_afastado", "colaboradores_para_ativo"), "Status do colaborador",
     "Ativo, Férias ou Afastado conforme as férias e os afastamentos em andamento"),
    (("convites_pesquisa", "convite_termometro", "prazos_vencendo_avisados"), "Avisos do dia",
     "Convites de pesquisa e do termômetro de humor, e avisos de prazos perto de vencer"),
]
RETENCAO = [
    (("sessoes_ip_dispositivo_limpos",), "Sessões antigas", "Limpar IP e dispositivo das sessões com prazo de guarda vencido (180 dias)"),
    (("emails_enviados_limpos",), "E-mails enviados antigos", "Trocar destinatário e corpo por marcadores (180 dias)"),
]
DESLIGADOS = ("desligados_prazo_cumprido", "Desligados com prazo de guarda cumprido")


def _numero(valor) -> int:
    if isinstance(valor, list):
        return len(valor)
    if isinstance(valor, bool):
        return int(valor)
    if isinstance(valor, (int, float)):
        return int(valor)
    return 0


def _soma(contagens: dict, chaves: tuple) -> int:
    return sum(_numero((contagens or {}).get(c)) for c in chaves)


def linhas(contagens: dict, aplicado: bool = False) -> dict:
    """{"transicoes": [...], "retencao": [...]}; cada linha {titulo, detalhe, quantidade}."""
    c = contagens or {}
    trans = [{"titulo": t, "detalhe": d, "quantidade": _soma(c, ch)} for ch, t, d in TRANSICOES]
    ret = [{"titulo": t, "detalhe": d, "quantidade": _soma(c, ch)} for ch, t, d in RETENCAO]
    ret.append({"titulo": DESLIGADOS[1], "quantidade": _numero(c.get(DESLIGADOS[0])),
                "detalhe": "Lista atualizada em Retenção e anonimização" if aplicado
                else "Só lista: a anonimização é feita pessoa a pessoa em Retenção e anonimização"})
    return {"transicoes": trans, "retencao": ret}


def totais(contagens: dict) -> tuple[int, int]:
    """(transições, registros a limpar). Os desligados com prazo cumprido não entram: a rotina só os lista."""
    c = contagens or {}
    return sum(_soma(c, ch) for ch, _, _ in TRANSICOES), sum(_soma(c, ch) for ch, _, _ in RETENCAO)


_data = para_brasilia


def ultima_execucao(eventos: list[dict], usuarios: list[dict] | None = None) -> dict | None:
    """O evento `processar_rotinas_diarias` mais recente: {quando "dd/mm/aaaa hh:mm", por}."""
    nomes = {u.get("id"): u.get("nome") for u in usuarios or []}
    rodadas = [e for e in eventos or [] if e.get("acao") == "processar_rotinas_diarias" and _data(e.get("created_at"))]
    if not rodadas:
        return None
    e = max(rodadas, key=lambda x: _data(x.get("created_at")))
    return {"quando": f"{_data(e['created_at']):%d/%m/%Y %H:%M}", "por": nomes.get(e.get("user_id"))}


def resumo_execucao(aplicadas: dict, quando: datetime, nome: str) -> str:
    trans, limpos = totais(aplicadas)
    if not trans and not limpos:
        return f"Rotina executada em {quando:%d/%m/%Y} às {quando:%H:%M} por {nome}. Nada para mudar: as contagens já estavam zeradas."
    return (f"Rotina executada em {quando:%d/%m/%Y} às {quando:%H:%M} por {nome}. "
            f"{trans} {'transição aplicada' if trans == 1 else 'transições aplicadas'} e "
            f"{limpos} {'registro limpo' if limpos == 1 else 'registros limpos'}.")
