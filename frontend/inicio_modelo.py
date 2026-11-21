"""
Regras do Início (Figma 62:38; tarefas 9 e 10 da change concluir-frontend-streamlit). Funções puras, sem Streamlit.

O número "Pendências" soma o que `central_de_tarefas` GET devolve para quem está logado: as pendências pessoais (senha
temporária, cadastro incompleto, férias próprias em análise) e as filas de decisão do perfil (férias, ausências,
documentos, desligamentos, avaliações da equipe e pedidos LGPD perto do prazo). Os campos foram conferidos contra a
resposta real do endpoint em 21/11/2026.
"""

PESSOAIS_BOOL = ("minha_senha_primeiro_acesso", "meu_cadastro_incompleto")
LISTAS = ("minhas_ferias_pendentes", "fila_ferias_pendentes", "fila_ausencias_pendentes", "fila_documentos_pendentes",
          "fila_desligamentos_pendentes", "equipe_avaliacoes_pendentes", "pedidos_lgpd_prazo_proximo")


def total_pendencias(central: dict | None) -> int | None:
    """None quando a Central não carregou (a tela mostra "—", nunca zero)."""
    if central is None:
        return None
    total = sum(1 for chave in PESSOAIS_BOOL if central.get(chave))
    return total + sum(len(central.get(chave) or []) for chave in LISTAS)


def resumo_pendencias(central: dict | None) -> str:
    """Linha embaixo do número: o que há de pessoal, para a pessoa saber por onde começar."""
    if central is None:
        return "Não carregou agora."
    partes = []
    if central.get("minha_senha_primeiro_acesso"):
        partes.append("trocar a senha temporária")
    if central.get("meu_cadastro_incompleto"):
        partes.append("completar o cadastro")
    if n := len(central.get("minhas_ferias_pendentes") or []):
        partes.append(f"{n} pedido{'s' if n > 1 else ''} de férias em análise")
    filas = sum(len(central.get(c) or []) for c in LISTAS[1:])
    if filas:
        partes.append(f"{filas} para decidir")
    return ", ".join(partes).capitalize() + "." if partes else "Nada pendente."
