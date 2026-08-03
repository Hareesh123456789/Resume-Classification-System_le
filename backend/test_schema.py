from schemas.resume_schema import *

resume = ResumeSchema(

    personal_info=PersonalInfo(),

    skills=Skills(),

    education=[],

    experience=[],

    projects=[],

    certifications=[]

)

print(resume.model_dump_json(indent=4))