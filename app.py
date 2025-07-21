from bank_reco.main import kickoff
from gst_reco.main import kickoff_gst_reconciliation
import uvicorn
from fastapi import FastAPI, UploadFile, File, Query, Form
from fastapi.responses import JSONResponse
import tempfile
import shutil
import os
import json


app = FastAPI(
    title="GST & Bank Reconciliation API",
    description="API for GST Input Tax Credit reconciliation and Bank statement reconciliation",
    version="1.0.0"
)


@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "GST & Bank Reconciliation API",
        "version": "1.0.0",
        "endpoints": {
            "gst_reconciliation": "/gst-reconcile",
            "bank_reconciliation": "/reconcile",
            "health": "/health"
        },
        "documentation": "/docs",
        "features": {
            "gst_formats_supported": ["GSTR-2A", "GSTR-2B"],
            "reconciliation_types": ["GST Input Tax Credit", "Bank Statements"]
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GST & Bank Reconciliation API"
    }


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


@app.post("/gst-reconcile")
def gst_reconcile(
    books_file: UploadFile = File(...),
    gstr_data: str = Form(...),
    company_id: str = Query(...),
    sheet_name: str = Query(default="Book ITC"),
    fuzzy_threshold: int = Query(default=85),
    date_tolerance: int = Query(default=0),
    amount_tolerance: float = Query(default=0.0),
):
    """
    GST Reconciliation API endpoint - Supports both GSTR-2A and GSTR-2B formats

    Args:
        books_file: Excel file containing Books of Accounts data (Book ITC sheet)
        gstr_data: JSON string containing GSTR-2A or GSTR-2B data
        company_id: Company identifier
        sheet_name: Sheet name in Excel file (default: "Book ITC")
        fuzzy_threshold: Fuzzy matching threshold for invoice numbers (default: 85)
        date_tolerance: Date tolerance in days (default: 2)
        amount_tolerance: Amount tolerance in rupees (default: 5.0)

    Supported GSTR Formats:
        - GSTR-2A: JSON with 'data' -> 'list' structure
        - GSTR-2B: JSON with 'docdata' structure

    Returns:
        JSON response with reconciliation results, summary, and report paths
    """
    temp_path = None
    try:
        # Parse GSTR JSON data
        try:
            gstr_json = json.loads(gstr_data)
        except json.JSONDecodeError as e:
            return JSONResponse(
                status_code=400,
                content={"error": f"Invalid GSTR JSON data: {str(e)}"},
            )


            
            
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
            shutil.copyfileobj(books_file.file, temp_file)
            temp_path = temp_file.name

        print(f"Temporary file saved at: {temp_path}")
        
        # Perform GST reconciliation
        results = kickoff_gst_reconciliation(
            gstr_json=gstr_json,
            books_file_path=temp_path,
            company_id=company_id,
            sheet_name=sheet_name,
            fuzzy_threshold=fuzzy_threshold,
            date_tolerance=date_tolerance,
            amount_tolerance=amount_tolerance,
        )

        if results.get("status") == "error":
            return JSONResponse(
                status_code=500,
                content={"error": results.get(
                    "message", "GST reconciliation failed")},
            )

        return JSONResponse(
            status_code=200,
            content={
                "message": "GST reconciliation completed successfully.",
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


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=int(
        os.getenv("PORT", 5000)), workers=1)
