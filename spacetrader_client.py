import requests
from typing import Optional, Any
import json
import os

# Define la URL base de la API
BASE_URL = "https://api.spacetraders.io/v2"

class SpaceTradersClient:
    """
    Cliente para interactuar con la API de SpaceTraders.io
    """
    def __init__(self, token: Optional[str] = None):
        """
        Inicializa el cliente. El token se puede cargar más tarde o usar en el registro.
        """
        self.token = token
        self.headers = {}
        if self.token:
            self._update_headers()
    
    def _update_headers(self):
        """Actualiza la cabecera con el token del agente."""
        self.headers = {
            "Authorization": f"Bearer {self.token}"
        }

    def _make_request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        """
        Método genérico para manejar peticiones a la API.
        Maneja errores y decodifica la respuesta JSON.
        """
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=data)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            # Agrega otros métodos (PUT, PATCH) según sea necesario
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")

            # Lanza una excepción para códigos de estado de error (4xx o 5xx)
            response.raise_for_status() 

            return response.json()
            
        except requests.exceptions.HTTPError as e:
            # Captura y muestra errores específicos de la API (ej. token inválido, 404)
            print(f"Error HTTP en {url}: {e}")
            try:
                error_details = response.json().get('error', {})
                print(f"Detalles del error de la API: {error_details.get('message', 'N/A')}")
            except json.JSONDecodeError:
                print("La respuesta no contiene JSON válido.")
            return {"error": str(e)} # Retorna el error para manejo externo

        except requests.exceptions.RequestException as e:
            # Captura errores de red (ej. problemas de conexión)
            print(f"Error de conexión: {e}")
            return {"error": str(e)}

    # --- Los métodos de la API irán aquí ---

    def register_agent(self, symbol: str, faction: str = "COSMIC") -> Optional[dict]:
        """
        Paso 1: Registra un nuevo agente en el juego.
        Retorna los datos del agente, incluyendo el token de acceso.
        """
        endpoint = "/register"
        data = {
            "symbol": symbol,
            "faction": faction 
            # Nota: Algunos endpoints requieren 'Account-Token' o una cabecera diferente
            # para el registro programático. Revisa la documentación si falla
            # y usa el dashboard si es necesario.
        }
        
        # El registro no requiere el token de agente, por lo que las cabeceras están vacías
        # si el cliente se inicializó sin él.
        response_data = self._make_request("POST", endpoint, data=data)

        # Si el registro fue exitoso, guarda el token y actualiza las cabeceras
        if response_data and 'data' in response_data and 'token' in response_data['data']:
            self.token = response_data['data']['token']
            self._update_headers()
            print(f"\n¡Registro exitoso! Agente: {response_data['data']['agent']['symbol']}")
            print(f"**IMPORTANTE:** Tu token de agente es: {self.token}")
            print("Guarda este token, es la llave para acceder al juego.")
            return response_data
        
        return None

# --- Zona de Ejecución / Pruebas ---
if __name__ == "__main__":
    
    # 1. Configura tu símbolo de agente
    # Debe ser único y solo mayúsculas, números y guiones bajos (ej. MI_BOT_001)
    AGENT_SYMBOL = "YOUR_CUSTOM_AGENT_NAME" 
    
    # 2. Inicializa el cliente
    client = SpaceTradersClient()
    
    # 3. Intenta registrar
    print(f"Intentando registrar el agente '{AGENT_SYMBOL}'...")
    
    registration_result = client.register_agent(AGENT_SYMBOL)

    if client.token:
        print("\nCliente listo. Puedes empezar a añadir más métodos como:")
        # Ejemplo de lo que harías después (aunque no hemos escrito el método aún)
        # client.get_my_agent_data()
        pass
    else:
        print("\nNo se pudo completar el registro. Verifica el nombre del agente o el estado del servidor.")