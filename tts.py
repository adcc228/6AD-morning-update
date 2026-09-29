"""Kokoro TTS (ONNX) with espeak-ng phonemes. Offline, British voices.
Usage: python3 tts.py script.txt out.mp3
Script format: lines 'A: text' / 'B: text'; blank lines ignored; '[PAUSE]' inserts a beat.
"""
import os, re, sys, subprocess, numpy as np, onnxruntime as ort, wave

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.environ.get("TTS_ASSETS", os.path.join(HERE, "assets"))
PIPER = os.path.join(ASSETS, "piper")
SR = 24000
VOICES = {"A": ("bf_emma", 1.05), "B": ("bm_george", 1.05)}

VOCAB = {';':1,':':2,',':3,'.':4,'!':5,'?':6,'—':9,'…':10,'"':11,'(':12,')':13,'“':14,'”':15,' ':16,
'̃':17,'ʣ':18,'ʥ':19,'ʦ':20,'ʨ':21,'ᵝ':22,'ꭧ':23,'A':24,'I':25,'O':31,'Q':33,'S':35,'T':36,'W':39,'Y':41,'ᵊ':42,
'a':43,'b':44,'c':45,'d':46,'e':47,'f':48,'h':50,'i':51,'j':52,'k':53,'l':54,'m':55,'n':56,'o':57,'p':58,'q':59,'r':60,
's':61,'t':62,'u':63,'v':64,'w':65,'x':66,'y':67,'z':68,'ɑ':69,'ɐ':70,'ɒ':71,'æ':72,'β':75,'ɔ':76,'ɕ':77,'ç':78,'ɖ':80,
'ð':81,'ʤ':82,'ə':83,'ɚ':85,'ɛ':86,'ɜ':87,'ɟ':90,'ɡ':92,'ɥ':99,'ɨ':101,'ɪ':102,'ʝ':103,'ɯ':110,'ɰ':111,'ŋ':112,'ɳ':113,
'ɲ':114,'ɴ':115,'ø':116,'ɸ':118,'θ':119,'œ':120,'ɹ':123,'ɾ':125,'ɻ':126,'ʁ':128,'ɽ':129,'ʂ':130,'ʃ':131,'ʈ':132,'ʧ':133,
'ʊ':135,'ʋ':136,'ʌ':138,'ɣ':139,'ɤ':140,'χ':142,'ʎ':143,'ʒ':147,'ʔ':148,'ˈ':156,'ˌ':157,'ː':158,'ʰ':162,'ʲ':164,
'↓':169,'→':171,'↗':172,'↘':173,'ᵻ':177}

def espeak(texts):
    """Phonemize a list of clauses in one espeak call (one clause per line)."""
    env = dict(os.environ, LD_LIBRARY_PATH=PIPER)
    out = []
    for t in texts:
        r = subprocess.run([os.path.join(PIPER, "espeak-ng"), f"--path={PIPER}", "-q", "--ipa", "-v", "en-gb", t],
                           capture_output=True, text=True, env=env)
        out.append(" ".join(r.stdout.split()))
    return out

def normalise(t):
    t = re.sub(r"(?<=\d),(?=\d{3})", "", t)            # 7,684 -> 7684 (commas would split clauses)
    t = re.sub(r"\$(\d+)\.(\d{2})\b", r"\1 dollars \2", t)  # $107.35 -> 107 dollars 35
    t = re.sub(r"(?<=\d)\.(?=\d)", " point ", t)        # 5.25 -> 5 point 25
    t = t.replace("%", " percent").replace("&", " and ").replace("€", " euro ").replace("£", " pound ")
    t = re.sub(r"\$(\d[\d,.]*)\s*(bn|billion|m|million|trillion|tn)?", lambda m: f"{m.group(1)} {m.group(2) or ''} dollars", t)
    t = t.replace("–", ", ").replace("-", " ")
    return re.sub(r"\s+", " ", t).strip()

def to_phonemes(text):
    parts = re.split(r"([,;:.!?—]+)", normalise(text))
    clauses, puncts = parts[0::2], parts[1::2] + [""]
    phs = espeak([c for c in clauses])
    s = ""
    for ph, p, c in zip(phs, puncts, clauses):
        if not c.strip():
            s += p[:1]; continue
        ph = ph.replace("tʃ", "ʧ").replace("dʒ", "ʤ").replace("ʲ", "j").replace("r", "ɹ").replace("x", "k").replace("ɬ", "l")
        ph = ph.replace("͡", "").replace("‿", " ")
        s += ph + (p[:1] if p else "") + " "
    return s.strip()

class TTS:
    def __init__(self):
        self.sess = ort.InferenceSession(os.path.join(ASSETS, "kokoro.onnx"))
        self.voices = np.load(os.path.join(ASSETS, "voices.bin"))

    def say(self, text, voice, speed):
        ph = to_phonemes(text)
        chunks, cur = [], ""
        for piece in re.split(r"(?<=[.!?;,])\s+", ph):  # keep each chunk < 500 tokens
            if len(cur) + len(piece) > 400 and cur:
                chunks.append(cur); cur = piece
            else:
                cur = (cur + " " + piece).strip()
        if cur: chunks.append(cur)
        audio = []
        for c in chunks:
            ids = [VOCAB[ch] for ch in c if ch in VOCAB][:510]
            style = self.voices[voice][len(ids)]
            wav = self.sess.run(None, {"tokens": np.array([[0, *ids, 0]], dtype=np.int64),
                                       "style": style.astype(np.float32), "speed": np.array([speed], dtype=np.float32)})[0]
            audio.append(wav.squeeze()); audio.append(np.zeros(int(SR * 0.12), np.float32))
        return np.concatenate(audio)

def render(script_path, out_mp3):
    tts = TTS()
    segs = []
    for line in open(script_path, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        if line == "[PAUSE]":
            segs.append(np.zeros(int(SR * 0.9), np.float32)); continue
        m = re.match(r"^([AB]):\s*(.+)$", line)
        if not m: continue
        v, sp = VOICES[m.group(1)]
        segs.append(tts.say(m.group(2), v, sp))
        segs.append(np.zeros(int(SR * 0.35), np.float32))
    audio = np.concatenate(segs)
    audio = audio / max(1e-6, np.abs(audio).max()) * 0.9
    wav_path = out_mp3.rsplit(".", 1)[0] + ".wav"
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((audio * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav_path, "-af", "loudnorm=I=-16:TP=-1.5",
                    "-codec:a", "libmp3lame", "-b:a", "96k", out_mp3], check=True)
    os.remove(wav_path)
    return len(audio) / SR

if __name__ == "__main__":
    print(f"duration {render(sys.argv[1], sys.argv[2]) / 60:.1f} min")
