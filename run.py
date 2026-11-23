import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # El modo debug queda apagado salvo que se pida con FLASK_DEBUG=1.
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
