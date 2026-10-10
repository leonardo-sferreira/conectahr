"""Teste de fumaca do frontend Streamlit: a tela "Entrar" renderiza sem excecao.

Roda o app sem navegador, com o AppTest do proprio Streamlit, e confere que a tela de
entrada tem os campos e os botoes esperados. Nao chama a API: so precisa de um
`.streamlit/secrets.toml` (em CI, copiado de `.streamlit/secrets.toml.example`).

Uso (na raiz do repositorio):
    python tools/smoke_frontend.py

Sai com codigo 1 se houver excecao ou se a tela nao tiver o que se espera.
"""

import sys
from pathlib import Path

# Console do Windows em cp1252 não mostra "→" (rótulo de botão).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / "frontend" / "app.py"

CAMPOS_ESPERADOS = {"E-mail", "Senha"}
BOTOES_ESPERADOS = {"Entrar", "Esqueci minha senha"}


def main() -> int:
    if not (RAIZ / ".streamlit" / "secrets.toml").exists():
        print("Falta .streamlit/secrets.toml (copie de .streamlit/secrets.toml.example).")
        return 1

    at = AppTest.from_file(str(APP), default_timeout=60).run()
    campos = {t.label for t in at.text_input}
    botoes = {b.label for b in at.button}

    falhas = []
    if len(at.exception):
        falhas.append(f"{len(at.exception)} excecao(oes): {[e.value for e in at.exception][:2]}")
    if not CAMPOS_ESPERADOS <= campos:
        falhas.append(f"campos esperados {sorted(CAMPOS_ESPERADOS)}, encontrados {sorted(campos)}")
    if not BOTOES_ESPERADOS <= botoes:
        falhas.append(f"botoes esperados {sorted(BOTOES_ESPERADOS)}, encontrados {sorted(botoes)}")

    if falhas:
        for falha in falhas:
            print("FALHA:", falha)
        return 1
    print(f"OK: tela Entrar renderizou (campos {sorted(campos)}, botoes {sorted(botoes)}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
