import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from backend.db.base import AsyncSessionLocal
from backend.models.opportunity import Opportunity
from backend.models.user_profile import UserProfile
from backend.services.embedding_service import embedding_service

async def seed_data():
    async with AsyncSessionLocal() as session:
        # Create a mock opportunity
        opp_id = uuid.uuid4()
        full_text = "The Department of Energy requires a software contractor to build an AI-powered proposal generation and analysis system. The system must use modern web technologies, React, and Python, and must integrate with large language models. The contractor should have experience in federal software delivery and AI integration."
        
        print("Embedding opportunity text...")
        opp_embedding = await embedding_service.embed_text(full_text)
        
        opp = Opportunity(
            id=opp_id,
            notice_id="MOCK-DOE-2026-001",
            title="AI Software Development for DoE",
            description="Developing an AI-powered software application for the Department of Energy.",
            agency="Department of Energy",
            department="Energy",
            posted_date=datetime.now(timezone.utc),
            response_deadline=datetime.now(timezone.utc) + timedelta(days=30),
            notice_type="Solicitation",
            naics_code="541511",
            naics_description="Custom Computer Programming Services",
            set_aside_type="Small Business",
            estimated_value="$1,000,000 - $5,000,000",
            full_text=full_text,
            embedding=opp_embedding,
            active=True
        )
        session.add(opp)

        # Create a mock user profile
        prof_id = uuid.uuid4()
        capabilities = "Deloitte offers advanced software engineering, AI integration, and federal compliance services. We have delivered over 50 federal contracts using Python, React, and LLMs. Our team holds Top Secret clearances and specializes in rapid agile delivery."
        
        print("Embedding user profile text...")
        prof_embedding = await embedding_service.embed_text(capabilities)
        
        prof = UserProfile(
            id=prof_id,
            company_name="Deloitte Consulting",
            capabilities_statement=capabilities,
            past_performance="Built AI systems for DoD and VA. $50M in prior federal work.",
            certifications="ISO 9001, CMMI Level 3",
            naics_codes=["541511", "541512"],
            set_asides=[],
            location="Arlington, VA",
            years_experience=15,
            embedding=prof_embedding
        )
        session.add(prof)

        await session.commit()
        print(f"Successfully seeded database!")
        print(f"- Opportunity created: {opp.title} ({opp.notice_id})")
        print(f"- User Profile created: {prof.company_name}")

if __name__ == "__main__":
    asyncio.run(seed_data())
