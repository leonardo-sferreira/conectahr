"""
Regras de apresentação de Configurações → Privacidade (Figma 286:878, modais 286:1062, 286:1092 e
224:2379; tarefas 5 e 67 da change concluir-frontend-streamlit). Funções puras, sem Streamlit.

Dados: `minhas_preferencias_privacidade`, `minhas_solicitacoes` (só os pedidos `privacidade_lgpd`)
e `meus_dados` (exportação).
"""

import json

from onboarding_modelo import data_br

# Os sete subtipos do backend (solicitacoes_POST) e o nome de cada um na lista "Meus pedidos".
SUBTIPOS = {
    "confirmacao_acesso": "Confirmação e acesso aos dados",
    "correcao": "Correção de dados",
    "anonimizacao_eliminacao": "Apagar dados não obrigatórios",
    "portabilidade": "Cópia dos meus dados",
    "informacao_compartilhamento": "Com quem meus dados são compartilhados",
    "revogacao_consentimento": "Revogação de consentimento",
    "oposicao": "Oposição a um tratamento",
}

# As três opções do modal "Fazer um pedido" (Figma 224:2379). Os outros direitos já têm caminho
# próprio na tela: baixar os dados (acesso e portabilidade) e os dois botões de "O que os colegas
# veem" (oposição).
OPCOES_PEDIDO = {
    "correcao": "Corrigir um dado",
    "anonimizacao_eliminacao": "Apagar dados que não são obrigatórios",
    "informacao_compartilhamento": "Saber com quem meus dados são compartilhados",
}

_SITUACAO = {
    "recebida": ("Recebido", "neu"),
    "em_analise": ("Em análise", "amb"),
    "atendida": ("Concluído", "ok"),
    "indeferida": ("Indeferido", "err"),
}

FORMATOS = {
    "json": ("JSON", "Para levar os dados para outro sistema"),
    "csv": ("CSV", "Para abrir em uma planilha"),
}


def pedidos_privacidade(solicitacoes: list[dict]) -> list[dict]:
    """Linhas de "Meus pedidos de privacidade": {'titulo', 'detalhe', 'badge', 'tipo'}."""
    linhas = []
    for s in solicitacoes:
        if s.get("tipo") != "privacidade_lgpd":
            continue
        selo, tom = _SITUACAO.get(s.get("status") or "recebida", ("Recebido", "neu"))
        aberto = data_br(s.get("created_at") or s.get("updated_at"))
        partes = [f"Aberto em {aberto}"] if aberto else []
        prazo = data_br(s.get("prazo_resposta"))
        if prazo and s.get("status") in (None, "recebida", "em_analise"):
            partes.append(f"responder até {prazo}")
        linhas.append({
            "titulo": SUBTIPOS.get(s.get("subtipo_lgpd"), "Pedido de privacidade"),
            "detalhe": " · ".join(partes) or None,
            "badge": selo,
            "tipo": tom,
        })
    return linhas


def validar_pedido(subtipo: str | None, descricao: str) -> str | None:
    if subtipo not in OPCOES_PEDIDO:
        return "Escolha o que você precisa."
    texto = (descricao or "").strip()
    if len(texto) < 5:
        return "Detalhe o pedido em pelo menos 5 caracteres."
    if len(texto) > 2000:
        return "O detalhe pode ter no máximo 2000 caracteres."
    return None


def arquivo_exportado(resposta: dict, formato: str) -> tuple[str, bytes, str]:
    """(nome do arquivo, conteúdo, tipo MIME) a partir da resposta de `meus_dados`.

    JSON: a resposta inteira, menos os campos técnicos (`sucesso`, `formato`, `csv`). CSV: o texto
    que o backend montou."""
    if formato == "csv":
        return "meus_dados.csv", str(resposta.get("csv") or "").encode("utf-8-sig"), "text/csv"
    dados = {k: v for k, v in resposta.items() if k not in ("sucesso", "formato", "csv")}
    return "meus_dados.json", json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8"), "application/json"
