from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from utils.jwt import oauth, create_jwt_token
from database import get_db
from crud.login_admins_crud import get_admin_by_email, create_admin
from schemas.auth_schemas import AdminCreate

from fastapi import APIRouter, Request
from utils.jwt import oauth
from config import settings
from fastapi.responses import RedirectResponse, JSONResponse

router = APIRouter()

@router.get("/login")
async def login(request: Request):
    # Use renamed redirect URI from config
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)

@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = await oauth.google.parse_id_token(request, token)
        email = user_info['email']

        # Further checks and logic here (e.g., checking email in your database)

        return RedirectResponse(url="/admin/dashboard")

    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(status_code=500, content={"message": "Authentication failed"})


@router.post("/create_admin/")
async def create_admin(admin: AdminCreate, db: Session = Depends(get_db)):
    existing_admin = get_admin_by_email(db, admin.email)

    if existing_admin:
        return {"error": "Admin with this email already exists."}

    created_admin = create_admin(db, admin)
    return {"message": f"Admin {created_admin.email} created successfully."}
