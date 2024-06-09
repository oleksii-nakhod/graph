from flask import Flask
from waitress import serve
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

from utils.helpers import init_cache
init_cache(app)

# from models.transaction import TransactionClassifierGCN
# app.transaction_classifier = TransactionClassifierGCN()
# app.transaction_classifier.load_for_inference('models/transaction_classifier_gcn.pth')

# from models.helpers import load_preprocessed_data
# app.transaction_data = load_preprocessed_data('data/transaction/transactions.pkl')

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
    print("Starting server...")
    serve(app, host='0.0.0.0', port=5004, threads=6)