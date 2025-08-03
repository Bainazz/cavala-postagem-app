import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from PIL import Image, ImageTk, ImageOps
from tkinter.font import Font
import re

BASE = os.path.dirname(os.path.abspath(__file__))

def carregar_jsons(diretorio, recursivo=False, tipo="item"):
    itens = {}
    if not os.path.isdir(diretorio):
        print(f"[AVISO] Diretório não encontrado: {diretorio}")
        return itens
    walker = os.walk(diretorio) if recursivo else [(diretorio, [], os.listdir(diretorio))]
    for root, _, files in walker:
        for fname in files:
            if not fname.endswith('.json'):
                continue
            path = os.path.join(root, fname)
            try:
                with open(path, encoding='utf-8') as f:
                    dados = json.load(f)
                nome = dados.get('nome')
                if not nome:
                    print(f"[AVISO] JSON sem 'nome': {path}")
                    continue
                if nome in itens:
                    print(f"[AVISO] {tipo} duplicado '{nome}' em {path}")
                itens[nome] = dados
            except Exception as e:
                print(f"[ERRO] Falha lendo {path}: {e}")
    return itens

def carregar_cartas(diretorio):
    return carregar_jsons(diretorio, recursivo=True, tipo="carta")

def carregar_cavalas(diretorio):
    return carregar_jsons(diretorio, recursivo=False, tipo="cavala")


class EventoExpandivel(tk.Frame):
    def __init__(self, master, titulo, detalhes, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.aberto = False

        self.configure(bg='#606060')

        self.botao = tk.Button(
            self,
            text=f"▶ {titulo}",
            anchor="center",
            command=self.toggle,
            justify="center",
            fg='white',
            bg='#1a1a1a',
            activebackground='#333333',
            activeforeground='white',
            bd=0
        )
        self.botao.pack(fill='x')

        self.botao.update_idletasks()
        try:
            self.botao.config(width=int(4000 / self.botao.winfo_fpixels('1c')))
        except Exception:
            self.botao.config(width=200)

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
            padx=14,
            pady=7
        )
        self.text_widget.pack(fill='both', expand=True)
        self.text_widget.config(state='normal')

        font_normal = Font(family="Arial", size=10)
        font_bold = Font(family="Arial", size=10, weight="bold")

        self.text_widget.tag_configure("normal", font=font_normal, justify='center', foreground='white')
        self.text_widget.tag_configure("bold", font=font_bold, justify='center', foreground='#ffff99')

        patterns = [
            re.compile(r"\033\[1m(.*?)\033\[0m", re.DOTALL),
            re.compile(r"\\033\[1m(.*?)\\033\[0m", re.DOTALL),
        ]

        applied = False
        for pattern in patterns:
            pos = 0
            any_match = False
            for match in pattern.finditer(texto):
                any_match = True
                antes = texto[pos:match.start()]
                if antes:
                    self.text_widget.insert('end', antes, ("normal",))
                em_negrito = match.group(1)
                self.text_widget.insert('end', em_negrito, ("bold",))
                pos = match.end()
            if any_match:
                resto = texto[pos:]
                if resto:
                    self.text_widget.insert('end', resto, ("normal",))
                applied = True
                break

        if not applied:
            self.text_widget.insert('end', texto, ("normal",))

        self.text_widget.config(state='disabled')

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
        self.carta_avulsa = None
        self.cavala_selecionada = None
        self.root = root
        root.title("UmaMusume Companion")
        root.configure(bg='#606060')

        # Estilo base de cores
        self.btn_style = {
            'fg': 'white', 'bg': '#1a1a1a',
            'activebackground': '#333333', 'activeforeground': 'white'
        }

        # Barra superior com slots
        self.top_bar = tk.Frame(root, bg='#606060')
        self.top_bar.pack(pady=8)

        self.slot_cavala = tk.Frame(self.top_bar, bg='#606060')
        self.slot_cavala.pack(side='left', padx=6)
        self.slot_cartas = tk.Frame(self.top_bar, bg='#606060')
        self.slot_cartas.pack(side='left', padx=6)
        self.slot_avulsa = tk.Frame(self.top_bar, bg='#606060')
        self.slot_avulsa.pack(side='left', padx=6)

        # Botões iniciais
        self.btn_cavala = self.criar_botao_arredondado(
            self.slot_cavala, "Escolha sua cavala", comando=self.abrir_seletor_cavala, min_w=180, min_h=40
        )
        self.btn_cavala.pack()

        self.btn_cartas = self.criar_botao_arredondado(
            self.slot_cartas, "Escolha suas cartas", comando=self.abrir_seletor_cartas, min_w=190, min_h=40
        )
        self.btn_cartas.pack()

        self.btn_carta_avulsa = self.criar_botao_arredondado(
            self.slot_avulsa, "Carta avulsa", comando=self.abrir_seletor_carta_avulsa, min_w=140, min_h=40
        )
        self.btn_carta_avulsa.pack()

        # Painel principal arredondado
        self.area_cor = '#505050'
        self.area_border = '#6a6a6a'
        self.area_canvas = tk.Canvas(root, bg='#606060', highlightthickness=0, bd=0)
        self.area_canvas.pack(padx=10, pady=(6, 14), fill='x')
        self.area_radius = 18
        self.area_pad = 8

        self.frame_exibicao = tk.Frame(self.area_canvas, bg=self.area_cor)
        self._area_window = self.area_canvas.create_window((0, 0), window=self.frame_exibicao, anchor='n')

        def _redesenhar_area(event=None):
            w = self.area_canvas.winfo_width()
            h = max(self.frame_exibicao.winfo_reqheight() + 2 * self.area_pad, 160)
            self.area_canvas.config(height=h)
            self.area_canvas.coords(self._area_window, w // 2, self.area_pad)
            self.area_canvas.itemconfig(self._area_window, width=w - 2 * self.area_pad)
            self._desenhar_roundrect(self.area_canvas, 1, 1, w - 2, h - 2, self.area_radius, fill=self.area_cor, outline=self.area_border, width=1)

        self.area_canvas.bind("<Configure>", _redesenhar_area)
        self.frame_exibicao.bind("<Configure>", _redesenhar_area)

        # Botão reset
        self.btn_reset = self.criar_botao_arredondado(
            root, "Resetar escolhas", comando=self.resetar_escolhas, min_w=160, min_h=40
        )
        self.btn_reset.pack(pady=(2, 8))

        # Eventos + scrollbar
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
            self.canvas_eventos.itemconfig(self.wrapper_id, width=event.width)
        self.canvas_eventos.bind("<Configure>", on_canvas_configure)

        def on_mousewheel(event):
            if hasattr(event, "delta") and event.delta:
                self.canvas_eventos.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return "break"

        def on_button4(event):
            self.canvas_eventos.yview_scroll(-1, "units")
            return "break"

        def on_button5(event):
            self.canvas_eventos.yview_scroll(1, "units")
            return "break"

        def bind_mousewheel(_):
            self.canvas_eventos.bind("<MouseWheel>", on_mousewheel)
            self.canvas_eventos.bind("<Button-4>", on_button4)
            self.canvas_eventos.bind("<Button-5>", on_button5)

        def unbind_mousewheel(_):
            self.canvas_eventos.unbind("<MouseWheel>")
            self.canvas_eventos.unbind("<Button-4>")
            self.canvas_eventos.unbind("<Button-5>")

        self.canvas_eventos.bind("<Enter>", bind_mousewheel)
        self.canvas_eventos.bind("<Leave>", unbind_mousewheel)

        self.imagens_exibidas = {}
        self.evento_expandido_atual = None
        self.img_refs = {}
        self.selecionado = None

        self.janela_cavala_aberta = False
        self.janela_cartas_aberta = False
        self.janela_avulsa_aberta = False

        if not self.cv:
            messagebox.showwarning("Aviso", "Nenhuma cavala encontrada em 'cavalas/'.")
        if not self.c:
            messagebox.showwarning("Aviso", "Nenhuma carta encontrada em 'cartas/'.")

    # Botão arredondado minimalista (Canvas)
    def criar_botao_arredondado(self, parent, texto, comando=None, min_w=140, min_h=40, pad_x=16, pad_y=10, radius=14):
        c = tk.Canvas(parent, bg=parent['bg'], highlightthickness=0, bd=0, cursor="")
        bg_btn = self.btn_style['bg']
        active_bg = self.btn_style['activebackground']
        fg = self.btn_style['fg']

        temp = tk.Label(c, text=texto, font=("Arial", 11, "bold"))
        temp.update_idletasks()
        w = max(min_w, temp.winfo_reqwidth() + 2 * pad_x)
        h = max(min_h, temp.winfo_reqheight() + 2 * pad_y)
        temp.destroy()

        c.config(width=w, height=h)

        def draw(cor_bg):
            c.delete("all")
            x1, y1, x2, y2 = 1, 1, w - 2, h - 2
            r = max(6, min(radius, (x2 - x1) // 2, (y2 - y1) // 2))
            c.create_rectangle(x1 + r, y1, x2 - r, y2, fill=cor_bg, outline="")
            c.create_rectangle(x1, y1 + r, x2, y2 - r, fill=cor_bg, outline="")
            c.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, style="pieslice", fill=cor_bg, outline="")
            c.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, style="pieslice", fill=cor_bg, outline="")
            c.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, style="pieslice", fill=cor_bg, outline="")
            c.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, style="pieslice", fill=cor_bg, outline="")
            c.create_line(x1 + r, y1, x2 - r, y1, fill="#333333")
            c.create_line(x2, y1 + r, x2, y2 - r, fill="#333333")
            c.create_line(x1 + r, y2, x2 - r, y2, fill="#333333")
            c.create_line(x1, y1 + r, x1, y2 - r, fill="#333333")
            c.create_text(w // 2, h // 2, text=texto, fill=fg, font=("Arial", 11, "bold"))

        draw(bg_btn)

        c._texto = texto

        if comando:
            def on_press(_):
                draw(active_bg)

            def on_release(_):
                draw(bg_btn)
                comando()

            def on_enter(_):
                c.config(cursor="hand2")

            def on_leave(_):
                c.config(cursor="")

            c.bind("<ButtonPress-1>", on_press)
            c.bind("<ButtonRelease-1>", on_release)
            c.bind("<Enter>", on_enter)
            c.bind("<Leave>", on_leave)

        return c

    def _desenhar_roundrect(self, canvas, x1, y1, x2, y2, r, fill="", outline="", width=1):
        canvas.delete("roundpanel")
        r = max(0, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
        canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="", tags="roundpanel")
        canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="", tags="roundpanel")
        canvas.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, style="pieslice", fill=fill, outline="", tags="roundpanel")
        canvas.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, style="pieslice", fill=fill, outline="", tags="roundpanel")
        canvas.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, style="pieslice", fill=fill, outline="", tags="roundpanel")
        canvas.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, style="pieslice", fill=fill, outline="", tags="roundpanel")
        if outline and width > 0:
            canvas.create_line(x1 + r, y1, x2 - r, y1, fill=outline, width=width, tags="roundpanel")
            canvas.create_line(x2, y1 + r, x2, y2 - r, fill=outline, width=width, tags="roundpanel")
            canvas.create_line(x1 + r, y2, x2 - r, y2, fill=outline, width=width, tags="roundpanel")
            canvas.create_line(x1, y1 + r, x1, y2 - r, fill=outline, width=width, tags="roundpanel")
            canvas.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, style="arc", outline=outline, width=width, tags="roundpanel")
            canvas.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, style="arc", outline=outline, width=width, tags="roundpanel")
            canvas.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, style="arc", outline=outline, width=width, tags="roundpanel")
            canvas.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, style="arc", outline=outline, width=width, tags="roundpanel")

    def _criar_painel_arredondado(self, parent, fill='#505050', outline='#6a6a6a', radius=14, pad=8, min_height=80, fill_parent_x=True, pady=(6, 6), padx=10):
        canvas = tk.Canvas(parent, bg=parent['bg'], highlightthickness=0, bd=0)
        if fill_parent_x:
            canvas.pack(fill='x', padx=padx, pady=pady)
        else:
            canvas.pack(padx=padx, pady=pady)
        frame = tk.Frame(canvas, bg=fill)
        win = canvas.create_window((0, 0), window=frame, anchor='n')

        def redraw(event=None):
            w = canvas.winfo_width()
            h = max(frame.winfo_reqheight() + 2 * pad, min_height)
            canvas.config(height=h)
            canvas.coords(win, w // 2, pad)
            canvas.itemconfig(win, width=w - 2 * pad)
            self._desenhar_roundrect(canvas, 1, 1, w - 2, h - 2, radius, fill=fill, outline=outline, width=1)

        canvas.bind("<Configure>", redraw)
        frame.bind("<Configure>", redraw)
        return canvas, frame, redraw

    def abrir_seletor_cavala(self):
        if self.janela_cavala_aberta:
            return
        self.janela_cavala_aberta = True

        win = tk.Toplevel(self.root)
        win.title("Selecione sua Cavala")
        win.configure(bg='#606060')

        largura = 1245
        altura = 370

        self.root.update_idletasks()
        geom = self.root.winfo_geometry()
        parts = geom.split('+')
        pos = f"+{parts[1]}+{parts[2]}" if len(parts) >= 3 else ""
        win.geometry(f"{largura}x{altura}{pos}")
        win.transient(self.root)
        win.grab_set()
        win.focus_force()

        def fechar():
            try:
                win.unbind_all("<MouseWheel>")
                win.unbind_all("<Button-4>")
                win.unbind_all("<Button-5>")
            except Exception:
                pass
            self.janela_cavala_aberta = False
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", fechar)

        _, grade_frame, _ = self._criar_painel_arredondado(win, fill='#505050', outline='#6a6a6a', radius=16, pad=10, min_height=200, pady=(10, 10), padx=10)

        # Cabeçalho arredondado (sem comando)
        header_btn = self.criar_botao_arredondado(
            grade_frame, "Selecione sua cavala", comando=None, min_w=220, min_h=40
        )
        header_btn.pack(pady=(10, 0))

        # Área rolável de cavalas
        canvas = tk.Canvas(grade_frame, bg='#505050', highlightthickness=0)
        scrollbar = ttk.Scrollbar(grade_frame, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True, padx=(6, 6), pady=6)
        scrollbar.pack(side='right', fill='y', pady=6)

        frame = tk.Frame(canvas, bg='#505050')
        janela_id = canvas.create_window((0, 0), window=frame, anchor='nw')

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        frame.bind("<Configure>", on_configure)

        def on_canvas_configure(event):
            canvas.itemconfig(janela_id, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        # Scroll do mouse
        def on_mousewheel_any(event):
            widget = win.winfo_containing(event.x_root, event.y_root)
            if widget is None:
                return "break"
            if widget == canvas or canvas.winfo_containing(event.x_root, event.y_root):
                if hasattr(event, "delta") and event.delta != 0:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                elif getattr(event, "num", None) == 4:
                    canvas.yview_scroll(-1, "units")
                elif getattr(event, "num", None) == 5:
                    canvas.yview_scroll(1, "units")
                return "break"

        win.bind_all("<MouseWheel>", on_mousewheel_any)
        win.bind_all("<Button-4>", on_mousewheel_any)
        win.bind_all("<Button-5>", on_mousewheel_any)

        linha = 0
        coluna = 0
        max_colunas = 7

        for col in range(max_colunas):
            frame.grid_columnconfigure(col, weight=1)

        # Atualização do botão da cavala usando o slot (sem mudar posição)
        def atualizar_botao_cavala(texto, largura=220):
            for w in self.slot_cavala.winfo_children():
                w.destroy()
            self.btn_cavala = self.criar_botao_arredondado(
                self.slot_cavala, texto, comando=self.abrir_seletor_cavala, min_w=largura, min_h=40
            )
            self.btn_cavala.pack()

        for nome, dados in self.cv.items():
            caminho_img = os.path.join(BASE, dados.get("imagem", ""))
            try:
                pil_img = Image.open(caminho_img).convert("RGBA")
                bg = Image.new("RGBA", pil_img.size, "#505050")
                pil_img = Image.alpha_composite(bg, pil_img)
                img = ImageTk.PhotoImage(pil_img)
            except Exception as e:
                print(f"Erro ao carregar imagem de {nome}: {e}")
                continue

            def selecionar_cavala(n=nome):
                self.cavala_selecionada = n
                atualizar_botao_cavala(f"Cavala selecionada: {n}", largura=220)
                self.mostrar()
                fechar()

            frame_interno = tk.Frame(frame, bg='#505050')
            frame_interno.grid(row=linha, column=coluna, padx=10, pady=10)

            btn = tk.Button(
                frame_interno, image=img, command=selecionar_cavala,
                borderwidth=0, highlightthickness=0,
                bg='#1a1a1a', activebackground='#333333'
            )
            btn.image = img
            btn.pack()
            tk.Label(frame_interno, text=nome, fg='white', bg='#505050').pack()

            coluna += 1
            if coluna >= max_colunas:
                coluna = 0
                linha += 1

    def _abrir_seletor_cartas_base(self, limite, ao_confirmar):
        win = tk.Toplevel(self.root)
        win.title("Selecione suas Cartas")
        win.configure(bg='#606060')

        largura = 1245
        altura = 500

        self.root.update_idletasks()
        geom = self.root.winfo_geometry()
        parts = geom.split('+')
        pos = f"+{parts[1]}+{parts[2]}" if len(parts) >= 3 else ""
        win.geometry(f"{largura}x{altura}{pos}")
        win.transient(self.root)
        win.grab_set()
        win.focus_force()

        def fechar():
            try:
                win.unbind_all("<MouseWheel>")
                win.unbind_all("<Button-4>")
                win.unbind_all("<Button-5>")
            except Exception:
                pass
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", fechar)

        # Painel 1: tipo
        _, tipo_frame, _ = self._criar_painel_arredondado(win, fill='#505050', outline='#6a6a6a', radius=14, pad=10, min_height=60, pady=(10, 6), padx=10)
        inner_tipos = tk.Frame(tipo_frame, bg=tipo_frame['bg'])
        inner_tipos.pack(anchor='center', pady=4)

        # Painel 2: header
        _, header_frame, _ = self._criar_painel_arredondado(win, fill='#505050', outline='#6a6a6a', radius=14, pad=10, min_height=60, pady=(0, 6), padx=10)

        # Painel 3: grade
        _, conteiner_grade, _ = self._criar_painel_arredondado(win, fill='#505050', outline='#6a6a6a', radius=16, pad=10, min_height=200, pady=(0, 10), padx=10)

        # Contador e confirmar
        selecionadas_atual = lambda: len(self.deck) if limite > 1 else (1 if self.carta_avulsa else 0)
        contador_var = tk.StringVar()
        contador_var.set(f"{selecionadas_atual()}/{limite} cartas selecionadas")

        for w in header_frame.winfo_children():
            w.destroy()
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(2, weight=1)

        label_contador = tk.Label(header_frame, textvariable=contador_var, font=("Arial", 10, "bold"),
                                  fg='white', bg=header_frame['bg'])
        label_contador.grid(row=0, column=1, padx=8, pady=(6, 4))

        btn_confirm = self.criar_botao_arredondado(header_frame, "Confirmar seleção", comando=lambda: (ao_confirmar(), fechar()), min_w=200, min_h=40)
        btn_confirm.grid(row=1, column=1, padx=8, pady=(0, 8))

        # Área rolável de cartas
        canvas = tk.Canvas(conteiner_grade, bg='#505050', highlightthickness=0)
        scrollbar = ttk.Scrollbar(conteiner_grade, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(6, 6), pady=6)
        scrollbar.pack(side="right", fill="y", pady=6)

        conteudo_frame = tk.Frame(canvas, bg='#505050')
        id_janela = canvas.create_window((0, 0), window=conteudo_frame, anchor='nw')

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        conteudo_frame.bind("<Configure>", on_configure)

        def on_canvas_configure(event):
            canvas.itemconfig(id_janela, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        # Wheel na janela inteira, mas só rola se o ponteiro estiver sobre o canvas
        def on_mousewheel_any(event):
            widget = win.winfo_containing(event.x_root, event.y_root)
            if widget is None:
                return "break"
            if widget == canvas or canvas.winfo_containing(event.x_root, event.y_root):
                if hasattr(event, "delta") and event.delta != 0:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                elif getattr(event, "num", None) == 4:
                    canvas.yview_scroll(-1, "units")
                elif getattr(event, "num", None) == 5:
                    canvas.yview_scroll(1, "units")
                return "break"

        win.bind_all("<MouseWheel>", on_mousewheel_any)
        win.bind_all("<Button-4>", on_mousewheel_any)
        win.bind_all("<Button-5>", on_mousewheel_any)

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

            # Wrapper ocupa toda a largura do canvas
            inner_grade_wrap = tk.Frame(conteudo_frame, bg=conteudo_frame['bg'])
            inner_grade_wrap.pack(fill='x', pady=4)

            # Grade centralizada dentro do wrapper
            inner_grade = tk.Frame(inner_grade_wrap, bg=conteudo_frame['bg'])
            inner_grade.pack(anchor='center')

            linha = 0
            coluna = 0
            max_colunas = 6

            cartas_filtradas = [
                (nome, dados) for nome, dados in self.c.items()
                if tipo in dados.get("imagem", "")
            ]
            cartas_ordenadas = sorted(
                cartas_filtradas,
                key=lambda item: extrair_raridade(item[1].get("imagem", ""))
            )

            for nome, dados in cartas_ordenadas:
                img_path = os.path.join(BASE, dados.get("imagem", ""))
                try:
                    pil_image = Image.open(img_path).convert("RGBA")
                    bg = Image.new("RGBA", pil_image.size, "#505050")
                    pil_image_colorida = Image.alpha_composite(bg, pil_image)
                    pil_image_cinza = ImageOps.grayscale(pil_image_colorida.convert("RGB"))
                    img_colorida = ImageTk.PhotoImage(pil_image_colorida)
                    img_cinza = ImageTk.PhotoImage(pil_image_cinza)
                except Exception as e:
                    print(f"Erro ao carregar imagem da carta {nome}: {e}")
                    continue

                def alternar_carta_normal(n=nome, btn_ref=None, colorida=None, cinza=None):
                    if n in self.deck:
                        self.deck.remove(n)
                        btn_ref.config(image=cinza); btn_ref.image = cinza
                    elif len(self.deck) < limite:
                        self.deck.append(n)
                        btn_ref.config(image=colorida); btn_ref.image = colorida
                    contador_var.set(f"{len(self.deck)}/{limite} cartas selecionadas")
                    self.mostrar()
                    if len(self.deck) == limite:
                        win.after(300, lambda: (ao_confirmar(), fechar()))

                def alternar_carta_avulsa(n=nome, btn_ref=None, colorida=None, cinza=None):
                    if self.carta_avulsa == n:
                        self.carta_avulsa = None
                        btn_ref.config(image=cinza); btn_ref.image = cinza
                    else:
                        self.carta_avulsa = n
                        btn_ref.config(image=colorida); btn_ref.image = colorida
                    contador_var.set(f"{1 if self.carta_avulsa else 0}/{limite} cartas selecionadas")
                    self.mostrar()
                    if self.carta_avulsa:
                        win.after(300, lambda: (ao_confirmar(), fechar()))

                cell = tk.Frame(inner_grade, bg='#505050')
                cell.grid(row=linha, column=coluna, padx=10, pady=10)

                imagem = img_colorida if ((limite > 1 and nome in self.deck) or (limite == 1 and self.carta_avulsa == nome)) else img_cinza

                btn = tk.Button(
                    cell, image=imagem, borderwidth=0, highlightthickness=0,
                    bg='#1a1a1a', activebackground='#333333'
                )
                btn.image = imagem
                btn.pack()
                tk.Label(cell, text=nome, fg='white', bg='#505050').pack()

                if limite > 1:
                    btn.config(command=lambda n=nome, b=btn, c=img_colorida, g=img_cinza: alternar_carta_normal(n, b, c, g))
                else:
                    btn.config(command=lambda n=nome, b=btn, c=img_colorida, g=img_cinza: alternar_carta_avulsa(n, b, c, g))

                coluna += 1
                if coluna >= max_colunas:
                    coluna = 0
                    linha += 1

        tipos = ['speed', 'wisdom', 'power', 'stamina', 'guts', 'pal']
        for tipo in tipos:
            try:
                icon_path = os.path.join(BASE, 'icon_tipos', f"{tipo}.png")
                icon = tk.PhotoImage(file=icon_path)
                btn = tk.Button(
                    inner_tipos, image=icon, command=lambda t=tipo: mostrar_cartas_por_tipo(t),
                    bg=tipo_frame['bg'], activebackground='#333333', borderwidth=0, highlightthickness=0
                )
                btn.image = icon
                btn.pack(side='left', padx=4, pady=2)
            except Exception as e:
                print(f"Erro ao carregar ícone do tipo {tipo}: {e}")

        mostrar_cartas_por_tipo('speed')
        return win

    def abrir_seletor_cartas(self):
        if self.janela_cartas_aberta:
            return
        self.janela_cartas_aberta = True

        def ao_confirmar():
            self.janela_cartas_aberta = False

        win = self._abrir_seletor_cartas_base(limite=6, ao_confirmar=ao_confirmar)
        def on_close():
            self.janela_cartas_aberta = False
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", on_close)

    def abrir_seletor_carta_avulsa(self):
        if self.janela_avulsa_aberta:
            return
        self.janela_avulsa_aberta = True

        def ao_confirmar():
            self.janela_avulsa_aberta = False

        win = self._abrir_seletor_cartas_base(limite=1, ao_confirmar=ao_confirmar)
        def on_close():
            self.janela_avulsa_aberta = False
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", on_close)

    def _criar_separador_vertical(self, parent, altura=140, cor='#ffffff'):
        canvas = tk.Canvas(parent, width=10, height=altura, bg=parent['bg'], highlightthickness=0)
        canvas.create_line(5, 10, 5, altura - 10, fill=cor, width=2)
        return canvas

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

        dados_cavala = self.cv.get(self.cavala_selecionada)
        if not dados_cavala:
            messagebox.showerror("Erro", f"Dados da cavala '{self.cavala_selecionada}' não encontrados.")
            return

        caminho_img_cavala = os.path.join(BASE, dados_cavala.get("imagem", ""))
        try:
            pil_img_cavala = Image.open(caminho_img_cavala).convert("RGBA")
            pil_img_cavala_res = pil_img_cavala.resize((128, 128), Image.Resampling.LANCZOS)
            img_colorida = ImageTk.PhotoImage(pil_img_cavala_res)
            img_cinza = ImageTk.PhotoImage(ImageOps.grayscale(pil_img_cavala_res.convert("RGB")))
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar a imagem da cavala: {e}")
            return

        frame_cavala = tk.Frame(self.frame_exibicao, bg=self.area_cor)
        frame_cavala.pack(side='left', padx=10)

        def on_click_cavala():
            self.atualizar_selecao('cavala')

        btn_img = tk.Button(
            frame_cavala, image=img_cinza, borderwidth=0, command=on_click_cavala,
            bg=self.area_cor, activebackground=self.area_cor, highlightthickness=0
        )
        btn_img.image_colorida = img_colorida
        btn_img.image_cinza = img_cinza
        btn_img.pack()
        tk.Label(frame_cavala, text=self.cavala_selecionada, font=("Arial", 12, "bold"), fg='white', bg=self.area_cor).pack()

        self.imagens_exibidas['cavala'] = btn_img
        self.img_refs['cavala_colorida'] = img_colorida
        self.img_refs['cavala_cinza'] = img_cinza

        frame_cartas = tk.Frame(self.frame_exibicao, bg=self.area_cor)
        frame_cartas.pack(side='left', padx=20)

        for nome_carta in self.deck:
            dados_carta = self.c.get(nome_carta)
            if not dados_carta:
                continue
            caminho_img_carta = os.path.join(BASE, dados_carta.get("imagem", ""))
            try:
                pil_img_carta = Image.open(caminho_img_carta).convert("RGBA")
                pil_img_carta_res = pil_img_carta.resize((128, 128), Image.Resampling.LANCZOS)
                img_colorida = ImageTk.PhotoImage(pil_img_carta_res)
                img_cinza = ImageTk.PhotoImage(ImageOps.grayscale(pil_img_carta_res.convert("RGB")))
            except Exception as e:
                print(f"Erro ao carregar imagem da carta {nome_carta}: {e}")
                continue

            frame_carta = tk.Frame(frame_cartas, bg=self.area_cor)
            frame_carta.pack(side='left', padx=5)

            def on_click_carta(n=nome_carta):
                self.atualizar_selecao(n)

            btn_img_carta = tk.Button(
                frame_carta, image=img_cinza, borderwidth=0, command=on_click_carta,
                bg=self.area_cor, activebackground=self.area_cor, highlightthickness=0
            )
            btn_img_carta.image_colorida = img_colorida
            btn_img_carta.image_cinza = img_cinza
            btn_img_carta.pack()
            tk.Label(frame_carta, text=nome_carta, fg='white', bg=self.area_cor).pack()

            self.imagens_exibidas[nome_carta] = btn_img_carta
            self.img_refs[f'{nome_carta}_colorida'] = img_colorida
            self.img_refs[f'{nome_carta}_cinza'] = img_cinza

        sep = self._criar_separador_vertical(self.frame_exibicao, altura=160, cor='#ffffff')
        sep.pack(side='left', padx=10)

        avulsa_frame = tk.Frame(self.frame_exibicao, bg=self.area_cor)
        avulsa_frame.pack(side='left', padx=10)

        if self.carta_avulsa:
            dados_carta = self.c.get(self.carta_avulsa)
            if dados_carta:
                caminho_img_carta = os.path.join(BASE, dados_carta.get("imagem", ""))
                try:
                    pil_img_carta = Image.open(caminho_img_carta).convert("RGBA")
                    pil_img_carta_res = pil_img_carta.resize((128, 128), Image.Resampling.LANCZOS)
                    img_colorida = ImageTk.PhotoImage(pil_img_carta_res)
                    img_cinza = ImageTk.PhotoImage(ImageOps.grayscale(pil_img_carta_res.convert("RGB")))
                except Exception as e:
                    print(f"Erro ao carregar imagem da carta avulsa {self.carta_avulsa}: {e}")
                    img_colorida = img_cinza = None

                def on_click_avulsa(n=self.carta_avulsa):
                    self.atualizar_selecao(f"avulsa:{n}")

                if img_colorida and img_cinza:
                    frame_carta = tk.Frame(avulsa_frame, bg=self.area_cor)
                    frame_carta.pack(side='left', padx=5)

                    btn_img_carta = tk.Button(
                        frame_carta, image=img_cinza, borderwidth=0, command=on_click_avulsa,
                        bg=self.area_cor, activebackground=self.area_cor, highlightthickness=0
                    )
                    btn_img_carta.image_colorida = img_colorida
                    btn_img_carta.image_cinza = img_cinza
                    btn_img_carta.pack()
                    tk.Label(frame_carta, text=self.carta_avulsa + " (avulsa)", fg='white', bg=self.area_cor).pack()

                    self.imagens_exibidas[f"avulsa:{self.carta_avulsa}"] = btn_img_carta
                    self.img_refs[f"avulsa:{self.carta_avulsa}_colorida"] = img_colorida
                    self.img_refs[f"avulsa:{self.carta_avulsa}_cinza"] = img_cinza

        if not self.deck and not self.carta_avulsa:
            dica = tk.Label(
                self.frame_eventos,
                text="Dica: clique na imagem da cavala, de uma carta, ou na carta avulsa para ver os eventos.",
                fg='#e0e0e0', bg='#606060'
            )
            dica.pack(pady=8)

        self.selecionado = None
        self.mostrar_eventos(None)

    def atualizar_selecao(self, selecionado):
        if self.selecionado == selecionado:
            btn = self.imagens_exibidas.get(selecionado)
            if btn:
                btn.config(image=btn.image_cinza)
                btn.image = btn.image_cinza
            self.selecionado = None
            self.mostrar_eventos(None)
            return

        if self.selecionado is not None:
            btn_antigo = self.imagens_exibidas.get(self.selecionado)
            if btn_antigo:
                btn_antigo.config(image=btn_antigo.image_cinza)
                btn_antigo.image = btn_antigo.image_cinza

        btn_novo = self.imagens_exibidas.get(selecionado)
        if btn_novo:
            btn_novo.config(image=btn_novo.image_colorida)
            btn_novo.image = btn_novo.image_colorida
            self.selecionado = selecionado
            if selecionado.startswith("avulsa:"):
                nome = selecionado.split(":", 1)[1]
                self.mostrar_eventos(nome)
            else:
                self.mostrar_eventos(selecionado)

    def mostrar_eventos(self, selecionado):
        for w in self.frame_eventos.winfo_children():
            w.destroy()

        self.canvas_eventos.yview_moveto(0)

        if selecionado is None:
            return

        if selecionado == 'cavala':
            self.mostrar_eventos_cavala()
        else:
            self.mostrar_eventos_carta(selecionado)

    def mostrar_eventos_cavala(self):
        dados = self.cv.get(self.cavala_selecionada, {})
        eventos_por_cat = dados.get("eventos", {})

        for cat, eventos in eventos_por_cat.items():
            tk.Label(self.frame_eventos, text=f"-- {cat} --", font=('Arial', 10, 'bold'), fg='white', bg='#606060').pack(fill='x', pady=(10, 2))
            for ev in eventos:
                titulo = ev.get('nome', 'Evento')
                detalhes = ev.get('detalhes', '')
                ev_expand = EventoExpandivel(self.frame_eventos, titulo, detalhes)
                ev_expand.pack(fill='x', padx=10, pady=2)

    def mostrar_eventos_carta(self, nome_carta):
        dados_carta = self.c.get(nome_carta)
        if not dados_carta:
            return

        for cat, eventos in dados_carta.get("eventos", {}).items():
            tk.Label(self.frame_eventos, text=f"-- {cat} --", font=('Arial', 10, 'bold'), fg='white', bg='#606060').pack(fill='x', pady=(6, 2))
            for ev in eventos:
                titulo = ev.get('nome', 'Evento')
                detalhes = ev.get('detalhes', '')
                ev_expand = EventoExpandivel(self.frame_eventos, titulo, detalhes)
                ev_expand.pack(fill='x', padx=10, pady=1)

    def resetar_escolhas(self):
        self.deck = []
        self.carta_avulsa = None
        for widget in self.frame_exibicao.winfo_children():
            widget.destroy()
        for widget in self.frame_eventos.winfo_children():
            widget.destroy()
        self.imagens_exibidas.clear()
        self.img_refs.clear()
        self.selecionado = None
        self.cavala_selecionada = None

        # Recria apenas o conteúdo do slot, posição preservada
        for w in self.slot_cavala.winfo_children():
            w.destroy()
        self.btn_cavala = self.criar_botao_arredondado(
            self.slot_cavala, "Escolha sua cavala", comando=self.abrir_seletor_cavala, min_w=180, min_h=40
        )
        self.btn_cavala.pack()

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

    root = criar_janela_centrada(1245, 850)
    app = UmaApp(root, cartas, cavalas)
    root.mainloop()
