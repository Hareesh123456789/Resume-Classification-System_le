from services.resume_service import ResumeService

service = ResumeService()

resume = service.analyze_resume("../sample_resume/Resume.pdf")

print("=" * 80)
print("RESUME JSON")
print("=" * 80)

print(
    resume.model_dump_json(
        indent=4
    )
)