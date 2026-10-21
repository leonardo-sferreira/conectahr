"""
Regras das telas do canal de denúncias (Figma, seção 20 "Conformidade: canal de denúncias", 540:1194; change
canal-de-denuncias; Lei 14.457/2022). Funções puras, sem Streamlit.

O canal é público: funciona logado ou sem login, e nada liga a denúncia a uma conta. Quem envia recebe um código de 16
sinais, que só aparece uma vez e é o único jeito de acompanhar e conversar com a comissão de ética. Só os membros da
comissão veem a fila; quem se identificou tem o nome visto só por eles.
"""

import re

from onboarding_modelo import data_br

TIPOS = {
    "assedio_moral": "Assédio moral",
    "assedio_sexual": "Assédio sexual",
    "discriminacao": "Discriminação",
    "conduta_antietica": "Conduta antiética",
    "fraude": "Fraude ou corrupção",
    "seguranca": "Risco à segurança",
    "outro": "Outro",
}
SITUACOES = {"nova": ("Nova", "amb"), "em_apuracao": ("Em apuração", "azul"), "concluida": ("Concluída", "ok")}
RESULTADOS = {"procedente": "Procedente", "improcedente": "Improcedente", "inconclusiva": "Sem elementos suficientes"}
ABAS = {"Em aberto": ("nova", "em_apuracao"), "Concluídas": ("concluida",)}
COMO_FUNCIONA = [
    ("Você envia", "Recebe um código. Guarde: ele não aparece de novo."),
    ("A comissão de ética analisa", "Ninguém fora da comissão vê a denúncia."),
    ("Apuração", "A comissão pode pedir mais detalhes pelo código."),
    ("Conclusão", "Você vê o resultado pelo código. Retaliação é proibida (Lei 14.457/2022)."),
]
MIN_RELATO = 20


def tipo_legivel(tipo) -> str:
    return TIPOS.get(tipo, "—")


def situacao(status) -> tuple[str, str]:
    return SITUACOES.get(status, ("—", "neu"))


def validar_denuncia(tipo: str | None, relato: str, identificar: bool, identificacao: str) -> str | None:
    if tipo not in TIPOS:
        return "Escolha o que aconteceu."
    if len((relato or "").strip()) < MIN_RELATO:
        return f"Conte o que aconteceu com pelo menos {MIN_RELATO} caracteres."
    if identificar and len((identificacao or "").strip()) < 3:
        return "Para se identificar, escreva seu nome e um contato. Ou desligue a identificação."
    return None


def normalizar_codigo(codigo: str) -> str:
    return re.sub(r"[\s-]", "", (codigo or "")).upper()


def validar_codigo(codigo: str) -> str | None:
    if len(normalizar_codigo(codigo)) != 16:
        return "O código tem 16 letras e números (pode digitar com ou sem os hifens)."
    return None


def mascarar_codigo(codigo: str) -> str:
    """"K7QM-4HXP-2WRT-9FBD" → "K7QM-…-9FBD", para o título do acompanhamento."""
    c = normalizar_codigo(codigo)
    return f"{c[:4]}-…-{c[-4:]}" if len(c) == 16 else "—"


def linhas_conversa(mensagens: list[dict], para_comissao: bool) -> list[dict]:
    """Cada mensagem com quem escreveu do ponto de vista de quem lê, a data e o tom (âmbar para o lado de quem lê)."""
    saida = []
    for m in mensagens:
        do_denunciante = m.get("autor") == "denunciante"
        quem = ("Denunciante" if do_denunciante else "Comissão de ética") if para_comissao else ("Você" if do_denunciante else "Comissão de ética")
        meu_lado = do_denunciante != para_comissao
        saida.append({"quem": f"{quem} · {data_br(m.get('enviada_em'))}", "texto": m.get("texto") or "", "meu_lado": meu_lado})
    return saida


def indicadores(contagens: dict) -> list[tuple[str, str, str]]:
    return [("Novas", str(contagens.get("nova") or 0), "ambar"), ("Em apuração", str(contagens.get("em_apuracao") or 0), "azul"),
            ("Concluídas no ano", str(contagens.get("concluida_no_ano") or 0), "verde")]


def linhas_fila(lista: list[dict], aba: str, tipo: str | None = None) -> list[dict]:
    escolhidas = [d for d in lista if d.get("status") in ABAS[aba] and (not tipo or d.get("tipo") == tipo)]
    return [{"id": d["id"], "protocolo": d.get("protocolo") or "—", "identificacao": "Identificada" if d.get("identificada") else "Anônima",
             "pedido": f"{tipo_legivel(d.get('tipo'))} — {d.get('resumo') or ''}".rstrip(" —"), "recebida": data_br(d.get("recebida_em")),
             "situacao": situacao(d.get("status")) if aba == "Em aberto" else (RESULTADOS.get(d.get("resultado"), "Concluída"), "ok"),
             "destaque": d.get("status") == "nova"} for d in escolhidas]


def validar_mensagem(texto: str, minimo: int = 5) -> str | None:
    if len((texto or "").strip()) < minimo:
        return f"Escreva a mensagem (pelo menos {minimo} caracteres)."
    return None


def validar_conclusao(resultado: str | None, parecer: str) -> str | None:
    if resultado not in RESULTADOS:
        return "Escolha o resultado."
    if len((parecer or "").strip()) < 10:
        return "Escreva o parecer final (pelo menos 10 caracteres)."
    return None
