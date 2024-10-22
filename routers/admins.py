from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from utils.jwt import oauth, create_jwt_token, get_current_user
from database import get_db
from crud.login_admins_crud import get_admin_by_email, create_admin
from crud.view_data_crud import get_classes_by_department, get_table_data
from schemas.auth_schemas import AdminCreate
from config import settings
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from utils.rand import generate_random_string
from models.models import Admin

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Login endpoint (sign into admin google accounts)
@router.get("/")
async def login(request: Request):
    state = generate_random_string()  # Generate a random state string
    request.session["state"] = state
    return await oauth.google.authorize_redirect(request, "https://9992-192-248-41-45.ngrok-free.app/admin/callback", state=state)

# validate emails & redirect to correct department dashboard
@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    try:
        # Exchange authorization code for access token
        token = await oauth.google.authorize_access_token(request)
        # Directly access the 'userinfo' from the token
        if 'userinfo' in token:
            user_info = token['userinfo']
        else:
            # Fallback if userinfo isn't directly available
            user_info = await oauth.google.userinfo(token=token)

        email = user_info['email']
        # Query the admins table to check if the user is an admin
        admin = db.query(Admin).filter(Admin.email == email).first()
        if not admin:
            raise HTTPException(status_code=403, detail="Unauthorized: Admin access required")

        # Generate JWT token with email and department information
        jwt_token = create_jwt_token({
            "adm_email": email,
            "department": admin.dep_name,  # Using 'dep_name' from the admins table
            "is_super_admin": admin.is_super_admin  # Store super admin status in the token
        })
        
        # Store the JWT token in the session or send it in a cookie/header
        request.session['jwt_token'] = jwt_token

        return RedirectResponse(url="/admin/dashboard")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        # Render a custom HTML error page
        return HTMLResponse(content=f"""
        <html>
            <head><title>Authentication Error</title></head>
            <body>
                <h1>Authentication Failed</h1>
                <p>We're sorry, but there was an error during the authentication process.</p>
                <a href="/">Go back to home</a>
            </body>
        </html>
        """, status_code=500)

# Admin dashboard 
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)  # Extract current user from JWT
):
    # Extract department from the current user (JWT)
    user_department = current_user.get("department")

    # Ensure department is provided
    if not user_department:
        raise HTTPException(status_code=403, detail="Unauthorized: Department not found")

    # Fetch classes based on the department
    if user_department == 99:  # Load all tables if department is 99 (super admin)
        classes = db.execute(text("SELECT * FROM meta_class_data")).fetchall()
    else:  # Load tables for the specific department
        classes = db.execute(
            text("SELECT * FROM meta_class_data WHERE dep_name = :dep_name"),
            {"dep_name": user_department}
        ).fetchall()

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


@router.get("/logout")
async def logout(request: Request):
    # Clear the JWT token from the session
    request.session.pop("jwt_token", None)

    # Redirect to login page after logout
    return RedirectResponse(url="/")