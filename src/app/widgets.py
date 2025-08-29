import tkinter as tk
from tkinter.font import Font
from PIL import Image, ImageTk, ImageOps
import re

# Notas:
# - Painéis/Widgets compartilhados: botão arredondado, painel arredondado, separador, EventoExpandivel.
# - Preserva o comportamento e as notas originais.

class EventoExpandivel(tk.Frame):
    # painel simples com título clicável que expande/colapsa para mostrar detalhes
    # suporta marcações simples de negrito em ANSI (\033[1m ... \033[0m)
    def __init__(self, master, titulo, detalhes, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # Adicione um ID único para este evento
        self.evento_id = id(self)
        self.aberto = False

        # Adicione esta linha (se ainda não tiver):
        self.card_id = None  # Vai ser definido quando o evento for criado

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

        def _scroll_canvas_para_cima(event):
            try:
                widget = self
                while widget and not isinstance(widget, tk.Canvas):
                    widget = widget.master
                if widget:
                    top, bottom = widget.yview()
                    if top <= 0.0:  # já está no topo, não rola mais
                        return "break"
                    widget.yview_scroll(-1, "units")
                return "break"
            except Exception:
                return "break"

        def _scroll_canvas_para_baixo(event):
            try:
                widget = self
                while widget and not isinstance(widget, tk.Canvas):
                    widget = widget.master
                if widget:
                    top, bottom = widget.yview()
                    if bottom >= 1.0:  # já está no final, não rola mais
                        return "break"
                    widget.yview_scroll(1, "units")
                return "break"
            except Exception:
                return "break"

        def _scroll_mousewheel(event):
            try:
                delta = int(-1 * (event.delta / 120))
                widget = self
                while widget and not isinstance(widget, tk.Canvas):
                    widget = widget.master
                if widget:
                    top, bottom = widget.yview()
                    if delta < 0 and top <= 0.0:      # tentando subir além do topo
                        return "break"
                    if delta > 0 and bottom >= 1.0:   # tentando descer além do final
                        return "break"
                    widget.yview_scroll(delta, "units")
                return "break"
            except Exception:
                return "break"

        # Bindings
        self.text_widget.bind("<MouseWheel>", _scroll_mousewheel)
        self.text_widget.bind("<Button-4>", _scroll_canvas_para_cima)
        self.text_widget.bind("<Button-5>", _scroll_canvas_para_baixo)
        self.botao.bind("<MouseWheel>", _scroll_mousewheel)
        self.botao.bind("<Button-4>", _scroll_canvas_para_cima)
        self.botao.bind("<Button-5>", _scroll_canvas_para_baixo)



        self.text_widget.update_idletasks()
        num_linhas = int(self.text_widget.index('end-1c').split('.')[0])
        self.text_widget.config(height=num_linhas)

    def toggle(self):
        # expande/quebra esse painel e fecha outros que estiverem abertos no mesmo coiso
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


def criar_botao_arredondado(parent, texto, comando=None, min_w=140, min_h=40, pad_x=16, pad_y=10, radius=14, btn_style=None):
    # cria um "botão" custom desenhado com cantos arredondados (Canvas)
    c = tk.Canvas(parent, bg=parent['bg'], highlightthickness=0, bd=0, cursor="")
    btn_style = btn_style or {
        'fg': 'white', 'bg': '#1a1a1a',
        'activebackground': '#333333', 'activeforeground': 'white'
    }
    bg_btn = btn_style['bg']
    active_bg = btn_style['activebackground']
    fg = btn_style['fg']

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
        # corpo
        c.create_rectangle(x1 + r, y1, x2 - r, y2, fill=cor_bg, outline="")
        c.create_rectangle(x1, y1 + r, x2, y2 - r, fill=cor_bg, outline="")
        # cantos
        c.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, style="pieslice", fill=cor_bg, outline="")
        c.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, style="pieslice", fill=cor_bg, outline="")
        c.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, style="pieslice", fill=cor_bg, outline="")
        c.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, style="pieslice", fill=cor_bg, outline="")
        # linhas finas de borda (estética)
        c.create_line(x1 + r, y1, x2 - r, y1, fill="#333333")
        c.create_line(x2, y1 + r, x2, y2 - r, fill="#333333")
        c.create_line(x1 + r, y2, x2 - r, y2, fill="#333333")
        c.create_line(x1, y1 + r, x1, y2 - r, fill="#333333")
        # texto
        c.create_text(w // 2, h // 2, text=texto, fill=fg, font=("Arial", 11, "bold"))

    draw(bg_btn)
    c._texto = texto

    if comando:
        def on_press(_): draw(active_bg)
        def on_release(_): draw(bg_btn); comando()
        def on_enter(_): c.config(cursor="hand2")
        def on_leave(_): c.config(cursor="")
        c.bind("<ButtonPress-1>", on_press)
        c.bind("<ButtonRelease-1>", on_release)
        c.bind("<Enter>", on_enter)
        c.bind("<Leave>", on_leave)

    return c


def desenhar_roundrect(canvas, x1, y1, x2, y2, r, fill="", outline="", width=1):
    # desenha um retângulo com cantos arredondados no canvas.
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


def criar_painel_arredondado(parent, fill='#505050', outline='#6a6a6a', radius=14, pad=8, min_height=80, fill_parent_x=True, pady=(6, 6), padx=10):
    # cria um Canvas com conteúdo interno (frame) e desenha um painel arredondado ao fundo
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
        desenhar_roundrect(canvas, 1, 1, w - 2, h - 2, radius, fill=fill, outline=outline, width=1)
        # opcional: armazenar altura interna p/ outros cálculos
        canvas._round_inner_height = h

    canvas.bind("<Configure>", redraw)
    frame.bind("<Configure>", redraw)

    return canvas, frame, redraw


def criar_separador_vertical(parent, altura=140, cor='#ffffff'):
    canvas = tk.Canvas(parent, width=10, height=altura, bg=parent['bg'], highlightthickness=0)
    canvas.create_line(5, 10, 5, altura - 10, fill=cor, width=2)
    return canvas