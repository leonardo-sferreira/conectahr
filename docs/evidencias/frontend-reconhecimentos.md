# Reconhecimentos: mural, envio e moderação (tarefa 66 da change `concluir-frontend-streamlit`)

**Data:** 21/11/2026. **Figma:**
[291:908](https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn?node-id=291-908) (mural),
[291:1075](https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn?node-id=291-1075) (recebidos),
[291:1239](https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn?node-id=291-1239) (vazio),
[291:1374](https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn?node-id=291-1374) (moderação) e os modais
[291:1631](https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn?node-id=291-1631),
[291:1667](https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn?node-id=291-1667) e
[291:1703](https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn?node-id=291-1703).

## Backend (publicado)

- **`ConectaHR/enriquecer_reconhecimentos`** (nova): acrescenta o nome de quem enviou, de quem recebeu, de quem moderou
  e da competência. As rotas chamam a função depois das regras de visibilidade, então ela não muda quem aparece.
  Testada pela CLI.
- **`mural_reconhecimento` e `meus_reconhecimentos_recebidos`:** passaram a devolver os nomes. Só acrescentam campos;
  antes da publicação, conferi que o que estava no ar era igual ao git.
- **Rotas novas:**
  - `meus_reconhecimentos_enviados`: os que a pessoa enviou, com a moderação e o motivo;
  - `reconhecimentos_moderacao`: públicos no mural e moderados, só RH e Admin;
  - `competencias_reconhecimento`: só id e nome das ativas.
- `checar_endpoints`: 298, sem falha.

## Telas

- **"Mural de reconhecimentos"** (`frontend/pagina_reconhecimentos.py` e `reconhecimentos_modelo.py`): abre pela
  Trajetória ("Mural de reconhecimentos →"), que fica marcada no menu, como decidido no `design.md`.
  - abas Mural, Recebidos e Enviados;
  - filtros de competência e período;
  - vazio com a chamada;
  - aviso de "Aparecer no mural";
  - o feedback privado do gestor aparece com "Privado: só você vê".
- **"Reconhecer colega":** colega com o departamento, competência, título (100) e mensagem (1500). Escolher a si mesmo
  mostra o aviso e desliga o envio.
- **"Moderar reconhecimentos"** (RH e Admin, pelo "Moderar →" do mural):
  - filtros Todos, No mural e Moderados;
  - o moderado aparece com o conteúdo ocultado e o motivo;
  - o modal pede motivo de pelo menos 5 caracteres e avisa que não há volta.
- Nenhuma tela oferece promover nem punir.

## Testes

| Teste | Resultado |
|---|---|
| `python tools/testar_reconhecimentos.py` | 29/29 |
| `testar_trajetoria`, `testar_menu`, `medir_contraste` | 44/44, 12/12, 0 pares |

Prints com API simulada e dados fictícios em [`frontend-reconhecimentos/`](frontend-reconhecimentos/), com os nós do
Figma ao lado (`figma-*`): `1-mural`, `2-recebidos`, `3-modal-reconhecer`, `4-moderar` e `5-modal-moderar`.

Diferenças do Figma:
- "Moderar →" no topo do mural, para RH e Admin, porque o Figma não desenha o caminho até a moderação;
- em "Enviados", quem enviou vê o motivo da moderação, como diz o modal 291:1703.

**Não verificado por HTTP ainda.** Fica para a mesma sessão de login da Retenção.
