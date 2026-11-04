# 🔍 Prospecção B2B de CNPJs com Inteligência Artificial

Uma aplicação web desenvolvida em **Python (Flask)** focada em inteligência comercial e prospecção B2B. O sistema consulta uma base de dados local otimizada da Receita Federal (CNPJs, CNAEs, localizações e contatos) e utiliza a API do **Google Gemini (SDK `google-genai`)** para gerar abordagens altamente personalizadas via E-mail e WhatsApp para cada empresa encontrada.

---

## 🚀 Funcionalidades Principais

- **Filtros Avançados de Prospecção:**
  - Busca inteligente por **UF** e **Município** (com carregamento dinâmico via AJAX).
  - Seleção por **Ramo de Atuação / CNAE** com sugestões agrupadas por divisões industriais e comerciais.
  - Filtro por **Razão Social**, **Nome Fantasia** ou **CNPJ específico**.
  - Filtragem por **Situação Cadastral** (Ativas, Baixadas, etc.) e exigência de contatos (apenas empresas com e-mail/telefone).
- **Interface Interativa & Otimizada:**
  - Componente de busca avançada em *selects* utilizando **Choices.js**.
  - Tabela com seleção em lote (*Select All*) e trava anti-envio duplo.
  - Paginação eficiente via SQL com contagem de registros em tempo real.
- **Integração com IA (Google Gemini 3.1 Flash Lite):**
  - Geração automática de e-mails comerciais completos com assunto e proposta de valor contextualizada para o setor da empresa.
  - Criador de scripts de cold call e abordagens ágeis para WhatsApp.
  - Tela dedicada para **revisão e edição** do texto antes do disparo.
- **Ambiente de Homologação / Testes Seguro (`MODO_TESTE`):**
  - Redirecionamento automático dos disparos de e-mail e WhatsApp para contatos de teste cadastrados, garantindo total segurança durante o desenvolvimento.

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python 3.13+, Flask, SQLite3
- **Inteligência Artificial:** `google-genai` (SDK oficial do Google Gemini)
- **Frontend:** HTML5, JavaScript (ES6+), Bootstrap 5 / CSS3, Choices.js
- **Gerenciamento de Ambiente:** `python-dotenv`

---

## 📁 Estrutura do Projeto

```text
Prospeccao_cnpjs/
├── app/
│   ├── __init__.py       # Fábrica da aplicação Flask (Application Factory)
│   └── routes.py         # Controladores de rotas, SQL queries e integração Gemini
├── templates/
│   ├── index.html        # Formulário com filtros de prospecção
│   ├── resultados.html   # Tabela paginada de resultados e seleção de leads
│   └── revisao_mensagens.html # Painel de revisão e edição das abordagens por IA
├── .env                  # Variáveis de ambiente (Chave de API do Gemini)
├── .gitignore            # Arquivos ignorados pelo Git
├── leads.db              # Banco de dados SQLite de CNPJs/CNAEs
├── requirements.txt      # Dependências Python do projeto
└── run.py                # Ponto de entrada da aplicação
```

---

## ⚙️ Configuração e Instalação

### Pró-requisitos

- **Python 3.10+** instalado.
- Chave de API do Google Gemini (`GEMINI_API_KEY`).

### 1. Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/prospeccao-cnpjs.git
cd prospeccao-cnpjs
```

### 2. Criar e Ativar o Ambiente Virtual (`.venv`)

**No Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**No Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar as Variáveis de Ambiente (`.env`)

Crie um arquivo chamado `.env` na raiz do projeto (no mesmo diretório de `run.py`) com a sua chave da API do Gemini:

```env
GEMINI_API_KEY=sua_chave_api_aqui
```

> ⚠️ **Atenção:** Nunca compartilhe ou faça *commit* do seu arquivo `.env` contendo chaves privadas no GitHub.

---

## 💻 Executando a Aplicação

Para iniciar o servidor web local, execute:

```bash
python run.py
```

Acesse no seu navegador através do endereço:
👉 **`http://127.0.0.1:5000`**

---

## 🛡️ Segurança e Boas Práticas

- **Proteção SQL Injection:** Todas as consultas no `leads.db` utilizam parâmetros sanitizados (`?`).
- **Modo de Teste (`MODO_TESTE = True`):** Definido em `app/routes.py`, evita envios acidentais para e-mails ou números de telefones reais durante a fase de desenvolvimento.

---

## 📜 Licença

Este projeto é disponibilizado sob a licença [MIT](LICENSE). Sinta-se à vontade para utilizar, modificar e contribuir!