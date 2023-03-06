import uvicorn


def create_umls_server():
    uvicorn.run("src.UMLS.umls_services:app", host="127.0.0.1", port=5000, log_level="info")
