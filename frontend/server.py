# server.py - Servidor Web Local para el Frontend de SoyaLens
import http.server
import socketserver
import os
import sys

PORT = 8080
# Obtener el directorio donde se encuentra este archivo script
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        # Opcional: Silenciar registros HTTP ruidosos para mantener la terminal limpia
        pass

if __name__ == "__main__":
    print("-" * 50)
    print("      SOYALENS - CONTROL DE CALIDAD POR IA")
    print("-" * 50)
    print(f"Dirección del Servidor: http://localhost:{PORT}")
    print(f"Directorio Raíz: {DIRECTORY}")
    print("Para detener el servidor: Ctrl + C")
    print("-" * 50)

    # Configurar el socket para reutilizar la dirección y evitar el error "Address already in use"
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor SoyaLens apagado correctamente.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError al iniciar el servidor: {e}")
        sys.exit(1)
