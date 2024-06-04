from flask import Flask
from waitress import serve
import logging
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

from utils.helpers import init_cache
init_cache(app)

from models.transaction import TransactionClassifier
app.transaction_classifier = TransactionClassifier()
app.transaction_classifier.load_for_inference('models/transaction_classifier.pth')

from models.helpers import load_preprocessed_data
app.transaction_data = load_preprocessed_data('data/transaction/transactions.pkl')

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# app.logger.info('Logging setup complete')

from routes.main import main_bp
from routes.auth import auth_bp
from routes.files import files_bp
from routes.graph import graph_bp
from routes.openai_tools import openai_tools_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(files_bp)
app.register_blueprint(graph_bp)
app.register_blueprint(openai_tools_bp)

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5004)