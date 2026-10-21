"""Testes por HTTP do treinamento em vídeo (change treinamento-em-video), com login de verdade.

Roda no seu terminal: pede e-mail, senha e o código que chega por e-mail. Precisa de uma conta do RH ou do Admin com
ficha de colaborador. Cria um treinamento de teste (opcional, com um id de vídeo fictício: nada toca no Drive) e
um com vídeo do YouTube (desativado logo depois),
confere as validações do vídeo, o progresso (primeiro registro limitado, avanço rápido demais recusado, nunca
diminui), "concluir" recusado antes do mínimo e aceito depois, com o progresso zerado em seguida. No fim, desativa o
treinamento de teste. Fica gravado: os dois treinamentos inativos "TESTE automático" e uma conclusão para a sua ficha.

Uso (na raiz do repositório):
    python tools/testar_treinamento_video_http.py
"""

import sys
import tomllib
from pathlib import Path

from ler_senha import ler_senha
from limite_http import pedir

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
SEGREDOS = tomllib.loads((RAIZ / ".streamlit" / "secrets.toml").read_text(encoding="utf-8"))
BASE = SEGREDOS["xano"]["auth_base_url"].rstrip("/").rsplit("api:", 1)[0]
AUT, COL = "kFmShhlY", "ySciQ2YN"
VIDEO = "TESTEvideoFicticio_0001"
falhas: list[str] = []
total = 0


def conferir(ok, descricao, detalhe=None):
    global total
    total += 1
    print("  ok:" if ok else "  FALHA:", descricao, "" if ok or detalhe is None else f"-> {detalhe}")
    if not ok:
        falhas.append(descricao)


def chamar(metodo, caminho, token=None, corpo=None, grupo=COL):
    r = pedir(metodo, f"{BASE}api:{grupo}/{caminho}", json=corpo, headers={"Authorization": f"Bearer {token}"} if token else {}, timeout=60)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


def treinamento(**extra):
    return dict({"nome": "TESTE automático — vídeo (pode ignorar)", "descricao": None, "categoria": "desenvolvimento", "carga_horas": 0,
                 "validade_meses": 12, "obrigatorio": False, "publico": "todos", "departamento_ids": None, "video_drive_id": VIDEO,
                 "video_duracao": 600, "video_percentual_minimo": 95}, **extra)


print("\nConta para o teste (RH ou Admin, com ficha de colaborador)")
email = input("  e-mail: ").strip()
senha = ler_senha()
st, d = chamar("POST", "auth/login", corpo={"email": email, "password": senha}, grupo=AUT)
if st != 200:
    sys.exit(f"  login recusado ({st}): {d.get('message')}")
codigo = input("  código de acesso (chegou por e-mail): ").strip()
st, d = chamar("POST", "auth/otp/validar", corpo={"email": email, "codigo": codigo, "dispositivo": "teste Treinamento em vídeo"}, grupo=AUT)
if st != 200:
    sys.exit(f"  código recusado ({st}): {d.get('message')}")
tok, usuario = d["token"], d.get("usuario") or {}
if str(usuario.get("perfil") or "").strip().upper() not in ("RH", "ADMIN"):
    sys.exit("  use uma conta do RH ou do Admin (o teste cria um treinamento).")

print("\nSem login")
st, _ = chamar("POST", "meus_treinamentos/1/progresso", corpo={"segundos_vistos": 1, "posicao": 1})
conferir(st == 401, "progresso sem token: 401", st)
st, _ = chamar("POST", "meus_treinamentos/1/concluir", corpo={})
conferir(st == 401, "concluir sem token: 401", st)

print("\nCatálogo: validações do vídeo")
st, d = chamar("POST", "treinamentos", tok, treinamento(video_drive_id="drive.google.com/file/d/abc"))
conferir(st == 400, "id com barra: 400", (st, d.get("message")))
st, d = chamar("POST", "treinamentos", tok, treinamento(video_percentual_minimo=40))
conferir(st == 400, "mínimo abaixo de 50%: 400", (st, d.get("message")))
st, d = chamar("POST", "treinamentos", tok, treinamento(video_duracao=0))
conferir(st == 400, "vídeo sem duração: 400", (st, d.get("message")))
st, d = chamar("POST", "treinamentos", tok, treinamento(video_fonte="youtube", video_drive_id="curtoDemais00"))
conferir(st == 400, "YouTube com id que não tem 11 caracteres: 400", (st, d.get("message")))
st, d = chamar("POST", "treinamentos", tok, treinamento(video_fonte="vimeo"))
conferir(st == 400, "fonte desconhecida: 400", (st, d.get("message")))
st, d = chamar("POST", "treinamentos", tok, treinamento(video_fonte="youtube", video_drive_id="M7lc1UVf-VE"))
yid = (d.get("treinamento") or {}).get("id")
conferir(st == 200 and (d.get("treinamento") or {}).get("video_fonte") == "youtube", "cria com vídeo do YouTube", (st, d.get("message")))
if yid:
    chamar("PATCH", f"treinamentos/{yid}", tok, treinamento(video_fonte="youtube", video_drive_id="M7lc1UVf-VE", ativo=False))
st, d = chamar("POST", "treinamentos", tok, treinamento())
tid = (d.get("treinamento") or {}).get("id")
conferir(st == 200 and tid and d["treinamento"].get("video_drive_id") == VIDEO and d["treinamento"].get("video_duracao") == 600, "cria com vídeo",
         (st, d.get("message")))
if not tid:
    sys.exit("  sem o treinamento de teste, o resto não roda.")

print("\nProgresso")
st, d = chamar("POST", f"meus_treinamentos/{tid}/progresso", tok, {"segundos_vistos": 120, "posicao": 120})
conferir(st == 400, "primeiro registro acima de 90 segundos: 400", (st, d.get("message")))
st, d = chamar("POST", f"meus_treinamentos/{tid}/progresso", tok, {"segundos_vistos": 30, "posicao": 30})
conferir(st == 200 and d.get("segundos_vistos") == 30 and d.get("duracao") == 600, "primeiro registro de 30 segundos", (st, d))
st, d = chamar("POST", f"meus_treinamentos/{tid}/progresso", tok, {"segundos_vistos": 300, "posicao": 300})
conferir(st == 400, "avanço mais rápido que 2x o tempo real: 400", (st, d.get("message")))
st, d = chamar("POST", f"meus_treinamentos/{tid}/progresso", tok, {"segundos_vistos": 40, "posicao": 40})
conferir(st == 200 and d.get("segundos_vistos") == 40, "avanço pequeno (até 15 segundos) aceito", (st, d))
st, d = chamar("POST", f"meus_treinamentos/{tid}/progresso", tok, {"segundos_vistos": 5, "posicao": 5})
conferir(st == 200 and d.get("segundos_vistos") == 40, "nunca diminui (voltou no vídeo)", (st, d))
st, d = chamar("POST", f"meus_treinamentos/{tid}/progresso", tok, {"segundos_vistos": 9999, "posicao": 9999})
conferir(st == 400, "além da duração: 400", (st, d.get("message")))

print("\nConcluir")
st, d = chamar("POST", f"meus_treinamentos/{tid}/concluir", tok, {})
conferir(st == 403, "antes do mínimo (40 de 600 segundos): 403", (st, d.get("message")))
st, d = chamar("PATCH", f"treinamentos/{tid}", tok, treinamento(video_duracao=40, ativo=True))
conferir(st == 200, "RH ajusta a duração para 40 segundos (o progresso de 40 passa a ser 100%)", (st, d.get("message")))
st, d = chamar("POST", f"meus_treinamentos/{tid}/concluir", tok, {})
conferir(st == 200 and d.get("valido_ate"), "conclui com a validade calculada", (st, d))
st, d = chamar("POST", f"meus_treinamentos/{tid}/concluir", tok, {})
conferir(st == 403, "progresso zerado: concluir de novo pede o vídeo", (st, d.get("message")))
st, d = chamar("GET", "meus_treinamentos", tok)
conferir(st == 200 and "progressos" in d and any(c.get("treinamento_id") == tid for c in d.get("conclusoes") or []), "a conclusão aparece no histórico",
         (st, d.get("message")))

print("\nLimpeza")
st, d = chamar("PATCH", f"treinamentos/{tid}", tok, treinamento(video_duracao=40, ativo=False))
conferir(st == 200, "desativa o treinamento de teste", (st, d.get("message")))
st, d = chamar("POST", f"meus_treinamentos/{tid}/progresso", tok, {"segundos_vistos": 1, "posicao": 1})
conferir(st == 404, "treinamento inativo: progresso recusado", (st, d.get("message")))

print(f"\n{total - len(falhas)}/{total} verificações ok.")
sys.exit(1 if falhas else 0)
