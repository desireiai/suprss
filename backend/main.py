# main_minimal.py - Version ultra minimale pour tester
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SUPRSS API - Test",
    version="1.0.0",
    docs_url="/api/docs"
)

# CORS pour accepter toutes les origines
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "SUPRSS API is running", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "SUPRSS Backend"}

@app.get("/api/test")
def test():
    return {"test": "successful", "timestamp": "2024-01-01"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)