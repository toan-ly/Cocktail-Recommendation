import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

try:
    load_dotenv()
except Exception as e:
    print(f"Error loading .env file: {e}")

class DBSetup:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME", "cocktails_db")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "password")

    def create_database(self):
        try:
            with psycopg2.connect(
                database="postgres",
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            ) as conn:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                with conn.cursor() as cursor:
                    # Check if database exists
                    cursor.execute(
                        "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                        (self.db_name,)
                    )
                    exists = cursor.fetchone()

                    if not exists:
                        cursor.execute(f'CREATE DATABASE {self.db_name}')
                        print(f"Database '{self.db_name}' created successfully")
                    else:
                        print(f"Database '{self.db_name}' already exists")
        except Exception as e:
            print(f"Error creating database: {e}")
    
    def setup_pgvector(self):
        try:
            with psycopg2.connect(
                database=self.db_name,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            ) as conn:
                with conn.cursor() as cursor:
                    # Enable pgvector extension
                    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")

                    # Create cocktails table with vector embeddings
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS cocktails (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(255) NOT NULL,
                            ingredients TEXT NOT NULL,
                            recipe TEXT,
                            glass VARCHAR(100),
                            category VARCHAR(100),
                            iba VARCHAR(100),
                            alcoholic VARCHAR(50),
                            embedding vector(384)
                        )
                    """)

                    # Create index for vector search
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS cocktails_embedding_idx 
                        ON cocktails USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100)
                    """)

                conn.commit()
                print("pgvector extension and cocktails table set up successfully")
                    
        except Exception as e:
            print(f"Error setting up pgvector: {e}")
    
    def get_connection(self):
        return psycopg2.connect(
            database=self.db_name,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )

if __name__ == "__main__":
    setup = DBSetup()
    setup.create_database()
    setup.setup_pgvector()


