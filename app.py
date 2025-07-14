from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def obtener_detalles_tarjeta(entrada):
    numero_tarjeta = entrada.split('|')[0]
    primeros_seis_digitos = numero_tarjeta[:6]
    url = f"https://bincheck.io/es/details/{primeros_seis_digitos}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            brand_info = []
            country_info = "No encontrado"  # Inicializa la variable para el país
            flag_url = "No encontrado"  # Inicializa la variable para la URL de la bandera
            
            # Imprime el HTML para depuración
            print(soup.prettify())  # Esto te mostrará el HTML completo que estás analizando
            
            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) > 1:
                    if 'Marca de carro' in cols[0].text:
                        brand_info.append(cols[1].text.strip())
                    elif 'Tipo de tarjeta' in cols[0].text:
                        brand_info.append(cols[1].text.strip())
                    elif 'Nivel de tarjeta' in cols[0].text:
                        brand_info.append(cols[1].text.strip())
                    elif 'Nombre del emisor / Banco' in cols[0].text:
                        bank_name = cols[1].text.strip()
                        print(f"Banco encontrado: {bank_name}")  # Imprime el banco encontrado
                        country_info = "UNITED STATES" if "BANK" in bank_name else "No encontrado"

            # Obtener el nombre del banco y el país
            bank_info = soup.find('td', string=lambda x: x and 'Nombre del emisor / Banco' in x)
            bank_info_value = bank_info.find_next('td').text.strip() if bank_info else "No encontrado"

            country_iso_name = soup.find('td', string=lambda x: x and 'Nombre de país ISO' in x)
            country_iso_value = country_iso_name.find_next('td').text.strip() if country_iso_name else "No encontrado"

            # Obtener la URL de la bandera
            flag_info = soup.find('td', string=lambda x: x and 'Bandera del país' in x)
            if flag_info:
                flag_img = flag_info.find_next('td').find('img')
                flag_url = flag_img['src'] if flag_img else "No encontrado"

            return {
                "card": entrada,
                "brand": ' - '.join(brand_info),
                "bank": bank_info_value,
                "country": country_iso_value,  # Usa el país extraído
                "flag": flag_url,  # Agrega la URL de la bandera
                "bin": primeros_seis_digitos  # Ajusta esto si es necesario
            }
        else:
            return {"error": f"Error al obtener detalles: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def index():
    return render_template('index.html')  # Renderiza el archivo HTML

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
        print(f"Ocurrió un error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
