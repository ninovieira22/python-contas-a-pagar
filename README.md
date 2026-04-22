# Granafy Pro

Aplicação web em Flask para organizar gastos mensais a partir de faturas CSV, acompanhar contas fixas, receitas e gerar um resumo visual por mês.

## O que o projeto faz

- Importa faturas CSV e salva as transações localmente.
- Permite categorizar compras manualmente.
- Aprende com categorias já definidas e reaplica isso em lote no mês atual.
- Exibe resumo por categoria, total do cartão, receitas, contas fixas e valor restante.
- Mantém um dashboard comparativo entre meses.
- Permite configurar emojis por categoria.

## Tecnologias

- Python
- Flask
- Pandas
- HTML
- Tailwind via CDN
- JavaScript vanilla

## Estrutura do projeto

```text
.
├── app.py
├── migrar.py
├── README.md
├── data/
│   ├── aprendizado_manual.json
│   ├── config.json
│   ├── emojis.json
│   └── transacoes_salvas.json
├── imports/
│   ├── csv/
│   └── planilhas/
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
└── templates/
    └── index.html
```

## Arquivos locais

Os dados do app ficam em `data/` e não devem ir para o GitHub:

- `transacoes_salvas.json`: base principal de transações
- `aprendizado_manual.json`: histórico de categorias aprendidas
- `config.json`: receitas, contas fixas e configurações por mês
- `emojis.json`: emojis por categoria

Os arquivos de importação ficam em `imports/`:

- `imports/csv/`: faturas CSV
- `imports/planilhas/`: planilhas auxiliares ou históricas

Essas pastas já estão no `.gitignore`.

## Como rodar localmente

### 1. Criar e ativar ambiente virtual

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar dependências

```powershell
pip install flask pandas openpyxl
```

`openpyxl` é útil para o script `migrar.py`, que pode ler arquivos `.xlsx`.

### 3. Iniciar a aplicação

```powershell
python app.py
```

Depois acesse:

```text
http://127.0.0.1:5000
```

## Como usar

### Importar uma fatura

1. Abra a aplicação.
2. Clique em `Importar CSV`.
3. Escolha o mês de referência.
4. Envie o arquivo CSV da fatura.

### Categorizar compras

- Edite a categoria diretamente na tabela.
- O sistema salva esse aprendizado em `data/aprendizado_manual.json`.

### Auto-categorizar

- Use o botão `Auto-Categorizar` para reaplicar categorias aprendidas nas compras do mês atual.

### Configurar finanças

No modal de configurações é possível editar:

- receitas
- contas fixas
- gastos separados do Pedro
- emojis por categoria

## Script de migração

O arquivo `migrar.py` procura planilhas e arquivos compatíveis dentro de `imports/` para montar ou enriquecer o dicionário de categorias.

Execução:

```powershell
python migrar.py
```

## Observações

- O projeto hoje usa armazenamento em JSON local, sem banco de dados.
- O upload principal espera arquivos `.csv`.
- O app foi pensado para uso pessoal/local.

## Melhorias futuras

- criar `requirements.txt`
- adicionar testes
- permitir backup/exportação dos dados
- melhorar regras automáticas de categorização
- adicionar autenticação, caso o projeto evolua para uso remoto

## Licença

Você pode definir a licença que preferir antes de publicar no GitHub.
