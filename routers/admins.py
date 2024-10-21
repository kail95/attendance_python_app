from datetime import datetime
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from utils.jwt import oauth, create_jwt_token
from database import get_db
from crud.login_admins_crud import get_admin_by_email, create_admin
from crud.view_data_crud import get_classes_by_department, get_table_data
from schemas.auth_schemas import AdminCreate
from config import settings
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login")
async def login(request: Request):
    # Step 1: Redirect to Google's OAuth 2.0 login page
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_OAUTH_CONFIG["redirect_uri"])

@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = await oauth.google.parse_id_token(request, token)
        email = user_info['email']
        
        # You can now store user info in the session
        request.session['user'] = user_info  # Save the user in the session
        
        # Optionally create a JWT token
        jwt_token = create_jwt_token({"sub": email})  # Create JWT token with email
        return RedirectResponse(url="/admin/dashboard")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(status_code=500, content={"message": "Authentication failed"})



@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    classes = db.execute(text("SELECT * FROM meta_class_data WHERE dep_name = 99")).fetchall()

    if classes:
        first_class_table = classes[0][2]  # Accessing the third element in the tuple (class_table_name)
        first_class_records = db.execute(
            text(f"SELECT reg_number, student_name, present_days, absent_days FROM {first_class_table}")
        ).fetchall()
        first_class_label = classes[0][1]  # Accessing the second element in the tuple (class_label)
    else:
        first_class_table = None
        first_class_records = []
        first_class_label = "No classes available"

    return templates.TemplateResponse("admin/admin_dashboard.html", {
        "request": request,
        "classes": classes,
        "students": first_class_records,
        "active_class_label": first_class_label
    })

@router.get("/view_table/{table_name}", response_class=HTMLResponse)
async def view_table(table_name: str, request: Request, db: Session = Depends(get_db)):
    class_info = db.execute(text("SELECT class_label FROM meta_class_data WHERE class_table_name = :table_name"),
                            {"table_name": table_name}).fetchone()

    students = db.execute(
        text(f"SELECT reg_number, student_name, present_days, absent_days FROM {table_name}")
    ).fetchall()

    return templates.TemplateResponse(
        "admin/partial_table.html",
        {"request": request, "students": students, "active_class_label": class_info[0] if class_info else "Unknown Class"}
    )
