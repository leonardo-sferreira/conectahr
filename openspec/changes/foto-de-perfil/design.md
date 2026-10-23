# Design

## Context

Ver proposal.md. Padrão já usado nos documentos (change `anexo-de-arquivos`):
- a tela pede ao Xano um endereço de envio de uso único (`documentos/envio_arquivo`);
- a tela manda o arquivo direto para o bucket privado;
- a tela cadastra o caminho;
- para abrir, o Xano gera uma URL assinada (`object/sign`, `expiresIn: 300`).

A chave do Supabase fica só no ambiente do Xano (`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`).

## Decisions

### D1. Bucket e caminho

- **Bucket privado `fotos-perfil`**, separado de `documentos`: assim a política e a retenção não se misturam com os documentos.
- **Caminho `{uuid}.webp`**, sem nome nem CPF (como o D5 do `anexo-de-arquivos`).
- **`colaborador.foto_path`** (texto opcional) guarda o caminho, nunca uma URL pública.

### D2. Tratamento da imagem

- **A tela aceita** JPG, PNG ou WebP de até 2 MB. Acima disso, ou em outro formato (PDF, por exemplo), recusa com uma mensagem clara antes de enviar.
- **O servidor do Streamlit trata a imagem** com o Pillow, que já vem com o Streamlit:
  - abre a imagem e corrige a rotação pelo EXIF;
  - recorta um quadrado centralizado e reduz para 256 × 256;
  - grava em WebP de qualidade 85 e tira os metadados (EXIF, GPS).
  - **Decisão:** o arquivo que chega ao bucket é sempre o tratado.
- **O backend confere** o caminho (formato `{uuid}.webp`, do bucket certo) e que o objeto existe no Supabase antes de gravar, como `ConectaHR/verificar_arquivo_documento`.

### D3. Endpoints da própria pessoa

- **`minha_foto/envio` POST:** devolve o endereço de envio de uso único para um caminho novo.
- **`minha_foto` POST `{caminho}`:**
  - grava `foto_path`;
  - apaga a foto anterior do bucket;
  - audita `alterar_foto_perfil`, sem o caminho no texto.
- **`minha_foto` DELETE:** anula `foto_path`, apaga o objeto e audita `remover_foto_perfil`.
- **Os três só agem sobre a ficha de quem está logado.** O colaborador é achado pelo token, nunca vem na entrada. Não existe forma de trocar a foto de outra pessoa (403).

### D4. Remoção pelo RH e pelo Admin

- **`colaboradores/{id}/foto` DELETE `{justificativa}`:**
  - só RH e Admin; justificativa de 10 a 500 caracteres;
  - audita `remover_foto_perfil` com a justificativa;
  - avisa a pessoa no sino ("O RH removeu sua foto de perfil: {justificativa}").
- **O RH não envia foto por ninguém.**

### D5. Onde a foto aparece

- **URL assinada de curta duração:** 10 minutos, gerada na leitura. **Decisão:** é mais que os 5 minutos dos documentos, porque a tela de perfil e o organograma ficam abertos mais tempo; mesmo assim, não é um link público permanente.
- **No organograma**, as URLs saem numa chamada só ao Supabase (assinatura em lote, `object/sign/fotos-perfil` com a lista de caminhos), para não fazer uma chamada por pessoa. A lista `colaboradores` ganha só `foto_url`; o `output` explícito continua sem nenhum outro dado pessoal.
- **Em `meu_perfil_colaborador` GET e `auth/me`:** a `foto_url` da própria pessoa.
- **Na tela:** um componente `avatar(nome, foto_url, tamanho)` em `theme.py`; sem URL, mostra as iniciais. O cache de 20 segundos das telas não guarda a URL por mais que a validade dela.

### D6. LGPD

- **A foto é dado pessoal, não sensível:** não há tratamento biométrico, e o uso de reconhecimento facial fica proibido no registro.
- **Base legal:** consentimento implícito pelo envio voluntário. **Decisão:** o envio é opcional; quem não quer aparecer não envia, ou remove a qualquer momento.
- **Quem vê a foto:** só pessoas logadas no sistema (o organograma já é interno).
- **Retenção:** a foto sai do bucket ao remover, e no desligamento entra na anonimização da ficha (o `foto_path` é anulado e o objeto, apagado).
- **Supabase recebe a foto** (operador já listado), na mesma região do bucket `documentos`.

## Risks

- **A URL assinada pode ser copiada** e aberta por 10 minutos. É aceitável para uma foto de perfil; o link expira.
- **Imagem com conteúdo impróprio:** o RH e o Admin removem, com auditoria.
