# src/app/menu.py
import os
import threading
import random
import glob
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from .windows import criar_janela_centrada_custom
from .splash import mostrar_splash_custom
from ..data.loaders import carregar_cartas, carregar_cavalas
from .uma_app import UmaApp
from ..data.paths import asset_path

ICON_ICO = asset_path("icon_geral", "uma_icon.ico")
SOUNDS = asset_path("sounds")
IMAGENS_DIR = asset_path("imagens")

WIN_W, WIN_H = 1245, 715
COR_BG = "#606060"
COR_TB = "#303030"
FONTE_TIT = ("Arial", 16, "bold")
FONTE_BTN = ("Arial", 11, "bold")

SPLASH_DUR_MS = 5000

SND_MAIN = os.path.join(SOUNDS, "menu_1.wav")
SND_MAIN_R1 = os.path.join(SOUNDS, "menu_raro_1.wav")
SND_MAIN_R2 = os.path.join(SOUNDS, "menu_raro_2.wav")

SND_TRN_DIR = SOUNDS
SND_TRN_R1 = os.path.join(SOUNDS, "trainer_raro_1.wav")
SND_TRN_R2 = os.path.join(SOUNDS, "trainer_raro_2.wav")

def _carregar_e_tocar_wav(caminho):
    try:
        import winsound
        winsound.PlaySound(caminho, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        print(f"[AVISO] Não foi possível tocar áudio (winsound): {e}")

def _listar_sons(pasta, prefixo="trainer_", extensao=".wav", incluir_raros=False):
    try:
        nomes = os.listdir(pasta)
    except Exception as e:
        print(f"[SOM] Falha ao listar pasta '{pasta}': {e}")
        return []
    arquivos = []
    for nome in nomes:
        if not nome.lower().startswith(prefixo):
            continue
        if not nome.lower().endswith(extensao):
            continue
        if not incluir_raros and "raro" in nome.lower():
            continue
        arquivos.append(os.path.join(pasta, nome))
    arquivos.sort()
    return arquivos

def _sons_normais_e_raros(pasta, prefixo="trainer_", peso_normal=100, raros=(), peso_raro=4):
    lista = []
    normais = _listar_sons(pasta, prefixo=prefixo, extensao=".wav", incluir_raros=False)
    for n in normais:
        lista.append((n, peso_normal))
    for r in raros:
        if r and os.path.exists(r):
            lista.append((r, peso_raro))
        elif r:
            print(f"[SOM] Raro não encontrado: {r}")
    return lista

def _escolher_som_por_peso(pares):
    if not pares:
        return None
    arquivos = [p for p, _ in pares]
    pesos = [w for _, w in pares]
    return random.choices(arquivos, weights=pesos, k=1)[0]

def _carregar_gif_aleatorio(parent, largura=700, altura=400):
    padrao = os.path.join(IMAGENS_DIR, "main_menu_*.gif")
    arquivos = sorted(glob.glob(padrao))
    arquivos = [p for p in arquivos if any(p.endswith(f"main_menu_{i}.gif") for i in range(1, 13))]
    if not arquivos:
        return None
    try:
        pil = Image.open(random.choice(arquivos))
        frames, durations = [], []
        try:
            while True:
                frm = pil.convert("RGBA").copy()
                frm.thumbnail((largura, altura), Image.Resampling.LANCZOS)
                frames.append(frm)
                dur = pil.info.get("duration", 80)
                durations.append(max(20, int(dur)))
                pil.seek(pil.tell() + 1)
        except EOFError:
            pass
        if not frames:
            return None
        tk_frames = [ImageTk.PhotoImage(f, master=parent) for f in frames]
        lbl = tk.Label(parent, bg=COR_BG, bd=0, highlightthickness=0)
        lbl.pack()
        def anim(idx=0):
            if not lbl.winfo_exists():
                return
            lbl.config(image=tk_frames[idx])
            lbl.image = tk_frames[idx]
            next_idx = (idx + 1) % len(tk_frames)
            delay = durations[idx] if idx < len(durations) else 80
            lbl.after(delay, anim, next_idx)
        anim(0)
        return lbl
    except Exception as e:
        print(f"[AVISO] Falha ao carregar GIF: {e}")
        return None

def _mostrar_menu(root, content, estado):
    for w in content.winfo_children():
        w.destroy()

    frame = tk.Frame(content, bg=COR_BG)
    frame.pack(fill="both", expand=True)

    topo = tk.Frame(frame, bg=COR_BG)
    topo.pack(side="top", fill="x", pady=24)

    gif_lbl = _carregar_gif_aleatorio(topo, largura=700, altura=400)
    if not gif_lbl:
        tk.Label(topo, text="Menu Principal", fg="white", bg=COR_BG, font=FONTE_TIT).pack()

    centro_wrap = tk.Frame(frame, bg=COR_BG)
    centro_wrap.pack(expand=True)

    def btn(text, cmd):
        return tk.Button(
            centro_wrap, text=text, width=26, height=2, font=FONTE_BTN,
            fg="white", bg="#1a1a1a", activebackground="#333333", activeforeground="white",
            relief="flat", command=cmd
        )

    def em_breve():
        messagebox.showinfo(" ", "Em desenvolvimento!")

    btn("Em breve", em_breve).grid(row=0, column=0, padx=12, pady=10)
    btn("Em breve", em_breve).grid(row=0, column=1, padx=12, pady=10)
    btn("Trainer de Eventos", lambda: _fluxo_abrir_trainer(root, content, estado)).grid(
        row=1, column=0, columnspan=2, padx=12, pady=14
    )

def _fluxo_abrir_trainer(root, content, estado):
    # Esconde a janela inteira enquanto o splash do trainer está visível
    try:
        root.withdraw()
    except Exception:
        pass

    pares = _sons_normais_e_raros(
        SND_TRN_DIR,
        prefixo="trainer_",
        peso_normal=100,
        raros=(SND_TRN_R1, SND_TRN_R2),
        peso_raro=4
    )
    som = _escolher_som_por_peso(pares)
    if som:
        threading.Thread(target=_carregar_e_tocar_wav, args=(som,), daemon=True).start()

    def apos_splash_trainer():
        try:
            root.deiconify()
        except Exception:
            pass
        _construir_trainer(root, content, estado)

    mostrar_splash_custom(
        titulo="Trainer",
        rodape_linha1="Carregando trainer de eventos...",
        rodape_linha2="Aguarde um instante",
        logo_ico_path=ICON_ICO if os.path.exists(ICON_ICO) else None,
        sounds_dir=None,
        duracao_ms=SPLASH_DUR_MS,
        largura=560,
        altura=360,
        on_close=apos_splash_trainer,
        parent=root
    )

def _construir_trainer(root, content, estado):
    for w in content.winfo_children():
        w.destroy()

    tb = tk.Frame(content, bg=COR_TB)
    tb.pack(fill="x", side="top")
    body = tk.Frame(content, bg=COR_BG)
    body.pack(fill="both", expand=True)

    dummy_app = UmaApp(root, body, estado["cartas"], estado["cavalas"])

    def voltar():
        for w in content.winfo_children():
            w.destroy()
        _mostrar_menu(root, content, estado)

    volta_wrap = tk.Frame(tb, bg=COR_TB)
    volta_wrap.pack(side="left", padx=6, pady=4)

    try:
        btn_voltar = dummy_app.criar_botao_arredondado(
            volta_wrap, "◀ Voltar", comando=voltar, min_w=120, min_h=34
        )
        btn_voltar.pack()
    except Exception:
        tk.Button(volta_wrap, text="◀ Voltar", command=voltar).pack(padx=4, pady=4)

    for w in body.winfo_children():
        w.destroy()

    app = UmaApp(root, body, estado["cartas"], estado["cavalas"])
    app.mostrar()
    try:
        if not getattr(app, "cavala_selecionada", None) and not getattr(app, "deck", None) and not getattr(app, "carta_avulsa", None):
            app._mostrar_dica_inicial()
    except Exception:
        pass

def main():
    estado = {"cartas": {}, "cavalas": {}}

    def carregar_dados():
        try:
            estado["cartas"] = carregar_cartas(asset_path("cartas"))
            estado["cavalas"] = carregar_cavalas(asset_path("cavalas"))
            print(f"[DADOS] cartas: {len(estado['cartas'])} | cavalas: {len(estado['cavalas'])}")
        except Exception as e:
            print(f"[ERRO] Falha ao carregar dados: {e}")
            estado["cartas"], estado["cavalas"] = {}, {}

    t = threading.Thread(target=carregar_dados, daemon=True)
    t.start()

    root, content = criar_janela_centrada_custom(WIN_W, WIN_H, " ")

    # Ícone do root
    try:
        if os.path.exists(ICON_ICO):
            root.iconbitmap(ICON_ICO)
    except Exception as e:
        print(f"[AVISO] Falha ao definir ícone no menu: {e}")

    # Oculta root durante o splash inicial
    try:
        root.withdraw()
    except Exception:
        pass

    def apos_splash_inicial():
        def _quando_pronto():
            if t.is_alive():
                root.after(100, _quando_pronto)
                return
            try:
                root.deiconify()
            except Exception:
                pass
            _mostrar_menu(root, content, estado)
        _quando_pronto()

    mostrar_splash_custom(
        titulo="CAVALApostagem App",
        rodape_linha1="Iniciando app...",
        rodape_linha2="Feito por Braian Mezalira",
        logo_ico_path=ICON_ICO if os.path.exists(ICON_ICO) else None,
        sounds_dir=None,
        duracao_ms=SPLASH_DUR_MS,
        largura=560,
        altura=360,
        on_close=apos_splash_inicial,
        parent=root
    )

    # Som do splash inicial (opcional – se quiser usar a pasta sounds aqui)
    candidatos = []
    if os.path.exists(SND_MAIN):
        candidatos.append((SND_MAIN, 100))
    if os.path.exists(SND_MAIN_R1):
        candidatos.append((SND_MAIN_R1, 4))
    if os.path.exists(SND_MAIN_R2):
        candidatos.append((SND_MAIN_R2, 4))
    som = _escolher_som_por_peso(candidatos)
    if som:
        threading.Thread(target=_carregar_e_tocar_wav, args=(som,), daemon=True).start()

    root.mainloop()

if __name__ == "__main__":
    main()