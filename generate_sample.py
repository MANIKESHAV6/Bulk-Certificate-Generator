
from app.services.certificate_generator import generate_certificate


file_path = generate_certificate(
    recipient_name="Mani Keshav",
    course_name="Python Backend Development",
    completion_date="10 October 2026",
    certificate_id="CERT-DEMO-001",
    output_path="generated_certificates/sample_certificate.pdf",
)

print("Certificate generated successfully!")
print(f"Saved at: {file_path}")
