"""
Travel Hub - Experimento 2: Rate Limiting basado en JWT
Ejecutar con: flask run
"""
from api_gateway.app import app

if __name__ == '__main__':
    app.run(debug=True, port=5000)
