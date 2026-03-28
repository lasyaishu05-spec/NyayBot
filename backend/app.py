from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import process

app = FastAPI(
    title="NyayBot API",
    description="Legal Document Simplification & Translation Bot",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # Use False for "allow_origins=['*']" for highest compatibility
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(process.router)


@app.get("/")
def home():
    return {"message": "NyayBot Backend Running"}
