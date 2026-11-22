"""Gera o site da documentação (GitHub Pages) a partir de docs/tecnica/README.md e docs/usuario/manual-do-usuario.md.

Uso (na raiz do repositório):
    python tools/gerar_site.py            atualiza os números nos dois Markdown e gera o site em _site/
    python tools/gerar_site.py --checar   só confere: falha se algum número dos Markdown estiver desatualizado

Os números (telas, endpoints, tabelas...) são contados no código, para a documentação não divergir dele. No Markdown,
cada número fica entre comentários (<!--n:telas-->55<!--/n-->), invisíveis no GitHub; um marcador novo se escreve
{{telas}}. Os links para outros arquivos do repositório viram links para o GitHub; os dois documentos viram as páginas
do site. Precisa do pacote `markdown` (pip install markdown==3.11.3), que não é dependência do app.
"""

from __future__ import annotations

import html
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

RAIZ = Path(__file__).resolve().parent.parent
REPO = "https://github.com/leonardo-sferreira/conectahr"
APP = "https://conectahr-wtdxtqbzz4lyrpjv8a48nt.streamlit.app/"
DOCS = {"tecnica": RAIZ / "docs/tecnica/README.md", "usuario": RAIZ / "docs/usuario/manual-do-usuario.md"}
PAGINA_DE = {"docs/tecnica/README.md": "tecnica.html", "docs/usuario/manual-do-usuario.md": "usuario.html"}
ARQUIVOS_ESTATICOS = [(RAIZ / "site/assets/estilo.css", "assets/estilo.css"), (RAIZ / "site/assets/app.js", "assets/app.js"),
                      (RAIZ / "frontend/assets/logo-icon.svg", "assets/logo.svg")]
FONTES = ["sora-600", "sora-800", "manrope-400", "manrope-500", "manrope-600"]
MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"
NOMES_GRUPO = {"autenticacao": "Autenticação", "gestao_de_usuarios": "Gestão de usuários", "colaboradores": "Colaboradores",
               "departamentos": "Departamentos", "cargos": "Cargos", "ponto": "Ponto", "ferias": "Férias", "ausencias": "Ausências",
               "documentos": "Documentos", "desligamentos": "Desligamentos"}


# --------------------------------------------------------------------------------------------- números do código
def numeros() -> dict[str, str]:
    api = RAIZ / "xano-workspace/api"
    por_grupo = {}
    for g in sorted(p for p in api.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))):
        por_grupo[g.name] = sum(1 for f in g.rglob("*.xs") if re.search(r"_(GET|POST|PATCH|PUT|DELETE)\.xs$", f.name))
    spec = (RAIZ / "openspec/specs/conectahr/spec.md").read_text(encoding="utf-8")
    ci = (RAIZ / ".github/workflows/validar.yml").read_text(encoding="utf-8")
    passos = re.findall(r"- name: (.+)\n\s+run:", ci)
    linhas = ["| Grupo | Endpoints |", "|---|---:|"]
    for nome, n in sorted(por_grupo.items(), key=lambda x: -x[1]):
        chave = nome.removeprefix("conecta_rh_")
        linhas.append(f"| {NOMES_GRUPO.get(chave, chave)} | {n} |")
    return {
        "telas": str((RAIZ / "frontend/app.py").read_text(encoding="utf-8").count("st.Page(")),
        "endpoints": str(sum(por_grupo.values())),
        "grupos": str(len(por_grupo)),
        "tabelas": str(len(list((RAIZ / "xano-workspace/table").glob("*.xs")))),
        "funcoes": str(len([f for f in (RAIZ / "xano-workspace/function").rglob("*.xs") if not any(x.startswith(".") for x in f.parts)])),
        "requisitos": str(spec.count("\n### Requirement: ")),
        "cenarios": str(spec.count("\n#### Scenario: ")),
        "verificacoes_ci": str(len([p for p in passos if not p.lower().startswith("instalar")])),
        "changes": str(sum(1 for p in (RAIZ / "openspec/changes/archive").iterdir() if p.is_dir() and not p.name.startswith((".", "_")))),
        "tabela_grupos": "\n".join(linhas),
    }


def preencher(texto: str, valores: dict[str, str]) -> str:
    """Troca {{nome}} pelo marcador com o valor e atualiza os marcadores que já existem."""
    def bloco(nome: str, valor: str) -> str:
        return f"<!--n:{nome}-->\n{valor}\n<!--/n-->" if "\n" in valor else f"<!--n:{nome}-->{valor}<!--/n-->"

    def novo(m: re.Match) -> str:
        nome = m.group(1)
        if nome not in valores:
            raise SystemExit(f"Marcador desconhecido: {{{{{nome}}}}}")
        return bloco(nome, valores[nome])

    texto = re.sub(r"\{\{(\w+)\}\}", novo, texto)
    return re.sub(r"<!--n:(\w+)-->.*?<!--/n-->", lambda m: bloco(m.group(1), valores[m.group(1)]), texto, flags=re.S)


# --------------------------------------------------------------------------------------------- Markdown -> HTML
def _mermaid(texto: str) -> str:
    return re.sub(r"```mermaid\n(.*?)```", lambda m: f'\n<pre class="mermaid">{html.escape(m.group(1).strip())}</pre>\n', texto, flags=re.S)


def _recuo(texto: str) -> str:
    """O Markdown do GitHub aceita sub-lista com 2 espaços; o conversor pede 4. Dobra o recuo fora dos blocos de código
    que começam na margem (os de dentro de listas acompanham o item)."""
    saida, em_codigo = [], False
    for linha in texto.splitlines():
        if linha.startswith("```"):
            em_codigo = not em_codigo
        elif not em_codigo and linha.startswith("  "):
            espacos = len(linha) - len(linha.lstrip(" "))
            linha = " " * (espacos * 2) + linha.lstrip(" ")
        saida.append(linha)
    return chr(10).join(saida)


def _link(destino: str, origem: Path) -> str:
    if re.match(r"^(https?:|mailto:|#)", destino):
        return destino
    caminho, _, ancora = destino.partition("#")
    alvo = PurePosixPath((origem.parent / caminho).resolve().relative_to(RAIZ).as_posix())
    if str(alvo) in PAGINA_DE:
        return PAGINA_DE[str(alvo)] + (f"#{ancora}" if ancora else "")
    tipo = "tree" if (RAIZ / alvo).is_dir() else "blob"
    return f"{REPO}/{tipo}/master/{alvo}" + (f"#{ancora}" if ancora else "")


def converter(origem: Path) -> tuple[str, str, str, list[tuple[str, str]]]:
    """(título, subtítulo, corpo HTML, [(id, título)] das seções)."""
    import markdown

    texto = re.sub(r"<!--n:\w+-->\n?(.*?)\n?<!--/n-->", r"\1", origem.read_text(encoding="utf-8"), flags=re.S)
    titulo = re.search(r"^# (.+)$", texto, re.M).group(1).strip()
    texto = re.sub(r"^# .+\n", "", texto, count=1, flags=re.M).lstrip()
    subtitulo, _, texto = texto.partition("\n\n")
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"], extension_configs={"toc": {"toc_depth": "2"}})
    corpo = md.convert(_mermaid(_recuo(texto)))
    secoes = [(t["id"], t["name"]) for t in md.toc_tokens]
    corpo = re.sub(r'href="([^"]+)"', lambda m: f'href="{html.escape(_link(html.unescape(m.group(1)), origem))}"', corpo)
    corpo = corpo.replace("<table>", '<div class="tabela"><table>').replace("</table>", "</table></div>")
    corpo = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" rel="noopener"', corpo)
    return titulo, markdown.markdown(subtitulo), corpo, secoes


# --------------------------------------------------------------------------------------------- páginas
def _cabeca(titulo: str, descricao: str, com_mermaid: bool = False) -> str:
    script_mermaid = f'\n  <script defer src="{MERMAID}"></script>' if com_mermaid else ""
    return f"""<!doctype html>
<html lang="pt-BR" data-tema="claro">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(titulo)}</title>
  <meta name="description" content="{html.escape(descricao)}">
  <link rel="icon" href="assets/logo.svg" type="image/svg+xml">
  <link rel="stylesheet" href="assets/estilo.css">
  <script src="assets/app.js"></script>{script_mermaid}
</head>"""


def _topo(atual: str, com_menu: bool) -> str:
    def item(href: str, rotulo: str, classe: str = "") -> str:
        corrente = ' aria-current="page"' if href == atual else ""
        return f'<a{f" class={chr(34)}{classe}{chr(34)}" if classe else ""} href="{href}"{corrente}>{rotulo}</a>'
    botao_menu = '<button class="botao-icone abrir-menu" id="abrir-menu" type="button" aria-label="Abrir o sumário" aria-expanded="false">☰</button>\n    ' if com_menu else ""
    rotulo = {"index.html": "Documentação", "usuario.html": "Manual do usuário", "tecnica.html": "Documentação técnica"}[atual]
    return f"""  <header class="topo">
    {botao_menu}<a class="marca" href="index.html"><img src="assets/logo.svg" alt=""><span>conecta<b>RH</b><small>{rotulo}</small></span></a>
    <nav aria-label="Principal">
      {item("usuario.html", "Manual do usuário", "texto" if atual == "tecnica.html" else "")}
      {item("tecnica.html", "Documentação técnica", "texto" if atual == "usuario.html" else "")}
      <a class="texto" href="{APP}" rel="noopener">Abrir o app</a>
      <button class="botao-icone" id="alternar-tema" type="button" aria-label="Alternar o tema">☾</button>
    </nav>
  </header>"""


def _rodape(gerado: str) -> str:
    return (f'  <footer class="rodape">ConectaRH · Documentação gerada em {gerado} a partir do repositório '
            f'<a href="{REPO}" rel="noopener">conectahr</a> · Fonte em Markdown: '
            f'<a href="{REPO}/tree/master/docs" rel="noopener">docs/</a></footer>')


def pagina_documento(chave: str, gerado: str) -> str:
    titulo, subtitulo, corpo, secoes = converter(DOCS[chave])
    arquivo = f"{chave}.html"
    sumario = "\n".join(f'        <li><a href="#{html.escape(i)}">{n}</a></li>' for i, n in secoes)
    descricao = re.sub(r"<[^>]+>", "", subtitulo).strip()
    return f"""{_cabeca(f"{titulo} — ConectaRH", descricao, "pre class=\"mermaid\"" in corpo)}
<body>
{_topo(arquivo, True)}
  <div class="pagina">
    <nav class="menu-lateral" aria-label="Sumário">
      <h2>Sumário</h2>
      <ol>
{sumario}
      </ol>
    </nav>
    <main class="conteudo" id="conteudo">
      <h1>{html.escape(titulo)}</h1>
      <div class="subtitulo">{subtitulo}</div>
{corpo}
    </main>
  </div>
{_rodape(gerado)}
</body>
</html>
"""


def pagina_inicial(v: dict[str, str], gerado: str) -> str:
    indicadores = [("4", "perfis de acesso"), (v["telas"], "telas"), (v["endpoints"], "endpoints de API"), (v["tabelas"], "tabelas"),
                   (v["requisitos"], "requisitos na spec"), (v["changes"], "changes entregues")]
    blocos = "\n".join(f'      <div class="indicador"><strong>{n}</strong><span>{r}</span></div>' for n, r in indicadores)
    return f"""{_cabeca("ConectaRH — Documentação", "Documentação do ConectaRH, plataforma de gestão de pessoas: manual do usuário e documentação técnica.")}
<body>
{_topo("index.html", False)}
  <section class="capa">
    <img src="assets/logo.svg" alt="Logotipo do ConectaRH">
    <h1>conecta<b>RH</b></h1>
    <p>Plataforma de gestão de pessoas que centraliza o ciclo de vida do colaborador, da admissão ao desligamento, com autorização por perfil, decisões auditáveis e LGPD desde o desenho.</p>
  </section>
  <main class="inicio">
    <div class="cartoes">
      <a class="cartao" href="usuario.html">
        <div class="icone" aria-hidden="true">📘</div>
        <h2>Manual do usuário</h2>
        <p>Para colaboradores, gestores, RH e administradores: como entrar, o que cada tela faz, as regras explicadas de forma simples e as perguntas frequentes.</p>
      </a>
      <a class="cartao" href="tecnica.html">
        <div class="icone" aria-hidden="true">🛠️</div>
        <h2>Documentação técnica</h2>
        <p>Para quem vai manter, operar ou evoluir o sistema: arquitetura, decisões, dados, API, configuração, entrega, testes e limitações.</p>
      </a>
    </div>
    <div class="indicadores">
{blocos}
    </div>
    <div class="aviso"><p>O app está publicado em <a href="{APP}" rel="noopener">{APP.removeprefix("https://").rstrip("/")}</a>. Trabalho acadêmico, feito em grupo: bases legais, prazos de guarda e regras trabalhistas são referências de estudo, a confirmar com o jurídico de quem for usar o sistema de verdade.</p></div>
  </main>
{_rodape(gerado)}
</body>
</html>
"""


# --------------------------------------------------------------------------------------------- execução
def main() -> int:
    checar = "--checar" in sys.argv
    saida = RAIZ / "_site"
    if "--saida" in sys.argv:
        saida = Path(sys.argv[sys.argv.index("--saida") + 1]).resolve()
    valores = numeros()
    desatualizados = []
    for chave, arquivo in DOCS.items():
        atual = arquivo.read_text(encoding="utf-8")
        novo = preencher(atual, valores)
        if novo != atual:
            desatualizados.append(arquivo.relative_to(RAIZ).as_posix())
            if not checar:
                arquivo.write_text(novo, encoding="utf-8")
    if checar:
        if desatualizados:
            print("Números da documentação desatualizados em:", ", ".join(desatualizados))
            print("Rode `python tools/gerar_site.py` e faça commit dos Markdown atualizados.")
            return 1
        try:
            import markdown  # noqa: F401
        except ImportError:
            print("Números em dia. (O pacote `markdown` não está instalado: a geração do HTML não foi conferida.)")
            return 0
    gerado = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y")
    paginas = {"index.html": pagina_inicial(valores, gerado), "tecnica.html": pagina_documento("tecnica", gerado),
               "usuario.html": pagina_documento("usuario", gerado)}
    if checar:
        print(f"Números em dia e site gerado sem erro ({len(paginas)} páginas).")
        return 0
    if saida.exists():
        shutil.rmtree(saida)
    (saida / "assets/fonts").mkdir(parents=True)
    for nome, conteudo in paginas.items():
        (saida / nome).write_text(conteudo, encoding="utf-8")
    for de, para in ARQUIVOS_ESTATICOS:
        shutil.copyfile(de, saida / para)
    for fonte in FONTES:
        shutil.copyfile(RAIZ / f"frontend/static/fonts/{fonte}.woff2", saida / f"assets/fonts/{fonte}.woff2")
    (saida / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Site gerado em {saida} ({len(paginas)} páginas)." + (f" Números atualizados em: {', '.join(desatualizados)}." if desatualizados else ""))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
