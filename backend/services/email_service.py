from backend.services.ai_service import ai_service


class EmailService:

    def generate(self, email_type: str, recipient: str = "", company: str = "",
                 role: str = "", context: str = "", tone: str = "professional") -> dict:
        return ai_service.generate_email(email_type, recipient, company, role, context, tone)


email_service = EmailService()
