# SGDI - Sistema de Gestão de Demandas Internas

Sistema web para gerenciar demandas internas da empresa, com autenticação de usuários, controle de prioridades e rastreabilidade de edições.

## Como rodar

```bash
python init_db.py
python app.py
```

Acesse: http://localhost:5000

> Na primeira execução, crie um usuário em `/novo_usuario` e faça login para acessar o sistema.

---

## Funcionalidades

### Demandas
- Criar, editar e deletar demandas
- Visualizar detalhes de cada demanda
- Adicionar comentários
- Prioridade por nível: 🟠 Alta · 🟡 Média · 🟢 Baixa

### Filtros e Busca
- Filtrar demandas por prioridade
- Buscar demandas por título
- Filtrar demandas por responsável (usuário criador)
- Filtros combinados (prioridade + texto + responsável)
- Filtro ativo refletido na URL (compartilhável)

### Autenticação e Usuários
- Cadastro de usuários com senha armazenada em hash (werkzeug.security)
- Login e logout com sessão Flask
- Todas as rotas protegidas por `@login_required`
- Controle de cargo: `comum` e `admin`

### Controle de Acesso
- Apenas o criador da demanda ou um admin pode deletá-la
- Botão de deletar oculto para quem não tem permissão

### Rastreabilidade
- Demandas vinculadas ao usuário que as criou (`criado_por`)
- Histórico de edições campo a campo (valor anterior → novo valor)
- Registro de quem editou e quando

---

## Estrutura do Banco de Dados

| Tabela              | Descrição                                              |
|---------------------|--------------------------------------------------------|
| `demandas`          | Demandas internas com título, descrição, prioridade e criador |
| `usuarios`          | Usuários do sistema com hash de senha e cargo          |
| `comentarios`       | Comentários vinculados a cada demanda                  |
| `historico_edicoes` | Registro de cada campo alterado nas edições            |

---

## Tecnologias

- Python 3 + Flask
- SQLite
- Jinja2 (templates HTML)
- werkzeug.security (hash de senha)

---

*Desenvolvido em 2026*