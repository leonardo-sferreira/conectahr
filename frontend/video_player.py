"""
Player do vídeo de treinamento (Figma 557:1383; change treinamento-em-video), um componente v2 do Streamlit.

Duas fontes, o mesmo controle:
- Google Drive: `<video>` HTML5 com o arquivo direto da API do Drive (`drive_video.url_video`);
- YouTube: o player oficial (IFrame Player API, no domínio youtube-nocookie.com), com o vídeo "não listado".

O JavaScript guarda o ponto mais longe assistido sem pular: avançar além dele volta para ele, e um salto no tempo não
conta. Velocidade até 2x. A cada 25 segundos tocando, ao pausar e ao terminar, manda {vistos, posicao} para o Python,
que grava em `meus_treinamentos/{id}/progresso` (o backend recusa progresso mais rápido que 2x o tempo real). A barra e
o percentual são desenhados aqui, ao vivo.

O componente não fica num iframe: monta na própria página (com estilos isolados) e não é recriado quando a tela roda
de novo com o mesmo treinamento, então o vídeo não para.

`previa_youtube` (modal do RH): o mesmo player, só para conferir o vídeo e ler a duração, que o backend guarda.
"""

import streamlit as st

from theme import AMBAR, BORDA, ESC_BORDA, ESC_TEXTO, ESC_TEXTO_2, GRAFITE, GRAFITE_SECUNDARIO, tema_atual

_CSS = """
.crh-vp { font-family: inherit; color: var(--crh-texto); }
.crh-vp video, .crh-vp .yt { width: 100%; aspect-ratio: 16 / 9; background: #16181D; border-radius: 10px; display: block; overflow: hidden; }
.crh-vp .yt iframe { width: 100%; height: 100%; border: 0; display: block; }
.crh-vp .info { display: flex; justify-content: space-between; gap: 12px; margin-top: 12px; font-size: 13px; }
.crh-vp .info .v { font-weight: 600; }
.crh-vp .info .m { color: var(--crh-meta); }
.crh-vp .barra { height: 6px; border-radius: 3px; background: var(--crh-trilho); margin-top: 6px; overflow: hidden; }
.crh-vp .cheia { height: 100%; width: 0; background: var(--crh-ambar); transition: width .3s; }
.crh-vp .erro { color: #DC2626; font-size: 13px; margin: 8px 0 0; }
"""

_JS = """
// Carrega a IFrame Player API do YouTube uma vez por página.
function apiYouTube() {
  if (window.YT && window.YT.Player) return Promise.resolve(window.YT);
  if (!window.__crhYT) {
    window.__crhYT = new Promise((resolve) => {
      const anterior = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => { if (anterior) anterior(); resolve(window.YT); };
      const s = document.createElement('script');
      s.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(s);
    });
  }
  return window.__crhYT;
}

function playerYouTube(alvo, videoId, inicio, eventos) {
  return apiYouTube().then((YT) => new YT.Player(alvo, {
    host: 'https://www.youtube-nocookie.com',
    videoId: videoId,
    playerVars: { rel: 0, playsinline: 1, modestbranding: 1, start: Math.floor(inicio || 0) },
    events: eventos,
  }));
}

export default function (component) {
  const { data, setTriggerValue, parentElement } = component;
  let raiz = parentElement.querySelector('.crh-vp');
  if (raiz && raiz.dataset.chave === String(data.chave)) {
    if (raiz._atualizar) raiz._atualizar(data);
    return;
  }
  if (raiz) { raiz._parar(); raiz.remove(); }

  raiz = document.createElement('div');
  raiz.className = 'crh-vp';
  raiz.dataset.chave = String(data.chave);
  for (const [nome, cor] of Object.entries(data.cores)) raiz.style.setProperty('--crh-' + nome, cor);
  parentElement.appendChild(raiz);
  const youtube = data.fonte === 'youtube';
  raiz._parar = () => { };

  function mostrarErro(texto) {
    const erro = raiz.querySelector('.erro');
    erro.textContent = texto;
    erro.hidden = false;
  }

  // Prévia do RH: só o player e a duração.
  if (data.modo === 'previa') {
    raiz.innerHTML = '<div class="yt"><div></div></div><p class="erro" hidden></p>';
    let enviou = false;
    let espera = null;
    const pronto = (ev) => {
      espera = setInterval(() => {
        const d = ev.target.getDuration();
        if (d > 0 && !enviou) { enviou = true; clearInterval(espera); setTriggerValue('duracao', Math.round(d)); }
      }, 300);
    };
    playerYouTube(raiz.querySelector('.yt > div'), data.video_id, 0, {
      onReady: pronto,
      onError: () => mostrarErro('O YouTube não abriu este vídeo. Confira o link e se ele está como "não listado" (não privado) e com incorporação permitida.'),
    }).then((p) => { raiz._parar = () => { clearInterval(espera); try { p.pauseVideo(); } catch (e) { } }; });
    return;
  }

  raiz.innerHTML = (youtube ? '<div class="yt"><div></div></div>'
    : '<video controls playsinline preload="metadata" controlslist="nodownload noplaybackrate" disablepictureinpicture></video>')
    + '<div class="info"><span class="v"></span><span class="m"></span></div><div class="barra"><div class="cheia"></div></div>'
    + '<p class="erro" hidden></p>';

  const duracao = Number(data.duracao) || 1;
  const minimo = Number(data.minimo) || 95;
  let maxVisto = Number(data.vistos) || 0;
  let ultimo = 0;
  let enviado = Math.floor(maxVisto);
  let ultimoEnvio = Date.now();
  let posicaoAtual = 0;

  function desenhar() {
    const pct = Math.min(100, Math.floor(maxVisto * 100 / duracao));
    raiz.querySelector('.v').textContent = 'Você assistiu ' + pct + '% do vídeo';
    raiz.querySelector('.m').textContent = pct >= minimo ? 'Pronto: já pode concluir' : 'Precisa de ' + minimo + '% para concluir';
    raiz.querySelector('.cheia').style.width = pct + '%';
  }

  function enviar(terminou) {
    const vistos = Math.min(duracao, Math.floor(maxVisto));
    ultimoEnvio = Date.now();
    if (vistos <= enviado && !terminou) return;
    enviado = vistos;
    setTriggerValue('progresso', { vistos: vistos, posicao: Math.floor(posicaoAtual || 0), n: Date.now() });
  }

  // Um passo do tempo tocando: só conta o avanço normal a partir do ponto já assistido.
  function avancou(t, tocando) {
    if (tocando && t > ultimo && t - ultimo <= 2.5 && ultimo <= maxVisto + 1) maxVisto = Math.max(maxVisto, t);
    ultimo = t;
    posicaoAtual = t;
    desenhar();
    if (tocando && Date.now() - ultimoEnvio > 25000) enviar(false);
  }

  function terminou(total) {
    if (maxVisto >= total - 3) maxVisto = duracao;
    desenhar();
    enviar(true);
  }

  const inicio = Math.min(Number(data.posicao) || 0, maxVisto);
  const erroVideo = 'Não foi possível tocar o vídeo. Avise o RH: o link pode não estar compartilhado ou o formato não é aceito.';

  if (youtube) {
    let relogio = null;
    playerYouTube(raiz.querySelector('.yt > div'), data.video_id, inicio > 0 && inicio < duracao - 2 ? inicio : 0, {
      onReady: (ev) => {
        const p = ev.target;
        ultimo = p.getCurrentTime() || 0;
        // A API do YouTube não tem evento de tempo: confere 4 vezes por segundo.
        relogio = setInterval(() => {
          if (p.getPlayerState() !== 1) return;
          const t = p.getCurrentTime();
          if (t > maxVisto + 2) { p.seekTo(maxVisto, true); ultimo = maxVisto; return; }
          avancou(t, true);
        }, 250);
      },
      onStateChange: (ev) => {
        if (ev.data === 2) { posicaoAtual = ev.target.getCurrentTime(); enviar(false); }
        if (ev.data === 0) terminou(ev.target.getDuration() || duracao);
      },
      onPlaybackRateChange: (ev) => { if (ev.data > 2) ev.target.setPlaybackRate(2); },
      onError: () => mostrarErro(erroVideo),
    }).then((p) => { raiz._yt = p; raiz._parar = () => { clearInterval(relogio); try { p.pauseVideo(); } catch (e) { } }; });
  } else {
    const video = raiz.querySelector('video');
    video.addEventListener('loadedmetadata', () => {
      if (inicio > 0 && inicio < video.duration - 2) video.currentTime = inicio;
      ultimo = video.currentTime;
    });
    video.addEventListener('timeupdate', () => avancou(video.currentTime, !video.seeking && !video.paused));
    video.addEventListener('seeking', () => { if (video.currentTime > maxVisto + 1) video.currentTime = maxVisto; });
    video.addEventListener('seeked', () => { ultimo = video.currentTime; });
    video.addEventListener('ratechange', () => { if (video.playbackRate > 2) video.playbackRate = 2; });
    video.addEventListener('pause', () => { posicaoAtual = video.currentTime; if (!video.ended) enviar(false); });
    video.addEventListener('ended', () => terminou(isFinite(video.duration) ? video.duration : duracao));
    video.addEventListener('error', () => mostrarErro(erroVideo));
    raiz._parar = () => { try { video.pause(); } catch (e) { } };
    video.src = data.src;
  }

  raiz._atualizar = (novo) => {
    // O servidor pode ter gravado menos (recusou um trecho rápido demais); a tela nunca volta atrás sozinha.
    maxVisto = Math.max(maxVisto, Number(novo.vistos) || 0);
    desenhar();
  };
  desenhar();
}
"""


def _cores() -> dict:
    if tema_atual() == "escuro":
        return {"texto": ESC_TEXTO, "meta": ESC_TEXTO_2, "trilho": ESC_BORDA, "ambar": AMBAR}
    return {"texto": GRAFITE, "meta": GRAFITE_SECUNDARIO, "trilho": BORDA, "ambar": AMBAR}


def _componente():
    # O registro vale por runtime (o AppTest cria um a cada teste); registrar de novo a mesma definição não avisa nada.
    return st.components.v2.component("crh_video_treinamento", css=_CSS, js=_JS)


def player_video(chave: str, fonte: str, video_id: str, src: str | None, duracao: int, minimo: int, vistos: int, posicao: int) -> dict | None:
    """Desenha o player e devolve o último {vistos, posicao, n} mandado pelo navegador (None se ainda não mandou).
    `src` só para o Drive (o endereço com a chave); o YouTube usa o `video_id`."""
    resultado = _componente()(data={"chave": chave, "fonte": fonte, "video_id": video_id, "src": src, "duracao": int(duracao), "minimo": int(minimo),
                                    "vistos": int(vistos), "posicao": int(posicao), "cores": _cores()},
                              key=f"crh_vp_{chave}", on_progresso_change=lambda: None)
    return getattr(resultado, "progresso", None)


def previa_youtube(video_id: str) -> int | None:
    """Prévia do vídeo do YouTube no modal do RH; devolve a duração em segundos quando o player carrega."""
    resultado = _componente()(data={"chave": f"previa_{video_id}", "modo": "previa", "fonte": "youtube", "video_id": video_id, "cores": _cores()},
                              key=f"crh_vp_previa_{video_id}", on_duracao_change=lambda: None)
    duracao = getattr(resultado, "duracao", None)
    return int(duracao) if duracao else None
