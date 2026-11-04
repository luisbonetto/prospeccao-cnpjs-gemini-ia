import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para o ambiente do sistema
load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=False, port=5000)