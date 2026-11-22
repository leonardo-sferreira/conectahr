# Proposal

## Why

Mapeamento de Leonardo (23/10/2026). "Meus treinamentos" foi pensado para vídeo (change `treinamento-em-video`): a pessoa escolhe o treinamento numa lista e vê o player. Treinamentos só de leitura (PDF) ou de apresentação (slides) não ficam bem representados. A tela também não diferencia os tipos nem mostra uma prévia do conteúdo.

## What Changes

- **Cards em grade** (D4), cada um com:
  - a capa;
  - o nome e a descrição cortada em 2 a 3 linhas;
  - o tipo (vídeo, leitura em PDF ou apresentação), a categoria e a carga horária;
  - a situação: pendente, em andamento com %, concluído, vencendo, vencido ou obrigatório.
  - Filtro por "Pendentes", "Em andamento" e "Concluídos".
- **Treinamento expandido** (D5): clicar no card abre o detalhe, com o conteúdo completo e "Concluir treinamento". Voltar mantém o filtro.
- **Conteúdo por tipo** (D1, D2):
  - **vídeo:** o player atual, com as mesmas regras;
  - **PDF:** o arquivo no Supabase ou um link do Drive;
  - **apresentação:** Google Slides ou Drive, ou o PDF exportado.
- **Capa** (D3): a imagem enviada pelo RH ou, sem ela, uma automática: a miniatura do YouTube ou do Drive, ou a ilustração da categoria.
- **Conclusão de leitura** (D6): liberada depois que a pessoa abre o conteúdo e confirma "Li e compreendi o conteúdo". A conclusão é gravada como no vídeo, com validade e auditoria.
- **Modal do RH** (D7): escolher o tipo de conteúdo e enviar a capa e o arquivo ou o link.

## Non-goals

- **Medir a leitura real** (rolagem, tempo por página): não há como saber se a pessoa leu. A confirmação é declaratória e fica registrada.
- **Questionário ou prova depois do conteúdo.**
- **Editor de apresentação dentro do ConectaRH.**
- **Converter arquivos** (PPTX para PDF): o RH exporta antes de enviar.

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: treinamentos de vídeo, PDF e apresentação, em cards com capa, detalhe e conclusão por tipo.

## Impact

- **Backend:**
  - campos `treinamento.conteudo_tipo`, `conteudo_url`, `conteudo_path` e `capa_path`;
  - campo `treinamento_progresso.aberto_em`;
  - endpoints novos: `treinamentos/arquivos/envio` POST, `meus_treinamentos/{id}/abrir` POST e `meus_treinamentos/{id}/conteudo` GET;
  - alterados: `treinamentos` POST, `treinamentos/{id}` PATCH, `meus_treinamentos` GET e `meus_treinamentos/{id}/concluir` POST.
- **Supabase:** o bucket privado `treinamentos`, para capas e arquivos.
- **Frontend:**
  - `treinamentos_modelo.py`;
  - `pagina_meus_treinamentos.py` (os cards e o detalhe);
  - `pagina_treinamentos.py` (o modal);
  - `video_player.py` (sem mudança de regra);
  - `theme.py` (o card);
  - as ilustrações por categoria em `frontend/static`.
- **Figma:** novas telas:
  - "Meus treinamentos — cards", com o estado vazio;
  - "Treinamento expandido" (vídeo, PDF e apresentação);
  - o modal do RH com o tipo de conteúdo.
  - Nos temas claro e escuro, e numa coluna em tela estreita.
- **Testes:** `tools/testar_treinamentos.py` e o novo `tools/testar_cards_treinamentos_http.py`.
- **Documentação:**
  - `docs/regras-de-negocio.md` (seção 21);
  - `docs/lgpd/operadores.md` (Supabase também guarda o material de treinamento, sem dado pessoal).
- **Continua** a change `treinamento-em-video`, ainda aberta (tarefa 2.4).
