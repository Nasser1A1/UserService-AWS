# from sqlalchemy import Column, String, DateTime, Boolean
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.sql import func
# import uuid
# from infrastructure.database import Base


# class User(Base):
#     __tablename__ = "users"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
#     email = Column(String(255), unique=True, nullable=False, index=True)
#     full_name = Column(String(255), nullable=True)
#     phone_number = Column(String(50), nullable=True)
#     is_active = Column(Boolean, default=True)
#     is_verified = Column(Boolean, default=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())
