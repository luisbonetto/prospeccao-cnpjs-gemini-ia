import os
import sqlite3
import zipfile
import urllib.request
import glob
import re

# Caminho base do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "leads.db")
PASTA_DADOS = os.path.join(BASE_DIR, "dados_rfb")

# URLs dos arquivos públicos de Dados Abertos da Receita Federal
# Filtramos apenas os arquivos essenciais de Empresas e Estabelecimentos
URL_BASE = "https://arquivos.receitafederal.gov.br/dados/receita/cnpj/dados_abertos_cnpj/"

def criar_estrutura_banco():
    """Cria a estrutura de tabelas e índices otimizados no SQLite."""
    print(f"[*] Criando/conectando ao banco de dados em: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela de Estabelecimentos (Apenas empresas com situação cadastral 02 = ATIVA)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estabelecimentos (
            cnpj_basico TEXT,
            cnpj_ordem TEXT,
            cnpj_dv TEXT,
            cnpj TEXT PRIMARY KEY,
            matriz_filial TEXT,
            nome_fantasia TEXT,
            situacao_cadastral TEXT,
            data_situacao_cadastral TEXT,
            motivo_situacao_cadastral TEXT,
            nome_cidade_exterior TEXT,
            pais TEXT,
            data_inicio_atividade TEXT,
            cnae_fiscal_principal TEXT,
            cnae_fiscal_secundaria TEXT,
            tipo_logradouro TEXT,
            logradouro TEXT,
            numero TEXT,
            complemento TEXT,
            bairro TEXT,
            cep TEXT,
            uf TEXT,
            municipio TEXT,
            ddd_1 TEXT,
            telefone_1 TEXT,
            ddd_2 TEXT,
            telefone_2 TEXT,
            ddd_fax TEXT,
            fax TEXT,
            correio_eletronico TEXT,
            situacao_especial TEXT,
            data_situacao_especial TEXT
        )
    """)

    # Tabela de Empresas (Razão Social principal)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            cnpj_basico TEXT PRIMARY KEY,
            razao_social TEXT,
            natureza_juridica TEXT,
            qualificacao_responsavel TEXT,
            capital_social TEXT,
            porte_empresa TEXT,
            ente_federativo_responsavel TEXT
        )
    """)

    # Tabela de Histórico de Disparos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_disparos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            razao_social TEXT,
            email_destino TEXT,
            modo_teste BOOLEAN,
            status TEXT,
            data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Índices para alta velocidade de busca na aplicação Flask
    print("[*] Criando índices de performance (UF, Município, CNAE, Razão Social)...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_estab_uf ON estabelecimentos(uf);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_estab_mun ON estabelecimentos(municipio);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_estab_cnae ON estabelecimentos(cnae_fiscal_principal);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_estab_situacao ON estabelecimentos(situacao_cadastral);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_emp_basico ON empresas(cnpj_basico);")

    conn.commit()
    conn.close()
    print("[+] Estrutura do banco de dados e índices criados com sucesso!")

def processar_e_inserir_dados():
    """
    Varre os arquivos extraídos da Receita Federal e insere no SQLite.
    REGRA DE NEGÓCIO: Insere APENAS empresas com situação cadastral '02' (ATIVA).
    """
    os.makedirs(PASTA_DADOS, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    arquivos_estab = glob.glob(os.path.join(PASTA_DADOS, "*ESTABELE*")) + glob.glob(os.path.join(PASTA_DADOS, "*.ESTAB*"))
    
    if not arquivos_estab:
        print(f"[!] Nenhum arquivo de Estabelecimentos encontrado na pasta '{PASTA_DADOS}'.")
        print("💡 Baixe os arquivos .zip de Estabelecimentos e Empresas da Receita Federal e extraia-os nesta pasta.")
        conn.close()
        return

    print("[*] Iniciando processamento dos arquivos com filtro de EMPRESAS ATIVAS (Código 02)...")

    total_inseridos = 0
    total_ignorados = 0

    for arquivo in arquivos_estab:
        print(f"  -> Processando arquivo: {os.path.basename(arquivo)}")
        with open(arquivo, 'r', encoding='latin-1', errors='ignore') as f:
            batch_estab = []
            for linha in f:
                campos = [c.strip('"') for c in linha.strip().split(';')]
                if len(campos) >= 30:
                    situacao_cadastral = campos[6]
                    
                    # FILTRO RÍGIDO: Apenas Ativas (02)
                    if situacao_cadastral == "02":
                        cnpj_basico = campos[0]
                        cnpj_ordem = campos[1]
                        cnpj_dv = campos[2]
                        cnpj_completo = f"{cnpj_basico}{cnpj_ordem}{cnpj_dv}"
                        
                        registro = (
                            cnpj_basico, cnpj_ordem, cnpj_dv, cnpj_completo,
                            campos[3], campos[4], situacao_cadastral, campos[7],
                            campos[8], campos[9], campos[10], campos[11],
                            campos[12], campos[13], campos[14], campos[15],
                            campos[16], campos[17], campos[18], campos[19],
                            campos[20], campos[21], campos[22], campos[23],
                            campos[24], campos[25], campos[26], campos[27],
                            campos[28], campos[29], campos[30] if len(campos) > 30 else ""
                        )
                        batch_estab.append(registro)
                        total_inseridos += 1
                    else:
                        total_ignorados += 1

                if len(batch_estab) >= 10000:
                    cursor.executemany("""
                        INSERT OR IGNORE INTO estabelecimentos VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    """, batch_estab)
                    conn.commit()
                    batch_estab = []

            if batch_estab:
                cursor.executemany("""
                    INSERT OR IGNORE INTO estabelecimentos VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, batch_estab)
                conn.commit()

    print(f"[✔] Importação concluída! {total_inseridos} estabelecimentos ATIVOS inseridos. ({total_ignorados} empresas inativas foram ignoradas).")
    conn.close()

if __name__ == "__main__":
    print("=== Pipeline Automático de Construção da Base de Dados RFB ===")
    criar_estrutura_banco()
    processar_e_inserir_dados()