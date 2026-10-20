"""
Regras das abas "Segurança" (Figma 213:142) e "Notificações" (213:236) de Configurações (change
configuracoes-seguranca-notificacoes). Funções puras, sem Streamlit. O backend decide; estas regras só preparam a
tela e evitam uma chamada que seria recusada.
"""

from ponto_modelo import para_brasilia

# (assunto, título, descrição, tem e-mail). Ordem e textos do Figma 213:236; "Solicitações ao RH" entra porque já
# manda e-mail (design D2). O ponto não manda e-mail.
ASSUNTOS = [
    ("ferias_ausencias", "Férias e ausências", "Pedido aprovado, recusado ou perto de vencer", True),
    ("ponto", "Ponto e correções", "Correção decidida, ajuste feito pelo RH ou gestor", False),
    ("documentos", "Documentos", "Documento recusado, pedido ou vencendo", True),
    ("avaliacoes_metas", "Avaliações e metas", "Avaliação atribuída, etapa do ciclo e feedback", True),
    ("solicitacoes", "Solicitações ao RH", "Sua solicitação atendida ou indeferida", True),
]
SEMPRE_LIGADOS = [
    ("Benefícios", "Benefício novo, alterado, com pergunta nova ou encerrado"),
    ("Alertas de segurança", "Novo acesso, troca de senha, e-mail da conta alterado"),
    ("Pedidos para você decidir", "Férias, ausências, correções e documentos da sua equipe"),
]


def regras_senha(nova: str, atual: str) -> list[tuple[str, bool]]:
    """As três regras do Figma, para ficarem verdes enquanto a pessoa digita."""
    nova = nova or ""
    return [
        ("8 caracteres ou mais", len(nova) >= 8),
        ("Letras e números", any(c.isalpha() for c in nova) and any(c.isdigit() for c in nova)),
        ("Diferente da senha atual", bool(nova) and nova != (atual or "")),
    ]


def validar_troca(atual: str, nova: str, confirmar: str) -> str | None:
    if not atual:
        return "Informe a senha atual."
    if not all(ok for _, ok in regras_senha(nova, atual)):
        return "A nova senha precisa ter 8 caracteres ou mais, com letras e números, e ser diferente da atual."
    if len(nova) > 64:
        return "A nova senha pode ter no máximo 64 caracteres."
    if nova != confirmar:
        return "A confirmação não corresponde à nova senha."
    return None


def _quando(valor) -> str:
    momento = para_brasilia(valor)
    return f"desde {momento:%d/%m/%Y às %H:%M}" if momento else "início não informado"


def linhas_sessoes(sessoes: list[dict], sessao_atual_id) -> list[dict]:
    """Só as sessões ativas; a deste aparelho primeiro, marcada como "Este dispositivo"."""
    linhas = []
    for s in sessoes or []:
        if not s.get("ativa") or s.get("revogada_em"):
            continue
        atual = s.get("id") == sessao_atual_id
        ip = f"IP {s['endereco_ip']}" if s.get("endereco_ip") else "IP não informado"
        linhas.append({"id": s.get("id"), "titulo": s.get("dispositivo") or "Navegador não identificado",
                       "detalhe": f"{ip} · {'ativo agora' if atual else _quando(s.get('created_at'))}", "atual": atual})
    return sorted(linhas, key=lambda l: not l["atual"])


def preferencias_por_assunto(preferencias: list[dict]) -> dict:
    """{assunto: (plataforma, email)}; sem registro, os dois ligados."""
    salvas = {p.get("assunto"): (bool(p.get("plataforma", True)), bool(p.get("email", True))) for p in preferencias or []}
    return {a: salvas.get(a, (True, True)) for a, *_ in ASSUNTOS}


def alteradas(salvas: dict, escolhidas: dict) -> list[tuple[str, bool, bool]]:
    """(assunto, plataforma, email) que mudaram em relação ao que está gravado."""
    return [(a, *escolhidas[a]) for a, *_ in ASSUNTOS if a in escolhidas and escolhidas[a] != salvas.get(a)]
