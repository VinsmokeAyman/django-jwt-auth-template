from rest_framework.decorators import (
    api_view,
    permission_classes,
    throttle_classes,
) 
from rest_framework.permissions import IsAdminUser, AllowAny
from .permissions import IsTier1, IsCompanyAdmin

from .throttles import LoginRateThrottle

from rest_framework.response import Response
from .models import *

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .serializers import *

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


@api_view(["GET"])
def test_api(request):
    return Response({
        "message": "Django API is working!"
    })

@api_view(["POST"])
@permission_classes([IsCompanyAdmin])
def create_user(request):
    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")
    phone_number = request.data.get("phone_number")
    fullName = request.data.get("fullName")


    if not username or not email or not password or not fullName or not phone_number :
        return Response({"error": "Missing required fields."}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists."}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already exists."}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password, phone=phone_number, fullName=fullName)
    user.save()

    return Response({"message": "User created successfully."}, status=201)



def is_email(value):
    try:
        validate_email(value)
        return True
    except ValidationError:
        return False


    
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def verify_user(request):
    username = request.data.get("username")
    password = request.data.get("password")
    remember_me = request.data.get("rememberMe", False)

    if not username or not password:
        return Response(
            {"error": "Missing required fields."},
            status=400
        )

    # Find user by email or username
    try:
        if is_email(username):
            user = User.objects.get(email=username)
        else:
            user = User.objects.get(username=username)

    except User.DoesNotExist:
        return Response(
            {"error": "Invalid username or password."},
            status=401
        )

    # Check password
    if not user.check_password(password):
        return Response(
            {"error": "Invalid username or password."},
            status=401
        )

    # Generate tokens
    refresh = RefreshToken.for_user(user)
    refresh["remember_me"] = remember_me

    response = Response({
        "message": "Login successful",
        "access": str(refresh.access_token),
        "user": UserSerializer(user).data,
    })

    # Refresh token
    cookie_options = {
        "key": "refresh_token",
        "value": str(refresh),
        "httponly": True,
        "secure": False,   # True in production
        "samesite": "Lax",
        "path": "/",
    }

    # ONLY persistent when Remember Me is checked
    if remember_me:
        cookie_options["max_age"] = 7 * 24 * 60 * 60

    response.set_cookie(**cookie_options)

    return response

    
@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token(request):

    old_refresh_token = request.COOKIES.get("refresh_token")

    if not old_refresh_token:
        return Response(
            {"error": "Refresh token missing."},
            status=401
        )

    try:
        old_refresh = RefreshToken(old_refresh_token)

        user_id = old_refresh["user_id"]
        remember_me = old_refresh.get("remember_me", False)

        user = User.objects.get(id=user_id)

        # Create NEW refresh
        new_refresh = RefreshToken.for_user(user)
        new_refresh["remember_me"] = remember_me

        # Create new access
        new_access = new_refresh.access_token

        # OLD REFRESH CAN NEVER BE USED AGAIN
        old_refresh.blacklist()

        response = Response({
            "access": str(new_access)
        })

        cookie_options = {
            "key": "refresh_token",
            "value": str(new_refresh),
            "httponly": True,
            "secure": False,
            "samesite": "Lax",
            "path": "/",
        }

        if remember_me:
            cookie_options["max_age"] = 7 * 24 * 60 * 60

        response.set_cookie(**cookie_options)

        return response

    except (TokenError, User.DoesNotExist):
        return Response(
            {"error": "Invalid or expired refresh token."},
            status=401
        )


@api_view(["POST"])
@permission_classes([IsCompanyAdmin])
def verify_user_admin(request):
    return Response({"message": "Admin user verified successfully.",
                     "user": UserSerializer(request.user).data}, status=200)



@api_view(["POST"])
@permission_classes([AllowAny])
def logout_user(request):
    refresh_token = request.COOKIES.get("refresh_token")

    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass

    response = Response({
        "message": "Logout successful"
    })

    response.delete_cookie(
        key="refresh_token",
        path="/",
        samesite="Lax",
    )

    return response