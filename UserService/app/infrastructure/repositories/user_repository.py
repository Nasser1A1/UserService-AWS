import boto3
from botocore.exceptions import ClientError
from decouple import config
from datetime import datetime
import hmac
import hashlib
import base64
from core.exceptions import AppException
from domain.schemas.user_schema import UserCreate, UserUpdate, UserOut
from core.dependancies import get_logger


class UserRepository:
    def __init__(self):
        self.client = boto3.client(
            "cognito-idp",
            region_name=config("AWS_REGION"),
            aws_access_key_id=config("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=config("AWS_SECRET_ACCESS_KEY")
        )
        self.user_pool_id = config("COGNITO_USER_POOL_ID")
        self.client_id = config("COGNITO_CLIENT_ID")
        self.client_secret = config("COGNITO_CLIENT_SECRET", default=None)
        self.logger = get_logger()

    # =====================================
    # Helper: Calculate SECRET_HASH
    # =====================================
    def _get_secret_hash(self, username: str) -> str:
        """Calculate SECRET_HASH for Cognito authentication"""
        if not self.client_secret:
            return None
            
        message = bytes(username + self.client_id, 'utf-8')
        secret = bytes(self.client_secret, 'utf-8')
        dig = hmac.new(secret, message, hashlib.sha256).digest()
        return base64.b64encode(dig).decode()

    # =====================================
    # Helper: Centralized Cognito error handler
    # =====================================
    def _handle_cognito_error(self, error: ClientError, context: str = ""):
        code = error.response["Error"]["Code"]
        message = error.response["Error"]["Message"]

        self.logger.error(f"Cognito error in {context} [{code}]: {message}")
        self.logger.error(f"Full error response: {error.response}")

        match code:
            case "UsernameExistsException":
                raise AppException("User account already exists", 409)
            case "UserNotFoundException":
                raise AppException("User not found", 404)
            case "UserNotConfirmedException":
                raise AppException("Please verify your email before logging in. Check your inbox for the confirmation code.", 403)
            case "NotAuthorizedException":
                raise AppException(f"Authentication failed: {message}", 401)
            case "InvalidParameterException":
                raise AppException(f"Invalid parameter: {message}", 400)
            case "CodeMismatchException":
                raise AppException("Invalid verification code. Please try again.", 400)
            case "ExpiredCodeException":
                raise AppException("Verification code has expired. Please request a new one.", 400)
            case "TooManyFailedAttemptsException":
                raise AppException("Too many failed attempts, please try again later", 429)
            case "TooManyRequestsException":
                raise AppException("Too many requests, please slow down", 429)
            case "LimitExceededException":
                raise AppException("Attempt limit exceeded, please try after some time", 429)
            case "ResourceNotFoundException":
                raise AppException("User pool or app client not found. Check your configuration.", 404)
            case _:
                raise AppException(f"Cognito error [{code}]: {message}", 500)

    # =====================================
    # Helper: Convert Cognito user → UserOut
    # =====================================
    def _map_user(self, user: dict) -> UserOut:
        attrs = {attr["Name"]: attr["Value"] for attr in user.get("Attributes", [])}

        # Use the 'name' attribute or email as username, not the UUID
        # Priority: custom name > preferred_username > email
        username = (
            attrs.get("name") or 
            attrs.get("preferred_username") or 
            attrs.get("email", "").split("@")[0] or
            user.get("Username", "")
        )

        return UserOut(
            email=attrs.get("email", ""),
            username=username,
            phone_number=attrs.get("phone_number", ""),
            profile_image_url=attrs.get("custom:profile_image_url", ""),
            is_active=user.get("Enabled", True),
            email_verified=attrs.get("email_verified", "false").lower() == "true",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    # =====================================
    # ✅ Signup with Email Confirmation
    # =====================================
    def signup(self, user_data: UserCreate):
        try:
            self.logger.info(f"Signing up user: {user_data.email}")
            
            # Prepare user attributes
            user_attributes = [
                {"Name": "email", "Value": user_data.email},
            ]
            
            # Add name/username as 'name' attribute (this will be used for display)
            if user_data.username:
                user_attributes.append({"Name": "name", "Value": user_data.username})
            else:
                # If no username provided, use email username part
                user_attributes.append({"Name": "name", "Value": user_data.email.split("@")[0]})
            
            if user_data.phone_number:
                user_attributes.append({"Name": "phone_number", "Value": user_data.phone_number})
            if user_data.profile_image_url:
                user_attributes.append({"Name": "custom:profile_image_url", "Value": user_data.profile_image_url})

            # Build sign up parameters
            signup_params = {
                "ClientId": self.client_id,
                "Username": user_data.email,
                "Password": user_data.password,
                "UserAttributes": user_attributes
            }
            
            # Add SECRET_HASH if client secret exists
            if self.client_secret:
                secret_hash = self._get_secret_hash(user_data.email)
                signup_params["SecretHash"] = secret_hash
                self.logger.info("SECRET_HASH added to signup parameters")

            # Sign up the user (this will send confirmation email automatically)
            response = self.client.sign_up(**signup_params)
            
            self.logger.info(f"✅ User signed up successfully: {user_data.email}")
            self.logger.info(f"User confirmation status: {response.get('UserConfirmed')}")
            self.logger.info(f"Code delivery details: {response.get('CodeDeliveryDetails')}")
            
            return {
                "message": "User registered successfully. Please check your email for the verification code.",
                "email": user_data.email,
                "username": user_data.username or user_data.email.split("@")[0],
                "user_confirmed": response.get("UserConfirmed", False),
                "code_delivery_medium": response.get("CodeDeliveryDetails", {}).get("DeliveryMedium"),
                "code_delivery_destination": response.get("CodeDeliveryDetails", {}).get("Destination")
            }

        except ClientError as e:
            self._handle_cognito_error(e, "signup")

    # =====================================
    # ✅ Confirm Email with Code
    # =====================================
    def confirm_email(self, email: str, code: str):
        try:
            self.logger.info(f"Confirming email for: {email}")
            
            # Build confirmation parameters
            confirm_params = {
                "ClientId": self.client_id,
                "Username": email,
                "ConfirmationCode": code
            }
            
            # Add SECRET_HASH if client secret exists
            if self.client_secret:
                secret_hash = self._get_secret_hash(email)
                confirm_params["SecretHash"] = secret_hash
            
            self.client.confirm_sign_up(**confirm_params)
            
            self.logger.info(f"✅ Email confirmed successfully for: {email}")
            return {"message": "Email confirmed successfully. You can now login."}
            
        except ClientError as e:
            self._handle_cognito_error(e, "confirm_email")

    # =====================================
    # ✅ Resend Confirmation Code
    # =====================================
    def resend_confirmation_code(self, email: str):
        try:
            self.logger.info(f"Resending confirmation code to: {email}")
            
            # Build resend parameters
            resend_params = {
                "ClientId": self.client_id,
                "Username": email
            }
            
            # Add SECRET_HASH if client secret exists
            if self.client_secret:
                secret_hash = self._get_secret_hash(email)
                resend_params["SecretHash"] = secret_hash
            
            response = self.client.resend_confirmation_code(**resend_params)
            
            self.logger.info(f"✅ Confirmation code resent to: {email}")
            return {
                "message": "Verification code has been resent to your email.",
                "code_delivery_medium": response.get("CodeDeliveryDetails", {}).get("DeliveryMedium"),
                "code_delivery_destination": response.get("CodeDeliveryDetails", {}).get("Destination")
            }
            
        except ClientError as e:
            self._handle_cognito_error(e, "resend_confirmation_code")

    # =====================================
    # ✅ Login (Blocks Unconfirmed Users)
    # =====================================
    def login(self, username: str, password: str):
        try:
            self.logger.info(f"=== LOGIN ATTEMPT ===")
            self.logger.info(f"Username: {username}")
            
            # Build auth parameters
            auth_params = {
                "USERNAME": username,
                "PASSWORD": password
            }
            
            # Add SECRET_HASH if client secret exists
            if self.client_secret:
                secret_hash = self._get_secret_hash(username)
                auth_params["SECRET_HASH"] = secret_hash
                self.logger.info("SECRET_HASH added to auth parameters")

            # Attempt authentication
            self.logger.info("Attempting admin_initiate_auth...")
            
            response = self.client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow="ADMIN_NO_SRP_AUTH",
                AuthParameters=auth_params
            )

            # Successful authentication
            tokens = response["AuthenticationResult"]
            self.logger.info(f"✅ Login successful for user: {username}")
            
            return {
                "status": "SUCCESS",
                "access_token": tokens["AccessToken"],
                "refresh_token": tokens["RefreshToken"],
                "id_token": tokens["IdToken"],
                "token_type": tokens["TokenType"],
                "expires_in": tokens["ExpiresIn"]
            }

        except ClientError as e:
            # UserNotConfirmedException will be caught and handled by _handle_cognito_error
            self.logger.error(f"❌ Login failed for {username}")
            self.logger.error(f"Error code: {e.response['Error']['Code']}")
            self.logger.error(f"Error message: {e.response['Error']['Message']}")
            self._handle_cognito_error(e, "login")

    # =====================================
    # ✅ Logout
    # =====================================
    def logout(self, access_token: str):
        try:
            self.client.global_sign_out(AccessToken=access_token)
            self.logger.info("User logged out successfully")
            return {"message": "User logged out successfully"}
        except ClientError as e:
            self._handle_cognito_error(e, "logout")

    # =====================================
    # ✅ Refresh Token
    # =====================================
    def refresh_token(self, refresh_token: str):
        try:
            # Build refresh parameters
            auth_params = {
                "REFRESH_TOKEN": refresh_token
            }
            
            # Note: SECRET_HASH is not needed for refresh token flow with admin auth
            
            response = self.client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters=auth_params
            )
            
            tokens = response["AuthenticationResult"]
            return {
                "status": "SUCCESS",
                "access_token": tokens["AccessToken"],
                "id_token": tokens["IdToken"],
                "token_type": tokens["TokenType"],
                "expires_in": tokens["ExpiresIn"]
            }
        except ClientError as e:
            self._handle_cognito_error(e, "refresh_token")

    # =====================================
    # ✅ Forgot Password
    # =====================================
    def forgot_password(self, email: str):
        try:
            self.logger.info(f"Initiating forgot password for: {email}")
            
            # Build forgot password parameters
            forgot_params = {
                "ClientId": self.client_id,
                "Username": email
            }
            
            # Add SECRET_HASH if client secret exists
            if self.client_secret:
                secret_hash = self._get_secret_hash(email)
                forgot_params["SecretHash"] = secret_hash
            
            response = self.client.forgot_password(**forgot_params)
            
            self.logger.info(f"✅ Password reset code sent to: {email}")
            return {
                "message": "Password reset code has been sent to your email.",
                "code_delivery_medium": response.get("CodeDeliveryDetails", {}).get("DeliveryMedium"),
                "code_delivery_destination": response.get("CodeDeliveryDetails", {}).get("Destination")
            }
            
        except ClientError as e:
            self._handle_cognito_error(e, "forgot_password")

    # =====================================
    # ✅ Confirm Forgot Password
    # =====================================
    def confirm_forgot_password(self, email: str, code: str, new_password: str):
        try:
            self.logger.info(f"Confirming password reset for: {email}")
            
            # Build confirm parameters
            confirm_params = {
                "ClientId": self.client_id,
                "Username": email,
                "ConfirmationCode": code,
                "Password": new_password
            }
            
            # Add SECRET_HASH if client secret exists
            if self.client_secret:
                secret_hash = self._get_secret_hash(email)
                confirm_params["SecretHash"] = secret_hash
            
            self.client.confirm_forgot_password(**confirm_params)
            
            self.logger.info(f"✅ Password reset successful for: {email}")
            return {"message": "Password has been reset successfully. You can now login with your new password."}
            
        except ClientError as e:
            self._handle_cognito_error(e, "confirm_forgot_password")

    # =====================================
    # 🔧 DEBUG: Test Cognito Connection
    # =====================================
    def test_connection(self):
        """Test if Cognito credentials and configuration are correct"""
        try:
            self.logger.info("=== TESTING COGNITO CONNECTION ===")
            self.logger.info(f"Region: {config('AWS_REGION')}")
            self.logger.info(f"User Pool ID: {self.user_pool_id}")
            self.logger.info(f"Client ID: {self.client_id}")
            self.logger.info(f"Has Client Secret: {self.client_secret is not None}")
            
            # Try to describe the user pool
            pool_info = self.client.describe_user_pool(UserPoolId=self.user_pool_id)
            self.logger.info(f"✅ User Pool found: {pool_info['UserPool']['Name']}")
            
            # Try to describe the app client
            client_info = self.client.describe_user_pool_client(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id
            )
            self.logger.info(f"✅ App Client found: {client_info['UserPoolClient']['ClientName']}")
            self.logger.info(f"Explicit Auth Flows: {client_info['UserPoolClient'].get('ExplicitAuthFlows', [])}")
            
            # Check if ADMIN_NO_SRP_AUTH is enabled
            auth_flows = client_info['UserPoolClient'].get('ExplicitAuthFlows', [])
            if 'ADMIN_NO_SRP_AUTH' not in auth_flows:
                self.logger.error("❌ ADMIN_NO_SRP_AUTH is NOT enabled in app client!")
                return {
                    "status": "error",
                    "message": "ADMIN_NO_SRP_AUTH not enabled in app client",
                    "required_action": "Enable ALLOW_ADMIN_USER_PASSWORD_AUTH in Cognito app client settings"
                }
            
            self.logger.info("✅ All configurations look good!")
            return {
                "status": "success",
                "message": "Cognito connection successful",
                "user_pool": pool_info['UserPool']['Name'],
                "app_client": client_info['UserPoolClient']['ClientName'],
                "auth_flows": auth_flows
            }
            
        except ClientError as e:
            self.logger.error(f"❌ Connection test failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "code": e.response['Error']['Code']
            }

    # =====================================
    # ✅ Get Current User Info (from access token)
    # =====================================
    def get_current_user(self, access_token: str) -> UserOut:
        """Get current user info from access token"""
        try:
            # Get user info from token
            response = self.client.get_user(AccessToken=access_token)
            
            # Map to UserOut format
            attrs = {attr["Name"]: attr["Value"] for attr in response.get("UserAttributes", [])}
            
            # Use the 'name' attribute or email as username
            username = (
                attrs.get("name") or 
                attrs.get("preferred_username") or 
                attrs.get("email", "").split("@")[0]
            )
            
            return UserOut(
                email=attrs.get("email", ""),
                username=username,
                phone_number=attrs.get("phone_number", ""),
                profile_image_url=attrs.get("custom:profile_image_url", ""),
                is_active=True,
                email_verified=attrs.get("email_verified", "false").lower() == "true",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
        except ClientError as e:
            self._handle_cognito_error(e, "get_current_user")

    # =====================================
    # CRUD Operations
    # =====================================
    def get_all(self, limit: int = 20, pagination_token: str | None = None):
        try:
            params = {"UserPoolId": self.user_pool_id, "Limit": limit}
            if pagination_token:
                params["PaginationToken"] = pagination_token

            response = self.client.list_users(**params)
            users = [self._map_user(u) for u in response.get("Users", [])]

            return {"users": users, "next_token": response.get("PaginationToken")}

        except ClientError as e:
            self._handle_cognito_error(e, "get_all")

    def get_by_username(self, username: str) -> UserOut:
        try:
            response = self.client.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=username
            )
            user = {
                "Username": response["Username"],
                "Attributes": response["UserAttributes"],
                "Enabled": response.get("Enabled", True)
            }
            return self._map_user(user)
        except ClientError as e:
            self._handle_cognito_error(e, "get_by_username")

    def update(self, username: str, user_data: UserUpdate):
        try:
            attributes = []
            for key, value in user_data.dict(exclude_unset=True).items():
                if value is None:
                    continue
                    
                name_mapping = {
                    "profile_image_url": "custom:profile_image_url",
                    "phone_number": "phone_number",
                    "email": "email",
                    "username": "name"
                }
                
                name = name_mapping.get(key)
                if name:
                    attributes.append({"Name": name, "Value": str(value)})

            if not attributes:
                return {"message": "No attributes to update"}

            self.client.admin_update_user_attributes(
                UserPoolId=self.user_pool_id,
                Username=username,
                UserAttributes=attributes
            )

            self.logger.info(f"User updated: {username}")
            return {"message": "User updated successfully"}
        except ClientError as e:
            self._handle_cognito_error(e, "update")

    def delete(self, username: str):
        try:
            self.client.admin_delete_user(
                UserPoolId=self.user_pool_id,
                Username=username
            )
            self.logger.info(f"User deleted: {username}")
            return {"message": "User deleted successfully"}
        except ClientError as e:
            self._handle_cognito_error(e, "delete")