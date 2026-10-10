"""Confere que as fontes do frontend são servidas pelo próprio app, sem serviço externo (tarefa 4 da
change concluir-frontend-streamlit; LGPD: o navegador não deve mandar o IP de quem usa ao Google).

Verifica:
- nenhum endereço do Google Fonts (`googleapis.com`, `gstatic.com`) no frontend nem na configuração;
- cada `@font-face` de `frontend/theme.py` aponta para um arquivo `.woff2` válido em `frontend/static/fonts`;
- todo peso de fonte usado no CSS tem o arquivo correspondente;
- `server.enableStaticServing = true` em `.streamlit/config.toml` e as licenças (OFL) junto das fontes.

Uso (na raiz do repositório):
    python tools/checar_fontes_locais.py
"""

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
FRONTEND = RAIZ / "frontend"
FONTES = FRONTEND / "static" / "fonts"
falhas: list[str] = []


def conferir(ok: bool, descricao: str) -> None:
    print(("  ok: " if ok else "  FALHA: ") + descricao)
    if not ok:
        falhas.append(descricao)


arquivos = [*FRONTEND.rglob("*.py"), RAIZ / ".streamlit" / "config.toml"]
externos = [f"{a.relative_to(RAIZ)}" for a in arquivos if re.search(r"googleapis\.com|gstatic\.com", a.read_text(encoding="utf-8"))]
conferir(not externos, f"nenhum endereço do Google Fonts no frontend ({externos or 'nenhum'})")

tema = (FRONTEND / "theme.py").read_text(encoding="utf-8")
faces = re.findall(r"font-family: '(\w+)'; font-style: normal; font-weight: (\d+);.*?url\('app/static/fonts/([\w.-]+)'\)", tema)
conferir(len(faces) >= 5, f"{len(faces)} @font-face locais em theme.py")
for familia, peso, arquivo in faces:
    caminho = FONTES / arquivo
    valido = caminho.exists() and caminho.read_bytes()[:4] == b"wOF2"
    conferir(valido, f"{familia} {peso}: {arquivo} existe e é woff2")

pesos_declarados = {int(p) for _, p, _ in faces}
pesos_usados = {int(p) for p in re.findall(r"font-weight: ?(\d+)", tema.split("@font-face")[-1])}
conferir(pesos_usados <= pesos_declarados, f"pesos usados no CSS {sorted(pesos_usados)} têm arquivo ({sorted(pesos_declarados)})")

config = (RAIZ / ".streamlit" / "config.toml").read_text(encoding="utf-8")
conferir(re.search(r"^enableStaticServing\s*=\s*true", config, re.M) is not None, "server.enableStaticServing = true")
for familia in {f.lower() for f, _, _ in faces}:
    licenca = FONTES / f"LICENSE-{familia}.txt"
    conferir(licenca.exists() and "SIL Open Font License" in licenca.read_text(encoding="utf-8"), f"licença OFL de {familia}")

print(f"\n{'Falhou' if falhas else 'Tudo certo'}: {len(falhas)} problema(s).")
sys.exit(1 if falhas else 0)
