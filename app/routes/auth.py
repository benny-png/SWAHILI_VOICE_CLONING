# app/main.py
from fastapi import  Form, Depends, APIRouter,BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.services.user_service import UserService
from app.services.user_text_service import UserTextService
from app.models.schemas import (
    ResetPassword,
    UserCreate,
    UserLogin,
    LoginResponse,
    UserInDB,
    EmailStr
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

async def get_user_service():
    return UserService()

#authentication endpoints

# Registration endpoint
@router.post("/register/", response_model=UserInDB)
async def register_user(user: UserCreate, service: UserService = Depends(get_user_service)):
    return await service.create_user(user)

# Login endpoint
@router.post("/login/", response_model=LoginResponse)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), service: UserService = Depends(get_user_service)):
    user_login = UserLogin(username=form_data.username, password=form_data.password)  # username field is email
    return await service.login(user_login)

@router.post("/forgot_password")
async def forgot_password(email:EmailStr,background_tasks:BackgroundTasks,service: UserService = Depends(get_user_service)):
    return await service.send_reset_email(email,background_tasks)


@router.get("/request/reset-password", response_class=HTMLResponse,include_in_schema=False)
async def reset_password_page(token: str):
    # Serve HTML that contains form for new password + confirm
    return """
   <html>
   <head>
   <style>
                body {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #1a1a2e, #16213e);
                    font-family: 'Arial', sans-serif;
                    color: #e0e0e0;
                }
                #reset-form {
                    background: rgba(255, 255, 255, 0.05);
                    backdrop-filter: blur(10px);
                    padding: 2rem;
                    border-radius: 15px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
                    width: 100%;
                    max-width: 400px;
                    transition: transform 0.3s ease;
                }
                #reset-form:hover {
                    transform: translateY(-5px);
                }
                input[type="password"] {
                    width: 100%;
                    padding: 12px;
                    margin: 10px 0;
                    border: none;
                    border-radius: 8px;
                    background: rgba(255, 255, 255, 0.1);
                    color: #fff;
                    font-size: 16px;
                    transition: box-shadow 0.3s ease;
                }
                input[type="password"]::placeholder {
                    color: #aaa;
                }
                input[type="password"]:focus {
                    outline: none;
                    box-shadow: 0 0 10px rgba(138, 43, 226, 0.5);
                }
                button {
                    width: 100%;
                    padding: 12px;
                    border: none;
                    border-radius: 8px;
                    background: linear-gradient(45deg, #8b2be2, #ff69b4);
                    color: #fff;
                    font-size: 18px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: background 0.3s ease, transform 0.2s ease;
                }
                button:hover {
                    background: linear-gradient(45deg, #9b3cf3, #ff85c1);
                    transform: scale(1.05);
                }
                button:active {
                    transform: scale(0.95);
                }
                @media (max-width: 500px) {
                    #reset-form {
                        padding: 1.5rem;
                        max-width: 90%;
                    }
                }
            </style>
   </head>
        <body>
            <form id="reset-form" onsubmit="submitForm(event)">
                <input type="hidden" name="token" value="{token}">
                <input type="password" name="password" placeholder="New Password" required>
                <input type="password" name="confirm_password" placeholder="Confirm Password" required>
                <button type="submit">Reset Password</button>
            </form>
            <script>
                async function submitForm(event) {
    event.preventDefault();
    const form = event.target;
    const data = {
        token: form.token.value,
        password: form.password.value,
        confirm_password: form.confirm_password.value
    };

    // Check if passwords match
    if (data.password !== data.confirm_password) {
        alert('Passwords do not match');
        return;
    }

    try {
        const response = await fetch('/auth/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (response.ok) {
            alert('Password reset successfully');
            window.location.href = 'https://swahilivoicetz.netlify.app/login';
        } else {
            alert('Error resetting password');
        }
    } catch (error) {
        alert('Network error');
    }
}
            </script>
        </body>
    </html>
    """.replace("{token}", token)


@router.post("/reset-password",include_in_schema=False)
async def reset_password(data:ResetPassword,service: UserService = Depends(get_user_service)):
    return await service.reset_password(data)

