from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from typing import Dict
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from parser.parsing import run_single_crawl

app = FastAPI()

class Parsed(BaseModel):
    url: str
    domain: str
    title: str
    parsed_text: str

@app.get("/parse")
async def parse_url(url: str) -> Parsed:
    domain = url[8:].split("/")[0]
    
    SUPPORTED_DOMAINS = ["en.wikipedia.org"]
    if domain not in SUPPORTED_DOMAINS:
        raise HTTPException(status_code=400, detail=f"Dominio '{domain}' non supportato.")
    
    try:
        res = await run_single_crawl(url)
        return Parsed(
            url=res["url"],
            domain=res["domain"],
            title=res["title"],
            parsed_text=res["parsed_text"]
        )
    except ConnectionError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # ← mostra l'errore reale

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)