# Evidências — Colaboradores e Usuários e perfis (tarefas 50 e 53)

Telas construídas em 10/10/2026 no frontend Streamlit. O ponto de partida foi um problema prático: contas de RH
e de Admin criadas sem cadastro de colaborador não conseguem marcar ponto, porque o backend exige a ficha.
O Figma foi ajustado antes de codar (ver "Figma" abaixo).

| Nó do Figma | O que é | Código |
|---|---|---|
| 243:580 | RH — Colaboradores: lista, filtros e ficha com "Criar acesso" (**botão novo**) | `frontend/pagina_colaboradores.py` |
| 243:1075 | Modal "Admitir colaborador" (**campos novos**, os que o backend exige) | idem |
| 246:612 | Admin — Usuários e perfis, com a situação "Sem ficha" e "Vincular ficha" (**novo**) | `frontend/pagina_usuarios.py` |
| 246:1245 | Modal "Novo usuário" ("Criar acesso" quando aberto pela ficha) | `frontend/pagina_colaboradores.py` |
| 246:1280 | Modal "Trocar perfil" | `frontend/pagina_usuarios.py` |
| 440:1203 | Modal "Vincular ficha" (**novo**) | idem |

As regras de apresentação ficam em `frontend/cadastro_modelo.py` (sem Streamlit).

## O caminho de cadastro de um funcionário

1. **Admitir colaborador** (só o RH; `colaboradores` POST). Cria a ficha, sem conta de acesso.
2. **Criar acesso**, aberto logo depois de admitir ou pela ficha (`usuarios` POST).
   - A senha temporária é sorteada na tela e o backend a envia **por e-mail**. Quem cria a conta não a vê.
   - A conta nasce com o perfil Colaborador. Se quem cria for Admin, pode escolher outro perfil, que o backend
     aplica em seguida (`usuarios/{id}/perfil`).
3. **Vincular ficha** (Admin; `usuarios/{id}/vincular_colaborador`), para quem **já tem conta sem ficha**, como as
   contas de RH ou Admin criadas antes da ficha. Depois do vínculo, a pessoa marca ponto e pede férias.

A tela Ponto agora explica o que fazer quando a conta não tem ficha.

## Backend: o que mudou e como foi conferido

- **`usuarios/{id}/vincular_colaborador` (POST, novo).**
  - O Admin vincula qualquer conta; o RH, só contas de Colaborador.
  - **Ninguém vincula a própria conta.** Quem se ligasse à ficha de outra pessoa passaria a marcar ponto e pedir
    férias como ela.
  - A conta não pode ter ficha; a ficha não pode ter conta nem ser de colaborador desligado.
  - Fica na auditoria (`vincular_conta_colaborador`, só os ids).
- **`usuarios` (POST).** Envia a senha temporária por e-mail (Brevo, template genérico) e responde
  `email_enviado`. Se o envio falhar, a conta continua criada e a tela orienta "Esqueci minha senha". A senha não vai
  para a auditoria.
- **`usuarios` (GET).** Passa a devolver `senha_primeiro_acesso`, para a situação "Senha temporária".
- **Como foi publicado e conferido:**
  - `checar_endpoints.py` nos arquivos locais: 186 endpoints, nenhuma falha;
  - `--dry-run` mostrou só essas três mudanças (1 criada, 2 atualizadas), e o `push` publicou as três;
  - o `pull` seguinte trouxe as três;
  - por HTTP, sem token e com token inválido, a resposta foi 401 nos três (os POSTs com um corpo válido);
  - `checar_endpoints.py` depois do push: 186 endpoints, nenhuma falha.
- **O que não foi testado:** não criei conta nem vínculo de verdade, para não gravar dados na base real, e o login
  pede código por e-mail. O envio do e-mail com a senha só será visto na primeira conta criada pela tela.

## Como repetir

```
python tools/testar_cadastro.py   # 48 verificações
```

Roda sem rede, com uma API simulada (dados fictícios), e também no workflow `Validar`.
**Resultado em 10/10/2026: 48 de 48.** Os outros testes do frontend continuam passando.

## O que os testes conferem

| Estado | Caso | Resultado |
|---|---|---|
| Sucesso | Lista sem desligados, por nome; busca por nome, CPF ou e-mail; filtros de departamento e situação | ok |
| Sucesso | Ficha: gestor do departamento e conta de acesso, sem salário; "Criar acesso" só na ficha sem conta | ok |
| Sucesso | Admitir envia o cadastro completo (CPF só com dígitos, datas ISO) e abre "Criar acesso" com a pessoa escolhida | ok |
| Sucesso | "Criar acesso" sorteia uma senha forte, diferente a cada vez; o RH não escolhe perfil | ok |
| Sucesso | Admin: Novo usuário com perfil RH cria a conta e troca o perfil | ok |
| Sucesso | "Vincular ficha" sugere a ficha com o mesmo nome e vincula; trocar perfil; desativar (com confirmação) e reativar | ok |
| Própria conta | O Admin não tem nenhuma ação na própria conta; sem ficha, a tela diz que outro Admin vincula | ok |
| Escopo | Admin vê a lista, mas não admite; RH não abre Usuários e perfis; colaborador e gestor não abrem nenhuma das duas | ok |
| Erro | Antes de enviar: CPF inválido, campo obrigatório, carga horária, e-mail. A API não é chamada | ok |
| Erro | Recusa do backend no modal, que continua aberto (CPF repetido; vincular a própria conta) | ok |
| Erro | E-mail com a senha não enviado: a tela orienta "Esqueci minha senha" | ok |
| Erro | Erro ao carregar vira alerta | ok |
| Vazio | "Ninguém neste filtro." | ok |
| Carregando | Spinner enquanto as listas carregam | verificado no navegador |

## Verificado no navegador (Chrome, API simulada)

Prints com dados fictícios, em [`frontend-cadastro/`](frontend-cadastro/):

| Print | Compare com |
|---|---|
| `1-colaboradores` e `2-ficha-criar-acesso` | 243:580 |
| `3-admitir-colaborador` | 243:1075 |
| `4-criar-acesso` e `8-novo-usuario` | 246:1245 |
| `5-usuarios-e-perfis` | 246:612 |
| `6-vincular-ficha` | 440:1203 |
| `7-trocar-perfil` | 246:1280 |
| `9` a `11` | tema escuro (`frontend/theme.py`, `_ESCURO_CSS`) |

## Figma: o que foi ajustado antes de codar

- **Admitir colaborador (243:1075)** ganhou os campos que o backend exige e o desenho não tinha: telefone, bairro,
  logradouro, número, nível, carga horária e salário. A nota agora diz que o acesso vem em seguida.
- **Ficha (243:580)** ganhou "Criar acesso", para a ficha sem conta.
- **Usuários e perfis (246:612)** ganhou uma conta "Sem ficha" com "Vincular ficha". A nota diz que ninguém vincula a
  própria conta.
- **Modal novo "Vincular ficha" (440:1203)**, na seção 12.

## Decisões e diferenças em relação ao Figma

- **"Sem ficha" no lugar de "Bloqueados por senha".** O backend não informa o bloqueio por tentativas, então o
  segundo cartão do topo conta as contas sem ficha. "Desbloquear" e "Reenviar acesso" ficam para a tarefa 76.
- **Trocar perfil sem "motivo".** O `usuarios/{id}/perfil` não recebe motivo, e a auditoria já registra quem fez.
  O motivo também fica para a tarefa 76.
- **Ficha sem edição.** "Editar cadastro", "Mudar cargo ou salário" e "Linha do tempo" ficam para a continuação da
  tarefa 53, assim como o cartão "Onboarding em andamento".
- **Perfis como lista de opções.** O "Perfil" do Novo usuário é um seletor simples, e não os cartões do Figma.
