"""
Proposal Generation Service — builds full government proposals using RAG + LLM.
"""
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models.opportunity import Opportunity
from backend.models.proposal import Proposal
from backend.models.user_profile import UserProfile
from backend.services.rag_service import rag_service

logger = logging.getLogger(__name__)

# ─────────────────────── SYSTEM PROMPT (REQUIRED) ────────────────────────────
SYSTEM_PROMPT = """You are a government contract proposal writer specializing in federal solicitations.

CRITICAL RULES:

You must ONLY use information provided in the context.

DO NOT hallucinate experience, certifications, personnel, tools, or past performance.

If information is missing, explicitly state:
"Information not provided in company profile."

Tone must be:
- Professional
- Formal
- Government-compliant
- Clear
- Concise
- Evidence-based

You must:
- Match company capabilities to solicitation requirements
- Cite relevant experience
- Follow federal proposal structure
- Use realistic compliance language

Output format: Return a valid JSON object with these exact keys:
{
  "executive_summary": {"content": "...", "sources": [{"citation": "..."}]},
  "technical_approach": {"content": "...", "sources": [{"citation": "..."}]},
  "past_performance": {"content": "...", "sources": [{"citation": "..."}]},
  "compliance_matrix": {"content": "...", "sources": [{"citation": "..."}]},
  "company_overview": {"content": "...", "sources": [{"citation": "..."}]},
  "conclusion": {"content": "...", "sources": [{"citation": "..."}]}
}"""
# ─────────────────────────────────────────────────────────────────────────────


def _build_generation_prompt(
    context: Dict[str, Any],
    tone: str = "professional",
) -> str:
    """Build the user-side prompt for the LLM."""
    solicitation = context.get("solicitation_context", "No solicitation text available.")
    profile = context.get("user_profile_context", "No company profile available.")
    company = context.get("company_name", "Company")

    tone_instruction = {
        "professional": "Use a professional, formal tone.",
        "assertive": "Use a confident, assertive tone while remaining formal.",
        "concise": "Be concise and direct. Use bullet points where appropriate.",
        "detailed": "Be thorough and detailed in your explanations.",
    }.get(tone, "Use a professional, formal tone.")

    return f"""
You are writing a government contract proposal for: {company}

TONE INSTRUCTION: {tone_instruction}

=== SOLICITATION CONTEXT ===
{solicitation}

=== COMPANY PROFILE ===
{profile}

=== INSTRUCTIONS ===
Generate a complete, compliant federal government proposal with all six required sections.
Each section must:
1. Directly reference the solicitation requirements
2. Include [Source: ...] citations from the provided solicitation context
3. Map company capabilities to specific requirements
4. Use formal federal proposal language

For the compliance_matrix section, format it as a structured table in markdown:
| Requirement | Company Response | Compliance Status |

Return ONLY valid JSON with the structure defined in your system prompt.
Do NOT include any text outside the JSON object.
"""


class LLMClient:
    """Abstraction over OpenAI / Gemini completion APIs."""

    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self._openai_client = None

    def _get_openai(self):
        if self._openai_client is None:
            from openai import AsyncOpenAI
            self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai_client

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
    ) -> str:
        """Call the configured LLM and return the raw text response."""
        if self.provider == "openai":
            return await self._complete_openai(system_prompt, user_prompt, temperature)
        elif self.provider == "gemini":
            return await self._complete_gemini(system_prompt, user_prompt, temperature)
        elif self.provider == "groq":
            return await self._complete_groq(system_prompt, user_prompt, temperature)
        else:
            raise ValueError(f"Unknown AI provider: {self.provider}")

    async def _complete_openai(
        self, system_prompt: str, user_prompt: str, temperature: float
    ) -> str:
        client = self._get_openai()
        response = await client.chat.completions.create(
            model=settings.OPENAI_LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
            max_tokens=8192,
        )
        return response.choices[0].message.content or ""

    async def _complete_gemini(
        self, system_prompt: str, user_prompt: str, temperature: float
    ) -> str:
        import asyncio
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_LLM_MODEL,
            system_instruction=system_prompt,
            generation_config={
                "temperature": temperature,
                "response_mime_type": "application/json",
                "max_output_tokens": 8192,
            },
        )
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(user_prompt),
        )
        return response.text or ""

    async def _complete_groq(
        self, system_prompt: str, user_prompt: str, temperature: float
    ) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        response = await client.chat.completions.create(
            model=settings.GROQ_LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
            max_tokens=8192,
        )
        return response.choices[0].message.content or ""


llm_client = LLMClient()


class ProposalService:
    """
    Orchestrates the full proposal generation workflow using RAG.
    """

    async def generate_proposal(
        self,
        db: AsyncSession,
        opportunity_id: uuid.UUID,
        user_profile_id: uuid.UUID,
        tone: str = "professional",
        proposal_id: Optional[uuid.UUID] = None,
    ) -> Proposal:
        """
        Full proposal generation:
        1. Load opportunity and user profile
        2. Run RAG pipeline
        3. Call LLM with structured prompt
        4. Parse and store proposal sections
        """
        # Load opportunity
        opp_result = await db.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = opp_result.scalar_one_or_none()
        if not opportunity:
            raise ValueError(f"Opportunity {opportunity_id} not found")

        # Load user profile
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.id == user_profile_id)
        )
        user_profile = profile_result.scalar_one_or_none()
        if not user_profile:
            raise ValueError(f"UserProfile {user_profile_id} not found")

        # Get or Create proposal record
        proposal = None
        if proposal_id:
            prop_result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
            proposal = prop_result.scalar_one_or_none()
        
        if proposal:
            proposal.status = "processing"
            proposal.tone = tone
        else:
            proposal = Proposal(
                id=uuid.uuid4(),
                opportunity_id=opportunity_id,
                user_profile_id=user_profile_id,
                status="processing",
                tone=tone,
            )
            db.add(proposal)
        
        await db.flush()

        try:
            # Run RAG pipeline
            context = await rag_service.full_rag_pipeline(
                db=db,
                opportunity_id=opportunity_id,
                user_profile=user_profile,
            )

            # Build prompts
            user_prompt = _build_generation_prompt(context, tone=tone)

            # Call LLM
            logger.info(f"Calling LLM for proposal {proposal.id}")
            raw_response = await llm_client.complete(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3,
            )

            # Parse JSON response
            sections = self._parse_sections(raw_response, context["sources"])
            proposal.sections = sections
            proposal.status = "completed"

        except Exception as e:
            logger.error(f"Proposal generation failed: {e}", exc_info=True)
            proposal.status = "failed"
            proposal.error_message = str(e)

        await db.flush()
        return proposal

    async def refine_section(
        self,
        db: AsyncSession,
        proposal_id: uuid.UUID,
        section: str,
        instruction: str,
        tone: Optional[str] = None,
    ) -> Proposal:
        """
        Regenerate a single proposal section based on user instruction.
        """
        result = await db.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        current_sections = proposal.sections or {}
        current_content = (current_sections.get(section) or {}).get("content", "")

        # Load context
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.id == proposal.user_profile_id)
        )
        user_profile = profile_result.scalar_one_or_none()

        if not user_profile:
            raise ValueError(f"UserProfile not found for proposal {proposal_id}")

        context = await rag_service.full_rag_pipeline(
            db=db,
            opportunity_id=proposal.opportunity_id,
            user_profile=user_profile,
        )

        section_display = section.replace("_", " ").title()
        refine_prompt = f"""
You are refining the "{section_display}" section of a government proposal.

INSTRUCTION: {instruction}
TONE: {tone or proposal.tone}

=== CURRENT SECTION CONTENT ===
{current_content}

=== SOLICITATION CONTEXT ===
{context.get("solicitation_context", "")}

=== COMPANY PROFILE ===
{context.get("user_profile_context", "")}

Return ONLY a valid JSON object with this exact structure:
{{
  "{section}": {{
    "content": "the refined section content here with [Source: ...] citations",
    "sources": [{{"citation": "...", "snippet": "..."}}]
  }}
}}
"""
        raw = await llm_client.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=refine_prompt,
            temperature=0.4,
        )

        parsed = json.loads(raw)
        if section not in parsed:
            # Try wrapping if LLM returned just the content
            parsed = {section: parsed}

        updated_sections = dict(current_sections)
        updated_sections[section] = parsed.get(section, current_sections.get(section))
        proposal.sections = updated_sections
        proposal.version += 1
        if tone:
            proposal.tone = tone

        await db.flush()
        return proposal

    def _parse_sections(
        self, raw_response: str, sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Parse the LLM JSON response into section objects.
        Attaches source metadata to each section.
        """
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Attempt to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                except json.JSONDecodeError:
                    raise ValueError(f"LLM returned invalid JSON: {raw_response[:500]}")
            else:
                raise ValueError(f"No JSON found in LLM response: {raw_response[:500]}")

        section_keys = [
            "executive_summary", "technical_approach", "past_performance",
            "compliance_matrix", "company_overview", "conclusion"
        ]

        result = {}
        for key in section_keys:
            if key in parsed:
                raw_section = parsed[key]
                if isinstance(raw_section, str):
                    result[key] = {"content": raw_section, "sources": sources[:3]}
                elif isinstance(raw_section, dict):
                    if "sources" not in raw_section or not raw_section["sources"]:
                        raw_section["sources"] = sources[:3]
                    result[key] = raw_section
            else:
                result[key] = {
                    "content": "Information not provided in company profile.",
                    "sources": [],
                }

        return result


# Singleton
proposal_service = ProposalService()
