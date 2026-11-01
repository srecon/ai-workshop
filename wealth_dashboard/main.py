from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import os
import uuid
from dotenv import load_dotenv
from datetime import datetime
import contextvars

from models import (
    Asset, Liability, Income, Expense, UserOverride, FinancialGoal,
    get_stale_records, SessionLocal as _SessionLocal,
)
from parser import WealthParser
from metrics import MetricsCalculator
from charts import *
from llm_client import LLMClient

load_dotenv()

app = FastAPI(title="Intelligent Wealth Dashboard")


# Module-level variable for test session injection.
# Tests set this before making requests; production code ignores it.
_test_db_session = None


def get_session(db_session=None):
    """Return a database session.

    Production code calls ``get_session()`` with no arguments and gets a
    real connection to the file-based SQLite database.

    Tests call ``get_session(db_session=test_session)`` to route all queries
    into their in-memory fixture instead of the production database.
    """
    if db_session is not None:
        return db_session
    global _test_db_session
    if _test_db_session is not None:
        return _test_db_session
    return _SessionLocal()

# IMPORTANT FIX: Set templates directory correctly
templates = Jinja2Templates(directory="templates")

# Create static directory if it doesn't exist
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

# Create a simple CSS file if it doesn't exist
css_file = static_dir / "style.css"
if not css_file.exists():
    with open(css_file, "w") as f:
        f.write("""
body {
    background-color: #f8f9fa;
}
.card {
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
.card-header {
    background-color: #fff;
    border-bottom: 2px solid #007bff;
    font-weight: bold;
}
.navbar-brand {
    font-size: 1.5rem;
    font-weight: bold;
}
.table-responsive {
    max-height: 400px;
    overflow-y: auto;
}
.btn-primary {
    background-color: #007bff;
    border: none;
}
.btn-primary:hover {
    background-color: #0056b3;
}
#analysisText {
    font-size: 1rem;
    line-height: 1.6;
}
""")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Store session data (in production, use proper session management)
session_data = {}

# Initialize LLM client
llm_client = LLMClient()

@app.get("/", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Main upload page"""
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/upload", response_class=HTMLResponse)
async def upload_redirect(request: Request):
    """Redirect /upload to / (upload page)"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=302)

@app.post("/upload/excel")
async def upload_excel(file: UploadFile = File(...)):
    """Upload and parse Excel file"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Please upload Excel file (.xlsx or .xls)")
    
    # Parse file
    contents = await file.read()
    parser = WealthParser()
    data = parser.parse_excel(contents)
    
    # Store in database
    session_id = str(uuid.uuid4())
    db = get_session()

    try:
        # Clear previous data (simple approach - delete all)
        db.query(Asset).delete()
        db.query(Liability).delete()
        db.query(Income).delete()
        db.query(Expense).delete()

        # Store assets
        for asset in data['assets']:
            db_asset = Asset(**asset)
            db.add(db_asset)

        # Store liabilities
        for liability in data['liabilities']:
            db_liability = Liability(**liability)
            db.add(db_liability)

        # Store income
        for income in data['income_streams']:
            db_income = Income(**income)
            db.add(db_income)

        # Store expenses
        for expense in data['expenses']:
            db_expense = Expense(**expense)
            db.add(db_expense)

        db.commit()

        # Store session mapping
        session_data[session_id] = {
            'asset_count': len(data['assets']),
            'liability_count': len(data['liabilities'])
        }

        return JSONResponse({
            'session_id': session_id,
            'stats': data['stats'],
            'redirect': f'/dashboard/{session_id}'
        })

    except Exception as e:
        db.rollback()
        print(f"Database error: {str(e)}")  # For debugging
        raise HTTPException(500, f"Database error: {str(e)}")
    finally:
        db.close()

@app.get("/dashboard/{session_id}", response_class=HTMLResponse)
async def dashboard(request: Request, session_id: str):
    """Display wealth dashboard"""
    db = get_session()
    
    try:
        # Fetch data from database
        assets = db.query(Asset).all()
        liabilities = db.query(Liability).all()
        income_streams = db.query(Income).all()
        expenses = db.query(Expense).all()
        
        # Convert to dict for metrics
        assets_dict = [{'current_value': a.current_value, 'asset_type': a.asset_type, 
                       'category': a.category, 'name': a.name} for a in assets]
        liabilities_dict = [{'remaining_balance': l.remaining_balance} for l in liabilities]
        income_dict = [{'monthly_amount': i.monthly_amount} for i in income_streams]
        expenses_dict = [{'monthly_amount': e.monthly_amount} for e in expenses]
        
        # Calculate metrics
        calculator = MetricsCalculator(assets_dict, liabilities_dict, income_dict, expenses_dict)
        metrics = calculator.get_all_metrics()
        
        # Generate charts
        wealth_pyramid = create_wealth_pyramid(metrics['asset_allocation'])
        allocation_pie = create_asset_allocation_pie(metrics['category_breakdown'])
        net_worth_gauge = create_net_worth_gauge(metrics['net_worth'])
        cashflow_chart = create_cashflow_chart(metrics['total_income'], metrics['total_expenses'])
        risk_gauge = create_risk_gauge(metrics['risk']['score'])
        
        # Get stale records for the stale badge
        stale_records_list = get_stale_records(db)
        stale_count = len(stale_records_list)

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "session_id": session_id,
            "metrics": metrics,
            "wealth_pyramid": wealth_pyramid,
            "allocation_pie": allocation_pie,
            "net_worth_gauge": net_worth_gauge,
            "cashflow_chart": cashflow_chart,
            "risk_gauge": risk_gauge,
            "assets": assets_dict[:10],
            "liabilities": liabilities_dict,
            "income_streams": income_dict,
            "stale_count": stale_count,
            "stale_records": stale_records_list
        })
        
    except Exception as e:
        print(f"Dashboard error: {str(e)}")  # For debugging
        raise HTTPException(500, f"Dashboard error: {str(e)}")
    finally:
        db.close()

@app.post("/api/analyze")
async def analyze_with_llm(session_id: str, provider: str = "omlx"):
    """Analyze portfolio with selected LLM"""
    print(f"\n[ANALYZE] === START === session_id={session_id}, provider={provider}")
    db = get_session()

    try:
        # Fetch current metrics
        assets = db.query(Asset).all()
        liabilities = db.query(Liability).all()
        income_streams = db.query(Income).all()
        expenses = db.query(Expense).all()

        print(f"[ANALYZE] Records: assets={len(assets)}, liabilities={len(liabilities)}, income={len(income_streams)}, expenses={len(expenses)}")

        assets_dict = [{'current_value': a.current_value, 'asset_type': a.asset_type, 'category': a.category} for a in assets]
        liabilities_dict = [{'remaining_balance': l.remaining_balance} for l in liabilities]
        income_dict = [{'monthly_amount': i.monthly_amount} for i in income_streams]
        expenses_dict = [{'monthly_amount': e.monthly_amount} for e in expenses]

        calculator = MetricsCalculator(assets_dict, liabilities_dict, income_dict, expenses_dict)
        metrics = calculator.get_all_metrics()

        print(f"[ANALYZE] Metrics: net_worth={metrics.get('net_worth')}, cashflow={metrics.get('monthly_cashflow')}, risk={metrics.get('risk', {}).get('level')}")

        # Get LLM analysis
        print(f"[ANALYZE] Calling llm_client.analyze_portfolio(provider={provider})...")
        analysis = llm_client.analyze_portfolio(metrics, provider)
        print(f"[ANALYZE] Analysis returned (length={len(analysis)} chars)")

        return JSONResponse({
            'analysis': analysis,
            'provider': provider,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[ANALYZE] CRITICAL ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Analysis error: {str(e)}")
    finally:
        db.close()

@app.post("/api/ask")
async def ask_followup(question: str, session_id: str, provider: str = "omlx"):
    """Ask follow-up question"""
    db = get_session()

    try:
        # Get current metrics as context
        assets = db.query(Asset).all()
        liabilities = db.query(Liability).all()

        context = {
            'total_assets': sum(a.current_value for a in assets),
            'total_liabilities': sum(l.remaining_balance for l in liabilities),
            'net_worth': sum(a.current_value for a in assets) - sum(l.remaining_balance for l in liabilities)
        }

        answer = llm_client.ask_followup(question, context, provider)

        return JSONResponse({'answer': answer})

    except Exception as e:
        print(f"Question error: {str(e)}")
        raise HTTPException(500, f"Question error: {str(e)}")
    finally:
        db.close()

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page"""
    return templates.TemplateResponse("settings.html", {"request": request})

@app.get("/test-ollama")
async def test_ollama():
    """Test Ollama connection"""
    import requests
    ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    
    try:
        # Test connection
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        return {
            "status": "connected",
            "url": ollama_url,
            "ollama_response": response.json() if response.status_code == 200 else None,
            "status_code": response.status_code
        }
    except Exception as e:
        return {
            "status": "error",
            "url": ollama_url,
            "error": str(e)
        }

@app.get("/debug-data")
async def debug_data():
    """Debug endpoint to see what data is in the database"""
    db = get_session()
    try:
        assets = db.query(Asset).all()
        liabilities = db.query(Liability).all()
        income_streams = db.query(Income).all()
        expenses = db.query(Expense).all()
        
        return {
            "asset_count": len(assets),
            "assets": [{"name": a.name, "category": a.category, "asset_type": a.asset_type, 
                       "current_value": a.current_value, "purchase_price": a.purchase_price} 
                      for a in assets[:5]],
            "liability_count": len(liabilities),
            "income_count": len(income_streams),
            "expense_count": len(expenses)
        }
    finally:
        db.close()

@app.get("/debug-upload")
async def debug_upload():
    """Test uploading without saving to DB"""
    return templates.TemplateResponse("debug_upload.html", {"request": request})


# =============================================================================
# Task Group 7: API endpoints
# =============================================================================

@app.get("/api/stale-records")
async def api_stale_records():
    """Return all stale assets and liabilities as JSON.

    A record is stale when valuation_date is None or older than 90 days.

    Returns a list of dicts with keys:
        name, type, days_stale, last_value, edit_url
    """
    db = get_session()
    try:
        stale_records_list = get_stale_records(db)
        return JSONResponse({'stale_records': stale_records_list})
    finally:
        db.close()


@app.get("/api/goals/progress")
async def api_goals_progress():
    """Return all financial goals with their progress percentages.

    Each goal includes:
        id, name, target_amount, target_date, currency,
        progress_percentage, effective_currency
    """
    db = get_session()
    try:
        goals = db.query(FinancialGoal).all()
        goals_data = []
        for goal in goals:
            goals_data.append({
                'id': goal.id,
                'name': goal.name,
                'target_amount': goal.target_amount,
                'target_date': goal.target_date.isoformat() if goal.target_date else None,
                'currency': goal.currency,
                'current_value': goal.current_value,
                'progress_percentage': goal.progress_percentage,
                'effective_currency': goal.effective_currency,
                'description': goal.description,
                'notes': goal.notes,
            })
        return JSONResponse({'goals': goals_data})
    finally:
        db.close()




#Main method
if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("Intelligent Wealth Dashboard Starting...")
    print("Open http://127.0.0.1:9000 in your browser")
    print("=" * 50)
    uvicorn.run(app, host="127.0.0.1", port=9000)