# routers/user_router.py
from fastapi import APIRouter, Header, Query
from domain.schemas.user_schema import UserCreate, UserLogin, UserNewPassword, UserUpdate, UserOut
from core.response import JsonResponse
from infrastructure.repositories.user_repository import UserRepository
from core.exceptions import AppException

user_router = APIRouter(prefix="/users", tags=["Users"])
user_repo = UserRepository()


@user_router.get("/", response_model=JsonResponse)
def list_users(limit: int = Query(20, le=60), token: str | None = None):
    """List Cognito users with pagination"""
    users = user_repo.get_all(limit=limit, pagination_token=token)
    return JsonResponse( message="Users retrieved successfully", data=users)


@user_router.get("/{username}", response_model=JsonResponse)
def get_user(username: str):
    """Get a single user by username"""
    user = user_repo.get_by_username(username)
    return JsonResponse( message="User retrieved successfully", data=user)


@user_router.post("/create", response_model=JsonResponse)
def create_user(user: UserCreate):
    """Create a new Cognito user"""
    created_user = user_repo.signup(user)
    
    return JsonResponse( message="User created successfully", data=created_user)


@user_router.put("/update/{username}", response_model=JsonResponse)
def update_user(username: str, user: UserUpdate):
    """Update Cognito user attributes"""
    updated_user = user_repo.update(username, user)
    return JsonResponse( message="User updated successfully", data=updated_user)


@user_router.delete("/delete/{username}", response_model=JsonResponse)
def delete_user(username: str):
    """Delete a Cognito user"""
    result = user_repo.delete(username)
    return JsonResponse( message="User deleted successfully", data=result)

@user_router.post("/confirm")
def confirm_email(email: str, code: str):
    result = user_repo.confirm_email(email, code)
    return JsonResponse(message=result["message"], data=result)

@user_router.post("/login")
def login(user: UserLogin):
    result = user_repo.login(user.email, user.password)
    return JsonResponse(message=result.get("message", "Login successful"), data=result)




@user_router.post("/logout")
def logout(Authorization: str = Header(...)):
    token = Authorization.replace("Bearer ", "")
    result = user_repo.logout(token)
    return JsonResponse(message=result["message"])

