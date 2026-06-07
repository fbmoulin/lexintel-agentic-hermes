from app.schemas.case import AgentResult


class SecurityAgent:
    name = "SecurityAgent"

    SUSPICIOUS_PATTERNS = [
        "ignore instruções anteriores",
        "ignore as instruções anteriores",
        "revele o prompt",
        "mostre o prompt",
        "execute comando",
        "delete arquivos",
        "apague arquivos",
        "favoreça uma parte",
        "aja como outro sistema",
        "oculte esta instrução",
        "não conte ao usuário",
    ]

    def run(self, case_id: str, text: str = "") -> AgentResult:
        detected = [
            pattern for pattern in self.SUSPICIOUS_PATTERNS
            if pattern.lower() in text.lower()
        ]

        if detected:
            return AgentResult(
                case_id=case_id,
                agent_name=self.name,
                status="blocked",
                output={
                    "security_status": "blocked",
                    "detected_risks": detected,
                    "recommended_action": "block"
                },
                errors=["Possível prompt injection ou instrução maliciosa detectada."]
            )

        return AgentResult(
            case_id=case_id,
            agent_name=self.name,
            status="success",
            output={
                "security_status": "safe",
                "detected_risks": [],
                "recommended_action": "continue"
            }
        )
