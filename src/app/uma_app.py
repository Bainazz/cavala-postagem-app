import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageOps

# Notas:
# - Classe principal do "CAVALA Trainer".
# - Gerencia estado: deck, carta_avulsa, cavala_selecionada.
# - Exibição superior (cavala + deck + avulsa) e lista de eventos com filtro.
# - Usa widgets e selectors extraídos para módulos separados.

from .widgets import (
    EventoExpandivel,
    criar_botao_arredondado,
    criar_painel_arredondado,
    criar_separador_vertical,
    desenhar_roundrect,
)
from .selectors import abrir_seletor_cavala, abrir_seletor_cartas
from ..data.paths import BASE


class UmaApp:
    def __init__(self, root, content, cartas_data, cavalas_data):

        self._events_preserved = False
        self._events_state = {}  # Armazena o estado dos eventos

        # Adicionei esta linha junto com outras flags já existentes
        self._ultima_selecao_avulsa = None

        # self.c: mapeia card_id (imagem relativa) -> dados (dict da carta)
        self.c = cartas_data
        # self.cv: mapeia nome -> dados da cavala
        self.cv = cavalas_data

        # estado atual de seleção
        self.deck = []           # lista de card_id
        self.carta_avulsa = None # card_id
        self.cavala_selecionada = None

        self.root = root
        self.base = content
        self.base.configure(bg='#606060')

        # mapas auxiliares
        self.card_by_id = {}
        self.name_by_id = {}

        # estilo básico dos botões desenhados
        self.btn_style = {
            'fg': 'white', 'bg': '#1a1a1a',
            'activebackground': '#333333', 'activeforeground': 'white'
        }

        # barra superior
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

        # área arredondada superior
        self.area_cor = '#505050'
        self.area_border = '#6a6a6a'
        self.area_canvas = tk.Canvas(self.base, bg='#606060', highlightthickness=0, bd=0)
        self.area_canvas.pack(padx=10, pady=(6, 14), fill='x')
        self.area_radius = 18
        self.area_pad = 8

        self.frame_exibicao = tk.Frame(self.area_canvas, bg=self.area_cor)
        self._area_window = self.area_canvas.create_window((0, 0), window=self.frame_exibicao, anchor='n')

        def _redesenhar_area(event=None):
            # redesenha painel arredondado
            w = self.area_canvas.winfo_width()
            h = max(self.frame_exibicao.winfo_reqheight() + 2 * self.area_pad, 160)
            self.area_canvas.config(height=h)
            self.area_canvas.coords(self._area_window, w // 2, self.area_pad)
            self.area_canvas.itemconfig(self._area_window, width=w - 2 * self.area_pad)
            desenhar_roundrect(self.area_canvas, 1, 1, w - 2, h - 2, self.area_radius, fill=self.area_cor, outline=self.area_border, width=1)

        self.area_canvas.bind("<Configure>", _redesenhar_area)
        self.frame_exibicao.bind("<Configure>", _redesenhar_area)

        # caixa de busca
        self.search_frame = tk.Frame(self.base, bg='#606060')
        self.search_frame.pack(fill='x', padx=10, pady=(0, 6))
        self.search_var = tk.StringVar()
        left_spacer = tk.Frame(self.search_frame, bg='#606060')
        left_spacer.pack(side='left', expand=True)
        self.search_entry = tk.Entry(
            self.search_frame, textvariable=self.search_var,
            fg='#ffffff', bg='#404040', insertbackground='white', relief='flat', width=30
        )
        self.search_entry.pack(side='left', padx=(0, 6), ipady=4)

        self.btn_clear_search = tk.Button(
            self.search_frame, text="X", width=6, command=lambda: self._limpar_pesquisa(),
            fg='white', bg='#1a1a1a', activebackground='#333333', activeforeground='white', bd=0
        )
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

        # botão reset
        self.btn_reset = self.criar_botao_arredondado(
            self.base, "Resetar escolhas", comando=self.resetar_escolhas, min_w=160, min_h=40
        )
        self.btn_reset.pack(pady=(2, 8))

        # área de eventos com scrollbar
        self.canvas_eventos = tk.Canvas(self.base, height=300, bg='#606060', highlightthickness=0)
        self.scroll_eventos = ttk.Scrollbar(self.base, orient='vertical', command=self.canvas_eventos.yview)
        self.canvas_eventos.configure(yscrollcommand=self.scroll_eventos.set)
        self.canvas_eventos.pack(side='left', fill='both', expand=True, padx=(10, 0))
        self.scroll_eventos.pack(side='right', fill='y')

        self.wrapper_eventos = tk.Frame(self.canvas_eventos, bg='#606060')
        self.wrapper_id = self.canvas_eventos.create_window((0, 0), window=self.wrapper_eventos, anchor='n')

        self.frame_eventos = tk.Frame(self.wrapper_eventos, bg='#606060')
        self.frame_eventos.pack(anchor='n', pady=10)
        
        # Repassa scroll se o mouse estiver em qualquer espaço vazio entre os eventos
        self.frame_eventos.bind("<MouseWheel>", lambda e: self.canvas_eventos.event_generate("<MouseWheel>", delta=e.delta))
        self.frame_eventos.bind("<Button-4>", lambda e: self.canvas_eventos.yview_scroll(-1, "units"))
        self.frame_eventos.bind("<Button-5>", lambda e: self.canvas_eventos.yview_scroll(1, "units"))


        def on_frame_configure(event):
            self.canvas_eventos.configure(scrollregion=self.canvas_eventos.bbox("all"))
        self.wrapper_eventos.bind("<Configure>", on_frame_configure)

        def on_canvas_configure(event):
            self.canvas_eventos.itemconfig(self.wrapper_id, width=event.width)
        self.canvas_eventos.bind("<Configure>", on_canvas_configure)

        # binds de scroll com limites
        def on_mousewheel(event):
            try:
                if not self.canvas_eventos or not self.canvas_eventos.winfo_exists():
                    return "break"
                if hasattr(event, "delta") and event.delta:
                    up = event.delta > 0
                    top, bottom = self.canvas_eventos.yview()
                    if up and top <= 0.0:
                        return "break"
                    if not up and bottom >= 1.0:
                        return "break"
                    self.canvas_eventos.yview_scroll(int(-1 * (event.delta / 120)), "units")
                    return "break"
            except Exception:
                return "break"

        def on_button4(event):
            try:
                if not self.canvas_eventos or not self.canvas_eventos.winfo_exists():
                    return "break"
                top, _ = self.canvas_eventos.yview()
                if top <= 0.0:
                    return "break"
                self.canvas_eventos.yview_scroll(-1, "units")
                return "break"
            except Exception:
                return "break"

        def on_button5(event):
            try:
                if not self.canvas_eventos or not self.canvas_eventos.winfo_exists():
                    return "break"
                _, bottom = self.canvas_eventos.yview()
                if bottom >= 1.0:
                    return "break"
                self.canvas_eventos.yview_scroll(1, "units")
                return "break"
            except Exception:
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

        # estruturas de controle
        self.imagens_exibidas = {}
        self.evento_expandido_atual = None
        self.img_refs = {}
        self.selecionado = None

        # dica inicial
        self._dica_visivel = False
        self._dica_widget = None

        # flags para janelas seletoras
        self.janela_cavala_aberta = False
        self.janela_cartas_aberta = False
        self.janela_avulsa_aberta = False

        # cache do estado de eventos
        self._estado_eventos_cache = {"selecionado": None, "filtro": ""}

        if not self.cv:
            messagebox.showwarning("Aviso", "Nenhuma cavala encontrada em 'cavalas/'.")
        if not self.c:
            messagebox.showwarning("Aviso", "Nenhuma carta encontrada em 'cartas/'.")

    # utilitários visuais delegando ao módulo widgets (mas preservando assinatura)
    def criar_botao_arredondado(self, parent, texto, comando=None, min_w=140, min_h=40, pad_x=16, pad_y=10, radius=14):
        return criar_botao_arredondado(parent, texto, comando, min_w, min_h, pad_x, pad_y, radius, self.btn_style)

    # seletor (cavala/cartas)
    def abrir_seletor_cavala(self):
        abrir_seletor_cavala(self)

    def _abrir_seletor_cartas_base(self, limite, ao_confirmar):
        return abrir_seletor_cartas(self, limite, ao_confirmar)

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

    # renderização principal
    def mostrar(self):
        for widget in self.frame_exibicao.winfo_children():
            widget.destroy()
        if not self._dica_visivel:
            for widget in self.frame_eventos.winfo_children():
                widget.destroy()

        self.imagens_exibidas.clear()
        self.img_refs.clear()
        self.selecionado = None

        # estado da busca
        if not self._search_active or self.search_var.get() == self._search_placeholder:
            self._search_active = False
            self.search_entry.config(fg='#bfbfbf')
            self.search_var.set(self._search_placeholder)
        self.search_entry.configure(state='normal')
        self.search_entry.bind("<FocusIn>", lambda e: self._on_search_focus_in())
        self.search_entry.bind("<FocusOut>", lambda e: self._on_search_focus_out())
        self.search_entry.focus_set()

        # cavala
        if self.cavala_selecionada:
            dados_cavala = self.cv.get(self.cavala_selecionada)
            if dados_cavala:
                caminho_img_cavala = os.path.join(BASE, dados_cavala.get("imagem", ""))
                try:
                    pil_img_cavala = Image.open(caminho_img_cavala).convert("RGBA")
                    pil_img_cavala_res = pil_img_cavala.resize((128, 128), Image.Resampling.LANCZOS)
                    img_colorida = ImageTk.PhotoImage(pil_img_cavala_res)
                    img_cinza = ImageTk.PhotoImage(ImageOps.grayscale(pil_img_cavala_res.convert("RGB")))
                except Exception:
                    img_colorida = img_cinza = None

                if img_colorida and img_cinza:
                    frame_cavala = tk.Frame(self.frame_exibicao, bg=self.area_cor)
                    frame_cavala.pack(side='left', padx=10)

                    def on_click_cavala():
                        self._remover_dica_inicial()
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

        # deck
        frame_cartas = tk.Frame(self.frame_exibicao, bg=self.area_cor)
        frame_cartas.pack(side='left', padx=20)

        for card_id in self.deck:
            dados_carta = self.card_by_id.get(card_id) or self.c.get(card_id)
            nome_carta = self.name_by_id.get(card_id, dados_carta.get("nome", "Carta") if dados_carta else "Carta")
            if not dados_carta:
                continue
            caminho_img_carta = os.path.join(BASE, card_id)
            try:
                pil_img_carta = Image.open(caminho_img_carta).convert("RGBA")
                pil_img_carta_res = pil_img_carta.resize((96, 96), Image.Resampling.LANCZOS)
                img_colorida = ImageTk.PhotoImage(pil_img_carta_res)
                img_cinza = ImageTk.PhotoImage(ImageOps.grayscale(pil_img_carta_res.convert("RGB")))
            except Exception as e:
                print(f"Erro ao carregar imagem da carta {nome_carta}: {e}")
                continue

            frame_carta = tk.Frame(frame_cartas, bg=self.area_cor)
            frame_carta.pack(side='left', padx=5)

            def on_click_carta(cid=card_id):
                self._remover_dica_inicial()
                self.atualizar_selecao(cid)

            btn_img_carta = tk.Button(
                frame_carta, image=img_cinza, borderwidth=0, command=on_click_carta,
                bg=self.area_cor, activebackground=self.area_cor, highlightthickness=0
            )
            btn_img_carta.image_colorida = img_colorida
            btn_img_carta.image_cinza = img_cinza
            btn_img_carta.pack()
            tk.Label(frame_carta, text=nome_carta, fg='white', bg=self.area_cor).pack()

            self.imagens_exibidas[card_id] = btn_img_carta
            self.img_refs[f'{card_id}_colorida'] = img_colorida
            self.img_refs[f'{card_id}_cinza'] = img_cinza

        # separador
        sep = criar_separador_vertical(self.frame_exibicao, altura=160, cor='#ffffff')
        sep.pack(side='left', padx=10)

        # avulsa
        avulsa_frame = tk.Frame(self.frame_exibicao, bg=self.area_cor)
        avulsa_frame.pack(side='left', padx=10)

        if self.carta_avulsa:
            dados_carta = self.card_by_id.get(self.carta_avulsa) or self.c.get(self.carta_avulsa)
            nome_carta = self.name_by_id.get(self.carta_avulsa, dados_carta.get("nome", "Carta") if dados_carta else "Carta")
            if dados_carta:
                caminho_img_carta = os.path.join(BASE, self.carta_avulsa)
                try:
                    pil_img_carta = Image.open(caminho_img_carta).convert("RGBA")
                    pil_img_carta_res = pil_img_carta.resize((96, 96), Image.Resampling.LANCZOS)
                    img_colorida = ImageTk.PhotoImage(pil_img_carta_res)
                    img_cinza = ImageTk.PhotoImage(ImageOps.grayscale(pil_img_carta_res.convert("RGB")))
                except Exception as e:
                    print(f"Erro ao carregar imagem da carta avulsa {nome_carta}: {e}")
                    img_colorida = img_cinza = None

                def on_click_avulsa(cid=self.carta_avulsa):
                    self._remover_dica_inicial()
                    self.atualizar_selecao(f"avulsa:{cid}")

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
                    tk.Label(frame_carta, text=nome_carta, fg='white', bg=self.area_cor).pack()

                    self.imagens_exibidas[f"avulsa:{self.carta_avulsa}"] = btn_img_carta
                    self.img_refs[f"avulsa:{self.carta_avulsa}_colorida"] = img_colorida
                    self.img_refs[f"avulsa:{self.carta_avulsa}_cinza"] = img_cinza

        # dica inicial
        if not self.cavala_selecionada and not self.deck and not self.carta_avulsa:
            self._mostrar_dica_inicial()
        else:
            self._remover_dica_inicial()
            self.mostrar_eventos(None)

    # busca
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

    # seleção e eventos
    def atualizar_selecao(self, selecionado):
        # clicar no já selecionado = desmarcar
        if self.selecionado == selecionado:
            btn = self.imagens_exibidas.get(selecionado)
            if btn:
                btn.config(image=btn.image_cinza)
                btn.image = btn.image_cinza
            self.selecionado = None
            self.mostrar_eventos(None)
            return

        # volta o anterior para cinza
        if self.selecionado is not None:
            btn_antigo = self.imagens_exibidas.get(self.selecionado)
            if btn_antigo:
                btn_antigo.config(image=btn_antigo.image_cinza)
                btn_antigo.image = btn_antigo.image_cinza

        # marca o novo
        btn_novo = self.imagens_exibidas.get(selecionado)
        if btn_novo:
            btn_novo.config(image=btn_novo.image_colorida)
            btn_novo.image = btn_novo.image_colorida
            self.selecionado = selecionado
            if isinstance(selecionado, str) and selecionado.startswith("avulsa:"):
                cid = selecionado.split(":", 1)[1]
                self.mostrar_eventos(cid)
            else:
                self.mostrar_eventos(selecionado)

    def mostrar_eventos(self, selecionado):
        # mantém dica se nada selecionado e dica ativa
        if self._dica_visivel and selecionado is None and not (self.cavala_selecionada or self.deck or self.carta_avulsa):
            return

        filtro = self._texto_filtro()

        # cache
        if (self._estado_eventos_cache.get("selecionado") == selecionado and
            self._estado_eventos_cache.get("filtro") == filtro and not getattr(self, '_events_preserved', False)):
            try:
                self.canvas_eventos.update_idletasks()
            except Exception:
                pass
            return

        # Se a seleção for uma carta avulsa, extrai o ID real e adiciona verificação
        if isinstance(selecionado, str) and selecionado.startswith("avulsa:"):
            self._ultima_selecao_avulsa = selecionado
            self._events_preserved = False  # Reseta ao trocar de carta

        self._estado_eventos_cache["selecionado"] = selecionado
        self._estado_eventos_cache["filtro"] = filtro
        

        # Se for carta avulsa, salva os eventos abertos antes de recarregar
        eventos_abertos = []
        if isinstance(selecionado, str) and selecionado.startswith("avulsa:"):
            for child in self.frame_eventos.winfo_children():
                if isinstance(child, EventoExpandivel):
                    if child.aberto:
                        eventos_abertos.append(child.evento_id)

        self._estado_eventos_cache["selecionado"] = selecionado
        self._estado_eventos_cache["filtro"] = filtro

        # Limpa a flag de preservação após usar
        preserving = getattr(self, '_events_preserved', False)
        if hasattr(self, '_events_preserved'):
            self._events_preserved = False

        for w in self.frame_eventos.winfo_children():
            w.destroy()
        self._remover_dica_inicial()

        self.canvas_eventos.yview_moveto(0)
        if selecionado is None:
            return
        if selecionado == 'cavala':
            self.mostrar_eventos_cavala()
        else:
                    # Verifica se é uma carta avulsa e ajusta o selecionado se necessário
            selecionado_real = selecionado
            if isinstance(selecionado, str) and selecionado.startswith("avulsa:"):
                selecionado_real = selecionado.split(":", 1)[1]
            self.mostrar_eventos_carta(selecionado_real)

                    # Se for avulsa, reabre eventos que estavam abertos
        if isinstance(selecionado, str) and selecionado.startswith("avulsa:"):
            for child in self.frame_eventos.winfo_children():
                if isinstance(child, EventoExpandivel) and child.evento_id in eventos_abertos:
                    child.toggle()  # Reabre o evento

    def mostrar_eventos_cavala(self):
        dados = self.cv.get(self.cavala_selecionada, {})
        filtro = self._texto_filtro()
        for cat, eventos in dados.get("eventos", {}).items():
            eventos_filtrados = [ev for ev in eventos if self._combina_filtro(ev.get('nome', ''), filtro)]
            if not eventos_filtrados:
                continue
            lbl_cat = tk.Label(self.frame_eventos, text=f"-- {cat} --", font=('Arial', 10, 'bold'), fg='white', bg='#606060')
            lbl_cat.pack(fill='x', pady=(10, 2))  # ou (6, 2) se for o segundo caso

            # repassar scroll pro canvas
            def _scroll_event_categoria(event):
                self.canvas_eventos.event_generate("<MouseWheel>", delta=event.delta)

            lbl_cat.bind("<MouseWheel>", _scroll_event_categoria)
            lbl_cat.bind("<Button-4>", lambda e: self.canvas_eventos.yview_scroll(-1, "units"))
            lbl_cat.bind("<Button-5>", lambda e: self.canvas_eventos.yview_scroll(1, "units"))

            for ev in eventos_filtrados:
                titulo = ev.get('nome', 'Evento')
                detalhes = ev.get('detalhes', '')
                ev_expand = EventoExpandivel(self.frame_eventos, titulo, detalhes)
                ev_expand.pack(fill='x', padx=10, pady=2)

    def mostrar_eventos_carta(self, card_id):
        dados_carta = self.card_by_id.get(card_id) or self.c.get(card_id)
        if not dados_carta:
            return
        filtro = self._texto_filtro()
        for cat, eventos in dados_carta.get("eventos", {}).items():
            eventos_filtrados = [ev for ev in eventos if self._combina_filtro(ev.get('nome', ''), filtro)]
            if not eventos_filtrados:
                continue
            lbl_cat = tk.Label(self.frame_eventos, text=f"-- {cat} --", font=('Arial', 10, 'bold'), fg='white', bg='#606060')
            lbl_cat.pack(fill='x', pady=(10, 2))  # ou (6, 2) se for o segundo caso

            # repassar scroll pro canvas
            def _scroll_event_categoria(event):
                self.canvas_eventos.event_generate("<MouseWheel>", delta=event.delta)

            lbl_cat.bind("<MouseWheel>", _scroll_event_categoria)
            lbl_cat.bind("<Button-4>", lambda e: self.canvas_eventos.yview_scroll(-1, "units"))
            lbl_cat.bind("<Button-5>", lambda e: self.canvas_eventos.yview_scroll(1, "units"))

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
        # prefixo (mantido); trocar para "in" para conter
        return str(titulo).lower().startswith(filtro)

    def _aplicar_filtro_eventos(self):
        if self.selecionado is None:
            for w in self.frame_eventos.winfo_children():
                w.destroy()
            self._mostrar_dica_inicial() if not (self.cavala_selecionada or self.deck or self.carta_avulsa) else None
            return
        if self.selecionado == 'cavala':
            self.mostrar_eventos('cavala')
        else:
            self.mostrar_eventos(self.selecionado)

    def _limpar_pesquisa(self):
        self.search_entry.configure(state='normal')
        self.search_entry.focus_set()
        self._search_active = True
        self.search_var.set("")
        self.search_entry.config(fg='#ffffff')
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

        # restaura botão de cavala padrão
        for w in self.slot_cavala.winfo_children():
            w.destroy()
        self.btn_cavala = self.criar_botao_arredondado(
            self.slot_cavala, "Escolha sua cavala", comando=self.abrir_seletor_cavala, min_w=180, min_h=40
        )
        self.btn_cavala.pack()

        self._mostrar_dica_inicial()
        self.canvas_eventos.update_idletasks()
        self.canvas_eventos.yview_moveto(0)


    # dica inicial
    def _mostrar_dica_inicial(self):
        if self._dica_visivel:
            return

        for w in self.frame_eventos.winfo_children():
            w.destroy()

        dica_canvas, dica_frame, _ = criar_painel_arredondado(
            self.wrapper_eventos,
            fill='#505050',
            outline='#6a6a6a',
            radius=14,
            pad=6,
            min_height=80,
            fill_parent_x=True,
            pady=(8, 8),
            padx=16
        )

        self._dica_widget = tk.Label(
            dica_frame,
            text="Confuso sobre como usar? Começe escolhendo uma cavala e selecione suas cartas (ou uma carta avulsa)\n Em seguida, clique na cavala ou na carta para ver os eventos dela.",
            fg='#ffff99',
            bg=dica_frame['bg'],
            font=("Arial", 13, "bold"),
            wraplength=900,
            justify="center"
        )
        self._dica_widget.pack(pady=14, padx=16)
        self._dica_visivel = True

        self.canvas_eventos.update_idletasks()
        self.canvas_eventos.yview_moveto(0)

    def _remover_dica_inicial(self):
        if self._dica_visivel:
            try:
                if self._dica_widget and self._dica_widget.winfo_exists():
                    parent = self._dica_widget.nametowidget(self._dica_widget.winfo_parent())
                    self._dica_widget.destroy()
                    if parent and parent.winfo_exists():
                        canvas_parent = parent.master
                        if isinstance(canvas_parent, tk.Canvas) and canvas_parent.winfo_exists():
                            canvas_parent.destroy()
            except Exception:
                pass
            self._dica_visivel = False
            self._dica_widget = None