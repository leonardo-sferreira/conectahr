# Treinamentos em cards, por tipo de conteúdo (change `cards-de-treinamentos`)

**Data:** 21/11/2026. **Figma:** seção 23 (claro `633:1470`, escuro `637:1591`). Prints da tela em
`cards-de-treinamentos/`, tirados de uma prévia sem rede com dados fictícios. A conta mostrada é fictícia.

## O que entrou

| Tarefa | O quê | Verificação |
|---|---|---|
| 1.1 | Figma, nos temas claro e escuro e na tela estreita:<br>• o componente "Card/Treinamento";<br>• a grade;<br>• o detalhe de PDF, de apresentação e de vídeo;<br>• o estado vazio;<br>• o celular;<br>• o modal do RH. | `figma-secao-23-claro.png` e `figma-secao-23-escuro.png`. No escuro, nenhum texto fica abaixo de 3:1. |
| 1.2 | Em `treinamentos_modelo.py`:<br>• `situacao_card`, `cards`, `contagem` e `filtro_inicial`;<br>• `capa` (com a ilustração por categoria) e `mapa_capas`;<br>• `resumo`;<br>• `link_leitura` e `url_embutida`;<br>• `validar_conteudo`, `validar_capa` e `tratar_capa`. | `tools/testar_treinamentos.py`: 85 de 85 verificações passam. |
| 1.3 | "Meus treinamentos" em cards:<br>• filtros com a contagem;<br>• 3, 2 ou 1 coluna conforme a largura;<br>• o card inteiro é um botão ("Abrir: nome");<br>• os estados de carregando, vazio, sucesso, erro, conteúdo indisponível e conta sem ficha. | `testar_treinamentos.py` e Chrome em 1440, 1000 e 390 px. Nenhuma largura rola para o lado. |
| 1.4 | Detalhe:<br>• "Voltar para ‹filtro›" mantém o filtro;<br>• vídeo com o player;<br>• PDF e apresentação embutidos, com "Abrir em nova aba";<br>• "Li e compreendi o conteúdo" libera "Concluir treinamento". | `testar_treinamentos.py` e Chrome (sequência abaixo). |
| 1.5 | Modal do RH:<br>• "Tipo de conteúdo";<br>• PDF enviado (até 20 MB) ou link do Drive ou do Slides;<br>• capa opcional reduzida a 640 × 360 em WebP, com a opção de remover. | `testar_treinamentos.py` e Chrome, com o envio de verdade do arquivo na prévia (sequência abaixo). |
| 2.1–2.5 | Backend publicado no Xano:<br>• campos novos;<br>• `treinamentos/arquivos/envio`;<br>• validações no POST e no PATCH;<br>• `cards` e `capas` em `meus_treinamentos`;<br>• `conteudo`, `abrir` e `concluir` por tipo. | `checar_endpoints.py`: 306 de 306. A paridade com o Xano bate: só a ordem de `params` e `headers` difere. As validações rodaram numa função temporária (17 de 17 casos). |

## No Chrome (prévia sem rede)

- **Grade:**
  - 1440 px: 3 colunas, os cards de uma linha com a mesma altura;
  - 1000 px: 2 colunas;
  - 390 px: 1 coluna.

  Nenhuma largura rola para o lado. O botão transparente cobre o card inteiro.
- **Detalhe:**
  1. Filtro "Em andamento".
  2. Abrir o card do PDF.
  3. "Concluir treinamento" travado.
  4. Marcar "Li e compreendi o conteúdo".
  5. "Concluir" liberado.
  6. "Voltar para Em andamento": a grade volta com o filtro "Em andamento".
- **Modal do RH:**
  1. Novo treinamento, categoria e nome.
  2. "Leitura (PDF)".
  3. Enviar um PDF e uma foto JPG (1600 × 900, com EXIF).
  4. Salvar.

  A prévia registrou, nesta ordem:
  - o pedido de envio do PDF;
  - o `PUT` do PDF, que começa com `%PDF`;
  - o pedido de envio da capa;
  - o `PUT` da capa em `image/webp`, que começa com `RIFF`: a foto foi convertida;
  - o `POST treinamentos`, com `conteudo_tipo: "pdf"`, `conteudo_path` e `capa_path` (`{uuid}.pdf` e `{uuid}.webp`) e os campos de vídeo vazios.

  O modal fechou. O seletor de tipo e o campo de envio têm cores próprias no modal, nos dois temas.
- **Detalhe do PDF no print:** o iframe aparece vazio porque o Chrome headless não tem o leitor de PDF. O PDF real
  do bucket foi conferido à parte (abaixo).

## Bucket `treinamentos` no Supabase (conferido sem login)

Uma função temporária no Xano fez este teste e foi apagada depois:

1. Criou o bucket privado `treinamentos` (resposta 200).
2. Gerou um endereço de envio e subiu um PDF de teste: 200.
3. Pediu a URL assinada à função de produção `assinar_treinamentos`. O `GET` devolveu 200, `Content-Type: application/pdf`, sem `X-Frame-Options` e sem `Content-Disposition`. Por isso o PDF abre dentro da página, e os bytes conferem.
4. A mesma URL sem o token devolveu 400: o bucket é privado.
5. Um envio em `text/html` foi recusado: 415, `invalid_mime_type`.
6. O arquivo de teste foi apagado, e a assinatura dele deixou de sair.

**Defeito achado e corrigido.** O `set` do Xano trata o ponto da chave como caminho, então `"uuid.webp"` virava
`{uuid: {webp: url}}`. Por isso a capa enviada nunca chegaria à tela. Agora `meus_treinamentos` lê cada URL com
`get:caminho`, que percorre o mesmo caminho, e devolve `capas` como uma lista de `{caminho, url}`. O frontend monta o mapa
com `mapa_capas`. As fotos de perfil não têm o problema: lá, quem lê o mapa é o próprio Xano, com `get`.

## Segurança

- **O que vai para o `st.iframe`:** o detalhe só embute endereço `https://`, porque o `st.iframe` trata texto que não é URL como HTML e o executaria. Há teste para isso: `<script>` no lugar da URL não gera iframe nem marca a abertura.
- **Envio de arquivos:**
  - os arquivos sobem direto ao bucket privado, por endereço de uso único; a chave do Supabase fica só no Xano;
  - o caminho é `{uuid}.pdf` ou `{uuid}.webp`, sem nome de pessoa;
  - a capa perde os metadados (EXIF) antes de subir.

## Desvios do design

- **D3 pedia `onerror` no `<img>`, mas o `st.html` remove esse atributo.** No lugar, a capa é um fundo em duas camadas, com a miniatura por cima da ilustração da categoria. Se a miniatura não carrega, a ilustração aparece.
- **Rótulo "Em andamento".** Um treinamento vencido ou vencendo que a pessoa já começou fica em "Em andamento", mas com o selo de vencido ou de vencendo.

## Revisão independente

Uma revisão do diff achou um defeito grave, que foi corrigido antes do commit. O detalhe de um PDF enviado ao bucket quebrava a página: `conteudo` devolve `arquivo: true` e a tela esperava o nome do arquivo. A simulação do teste usava um nome e por isso não pegou; agora usa o formato real.

Também corrigido:
- o endereço do PDF fica o mesmo enquanto o detalhe está aberto, e só é renovado depois de 9 minutos;
- os dados e as capas ficam guardados por 5 minutos na sessão;
- a capa com mais de 40 milhões de pixels é recusada antes de ser decodificada;
- os caminhos de PDF e de capa com `%` são recusados no POST e no PATCH.

Ficam registrados, sem efeito no uso de hoje:
- um PATCH sem `conteudo_tipo` grava vídeo e apaga o PDF e a capa. O modal sempre manda todos os campos;
- um salvar que falha depois do envio, ou a troca do PDF, deixa o arquivo antigo sem uso no bucket. É material sem dado pessoal.

## Testes por HTTP (22/11/2026)

Feitos no Xano real com as contas de teste Admin, RH e Colaborador, pelo mesmo `api_client` da tela: 29 de 29 verificações. Os três treinamentos de teste foram desativados no fim; a conclusão do PDI pela conta Colaborador ficou registrada.

- **3.1, RH:**
  - **passa:**
    - envio do PDF ao bucket, com a capa convertida para WebP;
    - criação do treinamento de PDF (arquivo e capa), da apresentação pelo Slides e do vídeo.
  - **falha:**
    - 400 para um PDF com campos de vídeo, para uma apresentação com link de outro site e para um caminho com `%`;
    - 403 para o Colaborador criar o treinamento ou pedir o envio;
    - 403 também para o Gestor, conferido no teste de metas e PDI da equipe.
- **3.2, cards:**
  - **passa:**
    - a pessoa do público vê os três tipos, cada um com o seu tipo;
    - a capa volta assinada, na lista `{caminho, url}`, e abre em WebP;
    - o PDF assinado abre igual ao enviado e sem forçar download;
    - a apresentação devolve o link do Slides.
  - **falha:** a conta fora do público recebe 404 no conteúdo e no abrir, e não vê o card.
- **3.3, conclusão:**
  - **passa:**
    - o PDF conclui depois de abrir e confirmar, com validade e o instrutor "Leitura no ConectaRH";
    - o `aberto_em` volta a vazio, para a renovação pedir a abertura de novo;
    - o card vai para Concluídos.
  - **falha:**
    - 403 para concluir sem abrir;
    - 403 para concluir aberto, mas sem a confirmação;
    - 403 para o vídeo sem o mínimo assistido.

**Observação de desempenho:** na primeira rodada, um `POST treinamentos` passou dos 10 segundos que o app espera, mas o treinamento foi gravado. Na segunda, as criações levaram 1,1 s e 0,9 s. Uma delas levou 22,7 s porque bateu no limite de chamadas do plano gratuito do Xano, esperou e tentou de novo. Se a lentidão aparecer no uso, a tela mostra "Não foi possível conectar" mesmo com o cadastro feito.
