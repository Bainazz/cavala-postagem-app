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
    def __init__(self, root, content, cartas_data, cavalas_data):
        self.c = cartas_data
        self.cv = cavalas_data
        self.deck = []
        self.carta_avulsa = None
        self.cavala_selecionada = None
        self.root = root
        self.base = content
        self.base.configure(bg='#606060')

        self.btn_style = {
            'fg': 'white', 'bg': '#1a1a1a',
            'activebackground': '#333333', 'activeforeground': 'white'
        }

        self.top_bar = tk.Frame(self.base, bg='#606060')
        self.top_bar.pack(pady=8)

        self.slot_cavala = tk.Frame(self.top_bar, bg='#606060')
        self.slot_cavala.pack(side='left', padx=6)
        self.slot_cartas = tk.Frame(self.top_bar, bg='#606060')
        self.slot_cartas.pack(side='left', padx=6)
        self.slot_avulsa = tk.Frame(self.top_bar, bg='#606060')
        self.slot_avulsa.pack(side='left', padx=6)

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

        self.area_cor = '#505050'
        self.area_border = '#6a6a6a'
        self.area_canvas = tk.Canvas(self.base, bg='#606060', highlightthickness=0, bd=0)
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

        self.search_frame = tk.Frame(self.base, bg='#606060')
        self.search_frame.pack(fill='x', padx=10, pady=(0, 6))

        self.search_var = tk.StringVar()

        left_spacer = tk.Frame(self.search_frame, bg='#606060')
        left_spacer.pack(side='left', expand=True)

        self.search_entry = tk.Entry(self.search_frame, textvariable=self.search_var, fg='#ffffff', bg='#404040',
                                     insertbackground='white', relief='flat', width=30)
        self.search_entry.pack(side='left', padx=(0, 6), ipady=4)

        self.btn_clear_search = tk.Button(self.search_frame, text="X", width=6,
                                          command=lambda: self._limpar_pesquisa(),
                                          fg='white', bg='#1a1a1a', activebackground='#333333',
                                          activeforeground='white', bd=0)
        self.btn_clear_search.pack(side='left')

        right_spacer = tk.Frame(self.search_frame, bg='#606060')
        right_spacer.pack(side='left', expand=True)

        self._search_placeholder = "Pesquisar eventos…"
        self._search_active = False

        def _apply_placeholder():
            if not self.search_var.get():
                self._search_active = False
                self.search_entry.config(fg='#bfbfbf')
                self.search_var.set(self._search_placeholder)

        def _remove_placeholder(_=None):
            if not self._search_active:
                self._search_active = True
                self.search_entry.config(fg='#ffffff')
                self.search_var.set("")

        self.search_entry.bind("<FocusIn>", _remove_placeholder)
        self.search_entry.bind("<FocusOut>", lambda e: _apply_placeholder())

        def _on_type(*_):
            if not self._search_active:
                return
            self._aplicar_filtro_eventos()
        self.search_var.trace_add("write", lambda *args: _on_type())

        _apply_placeholder()

        self.btn_reset = self.criar_botao_arredondado(
            self.base, "Resetar escolhas", comando=self.resetar_escolhas, min_w=160, min_h=40
        )
        self.btn_reset.pack(pady=(2, 8))

        self.canvas_eventos = tk.Canvas(self.base, height=300, bg='#606060', highlightthickness=0)
        self.scroll_eventos = ttk.Scrollbar(self.base, orient='vertical', command=self.canvas_eventos.yview)
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

        self.canvas_eventos.bind("<MouseWheel>", on_mousewheel, add="+")
        self.canvas_eventos.bind("<Button-4>", on_button4, add="+")
        self.canvas_eventos.bind("<Button-5>", on_button5, add="+")

        self.wrapper_eventos.bind("<MouseWheel>", on_mousewheel, add="+")
        self.wrapper_eventos.bind("<Button-4>", on_button4, add="+")
        self.wrapper_eventos.bind("<Button-5>", on_button5, add="+")
        self.root.bind("<MouseWheel>", on_mousewheel, add="+")
        self.root.bind("<Button-4>", on_button4, add="+")
        self.root.bind("<Button-5>", on_button5, add="+")

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

    def _criar_painel_arredondado(self, parent, fill='#505050', outline='#6a6a6a', radius=14, pad=8, min_height=80, fill_parent_x=True, pady=(6, 6), padx=10):
        canvas = tk.Canvas(parent, bg=parent['bg'], highlightthickness=0, bd=0)
        if fill_parent_x:
            canvas.pack(fill='x', padx=padx, pady=pady)
        else:
            canvas.pack(padx=padx, pady=pady)

        canvas._round_pad = pad
        canvas._round_fill = fill
        canvas._round_outline = outline
        canvas._round_radius = radius
        canvas._round_min_height = min_height

        frame = tk.Frame(canvas, bg=fill)
        win = canvas.create_window((0, 0), window=frame, anchor='n')

        def redraw(event=None):
            w = canvas.winfo_width()
            h = max(frame.winfo_reqheight() + 2 * pad, min_height)
            canvas.config(height=h)
            canvas.coords(win, w // 2, pad)
            canvas.itemconfig(win, width=w - 2 * pad)
            self._desenhar_roundrect(canvas, 1, 1, w - 2, h - 2, radius, fill=fill, outline=outline, width=1)
            canvas._round_inner_height = h

        canvas.bind("<Configure>", redraw)
        frame.bind("<Configure>", redraw)
        canvas._round_inner_height = min_height

        return canvas, frame, redraw

    def abrir_seletor_cavala(self):
        if self.janela_cavala_aberta:
            return
        self.janela_cavala_aberta = True

        largura = 1245
        altura = 715
        win, win_content, _fechar = criar_toplevel_custom(
            self.root, largura, altura, "Selecione sua Cavala",
            on_close=lambda: setattr(self, "janela_cavala_aberta", False)
        )
        win.transient(self.root)
        win.grab_set()
        win.focus_force()

        painel_canvas, grade_frame, _ = self._criar_painel_arredondado(
            win_content, fill='#505050', outline='#6a6a6a', radius=16, pad=10, min_height=700, pady=(10, 10), padx=10
        )

        header_btn = self.criar_botao_arredondado(
            grade_frame, "Selecione sua cavala", comando=None, min_w=220, min_h=40
        )
        header_btn.pack(pady=(10, 0))

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

        def sync_canvas_height_cavala(event=None):
            h = getattr(painel_canvas, "_round_inner_height", 700)
            altura_util = max(300, h - 100)
            canvas.config(height=altura_util)
        painel_canvas.bind("<Configure>", sync_canvas_height_cavala)
        grade_frame.bind("<Configure>", sync_canvas_height_cavala)
        win.after(0, sync_canvas_height_cavala)

        def _on_mousewheel(event):
            if hasattr(event, "delta") and event.delta:
                up = event.delta > 0
                top, bottom = canvas.yview()
                if up and top <= 0.0:
                    return "break"
                if not up and bottom >= 1.0:
                    return "break"
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return "break"
        def _on_button4(event):
            top, _ = canvas.yview()
            if top <= 0.0:
                return "break"
            canvas.yview_scroll(-1, "units")
            return "break"
        def _on_button5(event):
            _, bottom = canvas.yview()
            if bottom >= 1.0:
                return "break"
            canvas.yview_scroll(1, "units")
            return "break"
        def _bind_wheel(_):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_button4)
            canvas.bind_all("<Button-5>", _on_button5)
        def _unbind_wheel(_):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)

        linha = 0
        coluna = 0
        max_colunas = 7

        for col in range(max_colunas):
            frame.grid_columnconfigure(col, weight=1)

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
                try:
                    win.destroy()
                finally:
                    self.janela_cavala_aberta = False

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
        self.root.update_idletasks()
        scr_h = self.root.winfo_screenheight()
        largura = 1245
        altura = min(715, scr_h - 120)

        def _on_close_flag():
            if limite > 1:
                self.janela_cartas_aberta = False
            else:
                self.janela_avulsa_aberta = False

        win, win_content, fechar = criar_toplevel_custom(
            self.root, largura, altura, "Selecione suas Cartas",
            on_close=_on_close_flag
        )
        win.transient(self.root)
        win.grab_set()
        win.focus_force()

        _, tipo_frame, _ = self._criar_painel_arredondado(
            win_content, fill='#505050', outline='#6a6a6a', radius=14, pad=10, min_height=60, pady=(10, 6), padx=10
        )
        inner_tipos = tk.Frame(tipo_frame, bg=tipo_frame['bg'])
        inner_tipos.pack(anchor='center', pady=4)

        _, header_frame, _ = self._criar_painel_arredondado(
            win_content, fill='#505050', outline='#6a6a6a', radius=14, pad=10, min_height=60, pady=(0, 6), padx=10
        )

        painel_grade_canvas, conteiner_grade, _ = self._criar_painel_arredondado(
            win_content, fill='#505050', outline='#6a6a6a', radius=16, pad=10, min_height=480, pady=(0, 10), padx=10
        )

        contador_var = tk.StringVar()
        def atualiza_contador():
            val = len(self.deck) if limite > 1 else (1 if self.carta_avulsa else 0)
            contador_var.set(f"{val}/{limite} cartas selecionadas")
        atualiza_contador()

        for w in header_frame.winfo_children():
            w.destroy()
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(2, weight=1)

        label_contador = tk.Label(header_frame, textvariable=contador_var, font=("Arial", 10, "bold"),
                                  fg='white', bg=header_frame['bg'])
        label_contador.grid(row=0, column=1, padx=8, pady=(6, 4))

        def _close_and_reset():
            _on_close_flag()
            try:
                win.destroy()
            except Exception:
                pass

        btn_confirm = self.criar_botao_arredondado(
            header_frame, "Confirmar seleção", comando=lambda: (ao_confirmar(), _close_and_reset()), min_w=200, min_h=40
        )
        btn_confirm.grid(row=1, column=1, padx=8, pady=(0, 8))

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

        def sync_canvas_height_cartas(event=None):
            h = getattr(painel_grade_canvas, "_round_inner_height", 400)
            altura_util = max(200, h - 24)
            canvas.config(height=altura_util)
        painel_grade_canvas.bind("<Configure>", sync_canvas_height_cartas)
        conteiner_grade.bind("<Configure>", sync_canvas_height_cartas)
        win.bind("<Configure>", sync_canvas_height_cartas)
        win.after(0, sync_canvas_height_cartas)

        def _on_mousewheel(event):
            if hasattr(event, "delta") and event.delta:
                up = event.delta > 0
                top, bottom = canvas.yview()
                if up and top <= 0.0:
                    return "break"
                if not up and bottom >= 1.0:
                    return "break"
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return "break"
        def _on_button4(event):
            top, _ = canvas.yview()
            if top <= 0.0:
                return "break"
            canvas.yview_scroll(-1, "units")
            return "break"
        def _on_button5(event):
            _, bottom = canvas.yview()
            if bottom >= 1.0:
                return "break"
            canvas.yview_scroll(1, "units")
            return "break"
        def _bind_wheel(_):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_button4)
            canvas.bind_all("<Button-5>", _on_button5)
        def _unbind_wheel(_):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)

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

            inner_grade_wrap = tk.Frame(conteudo_frame, bg=conteudo_frame['bg'])
            inner_grade_wrap.pack(fill='x', pady=4)

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
                    atualiza_contador()
                    self.mostrar()
                    if len(self.deck) == limite:
                        win.after(300, lambda: (ao_confirmar(), _close_and_reset()))

                def alternar_carta_avulsa(n=nome, btn_ref=None, colorida=None, cinza=None):
                    if self.carta_avulsa == n:
                        self.carta_avulsa = None
                        btn_ref.config(image=cinza); btn_ref.image = cinza
                    else:
                        self.carta_avulsa = n
                        btn_ref.config(image=colorida); btn_ref.image = colorida
                    atualiza_contador()
                    self.mostrar()
                    if self.carta_avulsa:
                        win.after(300, lambda: (ao_confirmar(), _close_and_reset()))

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

            canvas.update_idletasks()
            canvas.yview_moveto(0)

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

        # Fechamento garantindo reset de flags (✕, ESC, WM_DELETE_WINDOW, confirmar)
        win.protocol("WM_DELETE_WINDOW", _close_and_reset)
        win.bind("<Escape>", lambda e: _close_and_reset())

        return win

    def abrir_seletor_cartas(self):
        if self.janela_cartas_aberta:
            return
        self.janela_cartas_aberta = True

        def ao_confirmar():
            self.janela_cartas_aberta = False

        self._abrir_seletor_cartas_base(limite=6, ao_confirmar=ao_confirmar)

    def abrir_seletor_carta_avulsa(self):
        if self.janela_avulsa_aberta:
            return
        self.janela_avulsa_aberta = True

        def ao_confirmar():
            self.janela_avulsa_aberta = False

        self._abrir_seletor_cartas_base(limite=1, ao_confirmar=ao_confirmar)

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

        # Reativar busca após atualizar a área
        if not self._search_active or self.search_var.get() == self._search_placeholder:
            self._search_active = False
            self.search_entry.config(fg='#bfbfbf')
            self.search_var.set(self._search_placeholder)
        self.search_entry.configure(state='normal')
        self.search_entry.bind("<FocusIn>", lambda e: self._on_search_focus_in())
        self.search_entry.bind("<FocusOut>", lambda e: self._on_search_focus_out())
        self.search_entry.focus_set()

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

    # Helpers para focus da busca
    def _on_search_focus_in(self):
        if not self._search_active:
            self._search_active = True
            self.search_entry.config(fg='#ffffff')
            if self.search_var.get() == self._search_placeholder:
                self.search_var.set("")

    def _on_search_focus_out(self):
        if not self.search_var.get():
            self._search_active = False
            self.search_entry.config(fg='#bfbfbf')
            self.search_var.set(self._search_placeholder)

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
            if isinstance(selecionado, str) and selecionado.startswith("avulsa:"):
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

        filtro = self._texto_filtro()
        for cat, eventos in eventos_por_cat.items():
            eventos_filtrados = [ev for ev in eventos if self._combina_filtro(ev.get('nome', ''), filtro)]
            if not eventos_filtrados:
                continue
            tk.Label(self.frame_eventos, text=f"-- {cat} --", font=('Arial', 10, 'bold'), fg='white', bg='#606060').pack(fill='x', pady=(10, 2))
            for ev in eventos_filtrados:
                titulo = ev.get('nome', 'Evento')
                detalhes = ev.get('detalhes', '')
                ev_expand = EventoExpandivel(self.frame_eventos, titulo, detalhes)
                ev_expand.pack(fill='x', padx=10, pady=2)

    def mostrar_eventos_carta(self, nome_carta):
        dados_carta = self.c.get(nome_carta)
        if not dados_carta:
            return

        filtro = self._texto_filtro()
        for cat, eventos in dados_carta.get("eventos", {}).items():
            eventos_filtrados = [ev for ev in eventos if self._combina_filtro(ev.get('nome', ''), filtro)]
            if not eventos_filtrados:
                continue
            tk.Label(self.frame_eventos, text=f"-- {cat} --", font=('Arial', 10, 'bold'), fg='white', bg='#606060').pack(fill='x', pady=(6, 2))
            for ev in eventos_filtrados:
                titulo = ev.get('nome', 'Evento')
                detalhes = ev.get('detalhes', '')
                ev_expand = EventoExpandivel(self.frame_eventos, titulo, detalhes)
                ev_expand.pack(fill='x', padx=10, pady=1)

    def _texto_filtro(self):
        txt = self.search_var.get().strip()
        if not getattr(self, "_search_active", False) or txt == self._search_placeholder:
            return ""
        return txt.lower()

    def _combina_filtro(self, titulo, filtro):
        if not filtro:
            return True
        return str(titulo).lower().startswith(filtro)

    def _aplicar_filtro_eventos(self):
        if self.selecionado is None:
            for w in self.frame_eventos.winfo_children():
                w.destroy()
            return
        if self.selecionado == 'cavala':
            self.mostrar_eventos('cavala')
        else:
            self.mostrar_eventos(self.selecionado)

    def _limpar_pesquisa(self):
        self.search_entry.configure(state='normal')
        self.search_entry.focus_set()
        self.search_var.set("")
        self._search_active = False
        self.search_entry.config(fg='#bfbfbf')
        self.search_var.set(self._search_placeholder)
        self._aplicar_filtro_eventos()

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

        for w in self.slot_cavala.winfo_children():
            w.destroy()
        self.btn_cavala = self.criar_botao_arredondado(
            self.slot_cavala, "Escolha sua cavala", comando=self.abrir_seletor_cavala, min_w=180, min_h=40
        )
        self.btn_cavala.pack()


def criar_janela_centrada_custom(largura, altura, titulo="CAVALA Trainer"):
    root = tk.Tk()

    largura_tela = root.winfo_screenwidth()
    altura_tela = root.winfo_screenheight()
    pos_x = (largura_tela // 2) - (largura // 2)
    pos_y = (altura_tela // 2) - (altura // 2)

    root.overrideredirect(True)
    root.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
    root.configure(bg='#404040')

    cont = tk.Frame(root, bg='#606060', bd=1, highlightthickness=1, highlightbackground='#303030')
    cont.pack(fill='both', expand=True)

    titlebar = tk.Frame(cont, bg='#303030')
    titlebar.pack(fill='x', side='top')

    def start_move(e):
        root._ox, root._oy = e.x_root, e.y_root
    def do_move(e):
        dx = e.x_root - root._ox
        dy = e.y_root - root._oy
        x = root.winfo_x() + dx
        y = root.winfo_y() + dy
        root.geometry(f"+{x}+{y}")
        root._ox, root._oy = e.x_root, e.y_root
    titlebar.bind("<Button-1>", start_move)
    titlebar.bind("<B1-Motion>", do_move)

    btn_fg = '#ffffff'
    btn_bg = '#303030'
    btn_bg_hover = '#444444'
    def make_title_btn(text, cmd):
        b = tk.Label(titlebar, text=text, fg=btn_fg, bg=btn_bg, width=3)
        b.bind("<Enter>", lambda e: b.config(bg=btn_bg_hover))
        b.bind("<Leave>", lambda e: b.config(bg=btn_bg))
        b.bind("<Button-1>", lambda e: cmd())
        return b

    def close_app():
        root.destroy()
    def minimize_app():
        root.overrideredirect(False)
        root.iconify()
        def restore_overrideredirect(_):
            root.overrideredirect(True)
        root.bind("<Map>", restore_overrideredirect, add="+")

    btn_close = make_title_btn("✕", close_app)
    btn_close.pack(side='right', padx=(0, 6), pady=1)
    btn_min = make_title_btn("—", minimize_app)
    btn_min.pack(side='right', padx=(0, 2), pady=1)

    lbl_title = tk.Label(titlebar, text=titulo, fg='#ffffff', bg='#303030', font=("Arial", 11, "bold"))
    lbl_title.pack(side='top', pady=4)

    content = tk.Frame(cont, bg='#606060')
    content.pack(fill='both', expand=True)

    root.bind("<Escape>", lambda e: root.destroy())

    return root, content

def criar_toplevel_custom(parent, largura, altura, titulo="Janela", on_close=None):
    win = tk.Toplevel(parent)
    win.overrideredirect(True)
    win.configure(bg='#404040')

    parent.update_idletasks()
    try:
        geom = parent.winfo_geometry()
        parts = geom.split('+')
        pos = f"+{parts[1]}+{parts[2]}" if len(parts) >= 3 else ""
    except Exception:
        pos = ""
    win.geometry(f"{largura}x{altura}{pos}")

    cont = tk.Frame(win, bg='#606060', bd=1, highlightthickness=1, highlightbackground='#303030')
    cont.pack(fill='both', expand=True)

    titlebar = tk.Frame(cont, bg='#303030')
    titlebar.pack(fill='x', side='top')

    def start_move(e):
        win._ox, win._oy = e.x_root, e.y_root
    def do_move(e):
        dx = e.x_root - win._ox
        dy = e.y_root - win._oy
        x = win.winfo_x() + dx
        y = win.winfo_y() + dy
        win.geometry(f"+{x}+{y}")
        win._ox, win._oy = e.x_root, e.y_root
    titlebar.bind("<Button-1>", start_move)
    titlebar.bind("<B1-Motion>", do_move)

    def close_win():
        if on_close:
            try:
                on_close()
            except Exception:
                pass
        try:
            win.destroy()
        except Exception:
            pass

    def minimize_win():
        win.overrideredirect(False)
        win.iconify()
        def restore(_):
            win.overrideredirect(True)
        win.bind("<Map>", restore, add="+")

    btn_fg = '#ffffff'
    btn_bg = '#303030'
    btn_bg_hover = '#444444'
    def make_title_btn(text, cmd):
        b = tk.Label(titlebar, text=text, fg=btn_fg, bg=btn_bg, width=3)
        b.bind("<Enter>", lambda e: b.config(bg=btn_bg_hover))
        b.bind("<Leave>", lambda e: b.config(bg=btn_bg))
        b.bind("<Button-1>", lambda e: cmd())
        return b

    btn_close = make_title_btn("✕", close_win)
    btn_close.pack(side='right', padx=(0, 6), pady=1)
    btn_min = make_title_btn("—", minimize_win)
    btn_min.pack(side='right', padx=(0, 2), pady=1)

    lbl_title = tk.Label(titlebar, text=titulo, fg='#ffffff', bg='#303030', font=("Arial", 11, "bold"))
    lbl_title.pack(side='top', pady=4)

    content = tk.Frame(cont, bg='#606060')
    content.pack(fill='both', expand=True)

    win.bind("<Escape>", lambda e: close_win())

    def fechar():
        try:
            win.unbind_all("<MouseWheel>")
            win.unbind_all("<Button-4>")
            win.unbind_all("<Button-5>")
        except Exception:
            pass
        close_win()

    return win, content, fechar


if __name__ == "__main__":
    cartas = carregar_cartas(os.path.join(BASE, 'cartas'))
    cavalas = carregar_cavalas(os.path.join(BASE, 'cavalas'))

    root, content = criar_janela_centrada_custom(1245, 715, "CAVALA Trainer")
    app = UmaApp(root, content, cartas, cavalas)
    root.mainloop()
