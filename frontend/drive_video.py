"""
Vídeos dos treinamentos no Google Drive (change treinamento-em-video).

O arquivo fica no Drive da empresa, compartilhado como "qualquer pessoa com o link", em MP4. O navegador da pessoa
toca o vídeo direto da API do Drive (`files/{id}?alt=media`), com a chave de API em `st.secrets["google"]
["drive_api_key"]` (nunca no repositório). A chave aparece no navegador: no Google Cloud, ela fica restrita à Drive
API e ao endereço do app.

- `chave_api()`: a chave, ou None se não estiver configurada.
- `url_video(id, chave)`: o endereço que o player usa.
- `duracao_video(id, chave)`: a duração em segundos, lida do Drive quando o RH salva o treinamento (o backend
  guarda e usa essa, não a que o navegador diz). Erros viram `ErroDrive` com uma mensagem para o RH.
"""

from urllib.parse import quote

import requests
import streamlit as st

_API = "https://www.googleapis.com/drive/v3/files/"


class ErroDrive(Exception):
    pass


def chave_api() -> str | None:
    try:
        chave = st.secrets["google"]["drive_api_key"]
    except Exception:  # sem secrets.toml, sem a seção [google] ou sem a chave
        return None
    return str(chave).strip() or None


def url_video(video_id: str, chave: str) -> str:
    return f"{_API}{quote(video_id, safe='')}?alt=media&supportsAllDrives=true&key={quote(chave, safe='')}"


def _referer() -> str | None:
    # A chave restrita por site recusa chamadas sem o endereço do app; do servidor, ele vai no cabeçalho.
    try:
        return st.context.url
    except Exception:  # fora de um navegador (AppTest)
        return None


def duracao_video(video_id: str, chave: str) -> int:
    headers = {"Referer": ref} if (ref := _referer()) else {}
    try:
        resp = requests.get(f"{_API}{quote(video_id, safe='')}", params={"fields": "mimeType,videoMediaMetadata(durationMillis)",
                                                                           "supportsAllDrives": "true", "key": chave}, headers=headers, timeout=10)
    except requests.RequestException as exc:
        raise ErroDrive("Não foi possível falar com o Google Drive agora. Tente de novo.") from exc
    if resp.status_code == 404:
        raise ErroDrive("O Google Drive não achou o vídeo. Compartilhe o arquivo como \"qualquer pessoa com o link\" e cole o link de novo.")
    if resp.status_code in (400, 401, 403):
        raise ErroDrive("O Google Drive recusou o acesso. Confira se o arquivo está como \"qualquer pessoa com o link\" e se a chave da API está certa.")
    if not resp.ok:
        raise ErroDrive("O Google Drive não respondeu como esperado. Tente de novo.")
    dados = resp.json()
    if not str(dados.get("mimeType") or "").startswith("video/"):
        raise ErroDrive("O arquivo do link não é um vídeo. Use um MP4.")
    milis = (dados.get("videoMediaMetadata") or {}).get("durationMillis")
    if not milis:
        raise ErroDrive("O Google Drive ainda está processando o vídeo. Espere alguns minutos e salve de novo.")
    return max(1, round(int(milis) / 1000))
