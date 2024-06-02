from neo4j import GraphDatabase
from config import Config

class Neo4jConnection:
    def __init__(self, uri, auth):
        self.__uri = uri
        self.__auth = auth
        self.__driver = None
        try:
            self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__auth))
            # self.create_indexes()
        except Exception as e:
            print("Failed to create the driver:", e)
        
    def close(self):
        if self.__driver is not None:
            self.__driver.close()
        
    def query(self, query, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        try: 
            session = self.__driver.session(database=db) if db is not None else self.__driver.session() 
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed:", e)
        finally: 
            if session is not None:
                session.close()
        return response
    
    def create_indexes(self):
        index_queries = [
            f"""
            CREATE VECTOR INDEX `item_embedding_index` IF NOT EXISTS
            FOR (n:Item)
            ON (n.embedding)
            OPTIONS {{indexConfig: {{
                `vector.dimensions`: {Config.OPENAI_EMBEDDING_DIMENSIONS},
                `vector.similarity_function`: 'cosine'
            }}}}
            """,
            """
            CREATE INDEX item_composite_index IF NOT EXISTS
            FOR (n:Item)
            ON (n.id, n.title, n.created_at)
            """
        ]
        
        for query in index_queries:
            try:
                self.query(query)
                print(f"Index created successfully or already exists for query: {query.strip().split()[2]}")
            except Exception as e:
                print(f"Failed to create index for query: {query.strip().split()[2]}, error: {e}")

conn = Neo4jConnection(
    uri=Config.NEO4J_URI, 
    auth=(Config.NEO4J_ADMIN_USERNAME, Config.NEO4J_ADMIN_PASSWORD)
)