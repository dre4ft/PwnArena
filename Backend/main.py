from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import os
import uvicorn
from api.api import check_jwt,router as api_router


app = FastAPI()



# Serve static files (js, css) from Frontend/static at /static
app.mount("/static", StaticFiles(directory="Frontend/static"), name="static")

# Serve index.html at /
@app.get("/")
async def read_index():
    index_path = os.path.join("Frontend", "index.html")
    return FileResponse(index_path, media_type="text/html")

@app.get("/dashboard")
async def dashboard(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        # Try to get from Authorization header (for local dev)
        auth = request.headers.get("authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]
    if not token:
        return RedirectResponse("/", status_code=302)
    if True : #check_jwt(token):
        dashboard_path = os.path.join("Frontend", "dashboard.html")
        return FileResponse(dashboard_path, media_type="text/html")
    else:
        return RedirectResponse("/", status_code=302)
    

app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)