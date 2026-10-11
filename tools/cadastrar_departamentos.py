"""Cadastra no banco a lista padrão de departamentos do ConectaRH, pelo endpoint `departamentos` (POST).

Quem roda é uma pessoa do RH ou do Admin, no próprio terminal: o login pede e-mail, senha e o código
enviado por e-mail, então nenhuma credencial fica no script nem no repositório. O script:

  1. entra na conta e lista os departamentos que já existem;
  2. mostra quais da lista padrão faltam (compara sem acento e sem diferenciar maiúsculas, e entende
     apelidos: "TI" já cobre "Tecnologia da Informação");
  3. só cadastra depois da confirmação; o backend recusa nome repetido de qualquer forma;
  4. encerra a sessão no fim.

Não apaga nem altera departamento nenhum.

Uso (na raiz do repositório):
    python tools/cadastrar_departamentos.py            # prévia e confirmação
    python tools/cadastrar_departamentos.py --listar   # só mostra a lista padrão, sem entrar
"""

import getpass
import sys
import time
import tomllib
import unicodedata
from pathlib import Path

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
GRUPO_AUTENTICACAO = "kFmShhlY"
GRUPO_DEPARTAMENTOS = "wcbcMmlw"
# O plano do Xano aceita 10 chamadas a cada 20 segundos: uma pausa entre as chamadas evita o limite.
PAUSA_S = 2.2

# (nome, descrição, apelidos que já contam como o mesmo departamento)
DEPARTAMENTOS = [
    ("Diretoria", "Direção geral, estratégia e decisões da empresa.", ["Diretoria Executiva", "Direção", "Administração"]),
    ("Recursos Humanos", "Admissão, folha, benefícios, férias, ponto e desenvolvimento das pessoas.", ["RH", "Gente e Gestão", "Pessoas"]),
    ("Financeiro", "Contas a pagar e a receber, tesouraria e planejamento financeiro.", ["Finanças"]),
    ("Contabilidade e Fiscal", "Escrituração contábil, apuração de impostos e obrigações fiscais.", ["Contabilidade", "Fiscal"]),
    ("Tecnologia da Informação", "Sistemas, infraestrutura, suporte e segurança da informação.", ["TI", "Tecnologia"]),
    ("Comercial", "Vendas, relacionamento com clientes e prospecção.", ["Vendas"]),
    ("Marketing", "Comunicação, marca, campanhas e conteúdo.", ["Comunicação", "Marketing e Comunicação"]),
    ("Operações", "Execução dos serviços e da produção do dia a dia.", ["Produção", "Operacional"]),
    ("Logística e Suprimentos", "Compras, estoque, transporte e relação com fornecedores.", ["Logística", "Compras", "Suprimentos"]),
    ("Atendimento ao Cliente", "Suporte, pós-venda e central de relacionamento.", ["Atendimento", "SAC", "Suporte ao Cliente"]),
    ("Jurídico", "Contratos, consultoria jurídica e conformidade legal (inclui LGPD).", ["Juridico", "Compliance"]),
    ("Qualidade", "Processos, indicadores de qualidade e melhoria contínua.", ["Gestão da Qualidade"]),
    ("Segurança do Trabalho", "Saúde e segurança ocupacional (SST), EPIs e prevenção de acidentes.", ["SST", "Saúde e Segurança do Trabalho"]),
    ("Serviços Gerais", "Manutenção predial, limpeza, recepção e facilities.", ["Facilities", "Manutenção"]),
]


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return " ".join(sem_acento.casefold().split())


def faltantes(existentes: list[str]) -> list[tuple[str, str]]:
    """Os departamentos da lista padrão que ainda não existem, nem com outro nome conhecido."""
    ja = {normalizar(n) for n in existentes}
    return [(nome, desc) for nome, desc, apelidos in DEPARTAMENTOS if not ({normalizar(nome)} | {normalizar(a) for a in apelidos}) & ja]


def _base(canonical: str) -> str:
    arquivo = RAIZ / ".streamlit" / "secrets.toml"
    try:
        base = tomllib.loads(arquivo.read_text(encoding="utf-8"))["xano"]["auth_base_url"].rstrip("/")
    except (FileNotFoundError, KeyError) as exc:
        raise SystemExit(f"Configuração ausente: {arquivo} precisa de [xano] auth_base_url.") from exc
    return base.rsplit("api:", 1)[0] + f"api:{canonical}"


def _chamar(metodo: str, canonical: str, caminho: str, token: str | None = None, corpo: dict | None = None) -> dict:
    time.sleep(PAUSA_S)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = requests.request(metodo, f"{_base(canonical)}/{caminho}", json=corpo, headers=headers, timeout=15)
    try:
        dados = resp.json()
    except ValueError:
        dados = {}
    if not resp.ok:
        mensagem = (dados.get("message") if isinstance(dados, dict) else None) or f"HTTP {resp.status_code}"
        raise RuntimeError(mensagem)
    return dados if isinstance(dados, dict) else {}


def entrar() -> str:
    email = input("E-mail (conta RH ou Admin): ").strip()
    senha = getpass.getpass("Senha (não aparece na tela): ")
    _chamar("POST", GRUPO_AUTENTICACAO, "auth/login", corpo={"email": email, "password": senha})
    codigo = input("Código de 6 dígitos enviado por e-mail: ").strip()
    resposta = _chamar("POST", GRUPO_AUTENTICACAO, "auth/otp/validar", corpo={"email": email, "codigo": codigo, "dispositivo": "Script cadastrar_departamentos"})
    if resposta.get("senha_primeiro_acesso"):
        raise SystemExit("Esta conta ainda usa a senha temporária. Entre pelo app e troque a senha antes.")
    return resposta["token"]


def main() -> None:
    if "--listar" in sys.argv:
        for nome, desc, _ in DEPARTAMENTOS:
            print(f"- {nome}: {desc}")
        return
    token = entrar()
    try:
        existentes = [d.get("nome") or "" for d in _chamar("GET", GRUPO_DEPARTAMENTOS, "listar_departamentos", token).get("departamentos") or []]
        print(f"\nJá existem {len(existentes)} departamento(s): {', '.join(sorted(existentes)) or '(nenhum)'}")
        novos = faltantes(existentes)
        if not novos:
            print("Nada a cadastrar: a lista padrão já está toda no banco.")
            return
        print(f"\nSerão cadastrados {len(novos)}:")
        for nome, desc in novos:
            print(f"  + {nome} — {desc}")
        if input("\nCadastrar agora? Digite SIM para confirmar: ").strip().upper() != "SIM":
            print("Nada foi cadastrado.")
            return
        criados = 0
        for nome, desc in novos:
            try:
                _chamar("POST", GRUPO_DEPARTAMENTOS, "departamentos", token, {"nome": nome, "descricao": desc, "ativo": True})
                criados += 1
                print(f"  ok: {nome}")
            except RuntimeError as erro:
                print(f"  não cadastrado: {nome} ({erro})")
        print(f"\n{criados} de {len(novos)} cadastrado(s).")
    finally:
        try:
            _chamar("POST", GRUPO_AUTENTICACAO, "auth/logout", token)
        except RuntimeError:
            pass


if __name__ == "__main__":
    main()
