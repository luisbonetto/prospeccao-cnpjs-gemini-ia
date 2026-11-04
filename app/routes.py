import os
import sqlite3
from google import genai
from flask import Blueprint, render_template, request, jsonify, current_app

# Cria um Blueprint do Flask para modularizar as rotas principais
main_bp = Blueprint('main', __name__)

# --- CONFIGURAÇÕES DE HOMOLOGAÇÃO / SEGURANÇA ---
MODO_TESTE = True
EMAIL_TESTE = "luisinhobonetto@gmail.com"
WHATSAPP_TESTE = "(41) 98474-4757"

# Inicializa o cliente oficial da API do Google GenAI
ai_client = genai.Client()

# Dicionário de mapeamento para traduzir os códigos de situação cadastral da Receita Federal
SITUACAO_MAP = {
    "01": "NULA",
    "02": "ATIVA",
    "03": "SUSPENSA",
    "04": "INAPTA",
    "08": "BAIXADA",
}

def get_db_path():
    # Navega um nível acima do diretório atual ('app/') para localizar o arquivo 'leads.db' na raiz
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "leads.db")


@main_bp.route("/")
def index():
    conn = None
    cnaes_por_categoria = {}
    try:
        db_path = get_db_path()
        if os.path.exists(db_path):
            # Conecta ao banco de dados SQLite e define o modo de retorno como dicionário (Row)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Busca todos os CNAEs cadastrados ordenados pelo código
            cursor.execute("SELECT codigo, descricao FROM cnaes ORDER BY codigo ASC")
            rows = cursor.fetchall()

            # Agrupa dinamicamente os CNAEs por divisão com base nos dois primeiros dígitos
            for row in rows:
                codigo = str(row["codigo"]).strip()
                descricao = row["descricao"] or "Sem descrição"

                prefixo = codigo[:2] if len(codigo) >= 2 else "Geral"
                categoria_nome = f"Divisão {prefixo}"

                # Atribui nomes amigáveis para divisões industriais e comerciais comuns
                if prefixo == "27":
                    categoria_nome = "Divisão 27 - Fabricação de Máquinas e Equipamentos Elétricos"
                elif prefixo == "43":
                    categoria_nome = "Divisão 43 - Serviços Especializados para Construção (Elétrica, Obras)"
                elif prefixo == "46":
                    categoria_nome = "Divisão 46 - Comércio Atacadista"
                elif prefixo == "47":
                    categoria_nome = "Divisão 47 - Comércio Varejista"
                elif prefixo == "28":
                    categoria_nome = "Divisão 28 - Fabricação de Máquinas e Equipamentos"
                elif prefixo == "25":
                    categoria_nome = "Divisão 25 - Fabricação de Produtos de Metal"

                if categoria_nome not in cnaes_por_categoria:
                    cnaes_por_categoria[categoria_nome] = []

                cnaes_por_categoria[categoria_nome].append({
                    "codigo": codigo,
                    "descricao": descricao
                })
    except Exception as e:
        current_app.logger.exception("Erro ao carregar CNAEs para o index")
    finally:
        if conn:
            conn.close()

    return render_template("index.html", cnaes_por_categoria=cnaes_por_categoria)


@main_bp.route("/api/municipios/<uf>")
def api_municipios(uf):
    # Rota de API AJAX para buscar municípios filtrados pela UF selecionada
    conn = None
    try:
        db_path = get_db_path()
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Banco de dados não encontrado: {db_path}")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        uf_param = uf.strip().upper()

        cursor.execute(
            """
            SELECT DISTINCT codigo, nome
            FROM municipios_por_uf
            WHERE uf = ?
            ORDER BY nome ASC, codigo ASC
            """,
            (uf_param,),
        )

        cidades = []
        for row in cursor.fetchall():
            codigo = str(row["codigo"]).strip()
            nome = row["nome"] or f"Município {codigo}"
            cidades.append({"codigo": codigo, "nome": nome})

        return jsonify(cidades)

    except Exception as erro:
        current_app.logger.exception("Erro ao carregar municípios")
        return jsonify({"erro": str(erro)}), 500

    finally:
        if conn is not None:
            conn.close()


@main_bp.route("/resultados", methods=["POST", "GET"])
def resultados():
    # Coleta filtros enviados via formulário (POST) ou parâmetros de paginação (GET)
    if request.method == "POST":
        remetente_nome = request.form.get("remetente_nome", "")
        remetente_cargo = request.form.get("remetente_cargo", "")
        remetente_empresa = request.form.get("remetente_empresa", "")
        objetivo_prospeccao = request.form.get("objetivo_prospeccao", "")

        estado = request.form.get("estado", "")
        municipio = request.form.get("municipio", "")
        situacao = request.form.get("situacao", "")
        cnae = request.form.get("cnae", "")
        busca_nome = request.form.get("busca_nome", "")
        cnpj_busca = request.form.get("cnpj_busca", "")
        filtro_contato = request.form.get("filtro_contato", "todas")
    else:
        remetente_nome = request.args.get("remetente_nome", "")
        remetente_cargo = request.args.get("remetente_cargo", "")
        remetente_empresa = request.args.get("remetente_empresa", "")
        objetivo_prospeccao = request.args.get("objetivo_prospeccao", "")

        estado = request.args.get("estado", "")
        municipio = request.args.get("municipio", "")
        situacao = request.args.get("situacao", "")
        cnae = request.args.get("cnae", "")
        busca_nome = request.args.get("busca_nome", "")
        cnpj_busca = request.args.get("cnpj_busca", "")
        filtro_contato = request.args.get("filtro_contato", "todas")

    # Tratamento seguro da paginação
    try:
        pagina = int(request.args.get("pagina", 1))
        if pagina < 1:
            pagina = 1
    except ValueError:
        pagina = 1

    limite = 50
    offset = (pagina - 1) * limite

    db_path = get_db_path()
    if not os.path.exists(db_path):
        return f"Banco de dados não encontrado: {db_path}", 500

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()
        where_clauses = ["1=1"]
        params = []

        # Construção dinâmica das cláusulas de filtro SQL
        if estado:
            where_clauses.append("e.uf = ?")
            params.append(estado)

        if municipio:
            where_clauses.append("e.municipio = ?")
            params.append(municipio)

        if situacao == "ATIVA":
            where_clauses.append("e.situacao_cadastral = '02'")

        if cnae:
            where_clauses.append("e.cnae_fiscal_principal LIKE ?")
            params.append(f"{cnae}%")

        if busca_nome:
            where_clauses.append("(emp.razao_social LIKE ? OR e.nome_fantasia LIKE ?)")
            params.extend([f"%{busca_nome}%", f"%{busca_nome}%"])

        if cnpj_busca:
            cnpj_limpo = "".join(filter(str.isdigit, cnpj_busca))
            if cnpj_limpo:
                where_clauses.append("e.cnpj_basico LIKE ?")
                params.append(f"%{cnpj_limpo[:8]}%")

        if filtro_contato == "com_contato":
            where_clauses.append("""
                (
                    (e.ddd_1 IS NOT NULL AND e.ddd_1 != '' AND e.telefone_1 IS NOT NULL AND e.telefone_1 != '') 
                    OR 
                    (e.email IS NOT NULL AND e.email != '' AND e.email != 'não informado')
                )
            """)

        where_sql = " AND ".join(where_clauses)

        # Consulta para contar o total de registros atendidos pelos filtros (para paginação)
        count_query = f"""
            SELECT COUNT(DISTINCT e.id) as total
            FROM estabelecimentos e
            INNER JOIN empresas emp ON e.cnpj_basico = emp.cnpj_basico
            LEFT JOIN municipios m ON e.municipio = m.codigo
            WHERE {where_sql}
        """
        cursor.execute(count_query, params)
        total_registros = cursor.fetchone()["total"]

        total_paginas = (total_registros + limite - 1) // limite
        if total_paginas == 0:
            total_paginas = 1

        # Consulta principal paginada unindo estabelecimentos, empresas e descrições de CNAE
        query = f"""
            SELECT DISTINCT
                e.id,
                e.cnpj_basico || e.cnpj_ordem || e.cnpj_dv AS cnpj_completo,
                emp.razao_social,
                e.nome_fantasia,
                e.cnae_fiscal_principal,
                c.descricao AS desc_cnae,
                e.uf,
                e.municipio,
                e.situacao_cadastral,
                emp.capital_social,
                e.ddd_1,
                e.telefone_1,
                e.email
            FROM estabelecimentos e
            INNER JOIN empresas emp ON e.cnpj_basico = emp.cnpj_basico
            LEFT JOIN municipios m ON e.municipio = m.codigo
            LEFT JOIN cnaes c ON e.cnae_fiscal_principal = c.codigo
            WHERE {where_sql}
            LIMIT ? OFFSET ?
        """

        query_params = list(params) + [limite, offset]
        cursor.execute(query, query_params)
        rows = cursor.fetchall()

        empresas = []
        for row in rows:
            cnpj = row["cnpj_completo"] or ""
            cnpj_fmt = (
                f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/"
                f"{cnpj[8:12]}-{cnpj[12:14]}"
                if len(cnpj) == 14
                else cnpj
            )

            telefone = (
                f"({row['ddd_1']}) {row['telefone_1']}"
                if row["ddd_1"] and row["telefone_1"]
                else "Não informado"
            )
            situacao_texto = SITUACAO_MAP.get(row["situacao_cadastral"], row["situacao_cadastral"])

            cnae_codigo = row["cnae_fiscal_principal"] or "N/I"
            cnae_descricao = row["desc_cnae"] if row["desc_cnae"] else "Descrição não encontrada"

            empresas.append({
                "id": row["id"],
                "cnpj": cnpj_fmt,
                "razao_social": row["razao_social"] or row["nome_fantasia"] or "Não informada",
                "nome_fantasia": row["nome_fantasia"],
                "atividade_codigo": cnae_codigo,
                "atividade_descricao": cnae_descricao,
                "estado": row["uf"],
                "cidade": row["municipio"],
                "situacao": situacao_texto,
                "capital_social": f"R$ {row['capital_social']}" if row["capital_social"] else "R$ 0,00",
                "telefone": telefone,
                "email": row["email"].lower() if row["email"] else "Não informado",
            })

        return render_template(
            "resultados.html",
            empresas=empresas,
            pagina_atual=pagina,
            total_paginas=total_paginas,
            total_registros=total_registros,
            filtro_estado=estado,
            filtro_municipio=municipio,
            filtro_situacao=situacao,
            filtro_cnae=cnae,
            filtro_busca_nome=busca_nome,
            filtro_cnpj_busca=cnpj_busca,
            remetente_nome=remetente_nome,
            remetente_cargo=remetente_cargo,
            remetente_empresa=remetente_empresa,
            objetivo_prospeccao=objetivo_prospeccao
        )

    except Exception:
        current_app.logger.exception("Erro ao consultar resultados")
        return "Ocorreu um erro ao consultar as empresas. Verifique o terminal.", 500
    finally:
        conn.close()


@main_bp.route("/gerar-mensagens", methods=["POST"])
def gerar_mensagens():
    # Coleta os dados do remetente e IDs das empresas selecionadas para geração em lote via Gemini
    remetente_nome = request.form.get("remetente_nome")
    remetente_cargo = request.form.get("remetente_cargo")
    remetente_empresa = request.form.get("remetente_empresa")
    objetivo_prospeccao = request.form.get("objetivo_prospeccao")
    canal_prospeccao = request.form.get("canal_prospeccao", "ambos")

    ids_selecionados = request.form.getlist("empresas_selecionadas")
    if not ids_selecionados:
        return "Nenhuma empresa selecionada. <a href='javascript:history.back()'>Voltar</a>", 400

    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    placeholders = ",".join(["?"] * len(ids_selecionados))
    query = f"""
        SELECT DISTINCT
            e.id, emp.razao_social, e.nome_fantasia, c.descricao AS desc_cnae,
            e.uf, e.municipio, e.email, e.ddd_1, e.telefone_1
        FROM estabelecimentos e
        INNER JOIN empresas emp ON e.cnpj_basico = emp.cnpj_basico
        LEFT JOIN cnaes c ON e.cnae_fiscal_principal = c.codigo
        WHERE e.id IN ({placeholders})
    """
    cursor.execute(query, ids_selecionados)
    empresas = cursor.fetchall()
    conn.close()

    mensagens_geradas = []

    # Itera sobre cada empresa selecionada gerando abordagens personalizadas com IA
    for emp in empresas:
        razao = emp["razao_social"] or emp["nome_fantasia"] or "Empresa"
        cnae_desc = emp["desc_cnae"] or "Atividade comercial geral"
        cidade = emp["municipio"]
        uf = emp["uf"]
        telefone = f"({emp['ddd_1']}) {emp['telefone_1']}" if emp['ddd_1'] and emp['telefone_1'] else "Não informado"
        email = emp["email"].lower() if emp["email"] else "Não informado"

        prompt_email = f"""
        Você é um especialista em prospecção B2B por e-mail.
        Escreva um e-mail comercial completo, profissional e altamente personalizado.

        Remetente: {remetente_nome} ({remetente_cargo} na {remetente_empresa})
        Objetivo: {objetivo_prospeccao}
        Destinatário: {razao} | Atuação: {cnae_desc} | Local: {cidade}/{uf}

        Diretrizes do E-mail:
        1. Inclua uma linha de Assunto atrativa no topo no formato "Assunto: ...".
        2. Apresente de forma clara o valor técnico/operacional oferecido para o ramo ({cnae_desc}).
        3. Mantenha tom profissional e encerre com chamada para agendar conversa rápida.
        4. Retorne APENAS o texto do e-mail pronto (Assunto + Corpo), sem explicações adicionais.
        """

        prompt_telefone = f"""
        Você é um especialista em prospecção comercial por telefone e mensagens instantâneas (WhatsApp).
        Escreva um roteiro curto e direto para ligação ou mensagem rápida de WhatsApp.

        Remetente: {remetente_nome} ({remetente_empresa})
        Objetivo: {objetivo_prospeccao}
        Destinatário: {razao} | Atuação: {cnae_desc} | Local: {cidade}/{uf}

        Diretrizes de Telefone/WhatsApp:
        1. Seja extremamente conciso (máximo 3 a 4 parágrafos curtos).
        2. Abordagem rápida: Apresentação breve -> Dor/Oportunidade do setor -> Pergunta aberta/CTA.
        3. Use tom amigável e direto.
        4. Retorne APENAS o script/mensagem pronta, sem comentários nem notas de instrução.
        """

        msg_email = ""
        msg_telefone = ""

        if canal_prospeccao in ["email", "ambos"]:
            try:
                res = ai_client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=prompt_email
                )
                msg_email = res.text
            except Exception as e:
                msg_email = f"Erro na IA (E-mail): {str(e)}"

        if canal_prospeccao in ["telefone", "ambos"]:
            try:
                res = ai_client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=prompt_telefone
                )
                msg_telefone = res.text
            except Exception as e:
                msg_telefone = f"Erro na IA (Telefone): {str(e)}"

        mensagens_geradas.append({
            "id": emp["id"],
            "razao_social": razao,
            "email": email,
            "telefone": telefone,
            "canal": canal_prospeccao,
            "mensagem_email": msg_email,
            "mensagem_telefone": msg_telefone
        })

    return render_template(
        "revisao_mensagens.html",
        mensagens_geradas=mensagens_geradas,
        canal_selecionado=canal_prospeccao
    )


@main_bp.route("/enviar-email", methods=["POST"])
def enviar_email():
    # Processa o disparo de e-mail respeitando o Modo de Homologação (Sandbox/Teste)
    empresa_id = request.form.get("empresa_id")
    email_destino_original = request.form.get("contato")
    mensagem = request.form.get("mensagem")

    if MODO_TESTE:
        email_destino = EMAIL_TESTE
        aviso_teste = f"<div class='alert alert-warning'><strong>[MODO DE TESTE ATIVO]</strong> O e-mail original era para: <i>{email_destino_original}</i>, mas foi redirecionado com segurança para o seu e-mail de teste.</div>"
    else:
        email_destino = email_destino_original
        aviso_teste = ""

    print(f"[DISPARO E-MAIL] (Modo Teste: {MODO_TESTE}) | Destino Real: {email_destino}\nMensagem:\n{mensagem}\n{'-' * 40}")

    return f"""
    <!DOCTYPE html>
    <html lang='pt-br'>
    <head><link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'></head>
    <body class='bg-light'><div class='container mt-5 text-center'>
        <div class='card shadow p-4 mx-auto' style='max-width: 500px;'>
            <h2>E-mail Processado!</h2>
            {aviso_teste}
            <p>A mensagem foi disparada para: <strong>{email_destino}</strong></p>
            <a href='javascript:history.back()' class='btn btn-primary mt-3'>Voltar para Revisão</a>
        </div>
    </div></body></html>
    """


@main_bp.route("/enviar-whatsapp", methods=["POST"])
def enviar_whatsapp():
    # Processa o disparo de WhatsApp respeitando o Modo de Homologação
    empresa_id = request.form.get("empresa_id")
    telefone_destino_original = request.form.get("contato")
    mensagem = request.form.get("mensagem")

    if MODO_TESTE:
        telefone_destino = WHATSAPP_TESTE
        aviso_teste = f"<div class='alert alert-warning'><strong>[MODO DE TESTE ATIVO]</strong> O WhatsApp original era para: <i>{telefone_destino_original}</i>, mas foi redirecionado com segurança para o seu número de teste.</div>"
    else:
        telefone_destino = telefone_destino_original
        aviso_teste = ""

    print(f"[DISPARO WHATSAPP] (Modo Teste: {MODO_TESTE}) | Destino Real: {telefone_destino}\nMensagem:\n{mensagem}\n{'-' * 40}")

    return f"""
    <!DOCTYPE html>
    <html lang='pt-br'>
    <head><link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'></head>
    <body class='bg-light'><div class='container mt-5 text-center'>
        <div class='card shadow p-4 mx-auto' style='max-width: 500px;'>
            <h2>WhatsApp Processado!</h2>
            {aviso_teste}
            <p>O disparo para o WhatsApp <strong>{telefone_destino}</strong> foi acionado.</p>
            <a href='javascript:history.back()' class='btn btn-success mt-3'>Voltar para Revisão</a>
        </div>
    </div></body></html>
    """