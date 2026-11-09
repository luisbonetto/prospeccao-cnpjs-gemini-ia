import os
import sqlite3


def get_db_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "leads.db")


def limpar_empresas_inativas():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"Erro: Banco de dados não encontrado em {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 60)
    print(" 🧹 LIMPEZA DE EMPRESAS NÃO ATIVAS (Mantendo apenas Situação '02' - Ativa)")
    print("=" * 60)

    try:
        # 1. Contar total antes da limpeza na tabela de estabelecimentos
        cursor.execute("SELECT COUNT(*) FROM estabelecimentos;")
        total_antes = cursor.fetchone()[0]
        print(f"Estabelecimentos totais antes da limpeza: {total_antes:,}")

        # 2. Contar quantos serão removidos (tudo o que for diferente de '02')
        cursor.execute("SELECT COUNT(*) FROM estabelecimentos WHERE situacao_cadastral != '02';")
        total_remover = cursor.fetchone()[0]
        print(f"Estabelecimentos inativos/baixados identificados para remoção: {total_remover:,}")

        if total_remover == 0:
            print("O banco já está limpo! Nenhuma empresa inativa encontrada.")
            conn.close()
            return

        # 3. Executar a exclusão na tabela estabelecimentos
        print("\nRemovendo estabelecimentos com situação cadastral diferente de '02'...")
        cursor.execute("DELETE FROM estabelecimentos WHERE situacao_cadastral != '02';")

        # 4. Opcional: Remover empresas órfãs na tabela 'empresas' que já não possuem nenhum estabelecimento ativo
        print("Removendo empresas órfãs (sem estabelecimentos vinculados)...")
        cursor.execute("""
            DELETE FROM empresas 
            WHERE cnpj_basico NOT IN (SELECT DISTINCT cnpj_basico FROM estabelecimentos);
        """)
        empresas_removidas = cursor.rowcount
        print(f"Empresas órfãs removidas: {empresas_removidas:,}")

        # Efetivar as alterações no banco
        conn.commit()
        print("\nLimpeza concluída com sucesso no banco de dados!")

        # 5. Otimizar e compactar o arquivo SQLite com VACUUM
        print("Compactando o banco de dados (VACUUM)... Isso pode demorar alguns segundos.")
        cursor.execute("VACUUM;")
        print("Banco compactado com sucesso!")

        # 6. Contagem final
        cursor.execute("SELECT COUNT(*) FROM estabelecimentos;")
        total_depois = cursor.fetchone()[0]
        print(f"\nEstabelecimentos ativos restantes no banco: {total_depois:,}")

    except Exception as e:
        conn.rollback()
        print(f"\nOcorreu um erro durante a limpeza: {e}")
    finally:
        conn.close()
        print("=" * 60)


if __name__ == "__main__":
    resposta = input(
        "Atenção: Esta operação irá excluir permanentemente do banco todos os registos que não sejam 'ATIVA' (02). Deseja continuar? (s/n): ")
    if resposta.lower() == 's':
        limpar_empresas_inativas()
    else:
        print("Operação cancelada pelo usuário.")