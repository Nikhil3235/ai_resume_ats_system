import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import(
    ALLOWED_ORIGINS, 
    APP_DESCRIPTION, 
    APP_TITLE, 
    APP_VERSION, 
    SPACY_MODEL_PRIMARY, 
    SPACY_MODEL_SECONDARY, SENTENCE_TRANSFORMER_MODEL
)
from backend.api.routes import router

logger=logging.getLogger('ats_resume_scorer')

class AppState:
    def __init__(self):
        self._nlp = None
        self._embedder = None

    @property
    def nlp(self):
        if self._nlp is None:
            import spacy
            from backend.core.config import SPACY_MODEL_SECONDARY, SPACY_MODEL_PRIMARY
            try:
                self._nlp = spacy.load(SPACY_MODEL_SECONDARY)
            except OSError:
                self._nlp = spacy.load(SPACY_MODEL_PRIMARY)
        return self._nlp

    @property
    def embedder(self):
        if self._embedder is None:
            from backend.services.embedder import get_embedder
            self._embedder = get_embedder()
        return self._embedder

lazy_state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Starting ATS Resume Analyzer API (Fast 50MB Startup)...')
    app.state.nlp_getter = lambda: lazy_state.nlp
    app.state.embedder_getter = lambda: lazy_state.embedder
    logger.info('API Ready to serve requests immediately.')
    yield
    logger.info('Shutting down API.')

app=FastAPI(
    title=APP_TITLE, 
    description=APP_DESCRIPTION, 
    version=APP_VERSION, 
    lifespan=lifespan,
    docs_url='/docs',
    redoc_url='/redoc'
)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True, 
    allow_methods     = ['*'],
    allow_headers     = ['*'],

)

app.include_router(router)

@app.get('/')
async def root():
    return {
        'name':      'ATS Resume Analyzer API',
        'version':   '2.0.0',
        'endpoints': {
            'POST   /api/v1/analyze-resume': 'Analyze a resume',
            'GET    /api/v1/history':        'Get user history',
            'DELETE /api/v1/history/:id':    'Delete a history entry',
            'GET    /api/v1/health':         'Health check',
            'POST   /api/v1/generate-pdf':   'Generate PDF report from data',
        },
    }

if __name__=='__main__':
    import uvicorn
    uvicorn.run(
        'backend.main:app',
        host    = '0.0.0.0',
        port    = 8000,
        reload  = True,    # Auto-restart on code changes (dev only)
    )