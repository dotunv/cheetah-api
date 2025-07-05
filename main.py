from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Cheetah API",
    description="A FastAPI project built with uv package manager",
    version="1.0.0"
)

@app.get("/")
async def root():
    return JSONResponse(
        content={
            "message": "Welcome to Cheetah API!",
            "status": "running",
            "version": "1.0.0"
        }
    )

@app.get("/health")
async def health_check():
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "cheetah-api"
        }
    )

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return JSONResponse(
        content={
            "item_id": item_id,
            "q": q
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
