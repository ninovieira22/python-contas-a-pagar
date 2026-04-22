import glob
import json
import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMPORTS_DIR = os.path.join(BASE_DIR, "imports")


def migrar_dados():
    mapa_final = {}
    arquivos = glob.glob(os.path.join(IMPORTS_DIR, "**", "*Controle*"), recursive=True)
    arquivos += glob.glob(os.path.join(IMPORTS_DIR, "**", "*gastos*"), recursive=True)
    arquivos = list(set([f for f in arquivos if f.endswith((".xlsx", ".csv"))]))

    if not arquivos:
        print("Nenhum arquivo .xlsx ou .csv encontrado na pasta imports.")
        return

    print(f"Analisando {len(arquivos)} arquivos...")

    for arquivo in arquivos:
        try:
            if arquivo.endswith(".xlsx"):
                df = pd.read_excel(arquivo)
            else:
                df = pd.read_csv(arquivo, on_bad_lines="skip")

            df = df.dropna(how="all", axis=0).dropna(how="all", axis=1)

            col_titulo = None
            col_categoria = None

            for col in df.columns:
                col_str = str(col).lower()
                if "title" in col_str or "descri" in col_str:
                    col_titulo = col
                if "categoria" in col_str:
                    col_categoria = col

            if not col_titulo or not col_categoria:
                for col in df.columns:
                    amostra = df[col].astype(str).str.lower()
                    if any(amostra.str.contains("amazon|uber|99food|ifood", na=False)):
                        col_titulo = col
                    if any(amostra.str.contains("mercado|pedro|vitória|vitoria|gatos", na=False)):
                        col_categoria = col

            if col_titulo is not None and col_categoria is not None:
                dados = df[[col_titulo, col_categoria]].dropna()
                for _, row in dados.iterrows():
                    titulo = str(row[col_titulo]).strip()
                    categoria = str(row[col_categoria]).strip()
                    if categoria and categoria.lower() not in ["nan", "categoria", "-", "total"]:
                        mapa_final[titulo] = categoria
                print(f"Sucesso: {os.path.basename(arquivo)} ({len(dados)} itens)")
            else:
                print(f"Não identifiquei as colunas de dados em: {os.path.basename(arquivo)}")

        except Exception as exc:
            print(f"Erro em {os.path.basename(arquivo)}: {exc}")

    if mapa_final:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, "aprendizado_manual.json"), "w", encoding="utf-8") as f:
            json.dump(mapa_final, f, indent=4, ensure_ascii=False)
        print(f"\nFinalizado! {len(mapa_final)} itens salvos no dicionário.")
    else:
        print("\nNenhum dado foi extraído. Verifique o conteúdo dos arquivos.")


if __name__ == "__main__":
    migrar_dados()
