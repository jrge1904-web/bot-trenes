import os
import requests
from bs4 import BeautifulSoup
import urllib3
from datetime import datetime, timedelta
import pytz

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = os.getenv("TELEGRAM_TOKEN")
UMBRAL = 20

def obtener_usuarios():
    """Busca a todos los que han interactuado con el bot últimamente"""
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    usuarios = set()
    mi_id = os.getenv("TELEGRAM_CHAT_ID")
    if mi_id: usuarios.add(mi_id)
    
    try:
        r = requests.get(url, verify=False, timeout=10).json()
        if "result" in r:
            for update in r["result"]:
                if "message" in update:
                    usuarios.add(str(update["message"]["chat"]["id"]))
                elif "my_chat_member" in update:
                    usuarios.add(str(update["my_chat_member"]["chat"]["id"]))
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
    
    # --- MENSAJES PROGRAMADOS ---
    if hora_actual == "10:00":
        enviar_telegram_a_todos("☀️ *¡Buenos días!* \nIniciando vigilancia diaria de Adif.")
        return

    if hora_actual == "22:00":
        enviar_telegram_a_todos("🌙 *Fin de jornada* \nEl sistema entra en reposo hasta mañana.")
        return

    # --- ESCANEO DE ADIF ---
    url = "http://www.adif.es/estaciones/infotren/infotren_resultado.jsp"
    incidencias_detectadas = 0
    
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        filas = soup.find_all('tr')
        
        for fila in filas:
            cols = fila.find_all('td')
            if len(cols) >= 5:
                num, orig, dest, h_prog, estado = cols[0].text.strip(), cols[1].text.strip().upper(), cols[2].text.strip().upper(), cols[3].text.strip(), cols[4].text.strip().upper()

                # Cancelaciones
                if "CANCELADO" in estado or "SUPRIMIDO" in estado:
                    enviar_telegram_a_todos(f"❌ *CANCELADO*\n🚆 {num}\n📍 {orig} ➔ {dest}")
                    incidencias_detectadas += 1
                
                # Retrasos
                mins_str = "".join(filter(str.isdigit, estado))
                if mins_str and int(mins_str) >= UMBRAL:
                    mins = int(mins_str)
                    h_p = datetime.strptime(h_prog, "%H:%M")
                    h_est = (h_p + timedelta(minutes=mins)).strftime("%H:%M")
                    enviar_telegram_a_todos(f"⚠️ *RETRASO {mins}min*\n🚆 {num}\n⏰ Llega: {h_est}\n📍 {orig} ➔ {dest}")
                    incidencias_detectadas += 1
        
        # --- NUEVO: MENSAJE DE CONFIRMACIÓN SI TODO ESTÁ BIEN ---
        if incidencias_detectadas == 0:
            enviar_telegram_a_todos(f"✅ *Vigilancia activa ({ahora.strftime('%H:%M')})*\nSin incidencias graves en la red de Adif en este momento.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_adif()
