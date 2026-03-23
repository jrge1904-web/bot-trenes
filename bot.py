import os
import requests
from bs4 import BeautifulSoup
import urllib3
from datetime import datetime, timedelta
import pytz

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = os.getenv("TELEGRAM_TOKEN")
# Este es tu ID personal que guardamos en Secrets
MI_PROPIO_ID = os.getenv("TELEGRAM_CHAT_ID")
UMBRAL = 20

def obtener_usuarios():
    """Busca usuarios nuevos y añade siempre al dueño"""
    usuarios = set()
    # 1. Añadimos tu ID de los Secrets obligatoriamente
    if MI_PROPIO_ID:
        usuarios.add(str(MI_PROPIO_ID))
    
    # 2. Intentamos buscar a tus amigos que hayan escrito /start
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        r = requests.get(url, verify=False, timeout=10).json()
        if "result" in r:
            for update in r["result"]:
                if "message" in update:
                    usuarios.add(str(update["message"]["chat"]["id"]))
    except:
        pass
    return usuarios

def enviar_telegram_a_todos(mensaje):
    usuarios = obtener_usuarios()
    print(f"Enviando a los siguientes IDs: {usuarios}") # Esto saldrá en el log de GitHub
    for user_id in usuarios:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": user_id, "text": mensaje, "parse_mode": "Markdown"}
        try:
            res = requests.post(url, json=payload, verify=False, timeout=5)
            print(f"Resultado para {user_id}: {res.status_code}")
        except Exception as e:
            print(f"Error con {user_id}: {e}")

def check_adif():
    espana_tz = pytz.timezone('Europe/Madrid')
    ahora = datetime.now(espana_tz)
    hora_actual = ahora.strftime("%H:%M")
    
    # Mensajes programados (10:00 y 22:00)
    if hora_actual == "10:00":
        enviar_telegram_a_todos("☀️ *¡Buenos días!* \nVigilancia de Adif iniciada.")
        return
    if hora_actual == "22:00":
        enviar_telegram_a_todos("🌙 *Fin de jornada* \nHasta mañana.")
        return

    url = "http://www.adif.es/estaciones/infotren/infotren_resultado.jsp"
    incidencias = 0
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        filas = soup.find_all('tr')
        
        for fila in filas:
            cols = fila.find_all('td')
            if len(cols) >= 5:
                num, orig, dest, h_prog, estado = cols[0].text.strip(), cols[1].text.strip().upper(), cols[2].text.strip().upper(), cols[3].text.strip(), cols[4].text.strip().upper()
                if "CANCELADO" in estado or "SUPRIMIDO" in estado:
                    enviar_telegram_a_todos(f"❌ *CANCELADO*\n🚆 {num}\n📍 {orig} ➔ {dest}")
                    incidencias += 1
                mins_str = "".join(filter(str.isdigit, estado))
                if mins_str and int(mins_str) >= UMBRAL:
                    mins = int(mins_str)
                    enviar_telegram_a_todos(f"⚠️ *RETRASO {mins}min*\n🚆 {num}\n📍 {orig} ➔ {dest}")
                    incidencias += 1
        
        # Mensaje de confirmación SIEMPRE que le des al botón
        if incidencias == 0:
            enviar_telegram_a_todos(f"✅ *Vigilancia activa ({ahora.strftime('%H:%M')})*\nTodo en orden en Adif.")
    except Exception as e:
        print(f"Error General: {e}")

if __name__ == "__main__":
    check_adif()
