from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from utils.jwt import oauth, get_current_user
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
# @router.get("/")
# async def login(request: Request):
#     state = generate_random_string()  # Generate a random state string
#     request.session["state"] = state
#     return await oauth.google.authorize_redirect(request, "https://9992-192-248-41-45.ngrok-free.app/admin/callback", state=state)

# validate emails & redirect to correct department dashboard
# @router.get("/callback")
# async def callback(request: Request, db: Session = Depends(get_db)):
#     try:
#         # Exchange authorization code for access token
#         token = await oauth.google.authorize_access_token(request)
#         # Directly access the 'userinfo' from the token
#         if 'userinfo' in token:
#             user_info = token['userinfo']
#         else:
#             # Fallback if userinfo isn't directly available
#             user_info = await oauth.google.userinfo(token=token)

#         email = user_info['email']
#         # Query the admins table to check if the user is an admin
#         admin = db.query(Admin).filter(Admin.email == email).first()
#         if not admin:
#             raise HTTPException(status_code=403, detail="Unauthorized: Admin access required")

#         # Generate JWT token with email and department information
#         jwt_token = create_jwt_token({
#             "adm_email": email,
#             "department": admin.dep_name,  # Using 'dep_name' from the admins table
#             "is_super_admin": admin.is_super_admin  # Store super admin status in the token
#         })
        
#         # Store the JWT token in the session or send it in a cookie/header
#         request.session['jwt_token'] = jwt_token

#         return RedirectResponse(url="/admin/dashboard")
    
#     except Exception as e:
#         print(f"Error: {str(e)}")
#         # Render a custom HTML error page
#         return HTMLResponse(content=f"""
#         <html>
#             <head><title>Authentication Error</title></head>
#             <body>
#                 <h1>Authentication Failed</h1>
#                 <p>We're sorry, but there was an error during the authentication process.</p>
#                 <a href="/">Go back to home</a>
#             </body>
#         </html>
#         """, status_code=500)

# Admin dashboard 
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)  # Extract current user from JWT
):
    # check whether user is an admin
    if current_user['user_type'] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
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

    return templates.TemplateResponse("admin/admin_attendance.html", {
        "request": request,
        "classes": classes,
        "students": first_class_records,
        "active_class_label": first_class_label,
        "current_user": current_user
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


@router.get("/search", response_class=HTMLResponse)
async def admin_search_view(request: Request, current_user: dict = Depends(get_current_user)):
    # Ensure the user is an admin
    if current_user['user_type'] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Render the search form page
    return templates.TemplateResponse("admin/admin_search_student.html", {
        "request": request,
        "current_user": current_user
    })


@router.post("/search_student", response_class=HTMLResponse)
async def search_student(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    form_data = await request.form()
    reg_number = form_data.get("reg_number").lower()  # Get the registration number

    # Ensure the user is an admin
    if current_user['user_type'] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    department = current_user['department']

    # Step 1: Get the class IDs from the student_class_mapping table
    class_mappings = db.execute(
        text("SELECT class_id FROM student_class_mapping WHERE LOWER(reg_number) = :reg_number"),
        {"reg_number": reg_number}
    ).fetchall()

    if not class_mappings:
        return HTMLResponse(content="<h3>No classes found for the student</h3>", status_code=200)

    class_ids = [class_id[0] for class_id in class_mappings]  # Extract class IDs

    # Step 2: Get the class_table_names from the meta_class_data table, filtering by department
    query = """
        SELECT class_table_name, class_label 
        FROM meta_class_data 
        WHERE class_id IN :class_ids
    """
    
    if department != "99":
        query += " AND dep_name = :department"

    class_data = db.execute(text(query), {"class_ids": tuple(class_ids), "department": department}).fetchall()

    if not class_data:
        return HTMLResponse(content="<h3>No class tables found for this department</h3>", status_code=200)

    # Step 3: Query each class table to get attendance records for the student
    all_records = []
    for class_info in class_data:
        class_table_name = class_info.class_table_name
        class_label = class_info.class_label  # This is the class name
        
        # Query attendance records from each class table for the current student
        records = db.execute(
            text(f"SELECT *, :class_label AS class_name FROM {class_table_name} WHERE LOWER(reg_number) = :reg_number"),
            {"reg_number": reg_number, "class_label": class_label}
        ).fetchall()

        all_records.extend(records)  # Add the records from each table with class name included

    if not all_records:
        return HTMLResponse(content="<h3>No attendance records found for the student</h3>", status_code=200)

    # Step 4: Render the results in a table and return the HTML response
    return templates.TemplateResponse("admin/partials_students_search.html", {
        "request": request,
        "records": all_records
    })


@router.get("/manage-admins", response_class=HTMLResponse)
async def manage_admins(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Ensure only super admins can access this page
    if not current_user['is_super_admin']:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get the current user's department
    department = current_user['department']

    # Query only admins from the current super admin's department
    admins = db.execute(
        text("SELECT * FROM admins WHERE dep_name = :department"),
        {"department": department}
    ).fetchall()

    # Render the Manage Admins page
    return templates.TemplateResponse("admin/admin_manage_admins.html", {
        "request": request,
        "admins": admins,
        "current_user": current_user
    })


@router.delete("/delete_admin/{admin_id}", response_class=HTMLResponse)
async def delete_admin(admin_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Ensure the current user is a super admin
    if not current_user['is_super_admin']:
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch the admin to be deleted
    admin_to_delete = db.execute(
        text("SELECT * FROM admins WHERE id = :admin_id"),
        {"admin_id": admin_id}
    ).fetchone()

    # Ensure the admin exists
    if not admin_to_delete:
        return HTMLResponse(content="<div class='alert alert-danger'>Admin not found.</div>", status_code=404)

    # Prevent deleting super admins
    if admin_to_delete.is_super_admin:
        return HTMLResponse(content="<div class='alert alert-danger'>Cannot delete a super admin.</div>", status_code=400)

    # Delete the admin
    db.execute(text("DELETE FROM admins WHERE id = :admin_id"), {"admin_id": admin_id})
    db.commit()

    # Return success message
    return HTMLResponse(content="<div class='alert alert-success'>Admin deleted successfully.</div>", status_code=200)


@router.post("/add_admin", response_class=HTMLResponse)
async def add_admin(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Ensure the user is a super admin
    if not current_user['is_super_admin']:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get form data
    form_data = await request.form()
    email = form_data.get("email")

    # Ensure email is provided
    if not email:
        return HTMLResponse(content="<div class='alert alert-danger'>Email is required.</div>", status_code=400)

    # Use the department of the current user (super admin's department)
    dep_name = current_user['department']

    # Insert the new admin into the database (is_super_admin = 0 by default)
    db.execute(
        text("INSERT INTO admins (email, dep_name, is_super_admin, created_at) VALUES (:email, :dep_name, 0, NOW())"),
        {"email": email, "dep_name": dep_name}
    )
    db.commit()

    # Return success message
    return HTMLResponse(content="<div class='alert alert-success'>Admin added successfully.</div>", status_code=200)
