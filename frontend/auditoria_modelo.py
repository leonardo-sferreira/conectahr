"""
Regras da tela Auditoria (Figma 225:6784; tarefas 34 e 35 de concluir-frontend-streamlit). Funções puras, sem Streamlit.

Dados: `auditoria` GET (só RH e Admin): os eventos da janela de dias, já filtrados no backend, com as opções dos filtros
e os nomes de quem fez cada ação. Os valores anterior e novo já chegam mascarados (são gravados assim).
"""

from ponto_modelo import para_brasilia

PERIODOS = {7: "Últimos 7 dias", 30: "Últimos 30 dias", 90: "Últimos 90 dias", 366: "Último ano"}
RESULTADOS = {"sucesso": "Sucesso", "falha": "Falha"}


def nomes(usuarios: list[dict]) -> dict:
    """{id: "Ana Ribeiro (RH)"}: como no Figma, o perfil entre parênteses para RH e Admin."""
    saida = {}
    for u in usuarios or []:
        perfil = str(u.get("perfil") or "").strip().upper()
        sufixo = " (RH)" if perfil == "RH" else " (Admin)" if perfil == "ADMIN" else ""
        saida[u.get("id")] = f"{u.get('nome') or 'Usuário'}{sufixo}"
    return saida


def quando(valor) -> str:
    momento = para_brasilia(valor)
    return f"{momento:%d/%m/%Y %H:%M}" if momento else "—"


def tom_resultado(resultado) -> str:
    r = str(resultado or "").strip().lower()
    return "ok" if r == "sucesso" else "err" if r == "falha" else "neu"


def linhas(eventos: list[dict], usuarios: list[dict]) -> list[dict]:
    """Uma linha por evento: data e hora de Brasília, quem, ação, recurso, justificativa e resultado."""
    por_id = nomes(usuarios)
    saida = []
    for e in eventos or []:
        uid = e.get("user_id")
        saida.append({
            "id": e.get("id"),
            "quando": quando(e.get("created_at")),
            "usuario": por_id.get(uid) or ("Sistema" if uid is None else f"Usuário nº {uid}"),
            "acao": e.get("acao") or "—",
            "recurso": e.get("recurso") or "—",
            "justificativa": e.get("justificativa") or "—",
            "resultado": e.get("resultado") or "—",
            "tom": tom_resultado(e.get("resultado")),
            "registro_id": e.get("registro_id"),
            "valor_anterior": e.get("valor_anterior"),
            "valor_novo": e.get("valor_novo"),
            "endereco_ip": e.get("endereco_ip"),
        })
    return saida


def detalhes(linha: dict) -> list[tuple[str, str]]:
    """Os campos do evento para o modal "Detalhes" (os valores já vêm mascarados do backend)."""
    return [
        ("Data e hora", linha["quando"]), ("Usuário", linha["usuario"]), ("Ação", linha["acao"]), ("Recurso", linha["recurso"]),
        ("Registro", str(linha["registro_id"]) if linha.get("registro_id") is not None else "—"), ("Resultado", linha["resultado"]),
        ("Justificativa", linha["justificativa"]), ("Valor anterior", linha.get("valor_anterior") or "—"),
        ("Valor novo", linha.get("valor_novo") or "—"), ("IP", linha.get("endereco_ip") or "—"),
    ]


def opcoes_usuarios(ids: list, usuarios: list[dict]) -> dict:
    """{id: nome} só de quem aparece na janela, por nome."""
    por_id = nomes(usuarios)
    return dict(sorted(((i, por_id.get(i) or f"Usuário nº {i}") for i in ids or []), key=lambda par: par[1]))
