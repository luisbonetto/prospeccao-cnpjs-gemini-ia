import os
import sqlite3

def get_db_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "leads.db")

def analisar_estrutura():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"Erro: Banco de dados não encontrado em {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 60)
    print(" 📊 ANÁLISE DA ESTRUTURA DO BANCO DE DADOS (leads.db)")
    print("=" * 60)

    # Listar todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = cursor.fetchall()

    for tabela in tabelas:
        nome_tabela = tabela[0]
        print(f"\n📂 Tabela: [ {nome_tabela} ]")
        print("-" * 50)

        # Informações das colunas
        cursor.execute(f"PRAGMA table_info('{nome_tabela}');")
        colunas = cursor.fetchall()
        print("Colunas:")
        for col in colunas:
            # col: (cid, name, type, notnull, dflt_value, pk)
            pk_status = " (Chave Primária)" if col[5] > 0 else ""
            null_status = " NOT NULL" if col[3] == 1 else ""
            print(f"  - {col[1]} ({col[2]}){null_status}{pk_status}")

        # Informações de índices
        cursor.execute(f"PRAGMA index_list('{nome_tabela}');")
        indices = cursor.fetchall()
        print("\nÍndices:")
        if indices:
            for idx in indices:
                # idx: (seq, name, unique, origin, partial)
                idx_nome = idx[1]
                unique_status = "Unique" if idx[2] == 1 else "Normal"
                print(f"  - {idx_nome} ({unique_status})")
        else:
            print("  - Nenhum índice personalizado encontrado.")

        # Contagem de registos
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {nome_tabela};")
            total = cursor.fetchone()[0]
            print(f"\nTotal de Registros: {total:,}")
        except Exception as e:
            print(f"\nNão foi possível contar os registos: {e}")

        print("=" * 60)

    conn.close()

if __name__ == "__main__":
    analisar_estrutura()