import sys, time, re, locale, hashlib
import requests
from urllib.parse import urlencode, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import ollama

# ================== CONFIG ==================
UA = "AuryScanner/2025 Ethical"
TIMEOUT = 8
WORKERS = 30

PARAMS = ["id","q","search","file","page","url","dir"]

PAYLOADS = {
    "LFI": ["../../etc/passwd"],
    "SQLI": ["' OR '1'='1'--"],
    "CMD": ["|whoami"],
    "XSS": ["<svg/onload=alert(1)>"]
}

ERROR_SIGS = [
    "sql syntax","mysql","syntax error","warning:",
    "fatal error","exception","include(","uid=","root:x:"
]

STATIC_HOSTS = ["github.io","netlify.app","vercel.app"]

# ================== UTILS ==================
def sha(t): 
    return hashlib.sha256(t.encode(errors="ignore")).hexdigest()

def is_static(url):
    return any(x in urlparse(url).netloc.lower() for x in STATIC_HOSTS)

# ================== WORKER ==================
class Worker(QThread):
    log = pyqtSignal(str, bool)
    info = pyqtSignal(str)
    done = pyqtSignal()

    def __init__(self, base):
        super().__init__()
        self.base = base.rstrip("/")
        self.running = True
        self.s = requests.Session()
        self.s.headers["User-Agent"] = UA

    def stop(self): 
        self.running = False

    def run(self):
        try:
            base_r = self.s.get(self.base, timeout=TIMEOUT)
        except:
            self.info.emit("Hedefe erişilemedi.")
            self.done.emit()
            return

        base_len = len(base_r.text)
        base_hash = sha(base_r.text)

        static = is_static(self.base)
        if static:
            self.info.emit("Statik site algılandı → LFI/SQLI/CMD kapalı")

        tasks = []
        for vtype, pays in PAYLOADS.items():
            if static and vtype in ["LFI","SQLI","CMD"]:
                continue
            for p in PARAMS:
                for pay in pays:
                    q = urlencode({p: pay})
                    tasks.append((vtype, f"{self.base}?{q}"))

        with ThreadPoolExecutor(WORKERS) as ex:
            futs = [ex.submit(self.test, v, u, base_len, base_hash) for v,u in tasks]
            for f in as_completed(futs):
                if not self.running: break
                res = f.result()
                if res:
                    self.log.emit(res, True)

        self.done.emit()

    def test(self, vtype, url, blen, bhash):
        try:
            r = self.s.get(url, timeout=TIMEOUT)
            t = r.text.lower()

            # içerik farkı yoksa → geç
            if abs(len(t) - blen) < 30 and sha(t) == bhash:
                return None

            # XSS
            if vtype == "XSS":
                if "<svg/onload=alert(1)>" in r.text:
                    return f"[XSS] {url}"
                return None

            # Backend buglar için error şart
            if any(e in t for e in ERROR_SIGS):
                return f"[{vtype}] {url}"

        except:
            pass
        return None

# ================== GUI ==================
class AuryX2025(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aury Software © 2025")
        self.resize(1560, 960)

        # locale uyarısını düzelt
        try:
            loc = locale.getlocale()[0] or ""
        except:
            loc = ""
        self.lang = "TR" if loc.lower().startswith("tr") else "EN"

        central = QWidget(self)
        self.setCentralWidget(central)
        grid = QGridLayout(central)
        grid.setContentsMargins(30,30,30,30)
        grid.setSpacing(15)

        # ======= BAŞLIK =======
        title = QLabel("Aury Software © 2025")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #001040,stop:1 #003087);
            color:white;font-size:48px;font-weight:bold;
            padding:38px;border-radius:22px;
            border:4px solid #00f0ff;
        """)
        grid.addWidget(title, 0, 0, 1, 4)

        # ======= TARGET =======
        self.target = QLineEdit()
        self.target.setPlaceholderText("https://example.com")
        self.target.setFixedHeight(70)

        self.start = QPushButton("AGRESİF TARAMA BAŞLAT")
        self.stop = QPushButton("DURDUR")
        self.stop.setEnabled(False)

        target_layout = QVBoxLayout()
        target_layout.addWidget(self.target)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start)
        btn_layout.addWidget(self.stop)
        target_layout.addLayout(btn_layout)

        target_gb = QGroupBox("Hedef Sistem")
        target_gb.setLayout(target_layout)
        grid.addWidget(target_gb, 2, 0, 1, 4)

        # ======= AI ÇIKTI =======
        self.ai = QTextEdit()
        self.ai.setReadOnly(True)
        ai_layout = QVBoxLayout()
        ai_layout.addWidget(self.ai)
        ai_gb = QGroupBox("AI Tehdit Analizi")
        ai_gb.setLayout(ai_layout)
        grid.addWidget(ai_gb, 3, 0, 2, 2)

        # ======= SONUÇ =======
        self.res = QTextEdit()
        self.res.setReadOnly(True)
        res_layout = QVBoxLayout()
        res_layout.addWidget(self.res)
        res_gb = QGroupBox("Canlı Sonuçlar")
        res_gb.setLayout(res_layout)
        grid.addWidget(res_gb, 3, 2, 2, 2)

        self.start.clicked.connect(self.start_scan)
        self.stop.clicked.connect(self.stop_scan)

        self.setStyleSheet("""
            QMainWindow{background:#f0f4f8;}
            QLineEdit{font-size:22px;padding:20px;border:3px solid #003087;border-radius:16px;}
            QPushButton{background:#003087;color:white;font-weight:bold;font-size:20px;padding:20px;border-radius:16px;}
            QPushButton:hover{background:#00205b;}
            QTextEdit{font-family:Consolas;background:white;border:2px solid #ccc;font-size:15px;}
        """)

        self.ai.append("AI → Hazır. Sadece yetkili sistemleri tarayın.")

    def start_scan(self):
        url = self.target.text().strip()
        if not url: return
        if not url.startswith("http"): url = "https://" + url

        self.res.clear()
        self.ai.clear()
        self.ai.append(f"AI → Tarama başladı: {url}")

        self.worker = Worker(url)
        self.worker.log.connect(lambda t,_: self.res.append(f"<b style='color:#d00000'>{t}</b>"))
        self.worker.info.connect(lambda t: self.res.append(t))
        self.worker.done.connect(self.finish)

        self.start.setEnabled(False)
        self.stop.setEnabled(True)
        self.worker.start()

    def stop_scan(self):
        self.worker.stop()
        self.finish()

    def finish(self):
        self.start.setEnabled(True)
        self.stop.setEnabled(False)
        self.ai_report()

    def ai_report(self):
        urls = re.findall(r"https?://[^\s<]+", self.res.toPlainText())
        if not urls:
            self.ai.append("AI → Doğrulanmış zafiyet yok.")
            return

        prompt = f"""
Aşağıdaki doğrulanmış bulgular için profesyonel pentest raporu hazırla:

{chr(10).join(urls)}

Her biri için:
- Tür
- CVSS
- Risk
- Çözüm
"""

        try:
            r = ollama.chat(
                model="llama3.2",
                messages=[{"role":"user","content":prompt}],
                options={"temperature":0.2}
            )
            self.ai.append(r["message"]["content"])
        except:
            self.ai.append("AI çevrimdışı (ollama çalışıyor mu?)")

# ================== MAIN ==================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = AuryX2025()
    win.show()
    sys.exit(app.exec())
