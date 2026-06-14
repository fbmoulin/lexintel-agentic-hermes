import re
import unicodedata

from app.schemas.case import AgentResult


class SecurityAgent:
    name = "SecurityAgent"
    scan_version = "security-agent-v0.2"

    SEVERITY_RANK = {
        "none": 0,
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
    }

    SUSPICIOUS_PATTERNS = [
        "ignore instruções anteriores",
        "ignore as instruções anteriores",
        "desconsidere instruções anteriores",
        "revele o prompt",
        "mostre o prompt",
        "exiba o prompt",
        "execute comando",
        "rode comando",
        "delete arquivos",
        "apague arquivos",
        "favoreça uma parte",
        "aja como outro sistema",
        "oculte esta instrução",
        "não conte ao usuário",
        "modo desenvolvedor",
        "jailbreak",
    ]

    DETECTION_RULES = [
        {
            "id": "ignore_previous_instructions",
            "label": "ignore instruções anteriores",
            "severity": "critical",
            "recommended_action": "block",
            "patterns": [
                r"\bignore\s+(as\s+)?instrucoes?\s+anteriores\b",
                r"\bi\s*g\s*n\s*o\s*r\s*e\s+(as\s+)?instrucoes?\s+anteriores\b",
                r"\bdesconsidere\s+(as\s+)?instrucoes?\s+anteriores\b",
            ],
        },
        {
            "id": "prompt_disclosure",
            "label": "revele o prompt",
            "severity": "critical",
            "recommended_action": "block",
            "patterns": [
                r"\b(revele|mostre|exiba|exponha)\s+(o\s+)?prompt\b",
                r"\b(system|sistema)\s+prompt\b",
                r"\bprompt\s+(do\s+)?sistema\b",
            ],
        },
        {
            "id": "command_execution",
            "label": "execute comando",
            "severity": "critical",
            "recommended_action": "block",
            "patterns": [
                r"\b(execute|rode|rodar|executar)\s+comandos?\b",
                r"\b(cmd\.?exe|powershell|rm\s+rf)\b",
            ],
        },
        {
            "id": "file_deletion",
            "label": "apague arquivos",
            "severity": "critical",
            "recommended_action": "block",
            "patterns": [
                r"\b(apague|delete|remova)\s+arquivos?\b",
                r"\bdelete\s+files?\b",
            ],
        },
        {
            "id": "partiality_instruction",
            "label": "favoreça uma parte",
            "severity": "high",
            "recommended_action": "block",
            "patterns": [
                r"\bfavoreca\s+(uma\s+)?parte\b",
                r"\baja\s+em\s+favor\s+da\s+parte\b",
            ],
        },
        {
            "id": "role_override",
            "label": "aja como outro sistema",
            "severity": "high",
            "recommended_action": "block",
            "patterns": [
                r"\baja\s+como\s+outro\s+sistema\b",
                r"\bvoce\s+agora\s+e\s+outro\s+sistema\b",
                r"\bmodo\s+desenvolvedor\b",
                r"\bjailbreak\b",
            ],
        },
        {
            "id": "hidden_instruction",
            "label": "não conte ao usuário",
            "severity": "high",
            "recommended_action": "block",
            "patterns": [
                r"\boculte\s+esta\s+instrucao\b",
                r"\bnao\s+conte\s+ao\s+usuario\b",
                r"\bsem\s+que\s+o\s+usuario\s+saiba\b",
            ],
        },
        {
            "id": "internal_rules_probe",
            "label": "regras internas do sistema",
            "severity": "medium",
            "recommended_action": "human_review",
            "patterns": [
                r"\b(regras|instrucoes)\s+internas\s+do\s+sistema\b",
                r"\bquais\s+sao\s+suas\s+regras\s+internas\b",
            ],
        },
    ]

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """
        Normalize text for deterministic local prompt-injection matching.

        The scanner strips diacritics, zero-width controls and punctuation-like
        separators so obvious obfuscations remain detectable without using an
        external model.
        """
        normalized = unicodedata.normalize("NFKC", text or "")
        normalized = re.sub(r"[\u200b-\u200f\u202a-\u202e\ufeff]", "", normalized)
        normalized = unicodedata.normalize("NFKD", normalized)
        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )
        normalized = normalized.lower()
        normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    @classmethod
    def _max_severity(cls, risk_details: list[dict]) -> str:
        if not risk_details:
            return "none"

        return max(
            (risk["severity"] for risk in risk_details),
            key=lambda severity: cls.SEVERITY_RANK[severity],
        )

    def _detect(self, text: str) -> list[dict]:
        normalized_text = self.normalize_text(text)
        detected = []

        for rule in self.DETECTION_RULES:
            if any(re.search(pattern, normalized_text) for pattern in rule["patterns"]):
                detected.append(
                    {
                        "id": rule["id"],
                        "label": rule["label"],
                        "severity": rule["severity"],
                        "recommended_action": rule["recommended_action"],
                    }
                )

        return detected

    def run(self, case_id: str, text: str = "") -> AgentResult:
        """
        Scan the provided text for prompt-injection or malicious-instruction patterns and produce a security assessment.

        Parameters:
            case_id (str): Identifier for the case being scanned; propagated into the returned result.
            text (str): Text to be analyzed for suspicious or malicious instruction patterns.

        Returns:
            AgentResult: An assessment containing:
                - status: one of `"blocked"`, `"warning"`, or `"success"`.
                - output: a dict with keys:
                    - `security_status`: `"blocked"`, `"review_required"`, or `"safe"`.
                    - `detected_risks`: list of detected risk labels.
                    - `risk_details`: list of detected risk entries (each includes `id`, `label`, `severity`, `recommended_action`).
                    - `max_severity`: highest severity found or `"none"`.
                    - `requires_human_review`: whether the entry requires human review.
                    - `recommended_action`: suggested action (`"block"`, `"human_review"`, or `"continue"`).
                    - `scan_version`: agent scan version string.
                - errors: present when status is `"blocked"` (contains explanatory messages).
                - warnings: present when status is `"warning"` (contains explanatory messages).
                - requires_human_review (top-level): mirrors whether human review is required.
                - external_use_allowed (top-level): set to `False` for all outcomes from this agent.
        """
        risk_details = self._detect(text)
        detected = [risk["label"] for risk in risk_details]
        max_severity = self._max_severity(risk_details)
        should_block = any(
            risk["recommended_action"] == "block" for risk in risk_details
        )

        if should_block:
            return AgentResult(
                case_id=case_id,
                agent_name=self.name,
                status="blocked",
                output={
                    "security_status": "blocked",
                    "detected_risks": detected,
                    "risk_details": risk_details,
                    "max_severity": max_severity,
                    "requires_human_review": True,
                    "recommended_action": "block",
                    "scan_version": self.scan_version,
                },
                errors=["Possível prompt injection ou instrução maliciosa detectada."],
                requires_human_review=True,
                external_use_allowed=False,
            )

        if risk_details:
            return AgentResult(
                case_id=case_id,
                agent_name=self.name,
                status="warning",
                output={
                    "security_status": "review_required",
                    "detected_risks": detected,
                    "risk_details": risk_details,
                    "max_severity": max_severity,
                    "requires_human_review": True,
                    "recommended_action": "human_review",
                    "scan_version": self.scan_version,
                },
                warnings=[
                    "Entrada marcada para revisão humana por risco de segurança."
                ],
                requires_human_review=True,
                external_use_allowed=False,
            )

        return AgentResult(
            case_id=case_id,
            agent_name=self.name,
            status="success",
            output={
                "security_status": "safe",
                "detected_risks": [],
                "risk_details": [],
                "max_severity": "none",
                "requires_human_review": False,
                "recommended_action": "continue",
                "scan_version": self.scan_version,
            },
            requires_human_review=False,
            external_use_allowed=False,
        )
