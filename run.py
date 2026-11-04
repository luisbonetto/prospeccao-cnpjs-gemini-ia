import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente definidas no arquivo .env (ex: chaves de API)
load_dotenv()

# Importa a função de fábrica para criar a instância do aplicativo Flask
from app import create_app

# Inicializa o aplicativo web utilizando o padrão Application Factory
app = create_app()

if __name__ == "__main__":
    # Inicia o servidor de desenvolvimento local na porta 5000 com o modo debug desativado
    app.run(debug=False, port=5000)