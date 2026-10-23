"""
Regras da foto de perfil (Figma, seção 25, 571:870; change foto-de-perfil). Sem Streamlit.

A foto é opcional. A tela aceita JPG, PNG ou WebP de até 2 MB. Antes do envio, o servidor do app trata a imagem:
corrige a rotação pelo EXIF, recorta um quadrado centralizado, reduz para 256 × 256 e grava em WebP sem metadados
(nem EXIF, nem GPS). O arquivo que chega ao armazenamento é sempre o tratado. Sem foto, aparecem as iniciais.
"""

import base64
import html
import io

from PIL import Image, ImageOps

TAMANHO_MAXIMO = 2 * 1024 * 1024
LADO = 256
TIPOS = {"image/jpeg", "image/png", "image/webp"}
EXTENSOES = ("jpg", "jpeg", "png", "webp")


def validar_arquivo(nome: str | None, tamanho: int, tipo: str | None) -> str | None:
    extensao = (nome or "").rsplit(".", 1)[-1].lower() if "." in (nome or "") else ""
    if extensao not in EXTENSOES or (tipo and tipo not in TIPOS):
        return "Envie uma foto JPG, PNG ou WebP."
    if tamanho > TAMANHO_MAXIMO:
        return "A foto precisa ter até 2 MB."
    if tamanho <= 0:
        return "O arquivo está vazio."
    return None


def tratar(conteudo: bytes) -> bytes:
    """Imagem quadrada de 256 × 256 em WebP, sem metadados. Levanta ValueError se o arquivo não é uma imagem."""
    try:
        imagem = Image.open(io.BytesIO(conteudo))
        imagem.load()
    except Exception as exc:  # noqa: BLE001 - qualquer falha do Pillow quer dizer "não é uma imagem válida"
        raise ValueError("O arquivo não é uma imagem válida.") from exc
    imagem = ImageOps.exif_transpose(imagem).convert("RGB")
    imagem = ImageOps.fit(imagem, (LADO, LADO), method=Image.Resampling.LANCZOS)
    saida = io.BytesIO()
    imagem.save(saida, format="WEBP", quality=85)  # sem exif=: o arquivo sai sem metadados
    return saida.getvalue()


def iniciais(nome: str | None) -> str:
    partes = [p for p in (nome or "").split() if p[:1].isalpha()]
    if not partes:
        return "?"
    return (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper()


def avatar_html(nome: str | None, foto_url: str | None, tamanho: int = 40, classe: str = "") -> str:
    """Círculo com as iniciais e, por cima, a foto. Se a foto não carregar (URL vencida), as iniciais continuam à
    vista: a imagem tem alt vazio, e o navegador não desenha o ícone de imagem quebrada."""
    foto = f'<img src="{html.escape(foto_url)}" alt="" />' if foto_url else ""
    fonte = max(11, round(tamanho * 0.36))
    return (f'<span class="crh-avatar-foto {classe}" style="width:{tamanho}px;height:{tamanho}px;font-size:{fonte}px">'
            f'<span class="i">{html.escape(iniciais(nome))}</span>{foto}</span>')


def avatar_data_uri(nome: str | None) -> str:
    """O círculo das iniciais como imagem (SVG em data URI), para onde só cabe uma imagem: o rótulo dos cartões do
    organograma, que são botões com Markdown."""
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" rx="32" fill="#16181D"/>'
           '<text x="32" y="40" font-family="Manrope, Arial, sans-serif" font-size="22" font-weight="700" fill="#F5A623" '
           f'text-anchor="middle">{html.escape(iniciais(nome))}</text></svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")
