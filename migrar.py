import pandas as pd
import json
import glob
import os

def migrar_dados():
    mapa_final = {}
    # Busca arquivos Excel (.xlsx) e CSV (.csv) que contenham "Controle" ou "gastos"
    arquivos = glob.glob("*Controle*") + glob.glob("*gastos*")
    # Remove duplicados e o próprio script da lista
    arquivos = list(set([f for f in arquivos if f.endswith(('.xlsx', '.csv'))]))

    if not arquivos:
        print("❌ Nenhum arquivo .xlsx ou .csv encontrado na pasta!")
        return

    print(f"🔎 Analisando {len(arquivos)} arquivos...")

    for arquivo in arquivos:
        try:
            # Lê conforme a extensão
            if arquivo.endswith('.xlsx'):
                df = pd.read_excel(arquivo)
            else:
                df = pd.read_csv(arquivo, on_bad_lines='skip')

            # Limpeza: remove colunas e linhas totalmente vazias
            df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
            
            # Tenta encontrar as colunas certas analisando o conteúdo de cada uma
            col_titulo = None
            col_categoria = None

            # Procura nas colunas existentes
            for col in df.columns:
                col_str = str(col).lower()
                if 'title' in col_str or 'descri' in col_str: col_titulo = col
                if 'categoria' in col_str: col_categoria = col

            # Se não achou pelo cabeçalho, tenta olhar a primeira linha de dados
            if not col_titulo or not col_categoria:
                for col in df.columns:
                    amostra = df[col].astype(str).str.lower()
                    if any(amostra.str.contains('amazon|uber|99food|ifood', na=False)):
                        col_titulo = col
                    if any(amostra.str.contains('mercado|pedro|vitória|gatos', na=False)):
                        col_categoria = col

            if col_titulo is not None and col_categoria is not None:
                # Extrai os dados
                dados = df[[col_titulo, col_categoria]].dropna()
                for _, row in dados.iterrows():
                    t = str(row[col_titulo]).strip()
                    c = str(row[col_categoria]).strip()
                    if c and c.lower() not in ['nan', 'categoria', '-', 'total']:
                        mapa_final[t] = c
                print(f"✅ Sucesso: {arquivo} ({len(dados)} itens)")
            else:
                print(f"⚠️ Não identifiquei as colunas de dados em: {arquivo}")

        except Exception as e:
            print(f"❌ Erro em {arquivo}: {e}")

    if mapa_final:
        with open('aprendizado_manual.json', 'w', encoding='utf-8') as f:
            json.dump(mapa_final, f, indent=4, ensure_ascii=False)
        print(f"\n🚀 Finalizado! {len(mapa_final)} itens salvos no seu dicionário.")
    else:
        print("\n❌ Falha total: Nenhum dado foi extraído. Verifique se os arquivos estão abertos no Excel (feche-os antes).")

if __name__ == "__main__":
    migrar_dados()