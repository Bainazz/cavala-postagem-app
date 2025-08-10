import sys
import ctypes
from ctypes import wintypes

# ——— WinAPI base ———
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
try:
    shell32 = ctypes.windll.shell32
    SetCurrentProcessExplicitAppUserModelID = shell32.SetCurrentProcessExplicitAppUserModelID
    SetCurrentProcessExplicitAppUserModelID.argtypes = [wintypes.LPCWSTR]
    SetCurrentProcessExplicitAppUserModelID.restype  = wintypes.HRESULT
except Exception:
    SetCurrentProcessExplicitAppUserModelID = None

# estilos janela
GWL_STYLE   = -16
GWL_EXSTYLE = -20
GWL_WNDPROC = -4

WS_CAPTION      = 0x00C00000
WS_THICKFRAME   = 0x00040000
WS_SYSMENU      = 0x00080000
WS_MINIMIZEBOX  = 0x00020000
WS_MAXIMIZEBOX  = 0x00010000

WS_EX_APPWINDOW = 0x00040000
WS_EX_TOOLWINDOW= 0x00000080

HWND_TOP = 0
SWP_NOMOVE        = 0x0002
SWP_NOSIZE        = 0x0001
SWP_NOZORDER      = 0x0004
SWP_FRAMECHANGED  = 0x0020

# mensagens e hit-tests
WM_NCHITTEST   = 0x0084
HTCLIENT       = 1
HTCAPTION      = 2
HTLEFT         = 10
HTRIGHT        = 11
HTTOP          = 12
HTTOPLEFT      = 13
HTTOPRIGHT     = 14
HTBOTTOM       = 15
HTBOTTOMLEFT   = 16
HTBOTTOMRIGHT  = 17

# prototypes
GetWindowLongW  = user32.GetWindowLongW
SetWindowLongW  = user32.SetWindowLongW
SetWindowPos    = user32.SetWindowPos

GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
GetWindowLongW.restype  = ctypes.c_long
SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
SetWindowLongW.restype  = ctypes.c_long
SetWindowPos.argtypes   = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
SetWindowPos.restype    = wintypes.BOOL

# LongPtr para subclass
GetWindowLongPtrW = user32.GetWindowLongPtrW
SetWindowLongPtrW = user32.SetWindowLongPtrW
CallWindowProcW   = user32.CallWindowProcW
GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
GetWindowLongPtrW.restype  = ctypes.c_void_p
SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
SetWindowLongPtrW.restype  = ctypes.c_void_p
CallWindowProcW.argtypes   = [ctypes.c_void_p, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM]
CallWindowProcW.restype    = ctypes.c_ssize_t

# cursor pos
GetCursorPos = user32.GetCursorPos
GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
GetCursorPos.restype  = wintypes.BOOL

def _get_hwnd(root):
    # helper para pegar HWND do Tk root
    try:
        root.update_idletasks()
        root.update()
    except Exception:
        pass
    try:
        hwnd_val = root.winfo_id()
        if not hwnd_val:
            return None
        hwnd = wintypes.HWND(hwnd_val)

        # Sobe para o verdadeiro toplevel "TkTopLevel"
        GetParent = user32.GetParent
        GetParent.argtypes = [wintypes.HWND]
        GetParent.restype = wintypes.HWND

        GetClassNameW = user32.GetClassNameW
        GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        GetClassNameW.restype  = ctypes.c_int

        buf = ctypes.create_unicode_buffer(256)
        cur = hwnd
        for _ in range(5):
            buf.value = ""
            GetClassNameW(cur, buf, 256)
            if buf.value == "TkTopLevel":
                return cur
            parent = GetParent(cur)
            if not parent:
                break
            cur = parent

        return hwnd
    except Exception:
        return None

def force_appwindow_root(widget, appid="CAVALA.Trainer.Main"):
    # aplica AppUserModelID, WS_EX_APPWINDOW e FRAMECHANGED
    try:
        SetCurrentProcessExplicitAppUserModelID(appid)
    except Exception:
        pass
    try:
        hwnd = _get_hwnd(widget)
        if not hwnd:
            return
        ex = GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex = (ex | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
        SetWindowLongW(hwnd, GWL_EXSTYLE, ex)
        SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)
        
        s2 = GetWindowLongW(hwnd, GWL_STYLE)
        ex2 = GetWindowLongW(hwnd, GWL_EXSTYLE)
        print(f"DEBUG: estilos depois -> STYLE=0x{s2:08X} EXSTYLE=0x{ex2:08X}")

    except Exception:
        pass