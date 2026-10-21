"""
Player do vídeo de treinamento (Figma 557:1383; change treinamento-em-video), um componente v2 do Streamlit.

O vídeo toca direto do Google Drive (`drive_video.url_video`). O JavaScript guarda o ponto mais longe assistido sem
pular: avançar além dele volta para ele, e um salto no tempo não conta. Velocidade até 2x. A cada 25 segundos
tocando, ao pausar e ao terminar, manda {vistos, posicao} para o Python, que grava em `meus_treinamentos/{id}/progresso`
(o backend recusa progresso mais rápido que 2x o tempo real). A barra e o percentual são desenhados aqui, ao vivo.

O componente não fica num iframe: monta na própria página (com estilos isolados) e não é recriado quando a tela
roda de novo com o mesmo treinamento, então o vídeo não para.
"""

import streamlit as st

from theme import AMBAR, BORDA, ESC_BORDA, ESC_TEXTO, ESC_TEXTO_2, GRAFITE, GRAFITE_SECUNDARIO, tema_atual

_CSS = """
.crh-vp { font-family: inherit; color: var(--crh-texto); }
.crh-vp video { width: 100%; aspect-ratio: 16 / 9; background: #16181D; border-radius: 10px; display: block; }
.crh-vp .info { display: flex; justify-content: space-between; gap: 12px; margin-top: 12px; font-size: 13px; }
.crh-vp .info .v { font-weight: 600; }
.crh-vp .info .m { color: var(--crh-meta); }
.crh-vp .barra { height: 6px; border-radius: 3px; background: var(--crh-trilho); margin-top: 6px; overflow: hidden; }
.crh-vp .cheia { height: 100%; width: 0; background: var(--crh-ambar); transition: width .3s; }
.crh-vp .erro { color: #DC2626; font-size: 13px; margin: 8px 0 0; }
"""

_JS = """
export default function (component) {
  const { data, setTriggerValue, parentElement } = component;
  let raiz = parentElement.querySelector('.crh-vp');
  if (raiz && raiz.dataset.chave === String(data.chave)) {
    raiz._atualizar(data);
    return;
  }
  if (raiz) { raiz._parar(); raiz.remove(); }

  raiz = document.createElement('div');
  raiz.className = 'crh-vp';
  raiz.dataset.chave = String(data.chave);
  for (const [nome, cor] of Object.entries(data.cores)) raiz.style.setProperty('--crh-' + nome, cor);
  raiz.innerHTML = '<video controls playsinline preload="metadata" controlslist="nodownload noplaybackrate" disablepictureinpicture></video>'
    + '<div class="info"><span class="v"></span><span class="m"></span></div><div class="barra"><div class="cheia"></div></div>'
    + '<p class="erro" hidden></p>';
  parentElement.appendChild(raiz);

  const video = raiz.querySelector('video');
  const duracao = Number(data.duracao) || 1;
  const minimo = Number(data.minimo) || 95;
  let maxVisto = Number(data.vistos) || 0;
  let ultimo = 0;
  let enviado = Math.floor(maxVisto);
  let ultimoEnvio = Date.now();

  function desenhar() {
    const pct = Math.min(100, Math.floor(maxVisto * 100 / duracao));
    raiz.querySelector('.v').textContent = 'Você assistiu ' + pct + '% do vídeo';
    raiz.querySelector('.m').textContent = pct >= minimo ? 'Pronto: já pode concluir' : 'Precisa de ' + minimo + '% para concluir';
    raiz.querySelector('.cheia').style.width = pct + '%';
  }

  function enviar() {
    const vistos = Math.min(duracao, Math.floor(maxVisto));
    ultimoEnvio = Date.now();
    if (vistos <= enviado && !video.ended) return;
    enviado = vistos;
    setTriggerValue('progresso', { vistos: vistos, posicao: Math.floor(video.currentTime || 0), n: Date.now() });
  }

  video.addEventListener('loadedmetadata', () => {
    const inicio = Math.min(Number(data.posicao) || 0, maxVisto);
    if (inicio > 0 && inicio < video.duration - 2) video.currentTime = inicio;
    ultimo = video.currentTime;
  });
  video.addEventListener('timeupdate', () => {
    const t = video.currentTime;
    // Só conta o avanço normal a partir do ponto já assistido: um salto (seek) não entra.
    if (!video.seeking && !video.paused && t > ultimo && t - ultimo <= 2.5 && ultimo <= maxVisto + 1) maxVisto = Math.max(maxVisto, t);
    ultimo = t;
    desenhar();
    if (!video.paused && Date.now() - ultimoEnvio > 25000) enviar();
  });
  video.addEventListener('seeking', () => {
    if (video.currentTime > maxVisto + 1) video.currentTime = maxVisto;
  });
  video.addEventListener('seeked', () => { ultimo = video.currentTime; });
  video.addEventListener('ratechange', () => { if (video.playbackRate > 2) video.playbackRate = 2; });
  video.addEventListener('pause', enviar);
  video.addEventListener('ended', () => {
    const total = isFinite(video.duration) ? video.duration : duracao;
    if (maxVisto >= total - 3) maxVisto = duracao;
    desenhar();
    enviar();
  });
  video.addEventListener('error', () => {
    const erro = raiz.querySelector('.erro');
    erro.textContent = 'Não foi possível tocar o vídeo. Avise o RH: o arquivo pode não estar compartilhado ou não ser MP4.';
    erro.hidden = false;
  });

  raiz._atualizar = (novo) => {
    // O servidor pode ter gravado menos (recusou um trecho rápido demais); a tela nunca volta atrás sozinha.
    maxVisto = Math.max(maxVisto, Number(novo.vistos) || 0);
    desenhar();
  };
  raiz._parar = () => { try { video.pause(); } catch (e) { } };
  video.src = data.src;
  desenhar();
}
"""



def _cores() -> dict:
    if tema_atual() == "escuro":
        return {"texto": ESC_TEXTO, "meta": ESC_TEXTO_2, "trilho": ESC_BORDA, "ambar": AMBAR}
    return {"texto": GRAFITE, "meta": GRAFITE_SECUNDARIO, "trilho": BORDA, "ambar": AMBAR}


def player_video(chave: str, src: str, duracao: int, minimo: int, vistos: int, posicao: int) -> dict | None:
    """Desenha o player e devolve o último {vistos, posicao, n} mandado pelo navegador (None se ainda não mandou)."""
    # O registro vale por runtime (o AppTest cria um a cada teste); registrar de novo a mesma definição não avisa nada.
    player = st.components.v2.component("crh_video_treinamento", css=_CSS, js=_JS)
    resultado = player(data={"chave": chave, "src": src, "duracao": int(duracao), "minimo": int(minimo), "vistos": int(vistos),
                              "posicao": int(posicao), "cores": _cores()},
                        key=f"crh_vp_{chave}", on_progresso_change=lambda: None)
    return getattr(resultado, "progresso", None)
