from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


# -------------------------------
# ORGANIZATIONS (🔥 MULTI-LOCATION READY)
# -------------------------------
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    # 🔥 NEW: parent-child structure
    parent_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete")
    assessments = relationship("HIPAAAssessment", back_populates="organization", cascade="all, delete")
    subscriptions = relationship("Subscription", back_populates="organization", cascade="all, delete")
    reports = relationship("Report", back_populates="organization", cascade="all, delete")

    # 🔥 children (clinics under enterprise)
    children = relationship("Organization")


# -------------------------------
# USERS
# -------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    role = Column(String, default="staff")  # admin | staff
    is_admin = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)

    stripe_customer_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="users")


# -------------------------------
# SUBSCRIPTIONS
# -------------------------------
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    plan = Column(String, default="free")  # free | pro | enterprise
    status = Column(String, default="inactive")
    is_active = Column(Boolean, default=False)

    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)

    current_period_end = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="subscriptions")


# -------------------------------
# REPORTS
# -------------------------------
class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    file_path = Column(String)

    is_paid = Column(Boolean, default=False)
    stripe_session_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="reports")


# -------------------------------
# HIPAA ASSESSMENTS
# -------------------------------
class HIPAAAssessment(Base):
    __tablename__ = "hipaa_assessments"

    id = Column(Integer, primary_key=True)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    score = Column(Float)
    risk_level = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="assessments")
    answers = relationship("HIPAAAnswer", back_populates="assessment", cascade="all, delete")


# -------------------------------
# HIPAA ANSWERS
# -------------------------------
class HIPAAAnswer(Base):
    __tablename__ = "hipaa_answers"

    id = Column(Integer, primary_key=True)

    assessment_id = Column(Integer, ForeignKey("hipaa_assessments.id"), nullable=False)

    question_id = Column(String)
    answer = Column(String)

    assessment = relationship("HIPAAAssessment", back_populates="answers")


# -------------------------------
# ANALYTICS
# -------------------------------
class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(Integer, index=True, nullable=False)

    overall_score = Column(Float)
    risk_level = Column(String)

    admin_score = Column(Float)
    technical_score = Column(Float)
    physical_score = Column(Float)
    network_score = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)