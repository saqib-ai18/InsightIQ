from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog
from app.core.config import get_settings
from app.models.database import UserModel, APIKeyModel
from app.core.database import get_db_session
from uuid import uuid4
import secrets
import hashlib

logger = structlog.get_logger()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = get_settings()

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


class AuthService:
    def __init__(self):
        pass

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    def get_user_by_email(self, email: str) -> Optional[UserModel]:
        with get_db_session() as db:
            return db.query(UserModel).filter(UserModel.email == email).first()

    def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        with get_db_session() as db:
            return db.query(UserModel).filter(UserModel.id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[UserModel]:
        with get_db_session() as db:
            return db.query(UserModel).filter(UserModel.username == username).first()

    def create_user(self, email: str, username: str, password: str, full_name: Optional[str] = None) -> UserModel:
        with get_db_session() as db:
            existing = db.query(UserModel).filter(
                (UserModel.email == email) | (UserModel.username == username)
            ).first()
            if existing:
                raise ValueError("User with this email or username already exists")
            
            user = UserModel(
                id=str(uuid4()),
                email=email,
                username=username,
                hashed_password=self.get_password_hash(password),
                full_name=full_name,
                is_active=True,
                is_superuser=False,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

    def authenticate_user(self, email: str, password: str) -> Optional[UserModel]:
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def update_last_login(self, user_id: str):
        with get_db_session() as db:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                db.commit()

    def create_api_key(self, user_id: str, name: str, expires_days: Optional[int] = None) -> tuple[str, APIKeyModel]:
        raw_key = f"iq_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        prefix = raw_key[:8]
        
        with get_db_session() as db:
            api_key = APIKeyModel(
                id=str(uuid4()),
                user_id=user_id,
                name=name,
                key_hash=key_hash,
                prefix=prefix,
                is_active=True,
                expires_at=datetime.utcnow() + timedelta(days=expires_days) if expires_days else None,
            )
            db.add(api_key)
            db.commit()
            db.refresh(api_key)
            return raw_key, api_key

    def verify_api_key(self, raw_key: str) -> Optional[APIKeyModel]:
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        with get_db_session() as db:
            api_key = db.query(APIKeyModel).filter(
                APIKeyModel.key_hash == key_hash,
                APIKeyModel.is_active == True,
            ).first()
            if api_key and (api_key.expires_at is None or api_key.expires_at > datetime.utcnow()):
                api_key.last_used = datetime.utcnow()
                db.commit()
                return api_key
        return None

    def list_api_keys(self, user_id: str) -> list[APIKeyModel]:
        with get_db_session() as db:
            return db.query(APIKeyModel).filter(APIKeyModel.user_id == user_id).all()

    def revoke_api_key(self, user_id: str, key_id: str) -> bool:
        with get_db_session() as db:
            api_key = db.query(APIKeyModel).filter(
                APIKeyModel.id == key_id,
                APIKeyModel.user_id == user_id,
            ).first()
            if api_key:
                api_key.is_active = False
                db.commit()
                return True
        return False


auth_service = AuthService()