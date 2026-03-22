import requests
from bs4 import BeautifulSoup
import urllib3
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = "8604664584:AAGz1anzbGYRfhNrSayZgonzeEWuIf60yME"
CHAT_ID = "8482541926"
UMBRAL = 20

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}, verify=False)

def check_adif():
    url = "http://www.adif.es/estaciones/infotren/infotren_resultado.jsp"
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        filas = soup.find_all('tr')
        for fila in filas:
            cols = fila.find_all('td')
            if len(cols) >= 5:
                num, orig, dest, h_prog, estado = cols[0].text.strip(), cols[1].text.strip().upper(), cols[2].text.strip().upper(), cols[3].text.strip(), cols[4].text.strip().upper()
                if "CANCELADO" in estado or "SUPRIMIDO" in estado:
                    enviar_telegram(f"❌ *TREN CANCELADO*\n🚆 {num}\n📍 {orig} ➔ {dest}")
                mins = "".join(filter(str.isdigit, estado))
                if mins and int(mins) >= UMBRAL:
                    h_p = datetime.strptime(h_prog, "%H:%M")
                    h_est = (h_p + timedelta(minutes=int(mins))).strftime("%H:%M")
                    enviar_telegram(f"⚠️ *RETRASO >{UMBRAL}min*\n🚆 {num}\n⏰ {mins} min (Llega: {h_est})\n📍 {orig} ➔ {dest}")
    except: pass

if __name__ == "__main__":
    check_adif()
