import tkinter as tk
from tkinter import ttk
import json, os, random, threading, time, winsound, csv, winreg
from datetime import datetime, time as dtime
from winotify import Notification, audio

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

APP_DIR     = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, "config.json")
STATS_FILE  = os.path.join(APP_DIR, "stats.json")
HIST_FILE   = os.path.join(APP_DIR, "historial.csv")
APP_NAME    = "PausasActivas"
APP_PATH    = os.path.abspath(__file__)

DEFAULT_CONFIG = {
    "intervalo_min": 45,
    "duracion_pausa_min": 5,
    "hora_inicio": "08:00",
    "hora_fin": "18:00",
    "ejercicios_activos": [],
    "sonido": True,
    "posponer_min": 10,
    "autoarranque": False,
    "meta_pausas": 6,
}

EJERCICIOS = [
    {"id":"cuello",  "nombre":"Estiramiento de cuello",  "icono":"🧘", "pasos":["Inclina la cabeza a la derecha (10 seg)","Inclina la cabeza a la izquierda (10 seg)","Gira suavemente en circulos (3 veces)"]},
    {"id":"hombros", "nombre":"Estiramiento de hombros", "icono":"💪", "pasos":["Lleva el brazo derecho al pecho y sujetalo (10 seg)","Repite con el brazo izquierdo","Sube los hombros hasta las orejas y suelta (5 veces)"]},
    {"id":"espalda", "nombre":"Estiramiento de espalda", "icono":"🏃", "pasos":["Parate y estira los brazos hacia arriba (10 seg)","Inclinate hacia adelante y toca tus pies (10 seg)","Gira el tronco a cada lado (5 veces)"]},
    {"id":"visual",  "nombre":"Descanso visual",         "icono":"👁️", "pasos":["Mira un objeto lejano 6+ metros por 20 seg","Cierra los ojos y apoyalos con las palmas (10 seg)","Parpadea rapidamente 10 veces"]},
    {"id":"manos",   "nombre":"Ejercicio de manos",      "icono":"✋", "pasos":["Abre y cierra los punos (10 veces)","Gira las munecas en circulos (5 por lado)","Estira los dedos hacia atras suavemente (10 seg)"]},
    {"id":"sentad",  "nombre":"Sentadillas rapidas",     "icono":"🏋️", "pasos":["Parate con pies al ancho de los hombros","Baja lentamente hasta 90 grados (5 veces)","Manten la espalda recta en todo momento"]},
    {"id":"respira", "nombre":"Respiracion profunda",    "icono":"🌬️", "pasos":["Inhala profundo por 4 segundos","Reten el aire 4 segundos","Exhala lentamente por 6 segundos (repite 5 veces)"]},
    {"id":"caminar", "nombre":"Caminar",                 "icono":"🚶", "pasos":["Levantate y camina al menos 50 pasos","Sube y baja escaleras si es posible","Regresa y estira las piernas brevemente"]},
    {"id":"postura", "nombre":"Postura de poder",        "icono":"🧍", "pasos":["Parate derecho, pies al ancho de los hombros","Hombros hacia atras y abajo, pecho al frente","Menton paralelo al piso, manten 30 segundos respirando profundo"]},
]

FRASES = [
    "Excelente! Tu cuerpo te lo agradece.",
    "Cada pausa es una inversion en tu salud.",
    "Bien hecho! Sigue asi.",
    "Tu productividad mejora con cada descanso.",
    "Eres constante. Eso marca la diferencia.",
    "Pequenos habitos, grandes cambios.",
    "Tu espalda y tus ojos te lo agradecen.",
    "Pausa completada. Vuelves mas fuerte.",
]

BG="#0F1117"; BG2="#1A1D27"; BG3="#252836"; ACCENT="#6C63FF"; ACCENT2="#FF6584"
GREEN="#43D9AD"; YELLOW="#F5C542"; TEXT="#E8E8F0"; TEXT_DIM="#7B7D8E"; BORDER="#2E3148"
TRAY_ACTIVE=(108,99,255); TRAY_PAUSED=(123,125,142); TRAY_OFF=(255,101,132)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f: c=json.load(f)
        for k,v in DEFAULT_CONFIG.items(): c.setdefault(k,v)
        if not c["ejercicios_activos"]: c["ejercicios_activos"]=[e["id"] for e in EJERCICIOS]
        return c
    c=dict(DEFAULT_CONFIG); c["ejercicios_activos"]=[e["id"] for e in EJERCICIOS]
    return c

def save_config(cfg):
    with open(CONFIG_FILE,"w") as f: json.dump(cfg,f,indent=2)

def load_stats():
    today=datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE) as f: s=json.load(f)
        if s.get("fecha")!=today:
            racha=s.get("racha",0)
            ayer_ok=s.get("meta_cumplida",False)
            s={"fecha":today,"completadas":0,"saltadas":0,"historial":[],
               "racha":racha+1 if ayer_ok else 0,"meta_cumplida":False}
        return s
    return {"fecha":today,"completadas":0,"saltadas":0,"historial":[],"racha":0,"meta_cumplida":False}

def save_stats(s):
    with open(STATS_FILE,"w") as f: json.dump(s,f,indent=2)

def append_csv(row):
    exists=os.path.exists(HIST_FILE)
    with open(HIST_FILE,"a",newline="",encoding="utf-8") as f:
        w=csv.writer(f)
        if not exists: w.writerow(["fecha","hora","ejercicio","estado"])
        w.writerow(row)

def in_active_hours(cfg):
    try:
        now=datetime.now().time()
        h0,m0=map(int,cfg["hora_inicio"].split(":")); h1,m1=map(int,cfg["hora_fin"].split(":"))
        return dtime(h0,m0)<=now<=dtime(h1,m1)
    except: return True

def fmt_time(s):
    m,s=divmod(max(0,int(s)),60); return f"{m:02d}:{s:02d}"

def play_alert():
    try:
        for freq,dur in [(880,120),(0,60),(1100,180)]:
            if freq: winsound.Beep(freq,dur)
            else: time.sleep(dur/1000)
    except: pass

def make_tray_icon(color=(108,99,255),size=64):
    img=Image.new("RGBA",(size,size),(0,0,0,0))
    d=ImageDraw.Draw(img)
    d.ellipse([4,4,size-4,size-4],fill=color+(255,))
    d.text((size//2-6,size//2-10),"P",fill=(255,255,255,255))
    return img

def set_autoarranque(enable):
    key=winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                       r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_SET_VALUE)
    try:
        if enable: winreg.SetValueEx(key,APP_NAME,0,winreg.REG_SZ,f'python "{APP_PATH}"')
        else:
            try: winreg.DeleteValue(key,APP_NAME)
            except FileNotFoundError: pass
    finally: winreg.CloseKey(key)

def get_autoarranque():
    try:
        key=winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_READ)
        winreg.QueryValueEx(key,APP_NAME); winreg.CloseKey(key); return True
    except: return False

def send_win_notification(title,msg):
    try:
        toast=Notification(app_id=APP_NAME,title=title,msg=msg,duration="short")
        toast.set_audio(audio.Default,loop=False); toast.show()
    except: pass

class PausaWindow(tk.Toplevel):
    def __init__(self,parent,ejercicio,duracion_sec,on_done,on_skip,countdown_pct):
        super().__init__(parent)
        self.on_done=on_done; self.on_skip=on_skip
        self.remaining=duracion_sec; self.ejercicio=ejercicio; self._job=None
        self.title("Pausa Activa"); self.configure(bg=BG); self.resizable(False,False)
        self.attributes("-topmost",True); self._build(countdown_pct); self._center(); self._tick()
        self.protocol("WM_DELETE_WINDOW",self._skip)

    def _build(self,pct):
        tk.Label(self,text="PAUSA ACTIVA",font=("Segoe UI",11,"bold"),bg=BG,fg=ACCENT).pack(pady=(28,0))
        tk.Label(self,text=self.ejercicio["icono"],font=("Segoe UI Emoji",52),bg=BG).pack(pady=(8,0))
        tk.Label(self,text=self.ejercicio["nombre"],font=("Segoe UI",18,"bold"),bg=BG,fg=TEXT).pack()
        tk.Frame(self,bg=BORDER,height=1,width=340).pack(pady=14)
        fp=tk.Frame(self,bg=BG2,highlightthickness=1,highlightbackground=BORDER)
        fp.pack(padx=32,fill="x",pady=(0,12))
        for i,paso in enumerate(self.ejercicio["pasos"],1):
            r=tk.Frame(fp,bg=BG2); r.pack(fill="x",padx=16,pady=6)
            tk.Label(r,text=f"{i}",font=("Segoe UI",9,"bold"),bg=ACCENT,fg="white",width=2).pack(side="left",padx=(0,10))
            tk.Label(r,text=paso,font=("Segoe UI",10),bg=BG2,fg=TEXT,wraplength=280,justify="left").pack(side="left")
        self.lbl_t=tk.Label(self,text=fmt_time(self.remaining),font=("Courier New",36,"bold"),bg=BG,fg=GREEN)
        self.lbl_t.pack(pady=(8,4))
        tk.Label(self,text="tiempo restante",font=("Segoe UI",9),bg=BG,fg=TEXT_DIM).pack()
        self.pb=ttk.Progressbar(self,orient="horizontal",length=340,mode="determinate",maximum=self.remaining,value=self.remaining)
        s=ttk.Style(self); s.theme_use("default")
        s.configure("g.Horizontal.TProgressbar",troughcolor=BG3,background=GREEN,bordercolor=BG3,lightcolor=GREEN,darkcolor=GREEN)
        self.pb.configure(style="g.Horizontal.TProgressbar"); self.pb.pack(padx=32,pady=12)
        tk.Button(self,text="Saltar pausa",font=("Segoe UI",9),bg=BG3,fg=TEXT_DIM,bd=0,cursor="hand2",
                  activebackground=BG3,activeforeground=TEXT,command=self._skip,relief="flat").pack(pady=(0,24))

    def _center(self):
        self.update_idletasks()
        w,h=self.winfo_width(),self.winfo_height(); sw,sh=self.winfo_screenwidth(),self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def _tick(self):
        if self.remaining<=0: self._done(); return
        self.lbl_t.config(text=fmt_time(self.remaining))
        self.pb["value"]=self.remaining; self.remaining-=1
        self._job=self.after(1000,self._tick)

    def _done(self):
        if self._job: self.after_cancel(self._job)
        self.destroy(); self.on_done()

    def _skip(self):
        if self._job: self.after_cancel(self._job)
        self.destroy(); self.on_skip()

class StatsWindow(tk.Toplevel):
    def __init__(self,parent,stats,meta):
        super().__init__(parent)
        self.title("Estadisticas"); self.configure(bg=BG); self.resizable(False,False)
        self.attributes("-topmost",True)
        total=stats["completadas"]+stats["saltadas"]
        pct=int(stats["completadas"]/total*100) if total else 0
        meta_ok=stats["completadas"]>=meta
        tk.Label(self,text="Estadisticas de hoy",font=("Segoe UI",13,"bold"),bg=BG,fg=ACCENT).pack(pady=(24,16))
        frame=tk.Frame(self,bg=BG2,highlightthickness=1,highlightbackground=BORDER); frame.pack(padx=28,fill="x")
        rows=[
            ("Pausas completadas",f"{stats['completadas']} / {meta}",GREEN),
            ("Pausas saltadas",str(stats["saltadas"]),ACCENT2),
            ("Tasa de exito",f"{pct}%",ACCENT),
            ("Racha actual",f"{stats.get('racha',0)} dias consecutivos",YELLOW),
            ("Meta diaria",f"{'CUMPLIDA' if meta_ok else 'En progreso'}",GREEN if meta_ok else TEXT_DIM),
        ]
        for label,val,color in rows:
            r=tk.Frame(frame,bg=BG2); r.pack(fill="x",padx=16,pady=8)
            tk.Label(r,text=label,font=("Segoe UI",10),bg=BG2,fg=TEXT_DIM,anchor="w").pack(side="left")
            tk.Label(r,text=val,font=("Segoe UI",11,"bold"),bg=BG2,fg=color).pack(side="right")
        if stats["historial"]:
            tk.Label(self,text="Ultimas pausas",font=("Segoe UI",9,"bold"),bg=BG,fg=TEXT_DIM).pack(pady=(12,4))
            for entry in stats["historial"][-5:][::-1]:
                color=GREEN if entry["estado"]=="completada" else ACCENT2
                tk.Label(self,text=f"{entry['hora']}  {entry['ejercicio']}  [{entry['estado']}]",
                         font=("Segoe UI",9),bg=BG,fg=color).pack()
        bf=tk.Frame(self,bg=BG); bf.pack(pady=16)
        tk.Button(bf,text="Exportar CSV",font=("Segoe UI",9),bg=BG3,fg=TEXT,bd=0,cursor="hand2",
                  activebackground=BORDER,activeforeground=TEXT,relief="flat",padx=12,pady=6,
                  command=lambda:os.startfile(HIST_FILE) if os.path.exists(HIST_FILE) else None).pack(side="left",padx=6)
        tk.Button(bf,text="Cerrar",font=("Segoe UI",10,"bold"),bg=ACCENT,fg="white",bd=0,
                  cursor="hand2",activebackground="#5A52D5",activeforeground="white",
                  relief="flat",padx=24,pady=6,command=self.destroy).pack(side="left",padx=6)
        self.update_idletasks()
        w,h=self.winfo_width(),self.winfo_height(); sw,sh=self.winfo_screenwidth(),self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

class ConfigWindow(tk.Toplevel):
    def __init__(self,parent,cfg,on_save):
        super().__init__(parent)
        self.cfg=dict(cfg); self.on_save=on_save
        self.title("Configuracion"); self.configure(bg=BG); self.resizable(False,False)
        self.attributes("-topmost",True); self._build(); self._center()

    def _field(self,parent,label,var,row):
        tk.Label(parent,text=label,font=("Segoe UI",10),bg=BG2,fg=TEXT_DIM,anchor="w").grid(row=row,column=0,sticky="w",padx=16,pady=8)
        tk.Entry(parent,textvariable=var,font=("Segoe UI",11),bg=BG3,fg=TEXT,insertbackground=TEXT,
                 relief="flat",bd=0,width=10,highlightthickness=1,highlightbackground=BORDER,
                 highlightcolor=ACCENT).grid(row=row,column=1,padx=16,pady=8,sticky="e")

    def _build(self):
        tk.Label(self,text="Configuracion",font=("Segoe UI",13,"bold"),bg=BG,fg=ACCENT).pack(pady=(24,12))
        frame=tk.Frame(self,bg=BG2,highlightthickness=1,highlightbackground=BORDER); frame.pack(padx=28,fill="x")
        self.v_int=tk.StringVar(value=str(self.cfg["intervalo_min"]))
        self.v_dur=tk.StringVar(value=str(self.cfg["duracion_pausa_min"]))
        self.v_ini=tk.StringVar(value=self.cfg["hora_inicio"])
        self.v_fin=tk.StringVar(value=self.cfg["hora_fin"])
        self.v_pos=tk.StringVar(value=str(self.cfg["posponer_min"]))
        self.v_meta=tk.StringVar(value=str(self.cfg["meta_pausas"]))
        self._field(frame,"Intervalo entre pausas (min)",self.v_int,0)
        self._field(frame,"Duracion de la pausa (min)",  self.v_dur,1)
        self._field(frame,"Hora inicio (HH:MM)",         self.v_ini,2)
        self._field(frame,"Hora fin (HH:MM)",            self.v_fin,3)
        self._field(frame,"Minutos para posponer",       self.v_pos,4)
        self._field(frame,"Meta de pausas diarias",      self.v_meta,5)
        sep=tk.Frame(self,bg=BORDER,height=1); sep.pack(fill="x",padx=28,pady=12)
        tk.Label(self,text="Opciones",font=("Segoe UI",10,"bold"),bg=BG,fg=TEXT_DIM).pack()
        self.v_snd=tk.BooleanVar(value=self.cfg["sonido"])
        self.v_auto=tk.BooleanVar(value=get_autoarranque())
        for var,txt in [(self.v_snd,"Activar sonido al iniciar pausa"),
                        (self.v_auto,"Iniciar con Windows (autoarranque)")]:
            tk.Checkbutton(self,text=txt,variable=var,font=("Segoe UI",10),bg=BG,fg=TEXT,
                           selectcolor=BG3,activebackground=BG,activeforeground=TEXT).pack(anchor="w",padx=32,pady=2)
        sep2=tk.Frame(self,bg=BORDER,height=1); sep2.pack(fill="x",padx=28,pady=12)
        tk.Label(self,text="Ejercicios activos",font=("Segoe UI",10,"bold"),bg=BG,fg=TEXT_DIM).pack()
        ef=tk.Frame(self,bg=BG2,highlightthickness=1,highlightbackground=BORDER); ef.pack(padx=28,fill="x",pady=(4,0))
        self.ej_vars={}
        activos=self.cfg.get("ejercicios_activos",[e["id"] for e in EJERCICIOS])
        for ej in EJERCICIOS:
            v=tk.BooleanVar(value=ej["id"] in activos); self.ej_vars[ej["id"]]=v
            r=tk.Frame(ef,bg=BG2); r.pack(fill="x",padx=12,pady=2)
            tk.Checkbutton(r,text=f"{ej['icono']} {ej['nombre']}",variable=v,
                           font=("Segoe UI",9),bg=BG2,fg=TEXT,selectcolor=BG3,
                           activebackground=BG2,activeforeground=TEXT).pack(side="left")
        self.lbl_err=tk.Label(self,text="",font=("Segoe UI",9),bg=BG,fg=ACCENT2); self.lbl_err.pack(pady=(8,0))
        tk.Button(self,text="Guardar",font=("Segoe UI",10,"bold"),bg=ACCENT,fg="white",bd=0,
                  cursor="hand2",activebackground="#5A52D5",activeforeground="white",
                  relief="flat",padx=24,pady=8,command=self._save).pack(pady=16)

    def _save(self):
        try:
            iv=int(self.v_int.get()); dv=int(self.v_dur.get())
            pv=int(self.v_pos.get()); mv=int(self.v_meta.get())
            assert iv>0 and dv>0 and pv>0 and mv>0
            h0,m0=map(int,self.v_ini.get().split(":")); h1,m1=map(int,self.v_fin.get().split(":"))
            assert 0<=h0<24 and 0<=m0<60 and 0<=h1<24 and 0<=m1<60
            assert (h1,m1)>(h0,m0),"Hora fin debe ser mayor que hora inicio"
        except AssertionError as e:
            self.lbl_err.config(text=f"Error: {e}" if str(e) else "Revisa los valores"); return
        except:
            self.lbl_err.config(text="Revisa los valores ingresados"); return
        activos=[eid for eid,v in self.ej_vars.items() if v.get()]
        if not activos: self.lbl_err.config(text="Selecciona al menos un ejercicio"); return
        set_autoarranque(self.v_auto.get())
        self.cfg.update({"intervalo_min":iv,"duracion_pausa_min":dv,"hora_inicio":self.v_ini.get(),
                         "hora_fin":self.v_fin.get(),"posponer_min":pv,"sonido":self.v_snd.get(),
                         "ejercicios_activos":activos,"meta_pausas":mv})
        self.on_save(self.cfg); self.destroy()

    def _center(self):
        self.update_idletasks()
        w,h=self.winfo_width(),self.winfo_height(); sw,sh=self.winfo_screenwidth(),self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.cfg=load_config(); self.stats=load_stats()
        self.remaining=self.cfg["intervalo_min"]*60
        self.running=True; self.pausa_open=False; self._job=None; self._tray=None
        self._last_ej=""; self._total_sec=self.cfg["intervalo_min"]*60
        self.title("Pausas Activas"); self.configure(bg=BG); self.resizable(False,False)
        self._build(); self._center(); self._tick()
        self.protocol("WM_DELETE_WINDOW",self._hide)
        if TRAY_AVAILABLE: threading.Thread(target=self._start_tray,daemon=True).start()

    def _start_tray(self):
        menu=pystray.Menu(
            pystray.MenuItem("Abrir",self._show_cb,default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Pausa ya",       lambda i,it:self.after(0,self._now)),
            pystray.MenuItem("Posponer",       lambda i,it:self.after(0,self._posponer)),
            pystray.MenuItem("Pausar/Reanudar",lambda i,it:self.after(0,self._toggle)),
            pystray.MenuItem("Estadisticas",   lambda i,it:self.after(0,self._open_stats)),
            pystray.MenuItem("Configuracion",  lambda i,it:self.after(0,self._open_config)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir",self._quit),
        )
        self._tray=pystray.Icon("PausasActivas",make_tray_icon(TRAY_ACTIVE),"Pausas Activas",menu)
        self._tray.run()

    def _update_tray(self):
        if not TRAY_AVAILABLE or not self._tray: return
        if not self.running: c=TRAY_PAUSED; tip="Pausado"
        elif not in_active_hours(self.cfg): c=TRAY_OFF; tip="Fuera de horario"
        else: c=TRAY_ACTIVE; tip=f"Proxima pausa en {fmt_time(self.remaining)}"
        self._tray.icon=make_tray_icon(c); self._tray.title=f"Pausas Activas - {tip}"

    def _show_cb(self,i=None,it=None): self.after(0,self._show)
    def _show(self): self.deiconify(); self.lift(); self.focus_force()
    def _hide(self): self.withdraw()
    def _quit(self,i=None,it=None):
        self.running=False
        if self._tray: self._tray.stop()
        self.after(0,self.destroy)

    def _build(self):
        h=tk.Frame(self,bg=BG); h.pack(fill="x",padx=24,pady=(22,0))
        tk.Label(h,text="Pausas Activas",font=("Segoe UI",15,"bold"),bg=BG,fg=TEXT).pack(side="left")
        tk.Button(h,text="Stats",font=("Segoe UI",9),bg=BG,fg=TEXT_DIM,bd=0,cursor="hand2",
                  activebackground=BG,activeforeground=GREEN,relief="flat",command=self._open_stats).pack(side="right",padx=(4,0))
        tk.Button(h,text="Config",font=("Segoe UI",9),bg=BG,fg=TEXT_DIM,bd=0,cursor="hand2",
                  activebackground=BG,activeforeground=ACCENT,relief="flat",command=self._open_config).pack(side="right")
        tk.Frame(self,bg=BORDER,height=1).pack(fill="x",padx=24,pady=10)
        self.lbl_badge=tk.Label(self,text="ACTIVO",font=("Segoe UI",8,"bold"),bg=BG,fg=GREEN)
        self.lbl_badge.pack()
        tk.Label(self,text="PROXIMA PAUSA EN",font=("Segoe UI",8,"bold"),bg=BG,fg=TEXT_DIM).pack()
        self.lbl_cd=tk.Label(self,text="00:00",font=("Courier New",54,"bold"),bg=BG,fg=ACCENT)
        self.lbl_cd.pack(pady=(2,0))
        self.pb=ttk.Progressbar(self,orient="horizontal",length=280,mode="determinate",maximum=100,value=100)
        s=ttk.Style(self); s.theme_use("default")
        s.configure("a.Horizontal.TProgressbar",troughcolor=BG3,background=ACCENT,bordercolor=BG3,lightcolor=ACCENT,darkcolor=ACCENT)
        self.pb.configure(style="a.Horizontal.TProgressbar"); self.pb.pack(pady=(6,0))
        self.lbl_st=tk.Label(self,text="",font=("Segoe UI",9),bg=BG,fg=TEXT_DIM)
        self.lbl_st.pack(pady=(4,0))
        tk.Frame(self,bg=BORDER,height=1).pack(fill="x",padx=24,pady=12)
        self.lbl_meta=tk.Label(self,text="",font=("Segoe UI",9,"bold"),bg=BG,fg=TEXT_DIM)
        self.lbl_meta.pack()
        self.lbl_stats=tk.Label(self,text="",font=("Segoe UI",9),bg=BG,fg=TEXT_DIM)
        self.lbl_stats.pack()
        self.lbl_cfg=tk.Label(self,text="",font=("Segoe UI",9),bg=BG,fg=TEXT_DIM)
        self.lbl_cfg.pack()
        self._update_cfg_label(); self._update_stats_label()
        bf=tk.Frame(self,bg=BG); bf.pack(pady=(14,8))
        self.btn_p=tk.Button(bf,text="Pausar",font=("Segoe UI",10),bg=BG3,fg=TEXT,bd=0,cursor="hand2",
                             activebackground=BORDER,activeforeground=TEXT,relief="flat",padx=14,pady=7,command=self._toggle)
        self.btn_p.pack(side="left",padx=4)
        tk.Button(bf,text="Pausa ya",font=("Segoe UI",10),bg=ACCENT,fg="white",bd=0,cursor="hand2",
                  activebackground="#5A52D5",activeforeground="white",relief="flat",padx=14,pady=7,
                  command=self._now).pack(side="left",padx=4)
        tk.Button(bf,text="Posponer",font=("Segoe UI",10),bg=BG3,fg=TEXT,bd=0,cursor="hand2",
                  activebackground=BORDER,activeforeground=TEXT,relief="flat",padx=14,pady=7,
                  command=self._posponer).pack(side="left",padx=4)
        tk.Button(self,text="Minimizar a bandeja",font=("Segoe UI",8),bg=BG,fg=TEXT_DIM,bd=0,
                  cursor="hand2",activebackground=BG,activeforeground=TEXT,relief="flat",
                  command=self._hide).pack(pady=(0,18))

    def _update_cfg_label(self):
        c=self.cfg
        self.lbl_cfg.config(text=f"Cada {c['intervalo_min']} min  -  Pausa {c['duracion_pausa_min']} min  -  {c['hora_inicio']} a {c['hora_fin']}")

    def _update_stats_label(self):
        s=self.stats; meta=self.cfg["meta_pausas"]
        comp=s["completadas"]; racha=s.get("racha",0)
        self.lbl_stats.config(text=f"Hoy: {comp} completadas  /  {s['saltadas']} saltadas")
        barra="█"*comp+"░"*(max(0,meta-comp))
        color=GREEN if comp>=meta else (YELLOW if comp>=meta//2 else TEXT_DIM)
        self.lbl_meta.config(text=f"Meta: {barra} {comp}/{meta}",fg=color)

    def _center(self):
        self.update_idletasks()
        w,h=self.winfo_width(),self.winfo_height(); sw,sh=self.winfo_screenwidth(),self.winfo_screenheight()
        self.geometry(f"+{sw-w-30}+{30}")

    def _countdown_color(self):
        if self._total_sec==0: return ACCENT
        pct=self.remaining/self._total_sec
        if pct>0.5: return ACCENT
        if pct>0.2: return YELLOW
        return ACCENT2

    def _tick(self):
        if not self.running or self.pausa_open:
            self._job=self.after(1000,self._tick); return
        if not in_active_hours(self.cfg):
            self.lbl_st.config(text="Fuera del horario activo")
            self.lbl_cd.config(fg=TEXT_DIM,text="--:--")
            self.lbl_badge.config(text="FUERA DE HORARIO",fg=ACCENT2)
            self._update_tray(); self._job=self.after(1000,self._tick); return
        color=self._countdown_color()
        self.lbl_cd.config(fg=color,text=fmt_time(self.remaining))
        self.lbl_st.config(text="Trabajando...")
        self.lbl_badge.config(text="ACTIVO",fg=GREEN)
        total=self._total_sec if self._total_sec else 1
        self.pb["value"]=(self.remaining/total)*100
        if self.remaining%30==0: self._update_tray()
        if self.remaining<=0: self._trigger_pausa()
        else: self.remaining-=1
        self._job=self.after(1000,self._tick)

    def _trigger_pausa(self):
        if self.pausa_open: return
        self.pausa_open=True; self._show()
        if self.cfg.get("sonido",True): threading.Thread(target=play_alert,daemon=True).start()
        threading.Thread(target=lambda:send_win_notification("Pausa Activa","Es hora de moverte un poco!"),daemon=True).start()
        activos=[e for e in EJERCICIOS if e["id"] in self.cfg.get("ejercicios_activos",[e["id"] for e in EJERCICIOS])]
        if not activos: activos=EJERCICIOS
        ej=random.choice(activos); self._last_ej=ej["nombre"]
        dur=self.cfg["duracion_pausa_min"]*60
        pct=self.remaining/self._total_sec if self._total_sec else 0
        PausaWindow(self,ej,dur,self._done_pausa,self._skip_pausa,pct)

    def _done_pausa(self):
        self.pausa_open=False
        self._total_sec=self.cfg["intervalo_min"]*60
        self.remaining=self._total_sec
        self.stats["completadas"]+=1
        self.stats["historial"].append({"hora":datetime.now().strftime("%H:%M"),"ejercicio":self._last_ej,"estado":"completada"})
        meta=self.cfg["meta_pausas"]
        if self.stats["completadas"]==meta:
            self.stats["meta_cumplida"]=True
            threading.Thread(target=lambda:send_win_notification("Meta cumplida!",f"Completaste {meta} pausas hoy. Excelente habito!"),daemon=True).start()
        save_stats(self.stats); self._update_stats_label()
        append_csv([datetime.now().strftime("%Y-%m-%d"),datetime.now().strftime("%H:%M"),self._last_ej,"completada"])
        frase=random.choice(FRASES)
        self.lbl_st.config(text=frase)
        self._update_tray()

    def _skip_pausa(self):
        self.pausa_open=False
        self._total_sec=self.cfg["intervalo_min"]*60
        self.remaining=self._total_sec
        self.stats["saltadas"]+=1
        self.stats["historial"].append({"hora":datetime.now().strftime("%H:%M"),"ejercicio":self._last_ej,"estado":"saltada"})
        save_stats(self.stats); self._update_stats_label()
        append_csv([datetime.now().strftime("%Y-%m-%d"),datetime.now().strftime("%H:%M"),self._last_ej,"saltada"])
        self.lbl_st.config(text="Pausa saltada.")
        self._update_tray()

    def _toggle(self):
        self.running=not self.running
        if self.running:
            self.btn_p.config(text="Pausar",fg=TEXT); self.lbl_st.config(text="Trabajando...")
            self.lbl_badge.config(text="ACTIVO",fg=GREEN)
        else:
            self.btn_p.config(text="Reanudar",fg=GREEN); self.lbl_st.config(text="Timer pausado")
            self.lbl_badge.config(text="PAUSADO",fg=TEXT_DIM)
        self._update_tray()

    def _now(self): self.remaining=0
    def _posponer(self):
        mins=self.cfg.get("posponer_min",10)
        self._total_sec=mins*60; self.remaining=self._total_sec
        self.lbl_st.config(text=f"Pausa pospuesta {mins} min")

    def _open_config(self):
        def on_save(c):
            self.cfg=c
            self._total_sec=c["intervalo_min"]*60
            self.remaining=self._total_sec
            save_config(c); self._update_cfg_label()
        ConfigWindow(self,self.cfg,on_save)

    def _open_stats(self): StatsWindow(self,self.stats,self.cfg["meta_pausas"])

if __name__=="__main__":
    app=App()
    app.mainloop()