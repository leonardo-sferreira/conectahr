// Preferencias de privacidade do colaborador (LGPD, art. 18, par. 2): sair da
// lista de aniversariantes e do mural de reconhecimento. Uma linha por
// colaborador. Sem linha, valem os padroes: falso para adultos e verdadeiro para
// menores de 18 anos (art. 14 e ECA Digital). Reconhecimentos continuam visiveis
// para o proprio colaborador e para o RH, mesmo com o mural oculto.
table preferencia_privacidade {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    int colaborador_id {
      table = "colaborador"
    }
    bool ocultar_aniversario?=false
    bool ocultar_mural?=false
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "colaborador_id", op: "asc"}]}
  ]

  guid = "conectahr-preferencia-privacidade-0001"
}
