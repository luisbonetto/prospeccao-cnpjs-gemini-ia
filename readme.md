# 🔍 Prospecção B2B de CNPJs com Inteligência Artificial

Uma aplicação web desenvolvida em **Python (Flask)** focada em inteligência comercial e prospecção B2B. O sistema consulta uma base de dados local otimizada da Receita Federal (CNPJs, CNAEs, localizações e contatos) e utiliza a API do **Google Gemini (SDK `google-genai`)** para gerar abordagens altamente personalizadas via E-mail e WhatsApp para cada empresa encontrada.

---

## 🚀 Funcionalidades Principais

* **Filtros Avançados de Prospecção:**
  * Busca por **UF** e **Município** (com carregamento dinâmico via AJAX).
  * Seleção por **Ramo de Atuação / CNAE** com sugestões agrupadas por divisões industriais e comerciais.
  * Filtro por **Razão Social**, **Nome Fantasia** ou **CNPJ específico**.
  * Filtragem por **Exigência de Contatos** (apenas empresas com e-mail/telefone).
* **Base Sanitizada e Otimizada:**
  * O banco de dados é construído **exclusivamente com empresas ATIVAS** (situação cadastral `02`), garantindo alta assertividade nas abordagens.
* **Interface Interativa & Otimizada:**
  * Componente de busca avançada em *selects* utilizando **Choices.js**.
  * Tabela com seleção em lote (*Select All*) e trava anti-envio duplo.
  * Paginação eficiente via SQL com contagem de registros em tempo real.
* **Integração com IA (Google Gemini):**
  * Geração automática de e-mails comerciais completos com assunto e proposta de valor contextualizada para o setor da empresa.
  * Criador de scripts de cold call e abordagens ágeis para WhatsApp.
  * Tela dedicada para **revisão e edição** do texto antes do disparo.
* **Disparos & Canais de Comunicação:**
  * **E-mail:** Disparo automatizado com integração SMTP e formato HTML estilizado.
  * **WhatsApp (Gratuito & Seguro):** Geração de links pré-formatados oficiais (`wa.me`) permitindo envio imediato sem custos de API ou riscos de bloqueio.
* **Gestão de Disparos e Métricas:**
  * **Histórico de Disparos (`/historico`):** Registro persistido no SQLite com status, modo de envio, data/hora e empresa de destino.
  * **Dashboard (`/dashboard`):** Visualização de estatísticas da base e histórico de contatos.
* **Ambiente de Homologação / Testes Seguro (`MODO_TESTE`):**
  * Redirecionamento automático dos disparos de e-mail e WhatsApp para contatos de teste salvos no `.env`, garantindo total segurança durante o desenvolvimento.

---

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python 3.13+, Flask, SQLite3
* **Inteligência Artificial:** `google-genai` (SDK oficial do Google Gemini)
* **Frontend:** HTML5, JavaScript (ES6+), Bootstrap 5 / CSS3, Choices.js
* **Gerenciamento de Ambiente & Variáveis:** `python-dotenv`

---

## 📁 Estrutura do Projeto

```text
Prospeccao_cnpjs/
├── app/
│   ├── __init__.py            # Fábrica da aplicação Flask (Application Factory)
│   └── routes.py              # Controladores de rotas, SQL queries e integração Gemini
├── dados_rfb/                 # Pasta local para os arquivos .csv/.txt brutos da Receita Federal
├── scripts_auxiliares/
│   ├── analisar_banco.py      # Script de inspeção e métricas do SQLite
│   ├── importar_dados_rfb.py  # Pipeline que gera o leads.db filtrando APENAS empresas ativas
│   └── limpar_inativas.py     # Script de higienização de bases existentes
├── templates/
│   ├── dashboard.html         # Painel de controle e estatísticas
│   ├── historico.html         # Tabela de histórico de disparos realizados
│   ├── index.html             # Formulário com filtros de prospecção
│   ├── resultados.html        # Tabela paginada de resultados e seleção de leads
│   └── revisao_mensagens.html # Painel de revisão e edição das abordagens por IA
├── .env                       # Variáveis de ambiente (Chaves de API e Contatos de Teste)
├── .gitignore                 # Arquivos ignorados pelo Git
├── leads.db                   # Banco de dados SQLite de CNPJs/CNAEs e Histórico
├── readme.md                  # Documentação do projeto
├── requirements.txt           # Dependências Python do projeto
└── run.py                     # Ponto de entrada da aplicação
```

---

## ⚙️ Configuração e Instalação

### Pré-requisitos

* **Python 3.10+** instalado.
* Chave de API do Google Gemini (`GEMINI_API_KEY`).

### 1. Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/prospeccao-cnpjs.git
cd prospeccao-cnpjs
```

### 2. Criar e Ativar o Ambiente Virtual (`.venv`)

**No Windows (PyCharm Terminal / PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**No Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as Dependências

```bash
pip install -r requirements.txt
```

### 4. Construção da Base de Dados Local (`leads.db`)

Para popular o seu banco de dados SQLite com a base oficial da Receita Federal:

1. Baixe os arquivos de dados abertos no portal oficial da Receita Federal (arquivos de *Estabelecimentos* e *Empresas*).
2. Coloque os arquivos baixados ou extraídos na pasta `dados_rfb/`.
3. Execute o script automatizado de importação:

```bash
python scripts_auxiliares/importar_dados_rfb.py
```

> 🛡️ **Filtro de Higienização de Leads:** O script de importação descarta automaticamente qualquer empresa com situação cadastral inativa, suspensa, nula ou baixada. **Apenas empresas ativas (situação 02)** são gravadas no banco de dados, otimizando o tamanho do arquivo `leads.db` e a velocidade das buscas na aplicação.

---

### 5. Configurar as Variáveis de Ambiente (`.env`)

Crie um arquivo chamado `.env` na raiz do projeto com as suas credenciais:

```env
GEMINI_API_KEY=sua_chave_api_aqui
EMAIL_TESTE=seu_email_teste@exemplo.com
WHATSAPP_TESTE=41999999999
```

> ⚠️ **Atenção:** Nunca compartilhe ou faça *commit* do seu arquivo `.env` contendo chaves privadas no GitHub.

---

## 💻 Executando a Aplicação

Para iniciar o servidor web local, execute no PyCharm ou terminal:

```bash
python run.py
```

Acesse no seu navegador através do endereço:
👉 **`http://127.0.0.1:5000`**

---

## 🛡️ Segurança e Alternância de Ambientes

* **Modo de Homologação (`MODO_TESTE`):**
  Definido no topo do arquivo `app/routes.py`:
  * `MODO_TESTE = True`: Redireciona todos os e-mails e WhatsApps para as variáveis `EMAIL_TESTE` e `WHATSAPP_TESTE` do `.env`.
  * `MODO_TESTE = False`: Habilita o envio para os destinatários reais cadastrados na Receita Federal.
* **Proteção contra SQL Injection:** Consultas sanitizadas via trechos parametrizados no SQLite (`?`).

---

## 📜 Licença

Este projeto é disponibilizado sob a licença [MIT](LICENSE). Sinta-se à vontade para utilizar, modificar e contribuir!