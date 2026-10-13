"""
Regras de apresentação de "Solicitações ao RH" (tarefa 47 da change concluir-frontend-streamlit; Figma
225:5299 e 206:1072, "RH — Aplicar mudança no cadastro" — a conferir com o Figma, ver design.md).
Funções puras, sem Streamlit.

Os pedidos vêm de `solicitacoes` (RH e Admin). Os pedidos LGPD ficam fora: têm tela própria ("Pedidos
LGPD"). O pedido de alteração cadastral do Perfil é um texto com "Campo:", "Valor atual:", "Novo valor:" e
"Motivo:"; a tela lê esse texto para mostrar o antes e o depois e já preencher o cadastro. Atender não muda
o cadastro sozinho: o RH aplica a mudança (`colaboradores/{id}` PATCH) e então atende.
"""

import re
from datetime import date, timedelta

from cadastro_modelo import cpf_valido
from onboarding_modelo import data_br

TIPOS = {
    "alteracao_cadastral": "Alteração cadastral",
    "declaracao": "Declaração",
    "documento_avulso": "Documento avulso",
    "outra": "Outro pedido",
}
ABAS = {"Em aberto": ("recebida", "em_analise"), "Atendidas": ("atendida",), "Recusadas": ("indeferida",)}
_SITUACAO = {"recebida": ("Recebida", "amb"), "em_analise": ("Em análise", "amb"), "atendida": ("Atendida", "ok"), "indeferida": ("Recusada", "err")}
PRAZO_DIAS = 15
# Campo do pedido (Perfil) -> campo de `colaboradores/{id}` PATCH. Endereço o RH ajusta campo a campo.
CAMPO_PARA_CADASTRO = {"Nome completo": "nome", "CPF": "cpf", "Data de nascimento": "data_nascimento", "Telefone": "telefone", "E-mail pessoal": "email_pessoal"}
CAMPOS_PESSOAIS = ["nome", "cpf", "email_pessoal", "data_nascimento", "telefone", "cep", "logradouro", "numero", "complemento", "bairro", "cidade", "estado"]
_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _dia(valor) -> date | None:
    texto = data_br(valor)
    if not texto:
        return None
    d, m, a = texto.split("/")
    return date(int(a), int(m), int(d))


def ler_alteracao(descricao: str) -> dict | None:
    """{'campo', 'atual', 'novo', 'motivo'} do texto do Perfil; None se o texto não seguir esse formato."""
    partes = {}
    for linha in (descricao or "").splitlines():
        chave, _, valor = linha.partition(":")
        partes[chave.strip().casefold()] = valor.strip()
    if "campo" not in partes or "novo valor" not in partes:
        return None
    return {"campo": partes["campo"], "atual": partes.get("valor atual") or "—", "novo": partes["novo valor"], "motivo": partes.get("motivo") or ""}


def _resumo_pedido(s: dict) -> str:
    alt = ler_alteracao(s.get("descricao")) if s.get("tipo") == "alteracao_cadastral" else None
    if alt:
        return f"{alt['campo']}: {alt['atual']} → {alt['novo']}"
    texto = " ".join((s.get("descricao") or "").split())
    return texto if len(texto) <= 90 else texto[:87] + "..."


def prazo(s: dict) -> date | None:
    """Abertura + 15 dias (só quando o backend devolve a data de abertura)."""
    aberto = _dia(s.get("created_at"))
    return aberto + timedelta(days=PRAZO_DIAS) if aberto else None


def linhas(solicitacoes: list[dict], mapa: dict, aba: str, hoje: date, tipo=None, departamento_id=None) -> list[dict]:
    """{'id', 'colaborador_id', 'pessoa', 'detalhe', 'tipo', 'tipo_chave', 'pedido', 'aberto_em', 'prazo', 'atrasado',
    'situacao', 'alteracao', 'descricao', 'justificativa', 'decidido_em'}. Em aberto: do prazo mais curto ao mais longo."""
    status_aba = ABAS[aba]
    saida = []
    for s in solicitacoes:
        if s.get("tipo") not in TIPOS or (s.get("status") or "recebida") not in status_aba:
            continue
        if tipo and s.get("tipo") != tipo:
            continue
        p = mapa.get(s.get("colaborador_id")) or {"nome": f"Colaborador nº {s.get('colaborador_id')}", "detalhe": "—", "departamento_id": None}
        if departamento_id and p.get("departamento_id") != departamento_id:
            continue
        limite = prazo(s)
        aberto = (s.get("status") or "recebida") in ABAS["Em aberto"]
        saida.append({
            "id": s.get("id"), "colaborador_id": s.get("colaborador_id"), "pessoa": p["nome"], "detalhe": p["detalhe"],
            "tipo": TIPOS[s["tipo"]], "tipo_chave": s["tipo"], "pedido": _resumo_pedido(s),
            "aberto_em": data_br(s.get("created_at")) or "—",
            "prazo": limite.strftime("%d/%m/%Y") if limite else "—",
            "atrasado": bool(aberto and limite and limite < hoje),
            "situacao": _SITUACAO.get(s.get("status") or "recebida", ("Recebida", "amb")),
            "alteracao": ler_alteracao(s.get("descricao")) if s["tipo"] == "alteracao_cadastral" else None,
            "descricao": s.get("descricao") or "", "justificativa": s.get("justificativa_decisao") or "",
            "decidido_em": data_br(s.get("data_decisao")) or "—",
            # Em aberto: prazo mais curto primeiro; decididas: decisão mais recente primeiro.
            "_ordem": (limite.toordinal() if limite else 10**9) if aberto else -(_dia(s.get("data_decisao")) or date.min).toordinal(),
        })
    saida.sort(key=lambda l: l.pop("_ordem"))
    return saida


def resumo(solicitacoes: list[dict], hoje: date) -> dict:
    validas = [s for s in solicitacoes if s.get("tipo") in TIPOS]
    em_aberto = [s for s in validas if (s.get("status") or "recebida") in ABAS["Em aberto"]]
    mes = lambda s: (_dia(s.get("data_decisao")) or date.min).strftime("%m/%Y") == hoje.strftime("%m/%Y")
    return {
        "em_aberto": len(em_aberto),
        "cadastrais": sum(1 for s in em_aberto if s.get("tipo") == "alteracao_cadastral"),
        "atrasadas": sum(1 for s in em_aberto if prazo(s) and prazo(s) < hoje),
        "atendidas_mes": sum(1 for s in validas if s.get("status") == "atendida" and mes(s)),
    }


def dados_atuais(colab: dict) -> dict:
    """Os dados pessoais da ficha, no formato de `colaboradores/{id}` PATCH."""
    dados = {campo: str(colab.get(campo) or "") for campo in CAMPOS_PESSOAIS}
    dados["cpf"] = re.sub(r"\D", "", dados["cpf"])
    dados["data_nascimento"] = dados["data_nascimento"][:10]
    return dados


def aplicar_pedido(atuais: dict, alteracao: dict | None) -> dict:
    """Os dados atuais com o valor pedido já aplicado, quando o campo é reconhecido (endereço: o RH ajusta)."""
    dados = dict(atuais)
    campo = CAMPO_PARA_CADASTRO.get((alteracao or {}).get("campo"))
    if not campo:
        return dados
    novo = alteracao["novo"].strip()
    if campo == "cpf":
        novo = re.sub(r"\D", "", novo)
    elif campo == "data_nascimento":
        achado = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", novo)
        novo = f"{achado.group(3)}-{achado.group(2)}-{achado.group(1)}" if achado else novo
    elif campo == "email_pessoal":
        novo = novo.lower()
    dados[campo] = novo
    return dados


def validar_dados_pessoais(dados: dict, hoje: date) -> str | None:
    """As conferências de `colaboradores/{id}` PATCH, antes de enviar."""
    if len(dados.get("nome", "").strip()) < 2:
        return "Informe o nome completo."
    if not cpf_valido(dados.get("cpf", "")):
        return "CPF inválido. Confira os 11 dígitos."
    if not _RE_EMAIL.match(dados.get("email_pessoal", "").strip()):
        return "Informe um e-mail pessoal válido."
    try:
        nasc = date.fromisoformat(dados.get("data_nascimento", ""))
    except ValueError:
        return "Data de nascimento inválida. Use dd/mm/aaaa."
    if nasc >= hoje:
        return "A data de nascimento precisa ser anterior a hoje."
    # Contato e endereço são opcionais (13/10/2026): um pedido de CPF ou de nome é aplicado mesmo com a ficha sem
    # endereço; o backend mantém o que já está na ficha quando o campo vem vazio. Só se confere o que veio preenchido.
    if len(dados.get("cep", "").strip()) > 9:
        return "O CEP tem no máximo 9 caracteres."
    estado = dados.get("estado", "").strip()
    if estado and not re.fullmatch(r"[A-Za-z]{2}", estado):
        return "Informe o estado com 2 letras (por exemplo, SP)."
    return None


def validar_justificativa(texto: str) -> str | None:
    if len((texto or "").strip()) < 5:
        return "Explique a decisão em pelo menos 5 caracteres."
    return None
