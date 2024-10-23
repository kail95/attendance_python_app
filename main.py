from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from database import engine, Base
from routers import add_attendance, students, cleanup, admins
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from config import settings
from utils.rand import generate_random_string
from utils.jwt import oauth, create_jwt_token
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.models import Admin
from database import get_db
from utils.regno import generate_registration_number

# Initialize FastAPI
app = FastAPI(debug=True)

# Add the session middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY, session_cookie="session",  # Name of the session cookie           
)

# Create the database tables if they don't already exist
Base.metadata.create_all(bind=engine)

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include the routers
app.include_router(add_attendance.router, prefix="/input", tags=["Input"])
app.include_router(students.router, prefix="", tags=["Student"])
# app.include_router(cleanup.router)
app.include_router(admins.router, prefix="/admin", tags=["Admin"])


@app.get("/")
async def login(request: Request):
    state = generate_random_string()  # Generate a random state string
    request.session["state"] = state
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI, state=state)


@app.get("/callback")
async def unified_callback(request: Request, db: Session = Depends(get_db)):
    try:
        # Exchange authorization code for access token
        token = await oauth.google.authorize_access_token(request)

        # Directly access the 'userinfo' from the token
        if 'userinfo' in token:
            user_info = token['userinfo']
        else:
            # Fallback if userinfo isn't directly available
            user_info = await oauth.google.userinfo(token=token)

        email = user_info['email'].lower()  # Ensure case-insensitivity

        # Check if the user is an admin
        admin = db.query(Admin).filter(Admin.email == email).first()

        if admin:
            # Admin login flow
            jwt_token = create_jwt_token({
                "adm_email": email,
                "department": admin.dep_name,  # Admin-specific department information
                "is_super_admin": admin.is_super_admin,  # Super admin status
                "user_type": "admin"  # Specify user type
            })

            # Store the JWT token in the session
            request.session['jwt_token'] = jwt_token

            # Redirect to the admin dashboard
            return RedirectResponse(url="/admin/dashboard")
        
        else:
            # Student login flow
            reg_number = generate_registration_number(email)

            # Generate JWT token for student
            jwt_token = create_jwt_token({
                "email": email,
                "reg_number": reg_number,
                "user_type": "student"  # Specify user type
            })

            # Store the JWT token in the session
            request.session['jwt_token'] = jwt_token

            # Redirect to the student dashboard
            return RedirectResponse(url="/dashboard")

    except Exception as e:
        print(f"Error: {str(e)}")
        # Render a custom HTML error page in case of an exception
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

