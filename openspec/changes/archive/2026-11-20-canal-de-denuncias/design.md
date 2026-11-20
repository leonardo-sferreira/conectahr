# Design

## Context

Ver proposal.md. O anonimato é o ponto central: se a empresa conseguir descobrir quem denunciou, o canal não serve. Por isso o desenho evita qualquer dado que permita cruzar a denúncia com uma conta. Isso vale também para o horário, que poderia ser comparado com os registros de sessão e de auditoria.

## Decisions

### D1. Dados sem rastro

- `denuncia` não tem conta, colaborador, `created_at` nem horário: só `recebida_em` (a data). Quem quer se identificar digita o nome e o contato em `identificacao`.
- **O código de acompanhamento:**
  - tem 16 sinais, sorteados de um alfabeto de 30 sem sinais parecidos (78 bits);
  - o banco guarda só o HMAC-SHA256 (chave: o segredo do ambiente `CODIGO_ACESSO_PEPPER` e o sufixo `:denuncia`), com índice único;
  - o texto do código existe só na resposta do envio.
- `denuncia_mensagem` guarda o lado (`denunciante` ou `comissao`), o texto e a data. Quem da comissão escreveu fica só na auditoria.
- O protocolo (`DEN-<id>`) identifica a denúncia na fila. Não dá acesso a nada: quem acompanha precisa do código.

### D2. Comissão de ética

`comissao_etica` (`user_id` único, `ativo`):
- só membros ativos leem e apuram, qualquer que seja o perfil;
- ser RH ou Admin não dá acesso, porque a denúncia pode ser contra o RH ou o Admin;
- o Admin escolhe os membros (e pode se incluir, com auditoria).

### D3. Canal público

- **`denuncias` POST, sem `auth`:**
  - valida o tipo (lista fechada) e o relato (20 a 4000);
  - grava, gera o protocolo e o código, e avisa os membros no sino (só o protocolo);
  - audita sem usuário.
- **`denuncias/acompanhar` POST** (POST para o código não ir na URL):
  - normaliza o código (maiúsculas, sem hífens ou espaços) e procura pelo hash;
  - devolve situação, tipo, data, resultado, parecer e a conversa, sem a identificação.
- **`denuncias/responder` POST:** só antes da conclusão; avisa os membros.
- **A tela chama sempre sem token, mesmo logada.** No Streamlit, a página pública usa a faixa do aviso de privacidade (com "Entrar"), e a tela Entrar ganha o link "Canal de denúncias →".

### D4. Apuração

- **`denuncias` GET:** a lista e as contagens (novas, em apuração, concluídas no ano). Mostra se a denúncia é identificada, mas não a identificação.
- **`denuncias/{id}` GET:** o detalhe com a identificação e a conversa. Audita `abrir_denuncia`.
- **`denuncias/{id}/mensagem` POST:** a primeira mensagem passa a denúncia de `nova` para `em_apuracao`.
- **`denuncias/{id}/concluir` POST:**
  - pede o resultado (`procedente`, `improcedente` ou `inconclusiva`) e o parecer (10+ caracteres);
  - não reabre;
  - a auditoria guarda o resultado, sem o texto.

### D5. Membros e menu

- `comissao_etica` GET, POST (reativa quem já foi membro) e `{id}/remover` (desativa): só o Admin, com auditoria; quem entra recebe aviso.
- `minha_comissao_etica` responde se a conta é membro.
- `auth/me` passa a devolver `membro_comissao_etica`, guardado na sessão ao validar o token. Assim o menu não faz uma chamada a mais.

### D6. Telas (Figma, seção 20, 540:1194)

- **Canal de denúncias** (540:1196):
  - formulário: tipo, relato, quando, envolvidos e "Quero me identificar" (ao ligar, aparece "Seu nome e um contato");
  - "Acompanhar uma denúncia" e "Como funciona";
  - modais "Denúncia enviada" (541:1547, só fecha em "Já guardei o código") e "Acompanhar denúncia" (541:1565).
- **Denúncias** (540:1312):
  - indicadores, abas "Em aberto" e "Concluídas", filtro de tipo e "Abrir →";
  - modais "Denúncia" (544:1241) e "Concluir apuração" (544:1269).
- **Usuários e perfis:** cartão "Comissão de ética" (544:1306), com aviso quando não há membros.

## Risks / Trade-offs

- [Comissão vazia: denúncias chegam e ninguém lê] → o cartão do Admin avisa e pede pelo menos duas pessoas.
- [Membro citado na denúncia] → a comissão se organiza; não há impedimento automático (RIPD R4.2).
- [Spam no canal público] → o limite de requisições do plano e o relato mínimo; não há captcha.
- [Código perdido] → não há recuperação, de propósito; uma nova denúncia pode citar o protocolo.

## Migration Plan

1. Tabelas (`CREATE`).
2. Endpoints (`CREATE`).
3. `auth/me` (`UPDATE`, conferido igual ao git antes).

Rollback: publicar o `auth/me` do git e apagar os endpoints.
