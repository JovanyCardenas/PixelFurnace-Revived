#!/usr/bin/env python3
"""
PixelFurnace Studio 1.1
GUI for the original Gameband 20x7 LED display.

Features:
- Connect/read Gameband over HID
- Automatic timestamped backup on read
- Parse Time / Date / scrolling screen records
- Select scrolling screen
- 20x7-style bitmap editor (full message canvas, horizontal scrolling)
- Text generator
- Live 20-column viewport preview
- Timing word editor
- Save candidate .bin offline
- Guarded Apply to Gameband: fresh read, backup, validation, prepare/write/readback/commit/full verification
- Restore a valid backup through the same guarded path

This is independent software based on the validated protocol used in the user's
working reader/writer. It does not require the original Gameband launcher.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
import struct, hashlib, datetime as dt, json, time, threading, sys, os
from PIL import Image, ImageTk

def set_windows_app_identity():
    """Give Windows a stable taskbar identity for the branded app icon."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "Gameband.PixelFurnaceStudio.1.3"
            )
        except Exception:
            pass

set_windows_app_identity()

def resource_path(name):
    """Resolve bundled resources from source or a PyInstaller one-file EXE."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name

VID=0x2A90; PID=0x0021
CONFIG_BASE=0x1800; CONFIG_WORDS=2048; BLOCK=16; TIMEOUT_MS=5000

FONT={
" ":["000","000","000","000","000","000","000"],
"A":["010","101","101","111","101","101","101"],"B":["110","101","101","110","101","101","110"],
"C":["011","100","100","100","100","100","011"],"D":["110","101","101","101","101","101","110"],
"E":["111","100","100","110","100","100","111"],"F":["111","100","100","110","100","100","100"],
"G":["011","100","100","101","101","101","011"],"H":["101","101","101","111","101","101","101"],
"I":["111","010","010","010","010","010","111"],"J":["001","001","001","001","101","101","010"],
"K":["101","101","110","100","110","101","101"],"L":["100","100","100","100","100","100","111"],
"M":["10001","11011","10101","10101","10001","10001","10001"],"N":["1001","1101","1011","1001","1001","1001","1001"],
"O":["010","101","101","101","101","101","010"],"P":["110","101","101","110","100","100","100"],
"Q":["010","101","101","101","101","011","001"],"R":["110","101","101","110","101","101","101"],
"S":["011","100","100","010","001","001","110"],"T":["111","010","010","010","010","010","010"],
"U":["101","101","101","101","101","101","111"],"V":["101","101","101","101","101","101","010"],
"W":["10001","10001","10001","10101","10101","11011","10001"],"X":["101","101","101","010","101","101","101"],
"Y":["101","101","101","010","010","010","010"],"Z":["111","001","001","010","100","100","111"],
"0":["111","101","101","101","101","101","111"],"1":["010","110","010","010","010","010","111"],
"2":["110","001","001","010","100","100","111"],"3":["110","001","001","010","001","001","110"],
"4":["101","101","101","111","001","001","001"],"5":["111","100","100","110","001","001","110"],
"6":["011","100","100","110","101","101","010"],"7":["111","001","001","010","010","010","010"],
"8":["010","101","101","010","101","101","010"],"9":["010","101","101","011","001","001","110"],
"-":["000","000","000","111","000","000","000"],".":["000","000","000","000","000","000","010"],
"!":["010","010","010","010","010","000","010"],"?":["110","001","001","010","010","000","010"],
"_":["000","000","000","000","000","000","111"],
}

def words_from_bytes(data): return list(struct.unpack("<2048H",data))
def bytes_from_words(w): return struct.pack("<2048H",*w)
def sha(data): return hashlib.sha256(data).hexdigest()

def checksum(words,count):
    a=b=0
    for v in words[:count]:
        for x in (v&255,(v>>8)&0x3f):
            a=(a+x)%255; b=(b+a)%255
    return a,b

def parse(words):
    count=words[8]; pos=12; screens=[]
    for i in range(count):
        if pos+6>2048: raise ValueError("screen header out of range")
        h=words[pos:pos+6]; n=h[5]
        if pos+6+n>2048: raise ValueError("screen payload out of range")
        screens.append({"index":i,"pos":pos,"header":h[:],"payload":words[pos+6:pos+6+n]})
        pos += 6+n
    return screens,pos

def validate(words):
    if len(words)!=2048: return False,"not 2048 words"
    n=words[8]; count=words[9]
    if not 1<=n<=64 or not 0<count<=2036: return False,"invalid header"
    if checksum(words[12:],count)!=(words[10],words[11]): return False,"checksum mismatch"
    try: screens,end=parse(words)
    except Exception as e: return False,str(e)
    if end!=12+count: return False,f"screen data ends at {end}, expected {12+count}"
    return True,f"{n} screens, {count} active words, checksum {words[10]:02X} {words[11]:02X}"

def words_to_pixels(payload):
    px=[[False]*(len(payload)*2) for _ in range(7)]
    for i,w in enumerate(payload):
        for y in range(7):
            px[y][2*i]=bool(w&(1<<y)); px[y][2*i+1]=bool(w&(1<<(y+7)))
    return px

def pixels_to_words(px):
    if not px: return []
    width=len(px[0])
    q=[row[:] for row in px]
    if width%2:
        for row in q: row.append(False)
        width+=1
    out=[]
    for x in range(0,width,2):
        w=0
        for y in range(7):
            if q[y][x]: w|=1<<y
            if q[y][x+1]: w|=1<<(y+7)
        out.append(w)
    return out

def text_pixels(text,margin=10):
    text=text.upper()
    bad=sorted(set(c for c in text if c not in FONT))
    if bad: raise ValueError("Unsupported: "+", ".join(bad))
    width=margin*2+sum(len(FONT[c][0]) for c in text)+max(0,len(text)-1)
    px=[[False]*max(20,width) for _ in range(7)]
    x=margin
    for c in text:
        g=FONT[c]
        for y,row in enumerate(g):
            for dx,v in enumerate(row):
                if v=="1": px[y][x+dx]=True
        x+=len(g[0])+1
    return px

def rebuild_screen(words,index,payload,new_header=None):
    screens,end=parse(words); s=screens[index]
    active_end=12+words[9]
    before=words[12:s["pos"]]
    after=words[s["pos"]+6+len(s["payload"]):active_end]
    h=(new_header or s["header"])[:]; h[5]=len(payload)
    body=before+h+payload+after
    if len(body)>2036: raise ValueError("configuration too large")
    new=words[:12]+body+[0x3fff]*(2048-12-len(body))
    new[9]=len(body); new[10],new[11]=checksum(new[12:],new[9])
    return new


def rebuild_records(words, records):
    """Rebuild active screen records while preserving the 12-word global header."""
    body=[]
    for r in records:
        h=r["header"][:]
        h[5]=len(r["payload"])
        body += h + r["payload"]
    if len(body)>2036:
        raise ValueError("Screen configuration exceeds Gameband memory.")
    out=words[:12]+body+[0x3fff]*(2048-12-len(body))
    out[8]=len(records)
    out[9]=len(body)
    out[10],out[11]=checksum(out[12:],out[9])
    return out

def frame_to_words(px):
    """One 20x7 animation frame is exactly 10 packed words."""
    q=[row[:20]+[False]*max(0,20-len(row)) for row in px[:7]]
    while len(q)<7: q.append([False]*20)
    return pixels_to_words(q)[:10]

class HIDTransport:
    def __init__(self):
        import hid
        ds=hid.enumerate(VID,PID)
        if not ds: raise RuntimeError("Gameband HID 2A90:0021 not found.")
        if len(ds)>1: raise RuntimeError("Multiple matching Gameband HID interfaces found.")
        self.dev=hid.device(); self.dev.open_path(ds[0]["path"])
        try:self.dev.set_nonblocking(0)
        except:pass
    def close(self):
        try:self.dev.close()
        except:pass
    def exchange(self,req,reply):
        if self.dev.write(req)<=0: raise IOError("HID write failed")
        r=bytes(self.dev.read(64,TIMEOUT_MS))
        if not r: raise TimeoutError("Gameband response timed out")
        if len(r)>=3 and r[0]==0 and r[1]==reply:r=r[1:]
        if len(r)<2 or r[0]!=reply or r[1]!=0: raise IOError(f"Unexpected response: {r.hex()}")
        return r
    def read16(self,address):
        r=self.exchange(bytes((0,8,0))+struct.pack("<H",address),9)
        if len(r)<34: raise IOError("short response")
        return list(struct.unpack("<16H",r[2:34]))
    def read_all(self):
        out=[]
        for i in range(128): out+=self.read16(CONFIG_BASE+i*16)
        return out
    def prepare(self,address,length):
        self.exchange(bytes((0,4,0))+struct.pack("<HH",address,length),5)
    def write16(self,address,w):
        self.exchange(bytes((0,6,0))+struct.pack("<H",address)+struct.pack("<16H",*w),7)
    def set_clock_utc(self, unix_seconds):
        # Original Gameband command 0x02: 9-byte HID report.
        # 32-bit Unix UTC timestamp begins at byte offset 5; reply is 0x03.
        req=bytes((0,2,0,0,0))+struct.pack("<I",int(unix_seconds)&0xffffffff)
        self.exchange(req,3)
    def commit(self): self.exchange(bytes((0,10,0)),11)

class App(tk.Tk):
    CELL=22
    def __init__(self):
        super().__init__()
        self.title("PixelFurnace Studio 1.3 — Gameband")
        self.geometry("1180x760"); self.minsize(980,650)
        self.words=None; self.source_words=None; self.pixels=[[False]*20 for _ in range(7)]
        self.selected=None; self.anim_job=None; self.preview_offset=0
        self.advanced=tk.BooleanVar(value=False)
        self.status=tk.StringVar(value="Not connected / no configuration loaded")
        self.textvar=tk.StringVar(value="JOVANY")
        self.speedvar=tk.StringVar(value="71")
        self._bg_source=None; self._bg_photo=None; self._resize_job=None
        try:
            self._icon_photo=ImageTk.PhotoImage(Image.open(resource_path("icon.png")))
            self.iconphoto(True,self._icon_photo)
        except Exception:
            self._icon_photo=None
        if sys.platform == "win32":
            try:
                # Helps source-mode windows use the same branded icon too.
                self.iconbitmap(default=str(resource_path("PixelFurnaceStudio.ico")))
            except Exception:
                pass
        self._build()
    def _build(self):
        self.option_add("*Font",("Segoe UI",10))
        self.configure(background="#050607")

        # Use the supplied Gameband image as the actual window wallpaper.
        try:
            self._bg_source=Image.open(resource_path("background.png")).convert("RGBA")
            self.bg_label=tk.Label(self,borderwidth=0,highlightthickness=0,bg="#000000")
            self.bg_label.place(x=0,y=0,relwidth=1,relheight=1)
            self.bind("<Configure>",self._schedule_background_resize)
        except Exception:
            self.bg_label=None

        style=ttk.Style(self)
        try: style.theme_use("clam")
        except: pass
        panel="#0d1014"; panel2="#131820"; text="#eef2f7"; muted="#98a4b3"
        style.configure(".",background=panel,foreground=text,fieldbackground="#1a2029",borderwidth=0)
        style.configure("TFrame",background=panel)
        style.configure("Card.TFrame",background=panel2)
        style.configure("TLabel",background=panel,foreground=text)
        style.configure("Card.TLabel",background=panel2,foreground=text)
        style.configure("Title.TLabel",background=panel,foreground="#ffffff",font=("Segoe UI Semibold",20))
        style.configure("Sub.TLabel",background=panel,foreground=muted,font=("Segoe UI",9))
        style.configure("TButton",padding=(11,7),background="#242b35",foreground="#ffffff",borderwidth=0)
        style.map("TButton",background=[("active","#333c49"),("pressed","#1d232b")])
        style.configure("Primary.TButton",padding=(13,8),background="#e8ebef",foreground="#0c0e11",borderwidth=0)
        style.map("Primary.TButton",background=[("active","#ffffff"),("pressed","#cfd5dc")])
        style.configure("TCheckbutton",background=panel,foreground=text)
        style.configure("TSeparator",background="#2b313a")

        self.option_add("*Listbox.Background","#090c10")
        self.option_add("*Listbox.Foreground","#e8edf3")
        self.option_add("*Listbox.selectBackground","#3b4654")
        self.option_add("*Listbox.selectForeground","#ffffff")
        self.option_add("*Text.Background","#090c10")
        self.option_add("*Text.Foreground","#cdd6e0")

        # Leave the outer edge and lower-right area visible so the original
        # Gameband background/logo remains visibly part of the application.
        self.shell=ttk.Frame(self,style="TFrame",padding=(16,14))
        self.shell.place(relx=.035,rely=.045,relwidth=.91,relheight=.84)

        header=ttk.Frame(self.shell); header.pack(fill="x")
        brand=ttk.Frame(header); brand.pack(side="left")
        ttk.Label(brand,text="PixelFurnace Studio",style="Title.TLabel").pack(anchor="w")
        ttk.Label(brand,text="Gameband 20×7 Text & Pixel Editor",style="Sub.TLabel").pack(anchor="w")
        ttk.Checkbutton(header,text="Advanced mode",variable=self.advanced,command=self.update_mode).pack(side="right",pady=9)

        ttk.Separator(self.shell,orient="horizontal").pack(fill="x",pady=(12,10))

        simple=ttk.Frame(self.shell); simple.pack(fill="x",pady=(0,10))
        ttk.Button(simple,text="Read Gameband",command=self.read_device).pack(side="left")
        ttk.Button(simple,text="Sync Date & Time",command=self.sync_clock).pack(side="left",padx=6)
        ttk.Button(simple,text="Apply Changes",command=self.apply_device,style="Primary.TButton").pack(side="left")
        ttk.Label(simple,textvariable=self.status,style="Sub.TLabel").pack(side="right",padx=(12,0))

        self.advanced_bar=ttk.Frame(self.shell)
        ttk.Button(self.advanced_bar,text="Open Backup",command=self.open_backup).pack(side="left")
        ttk.Button(self.advanced_bar,text="Save Candidate",command=self.save_candidate).pack(side="left",padx=4)
        ttk.Button(self.advanced_bar,text="Restore Backup",command=self.restore_backup).pack(side="left",padx=4)
        ttk.Separator(self.advanced_bar,orient="vertical").pack(side="left",fill="y",padx=9)
        ttk.Button(self.advanced_bar,text="+ Text / Pixel Scroll",command=self.add_scroll_screen).pack(side="left")
        ttk.Button(self.advanced_bar,text="Delete Screen",command=self.delete_screen).pack(side="left",padx=4)
        ttk.Button(self.advanced_bar,text="Move ↑",command=lambda:self.move_screen(-1)).pack(side="left")
        ttk.Button(self.advanced_bar,text="Move ↓",command=lambda:self.move_screen(1)).pack(side="left",padx=4)

        self.body=ttk.Panedwindow(self.shell,orient="horizontal"); self.body.pack(fill="both",expand=True)
        body=self.body
        left=ttk.Frame(body,style="Card.TFrame",padding=12)
        right=ttk.Frame(body,style="Card.TFrame",padding=12)
        body.add(left,weight=1); body.add(right,weight=4)

        ttk.Label(left,text="Screens",font=("Segoe UI Semibold",12),style="Card.TLabel").pack(anchor="w")
        ttk.Label(left,text="Bracelet rotation",style="Card.TLabel").pack(anchor="w",pady=(0,8))
        self.list=tk.Listbox(left,height=12,relief="flat",highlightthickness=1,
                             highlightbackground="#222a34",highlightcolor="#46515f",borderwidth=0)
        self.list.pack(fill="both",expand=True)
        self.list.bind("<<ListboxSelect>>",self.select_screen)

        self.editor_title=ttk.Label(right,text="Screen editor",font=("Segoe UI Semibold",13),style="Card.TLabel")
        self.editor_title.pack(anchor="w")

        self.text_tools=ttk.Frame(right,style="Card.TFrame"); self.text_tools.pack(fill="x",pady=8)
        ttk.Label(self.text_tools,text="Text",style="Card.TLabel").pack(side="left")
        ttk.Entry(self.text_tools,textvariable=self.textvar,width=30).pack(side="left",padx=6)
        ttk.Button(self.text_tools,text="Generate",command=self.generate_text).pack(side="left")
        ttk.Button(self.text_tools,text="Clear",command=self.clear_pixels).pack(side="left",padx=4)

        self.advanced_controls=ttk.Frame(right,style="Card.TFrame")
        ttk.Label(self.advanced_controls,text="Timing word",style="Card.TLabel").pack(side="left")
        ttk.Entry(self.advanced_controls,textvariable=self.speedvar,width=7).pack(side="left",padx=4)
        ttk.Button(self.advanced_controls,text="Set",command=self.set_timing).pack(side="left")

        self.editor_wrap=ttk.Frame(right,style="Card.TFrame"); self.editor_wrap.pack(fill="both",expand=True)
        wrap=self.editor_wrap
        self.canvas=tk.Canvas(wrap,height=7*self.CELL+30,background="#07090c",highlightthickness=0)
        xs=ttk.Scrollbar(wrap,orient="horizontal",command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=xs.set)
        self.canvas.pack(fill="x"); xs.pack(fill="x")
        self.canvas.bind("<Button-1>",self.paint); self.canvas.bind("<B1-Motion>",self.paint)
        self.canvas.bind("<Button-3>",self.erase); self.canvas.bind("<B3-Motion>",self.erase)

        pvhead=ttk.Frame(right,style="Card.TFrame"); pvhead.pack(fill="x",pady=(11,4))
        ttk.Label(pvhead,text="Bracelet preview",font=("Segoe UI Semibold",11),style="Card.TLabel").pack(side="left")
        self.preview=tk.Canvas(right,width=20*14,height=7*14,background="#07090c",highlightthickness=0)
        self.preview.pack(anchor="w")
        pv=ttk.Frame(right,style="Card.TFrame"); pv.pack(anchor="w",pady=5)
        ttk.Button(pv,text="◀",command=lambda:self.shift_preview(-1)).pack(side="left")
        ttk.Button(pv,text="▶",command=lambda:self.shift_preview(1)).pack(side="left")
        self.playbtn=ttk.Button(pv,text="Play Scroll",command=self.toggle_play); self.playbtn.pack(side="left",padx=6)

        self.hint=ttk.Label(right,text="Left-click draws • Right-click erases",style="Card.TLabel")
        self.hint.pack(anchor="w",pady=(3,5))
        self.log=tk.Text(right,height=6,state="disabled",relief="flat",borderwidth=0)

        self.update_mode(); self.redraw()
        self.after(50,self._render_background)

    def _schedule_background_resize(self,event=None):
        if not self._bg_source:return
        if self._resize_job:
            try:self.after_cancel(self._resize_job)
            except:pass
        self._resize_job=self.after(80,self._render_background)

    def _render_background(self):
        if not self._bg_source or not getattr(self,"bg_label",None):return
        w=max(1,self.winfo_width()); h=max(1,self.winfo_height())
        sw,sh=self._bg_source.size
        scale=max(w/sw,h/sh)
        nw,nh=max(1,int(sw*scale)),max(1,int(sh*scale))
        img=self._bg_source.resize((nw,nh),Image.Resampling.LANCZOS)
        x=max(0,(nw-w)//2); y=max(0,(nh-h)//2)
        img=img.crop((x,y,x+w,y+h))
        self._bg_photo=ImageTk.PhotoImage(img)
        self.bg_label.configure(image=self._bg_photo)
        self.bg_label.lower()
        self._resize_job=None

    def update_mode(self):
        """Show/hide advanced tools without disturbing the normal editor layout."""
        if self.advanced.get():
            # advanced_bar and body share self.shell as parent.
            if not self.advanced_bar.winfo_manager():
                self.advanced_bar.pack(fill="x",pady=(0,10),before=self.body)

            # advanced_controls, editor_wrap and log all share the right editor panel.
            if not self.advanced_controls.winfo_manager():
                self.advanced_controls.pack(fill="x",pady=(0,7),before=self.editor_wrap)
            if not self.log.winfo_manager():
                self.log.pack(fill="x",pady=(7,0))
        else:
            self.advanced_bar.pack_forget()
            self.advanced_controls.pack_forget()
            self.log.pack_forget()

    def logmsg(self,s):
        self.log.config(state="normal"); self.log.insert("end",s+"\n"); self.log.see("end"); self.log.config(state="disabled")
    def refresh_list(self):
        self.list.delete(0,"end")
        if not self.words:return
        names={0:"Time",1:"Time",2:"Date",3:"Date",16:"Text / Pixel Scroll",17:"Scrolling Variant",32:"Legacy Animation (read-only)",34:"Legacy Animation (read-only)"}
        for s in parse(self.words)[0]:
            t=s["header"][0]; self.list.insert("end",f"{s['index']+1}. {names.get(t,'Type '+str(t))}")
    def load_words(self,w,label):
        ok,msg=validate(w)
        if not ok: raise ValueError(msg)
        self.words=w[:]; self.source_words=w[:]; self.status.set(label+" — "+msg); self.refresh_list()
        self.logmsg("Loaded "+label+": "+msg)
        # select first editable scroll screen
        for s in parse(self.words)[0]:
            if 16<=s["header"][0]<=31:
                self.list.selection_clear(0,"end"); self.list.selection_set(s["index"]); self.list.event_generate("<<ListboxSelect>>"); break
    def open_backup(self):
        p=filedialog.askopenfilename(filetypes=[("Gameband config","*.bin"),("All files","*.*")])
        if not p:return
        try:
            d=Path(p).read_bytes()
            if len(d)!=4096: raise ValueError("file must be exactly 4096 bytes")
            self.load_words(words_from_bytes(d),Path(p).name)
        except Exception as e: messagebox.showerror("Open failed",str(e))
    def _next_offset_transition(self, now_local):
        """Find next local UTC-offset transition using the PC's timezone rules."""
        base=now_local.utcoffset()
        probe=now_local
        # Search ahead hourly for up to ~400 days, then binary-refine to a minute.
        for _ in range(24*400):
            nxt=probe+dt.timedelta(hours=1)
            if nxt.utcoffset()!=base:
                lo,hi=probe,nxt
                while (hi-lo)>dt.timedelta(minutes=1):
                    mid=lo+(hi-lo)/2
                    if mid.utcoffset()==base: lo=mid
                    else: hi=mid
                return int(hi.timestamp()), int(base.total_seconds()//60), int(hi.utcoffset().total_seconds()//60)
            probe=nxt
        return None,int(base.total_seconds()//60),int(base.total_seconds()//60)

    @staticmethod
    def _enc14_signed_quarter(minutes):
        # Gameband stores signed 14-bit quarter-hour offsets.
        q=int(minutes//15)
        return q & 0x3fff

    def sync_clock(self):
        """Sync RTC and refresh the Gameband timezone/DST transition header."""
        try:
            now_local=dt.datetime.now().astimezone()
            now_ts=int(time.time())
            transition,current_min,next_min=self._next_offset_transition(now_local)
            shown=now_local.strftime("%Y-%m-%d %I:%M:%S %p %Z")
            trans_text=(dt.datetime.fromtimestamp(transition).astimezone().strftime("%Y-%m-%d %I:%M %p %Z")
                        if transition else "No transition found")
            if not messagebox.askyesno(
                "Sync Gameband Date & Time",
                "Synchronize the Gameband from this computer?\\n\\n"
                f"Computer time: {shown}\\n"
                f"Current UTC offset: {current_min//60:+d}:{abs(current_min)%60:02d}\\n"
                f"Next offset: {next_min//60:+d}:{abs(next_min)%60:02d}\\n"
                f"Next transition: {trans_text}\\n\\n"
                "This updates the Gameband timezone/DST header and its RTC. "
                "Your scrolling message is preserved."
            ): return

            h=HIDTransport()
            try:
                live=h.read_all()
                ok,msg=validate(live)
                if not ok: raise ValueError("Live Gameband invalid: "+msg)
                Path("gameband_backup").mkdir(exist_ok=True)
                stamp=dt.datetime.now().strftime("%Y%m%d_%H%M%S")
                bp=Path("gameband_backup")/f"gui_presync_{stamp}.bin"
                bp.write_bytes(bytes_from_words(live))

                target=live[:]
                # Header word 0 = offset in effect before the stored transition.
                # Header word 1 = offset in effect after it.
                target[0]=self._enc14_signed_quarter(current_min)
                target[1]=self._enc14_signed_quarter(next_min)
                if transition:
                    # Timestamp is stored byte-by-byte in words 2..5.
                    for i in range(4): target[2+i]=(transition>>(8*i))&0xff
                    target[6]=1
                # Screen data did not change, so its checksum remains valid.
                active=12+target[9]
                padded=((active+31)//32)*32

                # Safely rewrite header/config so the firmware receives fresh DST data.
                h.prepare(CONFIG_BASE,padded)
                for off in range(0,padded,16):
                    block=target[off:off+16]
                    h.write16(CONFIG_BASE+off,block)
                    if h.read16(CONFIG_BASE+off)!=block:
                        raise RuntimeError(f"Verification failed at 0x{CONFIG_BASE+off:04X}; commit not sent")
                h.commit()
                time.sleep(.2)

                # Now set the RTC in UTC using the original clock command.
                h.set_clock_utc(now_ts)
                time.sleep(.1)
                final=h.read_all()
                fok,fmsg=validate(final)
                if not fok or final[:padded]!=target[:padded]:
                    raise RuntimeError("Post-sync configuration verification failed: "+fmsg)
            finally:
                h.close()

            self.load_words(final,"Gameband after time sync")
            self.logmsg(f"Time/DST synchronized: {shown}; next transition {trans_text}; backup {bp}")
            messagebox.showinfo(
                "Time synchronized",
                "Gameband RTC and timezone/DST information were updated.\\n\\n"
                f"{shown}\\nNext transition: {trans_text}\\n\\n"
                "Unplug normally and check the Time and Date screens."
            )
        except Exception as e:
            messagebox.showerror("Clock sync failed",str(e))
            self.logmsg("CLOCK SYNC ERROR: "+str(e))

    def read_device(self):
        try:
            h=HIDTransport(); self.status.set("Reading Gameband…"); self.update_idletasks()
            w=h.read_all(); h.close()
            ok,msg=validate(w)
            if not ok: raise ValueError(msg)
            Path("gameband_backup").mkdir(exist_ok=True)
            stamp=dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            p=Path("gameband_backup")/f"gui_read_{stamp}.bin"; p.write_bytes(bytes_from_words(w))
            self.load_words(w,"Gameband")
            self.logmsg(f"Automatic backup: {p}")
        except Exception as e: messagebox.showerror("Gameband read failed",str(e)); self.status.set("Read failed")
    def select_screen(self,_=None):
        sel=self.list.curselection()
        if not sel or not self.words:return
        s=parse(self.words)[0][sel[0]]; self.selected=s["index"]; self.speedvar.set(str(s["header"][3]))
        t=s["header"][0]
        self.text_tools.pack_forget()
        if 16<=t<=31:
            self.editor_title.config(text="Text / Pixel Scroll")
            self.text_tools.pack(fill="x",pady=7,after=self.editor_title)
            self.pixels=words_to_pixels(s["payload"]); self.preview_offset=0
        elif t in (0,1):
            self.editor_title.config(text="Built-in Time Screen")
            self.pixels=[[False]*20 for _ in range(7)]
        elif t in (2,3):
            self.editor_title.config(text="Built-in Date Screen")
            self.pixels=[[False]*20 for _ in range(7)]
        elif 32<=t<=47:
            self.editor_title.config(text="Legacy Animation — unsupported/read-only")
            self.pixels=[[False]*20 for _ in range(7)]
            self.hint.config(text="Animation editing was intentionally removed in Studio 1.1. You can delete this screen in Advanced mode.")
        else:
            self.editor_title.config(text=f"Unsupported screen type {t}")
            self.pixels=[[False]*20 for _ in range(7)]
        self.redraw()

    def sync_pixels(self):
        if self.words is None or self.selected is None:return
        s=parse(self.words)[0][self.selected]; t=s["header"][0]
        if 16<=t<=31:
            self.words=rebuild_screen(self.words,self.selected,pixels_to_words(self.pixels))

    def generate_text(self):
        try:self.pixels=text_pixels(self.textvar.get()); self.preview_offset=0; self.sync_pixels(); self.redraw(); self.logmsg(f'Generated "{self.textvar.get()}"')
        except Exception as e:messagebox.showerror("Text error",str(e))
    def clear_pixels(self):
        self.pixels=[[False]*max(20,len(self.pixels[0]) if self.pixels else 20) for _ in range(7)]; self.sync_pixels(); self.redraw()
    def set_timing(self):
        if self.words is None or self.selected is None:return
        try:v=int(self.speedvar.get()); assert 1<=v<=65535
        except: messagebox.showerror("Timing","Enter an integer from 1 to 65535."); return
        s=parse(self.words)[0][self.selected]; h=s["header"][:]; h[3]=v
        self.words=rebuild_screen(self.words,self.selected,s["payload"],h); self.logmsg(f"Timing word set to {v}")
    def paint_at(self,e,val):
        x=int(self.canvas.canvasx(e.x)//self.CELL); y=int(e.y//self.CELL)
        if 0<=y<7 and 0<=x<len(self.pixels[0]):
            self.pixels[y][x]=val; self.sync_pixels(); self.redraw()
    def paint(self,e):self.paint_at(e,True)
    def erase(self,e):self.paint_at(e,False)
    def redraw(self):
        self.canvas.delete("all")
        width=max(20,len(self.pixels[0]) if self.pixels else 20)
        self.canvas.config(scrollregion=(0,0,width*self.CELL,7*self.CELL))
        for y in range(7):
            for x in range(width):
                on=x<len(self.pixels[y]) and self.pixels[y][x]
                fill="#ff4d5a" if on else "#242a33"
                self.canvas.create_oval(x*self.CELL+3,y*self.CELL+3,(x+1)*self.CELL-3,(y+1)*self.CELL-3,fill=fill,outline="")
        self.draw_preview()
    def draw_preview(self):
        self.preview.delete("all"); width=len(self.pixels[0]) if self.pixels else 0
        for y in range(7):
            for vx in range(20):
                x=(self.preview_offset+vx)%max(1,width)
                on=width and self.pixels[y][x]
                fill="#ff4d5a" if on else "#242a33"
                self.preview.create_oval(vx*14+2,y*14+2,(vx+1)*14-2,(y+1)*14-2,fill=fill,outline="")
    def shift_preview(self,d):
        if self.pixels:self.preview_offset=(self.preview_offset+d)%len(self.pixels[0]); self.draw_preview()
    def toggle_play(self):
        if self.anim_job:
            self.after_cancel(self.anim_job); self.anim_job=None; self.playbtn.config(text="Play")
        else:self.playbtn.config(text="Stop"); self.animate()
    def animate(self):
        self.shift_preview(1)
        self.anim_job=self.after(100,self.animate)


    def _select_index(self,i):
        self.refresh_list(); self.list.selection_clear(0,"end"); self.list.selection_set(i); self.list.see(i); self.list.event_generate("<<ListboxSelect>>")

    def add_scroll_screen(self):
        if self.words is None:return messagebox.showinfo("Load Gameband","Read the Gameband first.")
        recs=parse(self.words)[0]
        # Matches the working scroll record defaults closely.
        recs.append({"header":[16,0,0,71,0,10],"payload":[0]*10})
        try:self.words=rebuild_records(self.words,recs); self._select_index(len(recs)-1); self.logmsg("Added text/pixel screen.")
        except Exception as e:messagebox.showerror("Cannot add screen",str(e))


    def delete_screen(self):
        if self.words is None or self.selected is None:return
        recs=parse(self.words)[0]
        if len(recs)<=1:return messagebox.showinfo("Cannot delete","Keep at least one screen.")
        if not messagebox.askyesno("Delete screen",f"Delete screen {self.selected+1}?"):return
        recs.pop(self.selected)
        self.words=rebuild_records(self.words,recs); self._select_index(min(self.selected,len(recs)-1))

    def move_screen(self,d):
        if self.words is None or self.selected is None:return
        recs=parse(self.words)[0]; j=self.selected+d
        if not 0<=j<len(recs):return
        recs[self.selected],recs[j]=recs[j],recs[self.selected]
        self.words=rebuild_records(self.words,recs); self._select_index(j)

    def save_candidate(self):
        if self.words is None:return messagebox.showinfo("Nothing loaded","Read the Gameband or open a backup first.")
        ok,msg=validate(self.words)
        if not ok:return messagebox.showerror("Invalid configuration",msg)
        p=filedialog.asksaveasfilename(defaultextension=".bin",initialfile="gameband_candidate.bin",filetypes=[("Gameband config","*.bin")])
        if p:Path(p).write_bytes(bytes_from_words(self.words)); self.logmsg(f"Saved candidate: {p} — {msg}")
    def guarded_write(self,target,action_name):
        ok,msg=validate(target)
        if not ok:raise ValueError("Target invalid: "+msg)
        h=HIDTransport()
        try:
            live=h.read_all(); lok,lmsg=validate(live)
            if not lok:raise ValueError("Live Gameband invalid: "+lmsg)
            Path("gameband_backup").mkdir(exist_ok=True); stamp=dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            bp=Path("gameband_backup")/f"gui_prewrite_{stamp}.bin"; bp.write_bytes(bytes_from_words(live))
            active=12+target[9]; padded=((active+31)//32)*32
            if padded>2048:raise ValueError("target too large")
            changed=sum(live[i]!=target[i] for i in range(padded))
            if not messagebox.askyesno(action_name,f"Fresh backup saved:\n{bp}\n\nTarget: {msg}\nPrepared region: {padded} words\nChanged words: {changed}\n\nKeep Gameband connected.\nProceed with write + verification?"):
                return
            phrase=simpledialog.askstring("Final confirmation",'Type APPLY to perform the hardware write:')
            if phrase!="APPLY": self.logmsg("Write cancelled."); return
            h.prepare(CONFIG_BASE,padded)
            for off in range(0,padded,16):
                block=target[off:off+16]; h.write16(CONFIG_BASE+off,block)
                if h.read16(CONFIG_BASE+off)!=block: raise RuntimeError(f"Verification failed at 0x{CONFIG_BASE+off:04X}; commit not sent")
            h.commit(); time.sleep(.2)
            final=h.read_all(); fok,fmsg=validate(final)
            if not fok or final[:padded]!=target[:padded]: raise RuntimeError("Post-commit verification failed: "+fmsg)
            self.load_words(final,"Gameband after write")
            self.logmsg(f"{action_name} SUCCESS — {fmsg}")
            messagebox.showinfo("Success",f"{action_name} succeeded.\n\n{fmsg}")
        finally:h.close()
    def apply_device(self):
        if self.words is None:return messagebox.showinfo("Nothing loaded","Read/open a configuration first.")
        try:self.guarded_write(self.words,"Apply to Gameband")
        except Exception as e:messagebox.showerror("Write failed",str(e)); self.logmsg("WRITE ERROR: "+str(e))
    def restore_backup(self):
        p=filedialog.askopenfilename(title="Choose valid Gameband backup",filetypes=[("Gameband config","*.bin")])
        if not p:return
        try:
            d=Path(p).read_bytes()
            if len(d)!=4096:raise ValueError("backup must be exactly 4096 bytes")
            self.guarded_write(words_from_bytes(d),"Restore Backup")
        except Exception as e:messagebox.showerror("Restore failed",str(e)); self.logmsg("RESTORE ERROR: "+str(e))

if __name__=="__main__":
    App().mainloop()
