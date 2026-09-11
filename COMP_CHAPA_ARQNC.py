import os
import re

# Caminho da pasta onde estão os arquivos .nc
pasta_arquivos = r"\\SERVER\Dados\PROJETOS COM DOC PARA PRODUCAO\2026\003 - MARÇO\008 - PV 298 GIOVANA\4 - ARQUIVOS CUT\LOTE COMPLETO\GIOVANA ROSETO PV.298\2D\DXF_Nesting"

print(f"--- Analisando arquivos .nc e validando o parâmetro Z ---\n")


def extrair_espessura_nome(nome_arquivo):
  # Extrai o número que vem antes de 'mm' no nome do arquivo
  match = re.search(r"(\d+)\s*mm", nome_arquivo, re.IGNORECASE)
  if match:
    return float(match.group(1))
  return None


def extrair_z_material(cabecalho_texto):
  # Procura especificamente pelo padrão Z= valor dentro do cabeçalho
  match = re.search(r"Z\s*=\s*([\d\.]+)", cabecalho_texto, re.IGNORECASE)
  if match:
    return float(match.group(1))
  return None


for arquivo in os.listdir(pasta_arquivos):
  if arquivo.lower().endswith(".nc"):
    caminho_completo = os.path.join(pasta_arquivos, arquivo)

    # 1. Pega a espessura informada no nome do arquivo (ex: 6 em "6mm")
    espessura_nome = extrair_espessura_nome(arquivo)

    # 2. Lê as primeiras 25 linhas do arquivo .nc (onde fica o bloco Material Size)
    cabecalho_texto = ""
    try:
      with open(caminho_completo, "r", encoding="utf-8", errors="ignore") as f:
        for i in range(25):
          linha = f.readline()
          if not linha:
            break
          cabecalho_texto += linha + "\n"
    except Exception as e:
      print(f"Erro ao ler {arquivo}: {e}")
      continue

    # 3. Pega o valor real de Z no Material Size (ex: 18.0)
    z_material = extrair_z_material(cabecalho_texto)

    # 4. Compara o Nome vs o Z do Material Size
    if espessura_nome is None:
      status = "⚠️ ATENÇÃO: Não foi possível identificar a espessura no NOME."
    elif z_material is None:
      status = (
          "⚠️ ATENÇÃO: Não foi encontrado o parâmetro 'Z=' no cabeçalho do"
          " arquivo."
      )
    elif espessura_nome == z_material:
      status = (
          f"✅ APROVADO (Nome: {espessura_nome}mm confere com Z: {z_material}mm)"
      )
    else:
      status = (
          f"❌ ERRO DE DIVERGÊNCIA! O nome diz {espessura_nome}mm, mas a espessura"
          f" real da chapa no código é Z={z_material}mm!"
      )

    print(f"Arquivo: {arquivo}")
    print(f"Status: {status}\n" + "-" * 60)
