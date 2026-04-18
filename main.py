from dotenv import load_dotenv
from fastapi import FastAPI
from routers import auth, fetch, export

load_dotenv()

app = FastAPI(title="Postgram")

app.include_router(auth.router)
app.include_router(fetch.router)
app.include_router(export.router)
