"""
Validação e normalização dos campos antes de chamar a API.

Espelha as regras que o backend já aplica (xano-workspace/api/conecta_rh_autenticacao
e table/user.xs) só para dar uma mensagem clara em português antes do envio. A
validação de verdade continua sendo do backend; aqui a ideia é evitar uma
requisição que com certeza falharia. Isso importa em especial no código de acesso,
em que cada envio inválido gasta uma das 5 tentativas.

Cada função devolve a mensagem de erro, ou None quando o valor é aceitável.
"""

import re

# Limites do backend: e-mail (RFC 5321), senha min:8|max:64 (user.senha,
# auth/senha/redefinir, auth/senha PATCH) e código de 6 dígitos (otp_codigo).
EMAIL_MAX = 254
SENHA_MIN = 8
SENHA_MAX = 64
CODIGO_TAMANHO = 6

# O tipo `email` do Xano recusa caracteres fora do ASCII (acento, emoji).
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
_CODIGO_RE = re.compile(rf"^\d{{{CODIGO_TAMANHO}}}$")


def normalizar_email(email: str) -> str:
    """Mesmo tratamento do backend (filters=trim|lower)."""
    return (email or "").strip().lower()


def validar_email(email: str) -> str | None:
    email = normalizar_email(email)
    if not email:
        return "Informe o e-mail."
    if len(email) > EMAIL_MAX:
        return "O e-mail informado é longo demais."
    if not email.isascii():
        return "O e-mail não pode ter acentos, emojis ou outros caracteres especiais."
    if not _EMAIL_RE.match(email):
        return "Informe um e-mail válido, no formato nome@empresa.com."
    return None


def validar_senha_login(senha: str) -> str | None:
    """Senha do login: só confere o que nunca seria uma senha válida, sem revelar
    nada sobre a conta (a mensagem de credencial errada continua vindo do backend)."""
    if not senha or not senha.strip():
        return "Informe a senha."
    if not SENHA_MIN <= len(senha) <= SENHA_MAX:
        return f"A senha tem entre {SENHA_MIN} e {SENHA_MAX} caracteres."
    return None


def validar_codigo(codigo: str) -> str | None:
    codigo = (codigo or "").strip()
    if not codigo:
        return "Digite o código recebido por e-mail."
    if not _CODIGO_RE.match(codigo):
        return f"O código tem exatamente {CODIGO_TAMANHO} números, sem letras, espaços ou símbolos."
    return None


def validar_nova_senha(nova_senha: str, confirmar_senha: str) -> str | None:
    if not nova_senha or not nova_senha.strip():
        return "Informe a nova senha."
    if not SENHA_MIN <= len(nova_senha) <= SENHA_MAX:
        return f"A nova senha precisa ter entre {SENHA_MIN} e {SENHA_MAX} caracteres."
    if nova_senha != confirmar_senha:
        return "A confirmação não corresponde à nova senha."
    return None
