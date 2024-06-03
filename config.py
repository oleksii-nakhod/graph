import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DOMAIN_NAME = os.environ.get("DOMAIN_NAME")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL")
    OPENAI_COMPLETION_MODEL = os.environ.get("OPENAI_COMPLETION_MODEL")
    OPENAI_TRANSCRIPTION_MODEL = os.environ.get("OPENAI_TRANSCRIPTION_MODEL")
    NEO4J_URI = os.environ.get("NEO4J_URI")
    NEO4J_ADMIN_USERNAME = os.environ.get("NEO4J_ADMIN_USERNAME")
    NEO4J_ADMIN_PASSWORD = os.environ.get("NEO4J_ADMIN_PASSWORD")
    OPENAI_EMBEDDING_DIMENSIONS = os.environ.get("OPENAI_EMBEDDING_DIMENSIONS")
    RESERVED_FIELDS = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'username', 'password', 'embedding']
    HIDDEN_FIELDS = ['password', 'embedding']
    RESERVED_LABELS = ['User']
