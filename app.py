from flask import Flask, request, jsonify, render_template
import requests
import os

app = Flask(__name__)

# --- INICIO DE LA FUNCIÓN OBTENER_DETALLES_TARJETA ACTUALIZADA ---
def obtener_detalles_tarjeta(entrada):
    numero_tarjeta = entrada.split('|')[0]
    primeros_seis_digitos = numero_tarjeta[:6]
    
    # --- NUEVA CONFIGURACIÓN DE LA API DE RAPIDAPI ---
    url = "https://bin-info.p.rapidapi.com/bin.php"
    
    # IMPORTANTE: Estas son las keys proporcionadas en tu solicitud. 
    # En un entorno real, las keys secretas se deben manejar como variables de entorno.
    headers = {
        'x-rapidapi-host': "bin-info.p.rapidapi.com",
        'x-rapidapi-key': "a0f3fde9d1msh7927a2350950bd0p1fc2f7jsnebcb52da28ab"
    }
    
    querystring = {"bin": primeros_seis_digitos}
    
    try:
        # Hacemos una solicitud GET a la nueva API
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        
        if response.status_code == 200:
            # La respuesta es un JSON, no HTML
            data = response.json()
            
            # Mapeo de los datos obtenidos de la API al formato de salida deseado
            # Usamos .get() para evitar errores si un campo no existe
            
            # Para 'Brand', unimos brand, type y category
            brand_info = f"{data.get('brand', 'N/A')} - {data.get('type', 'N/A')} - {data.get('category', 'N/A')}"
            
            # Para 'Bank', usamos 'issuer'
            bank_info_value = data.get('issuer', 'No encontrado')
            
            # Para 'Country', usamos el 'country' completo y el código ISO2
            country_iso_value = f"{data.get('country', 'No encontrado')} - {data.get('iso2', 'N/A')}"
            
            # La nueva API no proporciona la URL de la bandera.
            flag_url = "No encontrado" 

            return {
                "card": entrada,
                "brand": brand_info,
                "bank": bank_info_value,
                "country": country_iso_value,
                "flag": flag_url,
                "bin": primeros_seis_digitos
            }
        else:
            return {"error": f"Error al obtener detalles: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}
# --- FIN DE LA FUNCIÓN OBTENER_DETALLES_TARJETA ACTUALIZADA ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/verificar_tarjeta', methods=['POST'])
def verificar_tarjeta():
    try:
        data = request.get_json()
        entrada = data.get('cardData')
        if entrada:
            detalles = obtener_detalles_tarjeta(entrada)
            return jsonify(detalles)
        else:
            return jsonify({"error": "No se proporcionaron datos de tarjeta."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========= ENVÍO A TELEGRAM POR BACKEND (POST JSON) =========
@app.route('/api/send_telegram', methods=['POST'])
def send_telegram():
    try:
        data = request.get_json(force=True)
        bot_token = (data.get('botToken') or '').replace('\u200b','').replace('\ufeff','').strip()
        chat_id   = (data.get('chatId') or '').strip()
        text      = data.get('text') or ''

        if not bot_token or not chat_id or not text:
            return jsonify({"ok": False, "description": "Faltan botToken/chatId/text"}), 400

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=15)

        try:
            payload = r.json()
        except Exception:
            payload = {"ok": False, "description": f"Respuesta no JSON ({r.status_code})", "raw": r.text}

        return jsonify(payload), r.status_code
    except Exception as e:
        return jsonify({"ok": False, "description": str(e)}), 500

# ✅ Bloque necesario para que Render detecte y publique la app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
