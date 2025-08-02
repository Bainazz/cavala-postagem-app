import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from PIL import Image, ImageTk, ImageOps
from tkinter.font import Font
import re

BASE = os.path.dirname(os.path.abspath(__file__))

def carregar_cartas(diretorio):
    cartas = {}
    for root, _, files in os.walk(diretorio):
        for fname in files:
            if fname.endswith('.json'):
                path = os.path.join(root, fname)
                with open(path, encoding='utf-8') as f:
                    dados = json.load(f)
                    nome = dados['nome']
                    cartas[nome] = dados
    return cartas

def carregar_cavalas(diretorio):
    cavalas = {}
    for fname in os.listdir(diretorio):
        if fname.endswith('.json'):
            path = os.path.join(diretorio, fname)
            with open(path, encoding='utf-8') as f:
                dados = json.load(f)
                nome = dados['nome']
                cavalas[nome] = dados
    return cavalas


class EventoExpandivel(tk.Frame):
    def __init__(self, master, titulo, detalhes, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.aberto = False

        # Botão com fundo #1a1a1a e texto branco
        self.botao = tk.Button(self, text=f"▶ {titulo}", anchor="center", command=self.toggle, justify="center",
                               fg='white', bg='#1a1a1a', activebackground='#333333', activeforeground='white', bd=0)
        self.botao.pack(fill='x')
        self.botao.update_idletasks()
        self.botao.config(width=int(4000 / self.botao.winfo_fpixels('1c')))

        self.frame = tk.Frame(self, bg='#324b4c')

        texto = '\n'.join(detalhes) if isinstance(detalhes, list) else detalhes

        self.text_widget = tk.Text(
            self.frame,
            wrap='word',
            height=1,
            width=50,
            borderwidth=0,
            background='#324b4c',
            fg='white',
            insertbackground='white',
            padx=10,
            pady=5
        )
        self.text_widget.pack(fill='both', expand=True)
        self.text_widget.config(state='normal')

        font_normal = Font(family="Arial", size=10)
        font_bold = Font(family="Arial", size=10, weight="bold")

        # Tags de formatação com texto branco
        self.text_widget.tag_configure("normal", font=font_normal, justify='center', foreground='white')
        self.text_widget.tag_configure("bold", font=font_bold, justify='center', foreground='#ffff99')

        pattern = re.compile(r"\\033\[1m(.*?)\\033\[0m", re.DOTALL)

        pos = 0
        for match in pattern.finditer(texto):
            antes = texto[pos:match.start()]
            if antes:
                self.text_widget.insert('end', antes, ("normal",))
            em_negrito = match.group(1)
            self.text_widget.insert('end', em_negrito, ("bold",))
            pos = match.end()

        resto = texto[pos:]
        if resto:
            self.text_widget.insert('end', resto, ("normal",))

        self.text_widget.config(state='disabled')

        # Ajusta altura automaticamente conforme o conteúdo
        self.text_widget.update_idletasks()
        num_linhas = int(self.text_widget.index('end-1c').split('.')[0])
        self.text_widget.config(height=num_linhas)

    def toggle(self):
        if self.aberto:
            self.frame.pack_forget()
            self.botao.config(text=f"▶ {self.botao.cget('text')[2:]}")
            self.aberto = False
        else:
            for child in self.master.winfo_children():
                if isinstance(child, EventoExpandivel) and child != self and child.aberto:
                    child.toggle()
            self.frame.pack(fill='x')
            self.botao.config(text=f"▼ {self.botao.cget('text')[2:]}")
            self.aberto = True


class UmaApp:
    def __init__(self, root, cartas_data, cavalas_data):
        self.c = cartas_data
        self.cv = cavalas_data
        self.deck = []
        self.cavala_selecionada = None
        self.root = root
        root.title("UmaMusume Companion")

        # Aplica fundo cinza e texto branco no root
        root.configure(bg='#606060')

        # Botões com texto branco e fundo #1a1a1a
        btn_style = {'fg': 'white', 'bg': '#1a1a1a', 'activebackground': '#333333', 'activeforeground': 'white', 'bd': 0}

        self.btn_cavala = tk.Button(root, text="Escolha sua cavala", command=self.abrir_seletor_cavala, **btn_style)
        self.btn_cavala.pack(pady=5)

        self.btn_cartas = tk.Button(root, text="Escolha suas cartas", command=self.abrir_seletor_cartas, **btn_style)
        self.btn_cartas.pack(pady=5)

        self.lista = tk.Listbox(root, height=6, bg='#606060', fg='white', bd=0, selectbackground='#333333', selectforeground='white')
        self.lista.pack()

        self.btn_limpar = tk.Button(root, text="Limpar Deck", command=self.limpar_eventos, **btn_style)
        self.btn_limpar.pack(pady=2)

        self.frame_exibicao = tk.Frame(root, bg='#606060')
        self.frame_exibicao.pack(pady=10)

        # --- SCROLLABLE EVENTOS ---
        self.canvas_eventos = tk.Canvas(root, height=300, bg='#606060', highlightthickness=0)
        self.scroll_eventos = ttk.Scrollbar(root, orient='vertical', command=self.canvas_eventos.yview)
        self.canvas_eventos.configure(yscrollcommand=self.scroll_eventos.set)

        self.canvas_eventos.pack(side='left', fill='both', expand=True, padx=(10, 0))
        self.scroll_eventos.pack(side='right', fill='y')

        self.wrapper_eventos = tk.Frame(self.canvas_eventos, bg='#606060')
        self.wrapper_id = self.canvas_eventos.create_window((0, 0), window=self.wrapper_eventos, anchor='n')

        self.frame_eventos = tk.Frame(self.wrapper_eventos, bg='#606060')
        self.frame_eventos.pack(anchor='n', pady=10)

        def on_frame_configure(event):
            self.canvas_eventos.configure(scrollregion=self.canvas_eventos.bbox("all"))

        self.wrapper_eventos.bind("<Configure>", on_frame_configure)

        def on_canvas_configure(event):
            canvas_width = event.width
            self.canvas_eventos.itemconfig(self.wrapper_id, width=canvas_width)

        self.canvas_eventos.bind("<Configure>", on_canvas_configure)

        def on_mousewheel(event):
            canvas_height = self.canvas_eventos.winfo_height()
            content_height = self.wrapper_eventos.winfo_height()
            if content_height > canvas_height:
                self.canvas_eventos.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.canvas_eventos.bind("<Enter>", lambda e: self.canvas_eventos.bind_all("<MouseWheel>", on_mousewheel))
        self.canvas_eventos.bind("<Leave>", lambda e: self.canvas_eventos.unbind_all("<MouseWheel>"))

        self.imagens_exibidas = {}
        self.evento_expandido_atual = None
        self.img_refs = {}  # para manter referências das imagens PhotoImage
        self.selecionado = None  # imagem selecionada atualmente: 'cavala' ou nome_carta
        
    def abrir_seletor_cavala(self):
        if hasattr(self, 'janela_cavala_aberta') and self.janela_cavala_aberta:
            return

        self.janela_cavala_aberta = True
        win = tk.Toplevel(self.root)
        win.title("Selecione sua Cavala")
        win.configure(bg='#606060')

        largura = 1080
        altura = 850

        self.root.update_idletasks()
        geom = self.root.winfo_geometry()
        pos = '+' + geom.split('+')[1] + '+' + geom.split('+')[2]
        win.geometry(f"{largura}x{altura}{pos}")
        win.transient(self.root)
        win.grab_set()
        win.focus_force()

        win.protocol("WM_DELETE_WINDOW", lambda: [win.destroy(), setattr(self, 'janela_cavala_aberta', False)])

        # Canvas com scrollbar visível
        canvas = tk.Canvas(win, bg='#606060', highlightthickness=0)
        scrollbar = ttk.Scrollbar(win, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas e scrollbar lado a lado
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        frame = tk.Frame(canvas, bg='#606060')
        janela_id = canvas.create_window((0, 0), window=frame, anchor='nw')

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        frame.bind("<Configure>", on_configure)

        def on_canvas_configure(event):
            # Ajusta largura do frame interno para largura do canvas
            canvas.itemconfig(janela_id, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        def on_mousewheel(event):
            # Scroll limitado para não passar do topo
            current = canvas.yview()
            if (event.delta > 0 and current[0] <= 0) or (event.delta < 0 and current[1] >= 1):
                return "break"
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"

        def bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", on_mousewheel)
            canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        def unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", bind_mousewheel)
        canvas.bind("<Leave>", unbind_mousewheel)

        linha = 0
        coluna = 0
        max_colunas = 7

        # Configura grid para centralizar colunas
        for col in range(max_colunas):
            frame.grid_columnconfigure(col, weight=1)

        for nome, dados in self.cv.items():
            caminho_img = os.path.join(BASE, dados.get("imagem", ""))
            try:
                pil_img = Image.open(caminho_img).convert("RGBA")
                bg = Image.new("RGBA", pil_img.size, "#606060")
                pil_img = Image.alpha_composite(bg, pil_img)
                img = ImageTk.PhotoImage(pil_img)
            except Exception as e:
                print(f"Erro ao carregar imagem de {nome}: {e}")
                continue

            def selecionar_cavala(n=nome):
                self.cavala_selecionada = n
                win.destroy()
                self.janela_cavala_aberta = False
                self.btn_cavala.config(text=f"Cavala selecionada: {n}")
                self.mostrar()

            frame_interno = tk.Frame(frame, bg='#606060')
            frame_interno.grid(row=linha, column=coluna, padx=10, pady=10)

            btn = tk.Button(frame_interno, image=img, command=selecionar_cavala, borderwidth=0, highlightthickness=0,
                            bg='#1a1a1a', activebackground='#333333')
            btn.image = img
            btn.pack()
            tk.Label(frame_interno, text=nome, fg='white', bg='#606060').pack()

            coluna += 1
            if coluna >= max_colunas:
                coluna = 0
                linha += 1



    def abrir_seletor_cartas(self):
        win = tk.Toplevel(self.root)
        win.title("Selecione suas Cartas")

        win.configure(bg='#606060')

        largura = 1080
        altura = 850

        self.root.update_idletasks()
        geom = self.root.winfo_geometry()
        pos = '+' + geom.split('+')[1] + '+' + geom.split('+')[2]
        win.geometry(f"{largura}x{altura}{pos}")
        win.transient(self.root)
        win.grab_set()
        win.focus_force()

        tipo_frame = tk.Frame(win, bg='#606060')
        tipo_frame.pack(pady=5)

        self.contador_var = tk.StringVar()
        self.contador_var.set(f"{len(self.deck)}/6 cartas selecionadas")
        label_contador = tk.Label(win, textvariable=self.contador_var, font=("Arial", 10, "bold"), fg='white', bg='#606060')
        label_contador.pack()

        canvas = tk.Canvas(win, bg='#606060', highlightthickness=0)
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        conteudo_frame = tk.Frame(canvas, bg='#606060')
        id_janela = canvas.create_window((largura//2, 0), window=conteudo_frame, anchor='n')

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        conteudo_frame.bind("<Configure>", on_configure)

        def on_canvas_configure(event):
            canvas.coords(id_janela, event.width//2, 0)
        canvas.bind("<Configure>", on_canvas_configure)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        self.botoes_cartas = {}

        def extrair_raridade(nome_arquivo):
            if nome_arquivo.endswith("_SSR.png"):
                return 0
            elif nome_arquivo.endswith("_SR.png"):
                return 1
            elif nome_arquivo.endswith("_R.png"):
                return 2
            return 3

        def mostrar_cartas_por_tipo(tipo):
            for widget in conteudo_frame.winfo_children():
                widget.destroy()
            self.botoes_cartas.clear()

            linha = 0
            coluna = 0
            max_colunas = 6

            cartas_filtradas = [
                (nome, dados) for nome, dados in self.c.items()
                if tipo in dados.get("imagem", "")
            ]
            cartas_ordenadas = sorted(cartas_filtradas, key=lambda item: extrair_raridade(item[1].get("imagem", "")))

            for nome, dados in cartas_ordenadas:
                img_path = os.path.join(BASE, dados.get("imagem", ""))
                try:
                    pil_image = Image.open(img_path).convert("RGBA")
                    bg = Image.new("RGBA", pil_image.size, "#606060")
                    pil_image_colorida = Image.alpha_composite(bg, pil_image)
                    pil_image_cinza = ImageOps.grayscale(pil_image_colorida.convert("RGB"))
                    img_colorida = ImageTk.PhotoImage(pil_image_colorida)
                    img_cinza = ImageTk.PhotoImage(pil_image_cinza)
                except Exception as e:
                    print(f"Erro ao carregar imagem da carta {nome}: {e}")
                    continue

                def alternar_carta(n=nome, btn_ref=None, colorida=None, cinza=None):
                    if n in self.deck:
                        self.deck.remove(n)
                        self.lista.delete(0, 'end')
                        for carta in self.deck:
                            self.lista.insert('end', carta)
                        btn_ref.config(image=cinza)
                        btn_ref.image = cinza
                    elif len(self.deck) < 6:
                        self.deck.append(n)
                        self.lista.insert('end', n)
                        btn_ref.config(image=colorida)
                        btn_ref.image = colorida

                    self.contador_var.set(f"{len(self.deck)}/6 cartas selecionadas")
                    self.mostrar()

                    if len(self.deck) == 6:
                        win.after(400, win.destroy)

                frame = tk.Frame(conteudo_frame, bg='#606060')
                frame.grid(row=linha, column=coluna, padx=10, pady=10)

                imagem = img_colorida if nome in self.deck else img_cinza
                btn = tk.Button(frame, image=imagem, borderwidth=0, highlightthickness=0, bg='#1a1a1a', activebackground='#333333')
                btn.image = imagem
                btn.pack()
                tk.Label(frame, text=nome, fg='white', bg='#606060').pack()

                btn.config(command=lambda n=nome, b=btn, c=img_colorida, g=img_cinza: alternar_carta(n, b, c, g))

                coluna += 1
                if coluna >= max_colunas:
                    coluna = 0
                    linha += 1

        tipos = ['speed', 'wisdom', 'power', 'stamina', 'guts', 'pal']
        for tipo in tipos:
            try:
                icon_path = os.path.join(BASE, 'icon_tipos', f"{tipo}.png")
                icon = tk.PhotoImage(file=icon_path)
                btn = tk.Button(tipo_frame, image=icon, command=lambda t=tipo: mostrar_cartas_por_tipo(t),
                bg='#606060', activebackground='#333333', borderwidth=0, highlightthickness=0)
                btn.image = icon
                btn.pack(side='left', padx=2)
            except Exception as e:
                print(f"Erro ao carregar ícone do tipo {tipo}: {e}")

        mostrar_cartas_por_tipo('speed')

    def mostrar(self):
        for widget in self.frame_exibicao.winfo_children():
            widget.destroy()
        for widget in self.frame_eventos.winfo_children():
            widget.destroy()
        self.imagens_exibidas.clear()
        self.img_refs.clear()
        self.selecionado = None

        if not self.cavala_selecionada:
            messagebox.showwarning("Aviso", "Selecione uma cavala primeiro!")
            return

        dados_cavala = self.cv[self.cavala_selecionada]
        caminho_img_cavala = os.path.join(BASE, dados_cavala.get("imagem", ""))
        try:
            pil_img_cavala = Image.open(caminho_img_cavala)
            pil_img_cavala = pil_img_cavala.resize((128, 128), Image.Resampling.LANCZOS)
            img_colorida = ImageTk.PhotoImage(pil_img_cavala)
            img_cinza = ImageTk.PhotoImage(ImageOps.grayscale(pil_img_cavala))
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar a imagem da cavala: {e}")
            return

        frame_cavala = tk.Frame(self.frame_exibicao, bg='#606060')
        frame_cavala.pack(side='left', padx=10)

        def on_click_cavala():
            self.atualizar_selecao('cavala')

        btn_img = tk.Button(frame_cavala, image=img_cinza, borderwidth=0, command=on_click_cavala,
                    bg='#606060', activebackground='#505050')
        btn_img.image_colorida = img_colorida
        btn_img.image_cinza = img_cinza
        btn_img.pack()
        tk.Label(frame_cavala, text=self.cavala_selecionada, font=("Arial", 12, "bold"), fg='white', bg='#606060').pack()

        self.imagens_exibidas['cavala'] = btn_img
        self.img_refs['cavala_colorida'] = img_colorida
        self.img_refs['cavala_cinza'] = img_cinza

        frame_cartas = tk.Frame(self.frame_exibicao, bg='#606060')
        frame_cartas.pack(side='left', padx=20)

        for nome_carta in self.deck:
            dados_carta = self.c.get(nome_carta)
            if not dados_carta:
                continue
            caminho_img_carta = os.path.join(BASE, dados_carta.get("imagem", ""))
            try:
                pil_img_carta = Image.open(caminho_img_carta)
                pil_img_carta = pil_img_carta.resize((128, 128), Image.Resampling.LANCZOS)
                img_colorida = ImageTk.PhotoImage(pil_img_carta)
                img_cinza = ImageTk.PhotoImage(ImageOps.grayscale(pil_img_carta))
            except Exception as e:
                print(f"Erro ao carregar imagem da carta {nome_carta}: {e}")
                continue

            frame_carta = tk.Frame(frame_cartas, bg='#606060')
            frame_carta.pack(side='left', padx=5)

            def on_click_carta(n=nome_carta):
                self.atualizar_selecao(n)

            btn_img_carta = tk.Button(frame_carta, image=img_cinza, borderwidth=0, command=on_click_carta,
                         bg='#606060', activebackground='#505050')
            btn_img_carta.image_colorida = img_colorida
            btn_img_carta.image_cinza = img_cinza
            btn_img_carta.pack()
            tk.Label(frame_carta, text=nome_carta, fg='white', bg='#606060').pack()

            self.imagens_exibidas[nome_carta] = btn_img_carta
            self.img_refs[f'{nome_carta}_colorida'] = img_colorida
            self.img_refs[f'{nome_carta}_cinza'] = img_cinza

        # Ao mostrar pela primeira vez, nenhuma imagem está selecionada e todas ficam cinza
        self.selecionado = None
        self.mostrar_eventos(None)

    def atualizar_selecao(self, selecionado):
        # Atualiza as imagens para refletir seleção (colorida) ou não (cinza)
        if self.selecionado == selecionado:
            # Clicou na mesma imagem, mostra eventos novamente
            self.mostrar_eventos(selecionado)
            return

        # Atualizar a imagem antiga para cinza
        if self.selecionado is not None:
            btn_antigo = self.imagens_exibidas.get(self.selecionado)
            if btn_antigo:
                btn_antigo.config(image=btn_antigo.image_cinza)
                btn_antigo.image = btn_antigo.image_cinza

        # Atualizar a nova imagem para colorida
        btn_novo = self.imagens_exibidas.get(selecionado)
        if btn_novo:
            btn_novo.config(image=btn_novo.image_colorida)
            btn_novo.image = btn_novo.image_colorida
            self.selecionado = selecionado
            self.mostrar_eventos(selecionado)

    def mostrar_eventos(self, selecionado):
        for w in self.frame_eventos.winfo_children():
            w.destroy()

        if selecionado is None:
            return

        if selecionado == 'cavala':
            self.mostrar_eventos_cavala()
        else:
            self.mostrar_eventos_carta(selecionado)

    def mostrar_eventos_cavala(self):
        dados = self.cv[self.cavala_selecionada]

        for cat, eventos in dados.get("eventos", {}).items():
            # Título das categorias no formato -- nome -- em negrito branco
            tk.Label(self.frame_eventos, text=f"-- {cat} --", font=('Arial', 10, 'bold'),
                     fg='white', bg='#606060').pack(fill='x', pady=(10, 2))
            for ev in eventos:
                ev_expand = EventoExpandivel(self.frame_eventos, ev['nome'], ev['detalhes'])
                ev_expand.pack(fill='x', padx=10, pady=2)

    def mostrar_eventos_carta(self, nome_carta):
        dados_carta = self.c.get(nome_carta)
        if not dados_carta:
            return

        for cat, eventos in dados_carta.get("eventos", {}).items():
            # Título das categorias no formato -- nome -- em negrito branco
            tk.Label(self.frame_eventos, text=f"-- {cat} --", font=('Arial', 10, 'bold'),
                     fg='white', bg='#606060').pack(fill='x', pady=(6, 2))
            for ev in eventos:
                ev_expand = EventoExpandivel(self.frame_eventos, ev['nome'], ev['detalhes'])
                ev_expand.pack(fill='x', padx=10, pady=1)

    def limpar_eventos(self):
        self.deck = []
        self.lista.delete(0, 'end')
        for widget in self.frame_exibicao.winfo_children():
            widget.destroy()
        for widget in self.frame_eventos.winfo_children():
            widget.destroy()
        self.imagens_exibidas.clear()
        self.img_refs.clear()
        self.selecionado = None
        self.cavala_selecionada = None
        self.btn_cavala.config(text="Escolha sua cavala")


def criar_janela_centrada(largura, altura):
    root = tk.Tk()
    largura_tela = root.winfo_screenwidth()
    altura_tela = root.winfo_screenheight()
    pos_x = (largura_tela // 2) - (largura // 2)
    pos_y = (altura_tela // 2) - (altura // 2)
    root.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
    root.configure(bg='#606060')
    return root


if __name__ == "__main__":
    cartas = carregar_cartas(os.path.join(BASE, 'cartas'))
    cavalas = carregar_cavalas(os.path.join(BASE, 'cavalas'))

    root = criar_janela_centrada(1080, 850)
    app = UmaApp(root, cartas, cavalas)
    root.mainloop()
