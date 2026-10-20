"""Testes das regras de campo (frontend/campos.py; pedido do usuário em 20/10/2026), sem Streamlit.

Confere o que cada tipo aceita, que nenhum aceita emoji (inclusive com tom de pele e sequências unidas) e a data em três
partes. O comportamento na tela (aviso embaixo do campo e o botão principal que não grava) está em tools/testar_cadastro.py e
tools/testar_perfil.py.

Uso (na raiz do repositório):
    python tools/testar_campos.py
"""

import sys
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "frontend"))

from campos import TIPOS, aviso, eh_emoji, limpar, montar_data  # noqa: E402

falhas: list[str] = []
total = 0


def conferir(ok: bool, descricao: str) -> None:
    global total
    total += 1
    if not ok:
        falhas.append(descricao)
        print("  FALHA:", descricao)
    else:
        print("  ok:", descricao)


EMOJIS = ["\U0001F600", "\U0001F44D\U0001F3FD", "\U0001F469\u200D\U0001F4BB", "\u2764\uFE0F", "\u2705", "\U0001F1E7\U0001F1F7", "\u0031\uFE0F\u20E3"]
conferir(all(not any(eh_emoji(c) for c in limpar("abc" + e, tipo)[0]) and limpar("abc" + e, tipo)[1] for e in EMOJIS for tipo in TIPOS), "nenhum tipo aceita emoji (tom de pele, sequências, bandeiras, teclas)")
conferir(limpar("(11) 98765-4321", "numero") == ("11987654321", "() -") and limpar("12A", "numero") == ("12", "A") and limpar("١٢", "numero")[0] == "",
         "número: só dígitos 0-9")
conferir(limpar("José D'Ávila-Souza Jr.", "nome")[1] == "" and limpar("Ana2", "nome") == ("Ana", "2"), "nome: letras com acento, espaço, hífen, apóstrofo e ponto")
conferir(limpar("Rua 7 de Setembro, 1° andar, nº 2 (fundos) #3", "endereco")[1] == "" and limpar("Casa B", "endereco")[1] == "", "endereço: letras, números e pontuação")
conferir(limpar("ana.maria+rh@exemplo.com", "email")[1] == "" and limpar("ana maria@ex.com", "email") == ("anamaria@ex.com", " ")
         and limpar("joão@ex.com", "email")[0] == "joo@ex.com", "e-mail: sem espaço e sem acento")
conferir(limpar("X", "codigo")[1] == "" and limpar("1-", "codigo") == ("1", "-"), "código (dígito da conta): letras e números")
conferir(limpar("Linha 1\nLinha 2\tok", "texto")[1] == "" and limpar("a\x07b", "texto") == ("ab", "\x07"), "texto livre: mantém quebra de linha e tira controle")
conferir(not eh_emoji("°") and not eh_emoji("ç") and not eh_emoji("€") and eh_emoji("❤"), "grau, letras e moeda não são emoji; coração é")
conferir(aviso("Nome", "Ana \U0001F600", "nome") == "Nome: não é permitido emoji. Apague para continuar." and aviso("Telefone", "11a", "numero") == "Telefone: aceita só números. Apague “a” para continuar."
         and aviso("Bairro", "Centro", "endereco") is None and aviso("Motivo", "ok \U0001F44D", "texto").endswith("não é permitido emoji. Apague para continuar."), "frase do aviso")
conferir(montar_data(29, 2, 2008) == date(2008, 2, 29) and montar_data(29, 2, 2007) is None and montar_data(None, 1, 2000) is None, "data em três partes: dia que existe")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
