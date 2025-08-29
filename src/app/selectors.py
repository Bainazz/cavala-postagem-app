import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageOps

# Notas:
# - Seletor de cavala e seletor de cartas (deck e avulsa) extraídos da UmaApp.
# - A UmaApp injeta callbacks e estado: deck, carta_avulsa, cavala_selecionada.
# - Mantém auto-confirm ao atingir limite e ordenação por raridade _SSR/_SR/_R.

from .widgets import criar_painel_arredondado, criar_botao_arredondado
from ..data.paths import BASE
from .windows import criar_toplevel_custom

def abrir_seletor_cavala(app):
    if app.janela_cavala_aberta:
        return
    app.janela_cavala_aberta = True

    largura = 1245
    altura = 715
    win, win_content, _fechar = criar_toplevel_custom(
        app.root, largura, altura, "Selecione sua Cavala",
        on_close=lambda: setattr(app, "janela_cavala_aberta", False)
    )
    win.transient(app.root)
    win.grab_set()
    win.focus_force()

    painel_canvas, grade_frame, _ = criar_painel_arredondado(
        win_content, fill='#505050', outline='#6a6a6a', radius=16, pad=10, min_height=670, pady=(10, 10), padx=10
    )

    header_btn = criar_botao_arredondado(grade_frame, "Cavalas disponíveis:", comando=None, min_w=220, min_h=40)
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
        for w in app.slot_cavala.winfo_children():
            w.destroy()
        btn = criar_botao_arredondado(
            app.slot_cavala, texto, comando=app.abrir_seletor_cavala, min_w=largura, min_h=40
        )
        btn.pack()
        app.btn_cavala = btn

    for nome, dados in app.cv.items():
        caminho_img = os.path.join(BASE, dados.get("imagem", ""))
        try:
            from PIL import Image
            pil_img = Image.open(caminho_img).convert("RGBA")
            # ADICIONE ESTA LINHA:
            pil_img = pil_img.resize((96, 96), Image.Resampling.LANCZOS)
            bg = Image.new("RGBA", pil_img.size, "#505050")
            pil_img = Image.alpha_composite(bg, pil_img)
            img = ImageTk.PhotoImage(pil_img)
        except Exception as e:
            print(f"Erro ao carregar imagem de {nome}: {e}")
            continue

        def selecionar_cavala(n=nome):
            app.cavala_selecionada = n
            atualizar_botao_cavala(f"Cavala selecionada: {n}", largura=220)
            app.mostrar()
            try:
                win.destroy()
            finally:
                app.janela_cavala_aberta = False

        frame_interno = tk.Frame(frame, bg='#505050')
        frame_interno.grid(row=linha, column=coluna, padx=10, pady=10)

        btn = tk.Button(
            frame_interno, image=img, command=selecionar_cavala,
            borderwidth=0, highlightthickness=0, bg='#1a1a1a', activebackground='#333333'
        )
        btn.image = img
        btn.pack()
        tk.Label(frame_interno, text=nome, fg='white', bg='#505050').pack()

        coluna += 1
        if coluna >= max_colunas:
            coluna = 0
            linha += 1


def abrir_seletor_cartas(app, limite, ao_confirmar):
    app.root.update_idletasks()
    scr_h = app.root.winfo_screenheight()
    largura = 1245
    altura = min(715, scr_h - 120)

    def _on_close_flag():
        if limite > 1:
            app.janela_cartas_aberta = False
        else:
            app.janela_avulsa_aberta = False

    win, win_content, fechar = criar_toplevel_custom(
        app.root, largura, altura, "Selecione seu deck", on_close=_on_close_flag
    )
    win.transient(app.root)
    win.grab_set()
    win.focus_force()

    _, tipo_frame, _ = criar_painel_arredondado(
        win_content, fill='#505050', outline='#6a6a6a', radius=14, pad=10, min_height=60, pady=(10, 6), padx=10
    )
    inner_tipos = tk.Frame(tipo_frame, bg=tipo_frame['bg'])
    inner_tipos.pack(anchor='center', pady=4)

    _, header_frame, _ = criar_painel_arredondado(
        win_content, fill='#505050', outline='#6a6a6a', radius=14, pad=10, min_height=60, pady=(0, 6), padx=10
    )
    painel_grade_canvas, conteiner_grade, _ = criar_painel_arredondado(
        win_content, fill='#505050', outline='#6a6a6a', radius=16, pad=10, min_height=450, pady=(0, 10), padx=10
    )

    contador_var = tk.StringVar()
    def atualiza_contador():
        val = len(app.deck) if limite > 1 else (1 if app.carta_avulsa else 0)
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

    btn_confirm = criar_botao_arredondado(
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
        canvas.bind_all("<Button-4>")
        canvas.bind_all("<Button-5>")
    def _unbind_wheel(_):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")
    canvas.bind("<Enter>", _bind_wheel)
    canvas.bind("<Leave>", _unbind_wheel)

    app.botoes_cartas = {}

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
            (card_id, dados) for card_id, dados in app.c.items()
            if tipo in card_id
        ]
        cartas_ordenadas = sorted(cartas_filtradas, key=lambda item: extrair_raridade(item[0]))

        for card_id, dados in cartas_ordenadas:
            img_path = os.path.join(BASE, card_id)
            nome = dados.get("nome", "Carta")
            try:
                pil_image = Image.open(img_path).convert("RGBA")
                # ADICIONE ESTA LINHA:
                pil_image = pil_image.resize((96, 96), Image.Resampling.LANCZOS)
                bg = Image.new("RGBA", pil_image.size, "#505050")
                pil_image_colorida = Image.alpha_composite(bg, pil_image)
                pil_image_cinza = ImageOps.grayscale(pil_image_colorida.convert("RGB"))
                img_colorida = ImageTk.PhotoImage(pil_image_colorida)
                img_cinza = ImageTk.PhotoImage(pil_image_cinza)
            except Exception as e:
                print(f"Erro ao carregar imagem da carta {nome}: {e}")
                continue

            app.card_by_id[card_id] = dados
            app.name_by_id[card_id] = nome

            def alternar_carta_normal(cid=card_id, btn_ref=None, colorida=None, cinza=None):
                if cid in app.deck:
                    app.deck.remove(cid)
                    btn_ref.config(image=cinza); btn_ref.image = cinza
                elif len(app.deck) < limite:
                    app.deck.append(cid)
                    btn_ref.config(image=colorida); btn_ref.image = colorida
                app._remover_dica_inicial()
                app.mostrar()
                atualiza_contador()
                if len(app.deck) == limite:
                    win.after(300, lambda: (ao_confirmar(), _close_and_reset()))

            def alternar_carta_avulsa(cid=card_id, btn_ref=None, colorida=None, cinza=None):
                if app.carta_avulsa == cid:
                    app.carta_avulsa = None
                    btn_ref.config(image=cinza); btn_ref.image = cinza
                else:
                    app.carta_avulsa = cid
                    btn_ref.config(image=colorida); btn_ref.image = colorida
                app._remover_dica_inicial()
                app.mostrar()
                atualiza_contador()
                if app.carta_avulsa:
                    win.after(300, lambda: (ao_confirmar(), _close_and_reset()))

            cell = tk.Frame(inner_grade, bg='#505050')
            cell.grid(row=linha, column=coluna, padx=10, pady=10)

            selecionada = ((limite > 1 and card_id in app.deck) or
                           (limite == 1 and app.carta_avulsa == card_id))
            imagem = img_colorida if selecionada else img_cinza

            btn = tk.Button(
                cell, image=imagem, borderwidth=0, highlightthickness=0,
                bg='#1a1a1a', activebackground='#333333'
            )
            btn.image = imagem
            btn.pack()
            tk.Label(cell, text=nome, fg='white', bg='#505050').pack()

            if limite > 1:
                btn.config(command=lambda cid=card_id, b=btn, c=img_colorida, g=img_cinza: alternar_carta_normal(cid, b, c, g))
            else:
                btn.config(command=lambda cid=card_id, b=btn, c=img_colorida, g=img_cinza: alternar_carta_avulsa(cid, b, c, g))

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
    win.protocol("WM_DELETE_WINDOW", _close_and_reset)
    win.bind("<Escape>", lambda e: _close_and_reset())
    return win