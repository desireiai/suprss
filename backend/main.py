from fastapi import FastAPI
app = FastAPI(Title="SUPRSS API", description="API backend dans le framework fastapi", version="1.0.0")
@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API SUPRSS"} 
       
@app.get("/health")
def health_check():
    return {"status": "healthy"} 
