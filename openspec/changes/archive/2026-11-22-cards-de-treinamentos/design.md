# Design

## Context

Ver proposal.md. Pontos do código levantados em 23/10/2026:
- **`treinamento`:** já tem `video_fonte` (`drive` ou `youtube`), `video_drive_id` (o id das duas fontes), `video_duracao` e `video_percentual_minimo`.
- **`treinamento_progresso`:** guarda `segundos_vistos` e `posicao`.
- **`meus_treinamentos/{id}/concluir`:** exige o mínimo do vídeo, grava a conclusão com validade e zera o progresso.
- **`meus_treinamentos` GET:** devolve os obrigatórios da pessoa, as conclusões e os progressos.
- **Arquivos:** ficam no Supabase Storage (change `anexo-de-arquivos`); o Xano do plano não guarda arquivo privado.

## Decisions

### D1. Tipo de conteúdo

- **`treinamento.conteudo_tipo`:** `video`, `pdf` ou `apresentacao`. Na migração, **decisão:** quem já tem `video_drive_id` vira `video`, e os demais também (os campos de vídeo vazios querem dizer "sem conteúdo no sistema", como hoje).
- **Vídeo:** os campos atuais, sem mudança.
- **PDF:** `conteudo_path`, um arquivo no bucket `treinamentos`, ou `conteudo_url`, um link de arquivo do Google Drive, aceito como no vídeo.
- **Apresentação:**
  - um link do Google Slides (`docs.google.com/presentation/d/{id}`), mostrado no `/embed`;
  - ou um link do Drive;
  - ou um PDF exportado no bucket.
- **O backend aceita só esses hosts.** Qualquer outro link é recusado (a mesma regra dos documentos: nada de link genérico).

### D2. Arquivos no Supabase

- **Bucket privado `treinamentos`**, com caminho `{uuid}.{pdf|webp}`. O material é da empresa, não tem dado pessoal, mas não deve ficar público.
- **`treinamentos/arquivos/envio` POST** (RH e Admin): devolve o endereço de envio de uso único, como `documentos/envio_arquivo`.
- **Para abrir:** `meus_treinamentos/{id}/conteudo` GET devolve uma URL assinada de 10 minutos, só se o treinamento está no público da pessoa.

### D3. Capa

- **`treinamento.capa_path`:** opcional. O RH envia uma imagem; o servidor do Streamlit reduz para 640 × 360 em WebP, sem metadados.
- **Sem capa, decisão, nesta ordem:**
  1. miniatura do YouTube (`https://img.youtube.com/vi/{id}/hqdefault.jpg`);
  2. miniatura do Drive (`https://drive.google.com/thumbnail?id={id}&sz=w640`), que só aparece com o arquivo compartilhado;
  3. a ilustração padrão da categoria (`frontend/static/capas/{categoria}.svg`).
- **Se a miniatura externa não carrega**, a tela mostra a ilustração (atributo `onerror` no `<img>`).
- **As miniaturas externas fazem o navegador falar com o Google** (já é operador pela `treinamento-em-video`); não há dado pessoal na requisição.

### D4. Cards

- **`meus_treinamentos` GET devolve uma lista `cards`**, com os treinamentos ativos do público da pessoa:
  - obrigatórios e opcionais;
  - **decisão:** o opcional entra como convite, sem cobrança.
- **Cada card traz:** id, nome, descrição (a tela corta em 3 linhas), categoria, carga horária, `conteudo_tipo`, a capa (a URL assinada ou a pista para a automática), obrigatório ou não, situação e percentual (vídeo).
- **A situação usa a mesma regra de hoje** (`treinamentos_modelo.situacao`): pendente, vencido, vencendo ou em dia, e mais:
  - "em andamento": vídeo com progresso, ou leitura aberta e ainda não concluída;
  - "concluído": em dia, ou opcional concluído.
- **Filtros:**
  - "Pendentes": pendente, vencido ou vencendo;
  - "Em andamento";
  - "Concluídos".
  - Vem aberto o filtro com itens, nesta ordem.
- **Card próprio, desenhado no Figma**, sem o padrão de pílulas:
  - capa 16:9 no alto;
  - selo de situação sobre a capa;
  - título forte;
  - descrição suave;
  - rodapé com o ícone do tipo, a categoria e a carga horária.
- **Grade:** 3 colunas na tela larga, 2 na média e 1 na estreita.
- **O card é um botão:** o clique abre o detalhe.

### D5. Detalhe

- **Abre na mesma página.** **Decisão:** a página troca de modo, guardando `mt_aberto = id` na sessão, em vez de um modal: o player e o PDF precisam de espaço.
- **O detalhe mostra:**
  - "Voltar", que mantém o filtro;
  - a capa pequena, o título, a descrição completa, a situação e a validade;
  - o conteúdo;
  - a ação de concluir.
- **Vídeo:** o player e as regras atuais.
- **PDF:** o visualizador embutido (iframe com a URL assinada, ou o `/preview` do Drive) e "Abrir em nova aba".
- **Apresentação:** o `/embed` do Google Slides, o `/preview` do Drive ou o PDF.

### D6. Conclusão de leitura

- **`meus_treinamentos/{id}/abrir` POST** grava `treinamento_progresso.aberto_em` na primeira vez. A tela chama quando mostra o conteúdo; o "Abrir em nova aba" também chama antes.
- **`meus_treinamentos/{id}/concluir` POST, para PDF e apresentação:**
  - exige `aberto_em` e `confirmo_leitura = true`;
  - grava a conclusão como no vídeo: data de hoje, validade e instrutor "Leitura no ConectaRH";
  - audita `concluir_treinamento_leitura`;
  - zera `aberto_em`, para a renovação pedir a abertura de novo.
- **Para vídeo, continua exigindo o mínimo assistido.**
- **Na tela:** "Concluir treinamento" fica travado até abrir o conteúdo e marcar "Li e compreendi o conteúdo".
- **Non-goal registrado:** não há medição da leitura real.

### D7. Modal do RH

- **"Tipo de conteúdo":** vídeo, leitura (PDF) ou apresentação. Os campos mudam com o tipo:
  - **vídeo:** o link do Drive ou do YouTube, como hoje;
  - **PDF:** enviar o arquivo (até 20 MB) ou colar o link do Drive;
  - **apresentação:** o link do Slides ou do Drive, ou enviar o PDF.
- **"Capa (opcional)":** enviar uma imagem, com a prévia da capa automática quando vazia.
- **O backend valida:**
  - tipo e conteúdo coerentes (vídeo sem `conteudo_*`; PDF ou apresentação sem os campos de vídeo);
  - os hosts aceitos;
  - os caminhos no padrão do bucket.

## Risks

- **Miniatura do Drive** de arquivo sem compartilhamento não carrega. A ilustração da categoria cobre o caso.
- **PDF grande no iframe** pode demorar a abrir. O limite é 20 MB, com "Abrir em nova aba" sempre visível.
