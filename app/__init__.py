from flask import Flask


def create_app():
    # Cria a instância do Flask configurando os diretórios personalizados de templates e arquivos estáticos
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    # Importa o Blueprint contendo as rotas principais da aplicação
    from app.routes import main_bp

    # Registra o Blueprint no aplicativo principal para disponibilizar as rotas
    app.register_blueprint(main_bp)

    return app