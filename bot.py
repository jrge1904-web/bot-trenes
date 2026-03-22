import os
import requests
from bs4 import BeautifulSoup
import urllib3
from datetime import datetime, timedelta
import pytz

# Desactivar avisos de seguridad de conexiones no seguras
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURACIÓN SEGURA MEDIANTE SECRETS ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
UMBRAL = 20

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, verify=False, timeout=10)
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

def check_adif():
    # Ajuste de hora a España
    espana_tz = pytz.timezone('Europe/Madrid')
    ahora = datetime.now(espana_tz)
    hora_actual = ahora.strftime("%H:%M")
    
    # 1. Informe de Buenos Días (10:00 AM)
    if hora_actual == "10:00":
        enviar_telegram("☀️ *¡Buenos días!* \nComienzo mi jornada de vigilancia. Te avisaré si detecto retrasos mayores a 20 min o cancelaciones.")
        return

    # 2. Informe de Fin de Jornada (22:00 PM)
    if hora_actual == "22:00":
        enviar_telegram("🌙 *Fin de jornada* \nHasta aquí mi vigilancia por hoy. ¡Que descanses!")
        return

    # 3. Vigilancia de Trenes
    url = "http://www.adif.es/estaciones/infotren/infotren_resultado.jsp"
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        filas = soup.find_all('tr')
        
        for fila in filas:
            cols = fila.find_all('td')
            if len(cols) >= 5:
                num = cols[0].text.strip()
                orig = cols[1].text.strip().upper()
                dest = cols[2].text.strip().upper()
                h_prog = cols[3].text.strip()
                estado = cols[4].text.strip().upper()

                # Detectar Cancelaciones
                if "CANCELADO" in estado or "SUPRIMIDO" in estado:
                    enviar_telegram(f"❌ *TREN CANCELADO*\n🚆 {num}\n📍 {orig} ➔ {dest}")
                
                # Detectar Retrasos
                mins_str = "".join(filter(str.isdigit, estado))
                if mins_str:
                    mins = int(mins_str)
                    if mins >= UMBRAL:
                        h_p = datetime.strptime(h_prog, "%H:%M")
                        h_est = (h_p + timedelta(minutes=mins)).strftime("%H:%M")
                        enviar_telegram(f"⚠️ *RETRASO >{UMBRAL}min*\n🚆 {num}\n⏰ {mins} min (Llegada: {h_est})\n📍 {orig} ➔ {dest}")
    except Exception as e:
        print(f"Error al consultar Adif: {e}")

if __name__ == "__main__":
    check_adif()
