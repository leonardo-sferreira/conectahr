# Design

## Context

Ver proposal.md. O Streamlit não tem player com eventos. O embed do Drive (`/preview`) é um iframe de outro domínio e não avisa nada à página, então não dá para saber quanto a pessoa assistiu. Por isso o vídeo toca num `<video>` HTML5, com o arquivo vindo da API do Drive.

## Decisions

### D1. Vídeo no catálogo

- **`treinamento` ganha três campos:**
  - `video_drive_id`: o id do arquivo, não o link;
  - `video_duracao`: segundos;
  - `video_percentual_minimo`: de 50 a 100, padrão 95.
- **A tela tira o id do link** (`/file/d/ID/` ou `?id=ID`). O backend recusa id com `/`, `?`, `&` ou espaço, e com menos de 10 ou mais de 100 caracteres.
- **A duração vem do Drive, não do navegador.** Ao salvar, o servidor do Streamlit lê `videoMediaMetadata.durationMillis` na API do Drive. Assim a pessoa não consegue dizer que o vídeo é mais curto.
  - Essa leitura também confere se o arquivo está acessível e é um vídeo. O erro vira uma mensagem para o RH: não compartilhado, não é vídeo ou ainda processando.
  - Se o id não mudou na edição, reaproveita a duração gravada.
- **A chave de API fica em `st.secrets["google"]["drive_api_key"]`.**
  - Ela aparece no navegador, porque o `<video>` precisa dela. Por isso fica restrita à Drive API e ao endereço do app no Google Cloud.
  - A chamada do servidor manda o endereço do app no cabeçalho `Referer`, para passar pela mesma restrição.
- **O arquivo fica como "qualquer pessoa com o link", em MP4.** Quem tiver o link do arquivo consegue abrir o vídeo. Para treinamentos internos, isso é aceitável; vídeo com dado pessoal não vai para lá.

### D2. Progresso

`treinamento_progresso` guarda, por pessoa e treinamento (par único):
- `segundos_vistos`: o ponto mais longe assistido sem pular;
- `posicao`: onde a pessoa parou;
- `atualizado_em`.

`meus_treinamentos/{id}/progresso` POST:
- exige o treinamento ativo e com vídeo;
- limita os segundos à duração gravada (recusa o que passar de duração + 2);
- **nunca diminui** o que já foi gravado (voltar no vídeo só muda a posição);
- **plausibilidade:**
  - o primeiro registro tem no máximo 90 segundos;
  - cada aumento cabe em 2 × (agora − última atualização) + 15 segundos. A conta é `atualizado_em + (aumento − 15) / 2 <= now`, com `add_secs_to_timestamp`, porque não há subtração de datas no XanoScript usado no projeto;
  - fora disso, recusa (400) e o valor anterior fica.

### D3. Conclusão pela pessoa

`meus_treinamentos/{id}/concluir` POST:
- exige `segundos_vistos × 100 >= mínimo × duração`, com o progresso gravado, não com o que a tela diz;
- cria a `treinamento_conclusao` com a data de hoje e a validade calculada como no registro do RH (mesmo bloco do gerador: ano e mês, dia limitado a 28);
- instrutor "Vídeo no ConectaRH"; `registrado_por_user_id` é a própria pessoa;
- no mesmo dia, não repete;
- **zera o progresso**, para a renovação no ano seguinte pedir o vídeo de novo;
- é auditado (`concluir_treinamento_video`).

### D4. Player

Componente v2 do Streamlit (`st.components.v2.component`). Ele monta na própria página, sem iframe e com estilos isolados.
- **Não reinicia o vídeo:** quando a tela roda de novo com o mesmo treinamento, o componente só atualiza os números.
- **Conta o avanço normal a partir do ponto já assistido.** Avançar além dele volta para ele; um salto não conta.
- **Velocidade:** até 2x (o seletor de velocidade some, e um valor maior volta para 2x).
- **Envio do progresso:** a cada 25 segundos tocando, ao pausar e ao terminar. O Python grava e mostra o aviso do backend se ele recusar.
- **O cartão do vídeo é um fragmento:** o envio do progresso não recarrega a página inteira.
- **Volta de onde parou:** a posição gravada.
- **Sem a chave configurada:** um aviso no lugar do player.

### D5. Telas

- **Modal do treinamento (RH; Figma 557:1477):**
  - "Vídeo no Google Drive (link, opcional)";
  - com link, "Assistir pelo menos (%)" e a orientação de compartilhamento;
  - o catálogo marca "Com vídeo".
- **"Meus treinamentos" (Figma 557:1383):**
  - no alto, o cartão do vídeo do treinamento mais urgente; com mais de um, a pessoa escolhe qual;
  - "Você assistiu X% do vídeo · Precisa de Y% para concluir";
  - "Concluir treinamento", travado até o mínimo;
  - na lista dos obrigatórios, "· vídeo" no nome.

### D6. YouTube como segunda fonte

O Google Cloud pode parecer cobrado (o console oferece o teste pago), e o usuário pediu uma opção sem ele.
- **O mesmo campo aceita os dois links.** A fonte sai do endereço: `drive.google.com` é Drive; `youtube.com`, `youtu.be` (watch, shorts, embed, live) é YouTube. Um id solto é recusado, porque não diz a fonte.
- **`treinamento.video_fonte`** (`drive` ou `youtube`, padrão `drive`). A coluna `video_drive_id` guarda o id das duas fontes: renomear apagaria a coluna no Xano. O backend exige 11 caracteres no id do YouTube.
- **Player:** IFrame Player API do YouTube, no domínio `youtube-nocookie.com`, dentro do mesmo componente. Ela não tem evento de tempo: o componente lê o tempo 4 vezes por segundo e aplica as mesmas regras (salto volta, até 2x, envios a cada 25 segundos, na pausa e no fim).
- **Duração sem chave:** no modal do RH, o link do YouTube mostra a prévia do vídeo; o player lê a duração e o Python guarda até salvar. Sem a prévia carregada, não salva. Quem lê a duração é a sessão do RH, não a pessoa que assiste.
- **Vídeo "não listado":** não aparece em buscas, mas quem tiver o link assiste, como no Drive. Vídeo privado não toca incorporado.

## Risks

- **A chave de API é visível no navegador.** Mitigação: restrição por API e por endereço; cota do Google; trocar a chave se vazar.
- **O link do arquivo fica aberto a quem tiver o link.** Mitigação: só vídeo de treinamento, sem dado pessoal; o RH pode tirar o compartilhamento depois do ciclo.
- **O Google recebe o IP de quem assiste** (Drive ou YouTube). Ele passa a ser operador (docs/lgpd/operadores.md). No YouTube, o domínio `youtube-nocookie.com` evita cookies de rastreamento até a pessoa dar play.
- **Arquivos grandes no Drive** podem ter limite de banda por dia. Mitigação: vídeos curtos e comprimidos (720p).
