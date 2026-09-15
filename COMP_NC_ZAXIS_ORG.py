import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

# Configuração inicial do tema da interface
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class ValidadorNCCApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Validador de G-Code (Nome, Espessura e Origem Z)")
        self.geometry("820x620")
        self.minsize(700, 500)

        # --- TÍTULO ---
        self.label_titulo = ctk.CTkLabel(
            self,
            text="Validador Completo Aspire/Masso (Nome vs Parâmetros)",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.label_titulo.pack(pady=(20, 10))

        # --- FRAME DE SELEÇÃO DE PASTA ---
        self.frame_topo = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_topo.pack(fill="x", padx=20, pady=10)

        self.entry_caminho = ctk.CTkEntry(
            self.frame_topo,
            placeholder_text="Selecione ou cole o caminho da pasta com os arquivos (.nc, .tap, .txt)...",
            height=35,
        )
        self.entry_caminho.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_procurar = ctk.CTkButton(
            self.frame_topo,
            text="Procurar Pasta",
            width=130,
            height=35,
            command=self.selecionar_pasta,
        )
        self.btn_procurar.pack(side="right")

        # --- BOTÃO DE EXECUTAR VALIDAÇÃO ---
        self.btn_validar = ctk.CTkButton(
            self,
            text="Iniciar Validação Completa",
            height=40,
            fg_color="#2fa572",
            hover_color="#248f5f",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.executar_validacao,
        )
        self.btn_validar.pack(fill="x", padx=20, pady=10)

        # --- ÁREA DE LOG / RESULTADOS ---
        self.caixa_texto = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.caixa_texto.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        # Configuração das Cores (Usando _textbox atualizado do CustomTkinter)
        self.caixa_texto._textbox.tag_config("azul", foreground="#3498db")      # Azul para Espessura / Info
        self.caixa_texto._textbox.tag_config("vermelho", foreground="#e74c3c")  # Vermelho para Erros / Origem Z errada
        self.caixa_texto._textbox.tag_config("verde", foreground="#2ecc71")     # Verde para Sucesso
        self.caixa_texto._textbox.tag_config("cinza", foreground="#95a5a6")     # Cinza para divisores/nomes

        self.caixa_texto.insert(
            "0.1", "Aguardando seleção da pasta para iniciar...\n"
        )

    def selecionar_pasta(self):
        caminho = filedialog.askdirectory()
        if caminho:
            self.entry_caminho.delete(0, tk.END)
            self.entry_caminho.insert(0, caminho)

    def extrair_espessura_nome(self, nome_arquivo):
        match = re.search(r"(\d+)\s*mm", nome_arquivo, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None

    def extrair_dados_arquivo(self, caminho_completo):
        z_material = None
        primeiro_z = None

        try:
            with open(caminho_completo, "r", encoding="latin-1", errors="ignore") as f:
                linhas = f.readlines()

            for linha in linhas:
                if z_material is None:
                    match_z_mat = re.search(r'Z\s*=\s*([\d\.]+)', linha, re.IGNORECASE)
                    if match_z_mat:
                        z_material = float(match_z_mat.group(1))

                if primeiro_z is None:
                    match_g00_z = re.search(r'G00\s+Z([\d.]+)', linha)
                    if match_g00_z:
                        primeiro_z = float(match_g00_z.group(1))

        except Exception as e:
            return None, None, str(e)

        return z_material, primeiro_z, None

    def executar_validacao(self):
        pasta_arquivos = self.entry_caminho.get().strip()

        if not pasta_arquivos or not os.path.exists(pasta_arquivos):
            messagebox.showerror(
                "Erro", "Por favor, selecione um caminho de pasta válido."
            )
            return

        self.caixa_texto.delete("0.1", tk.END)
        self.inserir_colorido(f"--- Analisando pasta: {pasta_arquivos} ---\n\n", "cinza")

        extensoes_validas = ('.nc', '.tap', '.txt')
        arquivos_validos = [
            f for f in os.listdir(pasta_arquivos) if f.lower().endswith(extensoes_validas)
        ]

        if not arquivos_validos:
            self.inserir_colorido("⚠️ Nenhum arquivo compatível (.nc, .tap, .txt) encontrado nesta pasta.\n", "vermelho")
            return

        erros_totais = 0
        total_analisados = 0

        for arquivo in arquivos_validos:
            total_analisados += 1
            caminho_completo = os.path.join(pasta_arquivos, arquivo)
            
            espessura_nome = self.extrair_espessura_nome(arquivo)
            z_material, primeiro_z, erro_leitura = self.extrair_dados_arquivo(caminho_completo)

            if erro_leitura:
                self.inserir_colorido(f"Arquivo: {arquivo}\n", "cinza")
                self.inserir_colorido(f"❌ Erro ao ler arquivo: {erro_leitura}\n", "vermelho")
                self.inserir_colorido("-" * 70 + "\n", "cinza")
                erros_totais += 1
                continue

            status_linhas = []
            arquivo_tem_erro = False

            # Check 1: Espessura (Azul se OK, Vermelho se erro)
            if espessura_nome is None:
                status_linhas.append(("⚠️ ATENÇÃO: Espessura não identificada no NOME do arquivo.", "vermelho"))
                arquivo_tem_erro = True
            elif z_material is None:
                status_linhas.append(("⚠️ ATENÇÃO: Parâmetro 'Z=' do material não encontrado no cabeçalho.", "vermelho"))
                arquivo_tem_erro = True
            elif espessura_nome == z_material:
                status_linhas.append((f"✅ ESPESSURA OK (Nome: {espessura_nome}mm == Z Material: {z_material}mm)", "azul"))
            else:
                status_linhas.append((f"❌ DIVERGÊNCIA DE ESPESSURA! Nome: {espessura_nome}mm | Z Material: {z_material}mm", "vermelho"))
                arquivo_tem_erro = True

            # Check 2: Origem Z (Verde se OK, Vermelho se erro)
            if z_material is not None and primeiro_z is not None:
                limite_minimo_mesa = z_material + 15.0  

                if primeiro_z < limite_minimo_mesa:
                    status_linhas.append((f"❌ ORIGEM Z ERRADA: O zero está NA SUPERFÍCIE! (1º Z muito baixo: {primeiro_z}mm para chapa de {z_material}mm)", "vermelho"))
                    arquivo_tem_erro = True
                else:
                    status_linhas.append((f"✅ ORIGEM Z OK: Base da máquina correta (1º Z: {primeiro_z}mm)", "verde"))
            else:
                status_linhas.append(("⚠️ ATENÇÃO: Não foi possível verificar o primeiro movimento de Z (G00 Z).", "vermelho"))

            if arquivo_tem_erro:
                erros_totais += 1

            # Exibição colorida na interface
            self.inserir_colorido(f"Arquivo: {arquivo}\n", "cinza")
            for texto_linha, cor_tag in status_linhas:
                self.inserir_colorido(f"  -> {texto_linha}\n", cor_tag)
            self.inserir_colorido("-" * 70 + "\n", "cinza")

        self.inserir_colorido(
            f"\nResumo Final: {total_analisados} arquivo(s) analisado(s). Arquivos com alertas/erros: {erros_totais}\n",
            "vermelho" if erros_totais > 0 else "verde"
        )

    def inserir_colorido(self, texto, tag):
        # Insere o texto na caixa utilizando a tag de cor correspondente no widget interno atualizado
        self.caixa_texto._textbox.insert("end", texto, tag)
        self.caixa_texto._textbox.see("end")


if __name__ == "__main__":
    app = ValidadorNCCApp()
    app.mainloop()
