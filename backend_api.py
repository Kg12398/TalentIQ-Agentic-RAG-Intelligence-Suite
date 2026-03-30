import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from Generation import run_rag_pipeline, get_cached_pipeline

app = FastAPI(title="TalentIQ Intelligence API", version="1.0.0")

# ── CORS CONFIGURATION ──
# Required so the React frontend (port 3000) can talk to this API (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with ['http://localhost:3000']
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    route: str

@app.get("/")
async def root():
    return {"status": "online", "engine": "TalentIQ Agentic RAG"}

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        print(f"[API] Neural Query Received: {request.question}")
        
        # Initialize RAG Pipeline
        pipeline = get_cached_pipeline()
        
        # Execute RAG
        result = run_rag_pipeline(
            user_question=request.question,
            pipeline=pipeline
        )
        
        return AnswerResponse(
            answer=result.get("answer", "No answer generated."),
            route=result.get("route", "RAG")
        )
        
    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the API on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
