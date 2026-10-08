"""Confere se todo endpoint autenticado do Xano tem a guarda de acesso obrigatoria.

Checklist (ver xano-workspace/AGENTS.md e o design.md da change
corrigir-brechas-e-alinhar-documentacao, decisoes D1 e D2):

1. carrega o usuario com `db.get user` pelo `$auth.id`;
2. `precondition ($usuario.ativo)`;
3. `precondition ($usuario.senha_primeiro_acesso == false)`, exceto nas rotas de
   troca de senha, `auth/me`, logout e sessoes;
4. valida a sessao do token (`db.get sessao` pelo `$auth.extras.sessao_id` e
   `precondition` sobre a sessao).

As guardas precisam aparecer antes da primeira escrita no banco.

Uso:
    python tools/checar_endpoints.py               # checa tudo
    python tools/checar_endpoints.py --sem-sessao  # ignora o item 4
    python tools/checar_endpoints.py --grupo conecta_rh_ponto

Sai com codigo 1 quando algum endpoint falha.
"""

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_API = RAIZ / "xano-workspace" / "api"

# Rotas liberadas para quem ainda tem senha temporaria (spec: "Guarda de acesso
# em todo endpoint autenticado").
EXCECOES_PRIMEIRO_ACESSO = {
    ("auth/senha", "PATCH"),
    ("auth/me", "GET"),
    ("auth/logout", "POST"),
    ("auth/minhas_sessoes", "GET"),
    ("auth/sessoes/{id}/encerrar", "POST"),
    ("auth/sessoes/encerrar_outras", "POST"),
}

RE_QUERY = re.compile(r'query\s+"?([^"\s]+)"?\s+verb=(\w+)')
RE_AUTH = re.compile(r'^\s*auth\s*=\s*"user"', re.MULTILINE)
RE_GET_USER = re.compile(
    r"db\.get\s+user\s*\{[^}]*?field_value\s*=\s*\$auth\.id[^}]*\}\s*as\s+\$(\w+)",
    re.DOTALL,
)
RE_GET_SESSAO = re.compile(
    r"db\.get\s+sessao\s*\{[^}]*?field_value\s*=\s*\$auth\.extras\.sessao_id[^}]*\}\s*as\s+\$(\w+)",
    re.DOTALL,
)
RE_ESCRITA = re.compile(r"\bdb\.(add|edit|patch|del|add_or_edit|bulk\.\w+)\b")


def _precondition(var, condicao):
    return re.compile(r"precondition\s*\(\s*\$" + var + r"\." + condicao + r"\s*\)")


RE_COMENTARIO = re.compile(r"(?m)(^|\s)//[^\n]*")


def checar_arquivo(caminho, checar_sessao):
    # Comentarios nao contam: um cabecalho que cita "db.add auditoria" nao e uma
    # escrita. O `\s` antes de `//` preserva URLs como "https://..." em strings.
    texto = RE_COMENTARIO.sub(r"\1", caminho.read_text(encoding="utf-8"))
    query = RE_QUERY.search(texto)
    if not query or not RE_AUTH.search(texto):
        return None  # definicao de grupo ou endpoint publico

    rota, verbo = query.group(1), query.group(2).upper()
    problemas = []
    primeira_escrita = RE_ESCRITA.search(texto)
    limite = primeira_escrita.start() if primeira_escrita else len(texto)

    def presente_antes_da_escrita(regex):
        achado = regex.search(texto)
        return achado is not None and achado.start() < limite

    get_user = RE_GET_USER.search(texto)
    if not get_user:
        problemas.append("nao carrega o usuario pelo $auth.id")
    else:
        var = get_user.group(1)
        if not presente_antes_da_escrita(_precondition(var, r"ativo(\s*==\s*true)?")):
            problemas.append("sem precondition de usuario ativo")
        if (rota, verbo) not in EXCECOES_PRIMEIRO_ACESSO and not presente_antes_da_escrita(
            _precondition(var, r"senha_primeiro_acesso\s*==\s*false")
        ):
            problemas.append("sem precondition de senha_primeiro_acesso == false")

    if checar_sessao:
        get_sessao = RE_GET_SESSAO.search(texto)
        if not get_sessao or get_sessao.start() >= limite:
            problemas.append("nao carrega a sessao pelo $auth.extras.sessao_id")
        elif not presente_antes_da_escrita(_precondition(get_sessao.group(1), r"ativa(\s*==\s*true)?[^)]*")):
            problemas.append("sem precondition de sessao ativa")

    return f"{verbo} {rota}", problemas


RE_SWAGGER = re.compile(r"swagger\s*=\s*\{([^}]*)\}")


def checar_swagger(pastas):
    """Grupos de API com swagger ligado ou com token no arquivo.

    O repositorio e publico: o swagger deve ficar desligado (`active: false`) e
    nenhum token pode ser commitado. Um `xano workspace pull` reescreve os
    arquivos de grupo com o token que esta no Xano; descarte essa linha antes
    do commit (git checkout no arquivo de grupo)."""
    problemas = []
    for pasta in pastas:
        for caminho in sorted(pasta.rglob("conecta_rh_*.xs")):
            texto = caminho.read_text(encoding="utf-8")
            if "api_group" not in texto:
                continue
            achado = RE_SWAGGER.search(texto)
            if not achado:
                problemas.append((caminho.relative_to(RAIZ), "sem `swagger = {active: false}` (o Xano deixa a documentacao aberta)"))
            elif "active: false" not in achado.group(1):
                problemas.append((caminho.relative_to(RAIZ), "swagger ligado"))
            elif "token" in achado.group(1):
                problemas.append((caminho.relative_to(RAIZ), "token de swagger no arquivo (repositorio publico: nao commitar)"))
    return problemas


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sem-sessao", action="store_true", help="nao exige a validacao de sessao")
    parser.add_argument("--grupo", action="append", help="pasta de grupo em xano-workspace/api (repetivel)")
    args = parser.parse_args()

    pastas = [PASTA_API / g for g in args.grupo] if args.grupo else [PASTA_API]
    autenticados = 0
    falhas = []
    for pasta in pastas:
        for caminho in sorted(pasta.rglob("*.xs")):
            resultado = checar_arquivo(caminho, not args.sem_sessao)
            if resultado is None:
                continue
            autenticados += 1
            endpoint, problemas = resultado
            if problemas:
                falhas.append((caminho.relative_to(RAIZ), endpoint, problemas))

    for caminho, endpoint, problemas in falhas:
        print(f"{caminho}  [{endpoint}]")
        for problema in problemas:
            print(f"    - {problema}")

    problemas_swagger = checar_swagger(pastas)
    for caminho, motivo in problemas_swagger:
        print(f"{caminho}  [grupo de API]\n    - {motivo}")

    print(f"\n{autenticados} endpoints autenticados, {len(falhas)} com falha; {len(problemas_swagger)} grupo(s) com problema de swagger.")
    return 1 if (falhas or problemas_swagger) else 0


if __name__ == "__main__":
    sys.exit(main())
