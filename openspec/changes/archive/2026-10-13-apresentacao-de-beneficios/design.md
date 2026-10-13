# Design

## Decisões

### D1. Materiais no Supabase, e não no Google Drive

O usuário perguntou (13/10/2026) se os materiais devem ficar no Google Drive ou no Supabase. Escolha: **Supabase**, pelo fluxo da change `anexo-de-arquivos`.

- Já está configurado e testado: bucket privado, endereço de envio de uso único, link assinado de 5 minutos e auditoria de cada abertura.
- O Drive pediria um dos dois: link público de compartilhamento, que a regra de domínio aprovado recusa (o arquivo fica aberto a quem tiver o link, mesmo depois de desligado); ou uma conta de serviço do Google com OAuth, um segundo operador e mais uma chave para guardar.
- Para o RH, anexar na própria tela é mais simples do que subir no Drive, ajustar o compartilhamento e copiar o link.

Caminho: `beneficios/<uuid>.<extensão>` no bucket `documentos` (mesmos limites: PDF, JPG ou PNG, até 10 MB). O RH dá um nome ao material ("Guia do plano"); o nome do arquivo original não é guardado.

### D2. Quem vê

O material é de leitura geral, sem dado pessoal. O colaborador vê os benefícios **ativos dele** (vínculo vigente) e abre os materiais deles; RH e Admin abrem qualquer material. `beneficio_arquivos/{id}/abrir` confere isso e audita (`abrir_material_beneficio`).

### D3. Links

Até 10 por benefício, cada um com título (2 a 80 caracteres) e endereço `https://`. São links públicos da operadora (site, aplicativo, rede credenciada), por isso não passam pela lista de domínios aprovados, que é dos arquivos com dado pessoal.

### D4. Tela do colaborador

Só o indicador "Benefícios ativos". Cada benefício ativo é um item que abre e fecha, como a FAQ: rótulo com o nome e o tipo; aberto, a operadora, a descrição, os links e os materiais com "Abrir". Sem valores, desconto nem histórico (pedido do usuário).

### D5. Edição pelo RH

"Editar" na linha do Catálogo abre o modal com os dados e os links (um por linha, "Título | https://endereço") e, abaixo, os materiais: lista com "Remover" e "Anexar material" (nome + arquivo). Salvar os dados usa `beneficios/{id}` PATCH, que já avisa quem tem o benefício; anexar e remover são ações próprias, auditadas, sem aviso.
