from pathlib import Path
from ..data.paths import asset_path
from ..win.winapi import SetCurrentProcessExplicitAppUserModelID

import sys
import tkinter as tk

# Notas:
# - Janela principal e toplevel custom (sem borda nativa), com barra de título custom.
# - Integração com WinAPI (drag/snap/resize) fica no módulo win.winapi.
# - Mantém os botões ✕ e —, com binds seguros para fechar/minimizar.
# - Corrige problema de minimização sem interferir em outras janelas

# Importações WinAPI (opcional, mas necessário para melhor funcionamento)
if sys.platform.startswith("win"):
    from ..win.winapi import (
        _get_hwnd, GetWindowLongW, SetWindowLongW, SetWindowPos,
        GWL_STYLE, WS_CAPTION, WS_THICKFRAME, WS_MAXIMIZEBOX, WS_SYSMENU, WS_MINIMIZEBOX,
        GWL_EXSTYLE, WS_EX_APPWINDOW, WS_EX_TOOLWINDOW, HWND_TOP,
        SWP_NOMOVE, SWP_NOSIZE, SWP_NOZORDER, SWP_FRAMECHANGED,
        SetCurrentProcessExplicitAppUserModelID, user32
    )


def criar_janela_centrada_custom(largura, altura, titulo="CAVALA Trainer"):
    root = tk.Tk()

    # Ícone
    try:
        ico_path = asset_path("icon_geral", "uma_icon.ico")
        if Path(ico_path).exists():
            root.iconbitmap(str(ico_path))
        else:
            print(f"[AVISO] Ícone não encontrado: {ico_path}")
    except Exception as e:
        print(f"[AVISO] Falha ao definir iconbitmap: {e}")

    # Centraliza
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = (sw // 2) - (largura // 2), (sh // 2) - (altura // 2)
    root.geometry(f"{largura}x{altura}+{x}+{y}")
    root.configure(bg="#404040")
    try:
        root.title(titulo)
    except Exception:
        pass

    # Remove moldura nativa
    root.overrideredirect(True)

    # Container com "borda" visual
    cont = tk.Frame(root, bg="#606060", bd=1, highlightthickness=1, highlightbackground="#303030")
    cont.pack(fill="both", expand=True)

    # Titlebar custom
    titlebar = tk.Frame(cont, bg="#303030")
    titlebar.pack(fill="x", side="top")

    # Arraste Python puro
    drag = {"ox": 0, "oy": 0}
    def on_press(e):
        drag["ox"], drag["oy"] = e.x_root, e.y_root
    def on_drag(e):
        dx = e.x_root - drag["ox"]
        dy = e.y_root - drag["oy"]
        drag["ox"], drag["oy"] = e.x_root, e.y_root
        try:
            root.geometry(f"+{root.winfo_x() + dx}+{root.winfo_y() + dy}")
        except Exception:
            pass
    titlebar.bind("<Button-1>", on_press)
    titlebar.bind("<B1-Motion>", on_drag)

    # Botões
    btn_fg, btn_bg, btn_bg_hover = "#ffffff", "#303030", "#444444"
    def make_title_btn(text, cmd):
        b = tk.Label(titlebar, text=text, fg=btn_fg, bg=btn_bg, width=3)
        b.bind("<Enter>", lambda e: b.config(bg=btn_bg_hover))
        b.bind("<Leave>", lambda e: b.config(bg=btn_bg))
        b.bind("<Button-1>", lambda e: cmd())
        return b

    def close_app():
        try:
            root.destroy()
        except Exception:
            pass

    # Minimização corrigida
    def minimize_app():
        try:
            # Se for Windows, usa API nativa para minimizar
            if sys.platform.startswith("win") and hasattr(user32, 'ShowWindow'):
                hwnd = _get_hwnd(root)
                if hwnd:
                    user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
                    return
            
            # Para outras plataformas, usa o método convencional
            # Mas apenas se a janela já estiver com moldura nativa (padrão)
            if not root.overrideredirect():
                root.iconify()
            else:
                # Se a janela tiver moldura custom, temporariamente remove a moldura
                # e depois restaura ao ser restaurada
                root._was_overriden = True
                root.overrideredirect(False)
                root.iconify()
        except Exception as e:
            print(f"Erro ao minimizar: {e}")
            # Último recurso
            try:
                root.iconify()
            except:
                pass
            
            # Restaurar a moldura custom se algo der errado
            if hasattr(root, '_was_overriden') and root._was_overriden:
                root.after(100, lambda: root.overrideredirect(True))

    btn_close = make_title_btn("✕", close_app)
    btn_close.pack(side="right", padx=(0, 6), pady=1)
    btn_min = make_title_btn("—", minimize_app)
    btn_min.pack(side="right", padx=(0, 2), pady=1)

    lbl_title = tk.Label(titlebar, text=titulo, fg="#ffffff", bg="#303030", font=("Arial", 11, "bold"))
    lbl_title.pack(side="top", pady=4)

    content = tk.Frame(cont, bg="#606060")
    content.pack(fill="both", expand=True)

    # Função para restaurar a moldura custom quando a janela é restaurada
    def on_restore(event=None):
        try:
            # Verifica se precisamos restaurar a moldura custom
            if hasattr(root, '_was_overriden') and root._was_overriden:
                # Adiciona um pequeno atraso para garantir que a janela já está restaurada
                root.after(100, lambda: root.overrideredirect(True))
                
                # Garante que a janela fique visível e no topo
                root.lift()
                root.attributes('-topmost', True)
                root.after(1, lambda: root.attributes('-topmost', False))
        except Exception as e:
            print(f"Erro ao restaurar janela: {e}")
        return "break"

    # Bind para eventos de mapeamento (restauração)
    root.bind("<Map>", on_restore)
    


    # Bind para eventos de foco (quando a janela ganha/perde foco)
    def focus_in_handler(_):
        try:
            # Quando o aplicativo ganha o foco, garante que a moldura customizada está ativa
            if hasattr(root, "_is_custom") and root._is_custom:
                root.overrideredirect(True)
                
                # Se a última seleção era uma carta avulsa, recarrega seus eventos
                if hasattr(root.master, '_ultima_selecao_avulsa') and root.master._ultima_selecao_avulsa:
                    # Marca que estamos preservando o estado dos eventos
                    selecao = root.master._ultima_selecao_avulsa

                    # Força uma recarga imediata dos eventos
                    root.master.mostrar_eventos(selecao)

                    # Adiciona pequeno atraso para garantir que os eventos estão atualizados
                    root.master.after(50, lambda: root.master.mostrar_eventos(selecao))
                    
                # Adiciona outro atraso para garantir que qualquer fechamento acidental é revertido
                root.master.after(200, lambda: root.master.mostrar_eventos(selecao))
        except Exception as e:
            print(f"Erro ao reexibir eventos da carta avulsa: {e}")
    
    # Bind para eventos de foco (quando a janela ganha/perde foco)
    root.bind("<FocusIn>", focus_in_handler)
    
    def focus_out_handler(event):
        # Não faz nada ao perder o foco para evitar conflitos
        return "break"
    
    root.bind("<FocusOut>", focus_out_handler)

    # Aplicar estilo WinAPI para bordas/Alt+Tab/taskbar e hit-test (drag/snap/resize)
    if sys.platform.startswith("win"):
        def _aplicar_estilo(hwnd):
            try:
                style = GetWindowLongW(hwnd, GWL_STYLE)
                style &= ~(WS_CAPTION | WS_THICKFRAME | WS_MAXIMIZEBOX)
                style |= (WS_SYSMENU | WS_MINIMIZEBOX)
                SetWindowLongW(hwnd, GWL_STYLE, style)

                ex = GetWindowLongW(hwnd, GWL_EXSTYLE)
                ex = (ex | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
                SetWindowLongW(hwnd, GWL_EXSTYLE, ex)

                SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0,
                             SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)
            except Exception as e:
                print(f"[WINAPI] estilo: {e}")

        def _instalar_estilo():
            try:
                hwnd = _get_hwnd(root)
                if not hwnd:
                    root.after(80, _instalar_estilo)
                    return
                try:
                    SetCurrentProcessExplicitAppUserModelID("CAVALA.Trainer.Main")
                except Exception:
                    pass
                _aplicar_estilo(hwnd)
                root.after(120, lambda: _aplicar_estilo(hwnd))
            except Exception as e:
                print(f"[WINAPI] instalar: {e}")

        root.after(100, _instalar_estilo)

    root.bind("<Escape>", lambda e: close_app())

    return root, content


def criar_toplevel_custom(parent, largura, altura, titulo="Janela", on_close=None):
    # cria Toplevel sem bordas com barra de título custom
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

    # barra de título custom (arrastar janela)
    titlebar = tk.Frame(cont, bg='#303030')
    titlebar.pack(fill='x', side='top')

    def start_move(e):
        win._ox, win._oy = e.x_root, e.y_root
    def do_move(e):
        dx = e.x_root - getattr(win, "_ox", e.x_root)
        dy = e.y_root - getattr(win, "_oy", e.y_root)
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
    
    # Minimização corrigida para toplevel também
    def minimize_win():
        try:
            # Se for Windows, usa API nativa para minimizar
            if sys.platform.startswith("win") and hasattr(user32, 'ShowWindow'):
                hwnd = _get_hwnd(win)
                if hwnd:
                    user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
                    return
            
            # Para outras plataformas, usa o método convencional
            # Mas apenas se a janela já estiver com moldura nativa (padrão)
            if not win.overrideredirect():
                win.iconify()
            else:
                # Se a janela tiver moldura custom, temporariamente remove a moldura
                # e depois restaura ao ser restaurada
                win._was_overriden = True
                win.overrideredirect(False)
                win.iconify()
        except Exception as e:
            print(f"Erro ao minimizar: {e}")
            # Último recurso
            try:
                win.iconify()
            except:
                pass
                
            # Restaurar a moldura custom se algo der errado
            if hasattr(win, '_was_overriden') and win._was_overriden:
                win.after(100, lambda: win.overrideredirect(True))


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

    tk.Label(titlebar, text=titulo, fg='#ffffff', bg='#303030', font=("Arial", 11, "bold")).pack(side='top', pady=4)

    content = tk.Frame(cont, bg='#606060')
    content.pack(fill='both', expand=True)

    # Função para restaurar a moldura custom quando a janela é restaurada
    def on_restore(event=None):
        try:
            # Verifica se precisamos restaurar a moldura custom
            if hasattr(win, '_was_overriden') and win._was_overriden:
                # Adiciona um pequeno atraso para garantir que a janela já está restaurada
                win.after(100, lambda: win.overrideredirect(True))
                
                # Garante que a janela fique visível e no topo
                win.lift()
                win.attributes('-topmost', True)
                win.after(1, lambda: win.attributes('-topmost', False))
        except Exception as e:
            print(f"Erro ao restaurar janela: {e}")
        return "break"

    # Bind para eventos de mapeamento (restauração)
    win.bind("<Map>", on_restore)
    
    # Bind para eventos de foco (quando a janela ganha/perde foco)
    win.bind("<FocusIn>", on_restore)
    
    def focus_out_handler(event):
        # Não faz nada ao perder o foco para evitar conflitos
        return "break"
    
    win.bind("<FocusOut>", focus_out_handler)

    win.bind("<Escape>", lambda e: close_win())
    
    def fechar():
        # Por via das dúvidas, fecha limpando binds globais de scroll
        try:
            win.unbind_all("<MouseWheel>")
            win.unbind_all("<Button-4>")
            win.unbind_all("<Button-5>")
        except Exception:
            pass
        close_win()

    return win, content, fechar