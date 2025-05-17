from .bank_reco.main import kickoff

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse
import tempfile
import shutil
import os


app = FastAPI()


@app.post("/reconcile")
def reconcile_statements(
    file: UploadFile = File(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
    company_id: str = Query(...),
):
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        results = kickoff(
            file_path=temp_path,
            start_date=start_date,
            end_date=end_date,
            company_id=company_id,
        )

        return JSONResponse(
            status_code=200,
            content={
                "message": "Reconciliation completed successfully.",
                "results": results,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
