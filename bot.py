import os
import requests
from bs4 import BeautifulSoup
import urllib3
from datetime import datetime, timedelta
import pytz

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = os.getenv("TELEGRAM_TOKEN")
# Ya no usaremos un solo CHAT_ID fijo, sino una lista
UMBRAL = 20

def obtener_usuarios():
    """Función para obtener todos los usuarios que han iniciado el bot"""
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    usuarios = set()
    # Añadimos tu ID por defecto desde los Secrets por si acaso
    mi_id = os.getenv("TELEGRAM_CHAT_ID")
    if mi_id: usuarios.add(mi_id)
    
    try:
        r = requests.get(url, verify=False, timeout=10).json()
        if "result" in r:
            for update in r["result"]:
                if "message" in update:
                    usuarios.add(str(update["message"]["chat"]["id"]))
    except: pass
    return usuarios

def enviar_telegram_a_todos(mensaje):
    usuarios = obtener_usuarios()
    for user_id in usuarios:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": user_id, "text": mensaje, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, verify=False, timeout=5)
        except: pass

def check_adif():
    espana_tz = pytz.timezone('Europe/Madrid')
    ahora = datetime.now(espana_tz)
    hora_actual = ahora.strftime("%H:%M")
    
    if hora_actual == "10:00":
        enviar_telegram_a_todos("☀️ *¡Buenos días!* \nSoy el Vigilante de Trenes. He empezado mi turno y os avisaré de cualquier incidencia grave.")
        return

    if hora_actual == "22:00":
        enviar_telegram_a_todos("🌙 *Fin de jornada* \nHasta mañana. ¡Que descanséis!")
        return

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

                if "CANCELADO" in estado or "SUPRIMIDO" in estado:
                    enviar_telegram_a_todos(f"❌ *TREN CANCELADO*\n🚆 {num}\n📍 {orig} ➔ {dest}")
                
                mins_str = "".join(filter(str.isdigit, estado))
                if mins_str:
                    mins = int(mins_str)
                    if mins >= UMBRAL:
                        h_p = datetime.strptime(h_prog, "%H:%M")
                        h_est = (h_p + timedelta(minutes=mins)).strftime("%H:%M")
                        enviar_telegram_a_todos(f"⚠️ *RETRASO >{UMBRAL}min*\n🚆 {num}\n⏰ {mins} min (Llega: {h_est})\n📍 {orig} ➔ {dest}")
    except: pass

if __name__ == "__main__":
    check_adif()
