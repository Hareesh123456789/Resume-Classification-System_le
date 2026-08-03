"""
---------------------------------------------------------
Resume JSON Schema
---------------------------------------------------------
Defines the standard structure of a parsed resume.
---------------------------------------------------------
"""

from typing import List, Optional
from pydantic import BaseModel


# -----------------------------
# Personal Information
# -----------------------------

class PersonalInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    location: Optional[str] = None


# -----------------------------
# Skills
# -----------------------------

class Skills(BaseModel):
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    web_technologies: List[str] = Field(default_factory=list)
    ai_ml: List[str] = Field(default_factory=list)
    cloud: List[str] = Field(default_factory=list)
    devops: List[str] = Field(default_factory=list)
    mobile: List[str] = Field(default_factory=list)
    testing: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    operating_systems: List[str] = Field(default_factory=list)
    embedded_iot: List[str] = Field(default_factory=list)
    concepts: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)


# -----------------------------
# Education
# -----------------------------

class Education(BaseModel):
    degree: Optional[str] = None
    specialization: Optional[str] = None
    institution: Optional[str] = None
    university: Optional[str] = None
    year: Optional[str] = None
    score: Optional[str] = None


# -----------------------------
# Experience
# -----------------------------

class Experience(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None


# -----------------------------
# Project
# -----------------------------

class Project(BaseModel):
    title: Optional[str] = None
    technologies: List[str] = []
    description: Optional[str] = None


# -----------------------------
# Certification
# -----------------------------

class Certification(BaseModel):
    name: Optional[str] = None
    organization: Optional[str] = None
    year: Optional[str] = None


# -----------------------------
# Final Resume Schema
# -----------------------------

class ResumeSchema(BaseModel):

    personal_info: PersonalInfo

    skills: Skills

    education: List[Education]

    experience: List[Experience]

    projects: List[Project]

    certifications: List[Certification]