from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from dotenv import load_dotenv
from contextlib import contextmanager
import os
import time
from sqlalchemy.exc import OperationalError


load_dotenv()

DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_NAME = os.getenv("MYSQL_DATABASE")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@db:3306/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_session():
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


Base = declarative_base()


def init_db():
    retries = 10
    while retries > 0:
        try:
            print("[...] Intentando conectar a la base de datos...")
            Base.metadata.create_all(engine)
            print("[+] Tablas creadas exitosamente.")
            return
        except OperationalError:
            print("[-] Base de datos no responde. Esperando 5 segundos...")
            time.sleep(5)
            retries -= 1
    raise Exception(
        "No se pudo conectar a la base de datos después de varios intentos."
    )
