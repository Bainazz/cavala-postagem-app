import os
import threading
import wave
import random
import tkinter as tk
from PIL import Image, ImageTk

def _carregar_e_tocar_wav(caminho):
    try:
        import sys
        if sys.platform.startswith("win"):
            import winsound
            winsound.PlaySound(caminho, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            with wave.open(caminho, "rb"):
                pass
    except Exception as e:
        print(f"[AVISO] Falha ao tocar som '{caminho}': {e}")

def _escolher_som_random(sounds_dir):
    try:
        arquivos = [f for f in os.listdir(sounds_dir) if f.lower().endswith(".wav")]
        if not arquivos:
            return None
        raro = "cavalo_raro.wav"
        pesos = [1 if f == raro else 5 for f in arquivos]
        escolha = random.choices(arquivos, weights=pesos, k=1)[0]
        return os.path.join(sounds_dir, escolha)
    except Exception as e:
        print(f"[AVISO] Falha listando sons em '{sounds_dir}': {e}")
        return None

def mostrar_splash_custom(
    titulo="CAVALA Trainer",
    rodape_linha1="Feito por Braian Mezalira",
    rodape_linha2="Oferecimento: Uma Musume Pretty Derby - Cavalapostagem (facebook)",
    logo_ico_path=None,
    sounds_dir=None,
    duracao_ms=5000,
    largura=560,
    altura=360,
    on_close=None,
    parent=None
):
    # 1) Usa Toplevel filho (sem mainloop próprio)
    if parent is None:
        parent = tk._get_default_root()  # usa root atual
    splash = tk.Toplevel(parent)
    splash.overrideredirect(True)
    splash.configure(bg="#212121")

    # centraliza na tela (ou sobre o parent)
    parent.update_idletasks()
    try:
        sw, sh = parent.winfo_screenwidth(), parent.winfo_screenheight()
    except Exception:
        sw, sh = splash.winfo_screenwidth(), splash.winfo_screenheight()
    x = (sw // 2) - (largura // 2)
    y = (sh // 2) - (altura // 2)
    splash.geometry(f"{largura}x{altura}+{x}+{y}")

    # ícone do splash
    if logo_ico_path and os.path.exists(logo_ico_path):
        try:
            splash.iconbitmap(logo_ico_path)
        except Exception:
            pass

    cont = tk.Frame(splash, bg="#2b2b2b", bd=1, highlightthickness=1, highlightbackground="#141414")
    cont.pack(fill="both", expand=True)

    lbl_titulo = tk.Label(cont, text=titulo, fg="#ffffff", bg="#2b2b2b", font=("Arial", 16, "bold"))
    lbl_titulo.pack(pady=(16, 10))

    # exibe o ícone também como imagem grande no corpo (se existir)
    if logo_ico_path and os.path.exists(logo_ico_path):
        try:
            pil = Image.open(logo_ico_path).convert("RGBA")
            pil.thumbnail((160, 160), Image.Resampling.LANCZOS)
            img = ImageTk.PhotoImage(pil, master=splash)
            lbl_img = tk.Label(cont, image=img, bg="#2b2b2b")
            lbl_img.image = img
            lbl_img.pack(pady=(0, 8))
        except Exception as e:
            print(f"[AVISO] Falha ao renderizar logo do splash: {e}")

    lbl_loading = tk.Label(cont, text="Carregando", fg="#e0e0e0", bg="#2b2b2b", font=("Arial", 11))
    lbl_loading.pack(pady=(0, 6))
    dots = {"n": 0}
    anim_id = {"id": None}
    def anim():
        if not splash.winfo_exists():
            return
        dots["n"] = (dots["n"] + 1) % 4
        try:
            lbl_loading.config(text="Carregando" + "." * dots["n"])
        except tk.TclError:
            return
        anim_id["id"] = splash.after(300, anim)
    anim_id["id"] = splash.after(300, anim)

    rodape = tk.Frame(cont, bg="#2b2b2b")
    rodape.pack(side="bottom", fill="x", pady=(0, 10))
    tk.Label(rodape, text=rodape_linha1, fg="#bdbdbd", bg="#2b2b2b", font=("Arial", 10)).pack()
    tk.Label(rodape, text=rodape_linha2, fg="#9e9e9e", bg="#2b2b2b", font=("Arial", 9)).pack()

    # som opcional
    if sounds_dir:
        som = _escolher_som_random(sounds_dir)
        if som:
            threading.Thread(target=_carregar_e_tocar_wav, args=(som,), daemon=True).start()

    def fechar_splash():
        try:
            if anim_id["id"] is not None:
                splash.after_cancel(anim_id["id"])
        except Exception:
            pass
        try:
            splash.destroy()
        except Exception:
            pass
        if callable(on_close):
            try:
                on_close()
            except Exception as e:
                print(f"[AVISO] on_close do splash lançou erro: {e}")

    splash.after(duracao_ms, fechar_splash)
    # importante: retorna o Toplevel, sem chamar mainloop
    return splash