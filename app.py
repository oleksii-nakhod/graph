from flask import Flask
from waitress import serve
import logging
import os
from dotenv import load_dotenv

load_dotenv()

from utils.helpers import init_cache

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

init_cache(app)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app.logger.info('Logging setup complete')

from routes.main import main_bp
from routes.auth import auth_bp
from routes.files import files_bp
from routes.graph import graph_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(files_bp)
app.register_blueprint(graph_bp)

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5004)