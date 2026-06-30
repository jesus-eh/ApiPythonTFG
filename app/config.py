import os
from dotenv import load_dotenv

load_dotenv()

# Aqui esta todo lo relacionado con la configuracion de la api
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")