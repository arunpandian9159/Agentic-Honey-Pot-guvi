# Product Requirements Document (PRD)
## AI Agentic Honey-Pot for Scam Detection & Intelligence Extraction

**Version:** 1.0  
**Date:** February 3, 2026  
**Project Timeline:** 3 Days  
**Target Platform:** Railway  
**Budget Constraint:** Groq Free Tier  

---

## Executive Summary

Build a production-ready AI-powered honeypot system that autonomously detects scam messages, engages scammers with convincing human-like personas, extracts actionable intelligence (bank accounts, UPI IDs, phishing links), and reports results to GUVI's evaluation endpoint—all within a 3-day development timeline using cost-optimized infrastructure.

---

## 1. Project Overview

### 1.1 Business Objective
Create an API-driven agentic system that:
- Identifies scam intent from incoming messages
- Deploys adaptive AI personas to engage scammers
- Extracts valuable intelligence through multi-turn conversations
- Operates within free-tier constraints while maintaining competitive performance

### 1.2 Success Metrics
- **Scam Detection Accuracy:** >90% true positive rate
- **Engagement Depth:** Average 8-15 message exchanges per session
- **Intelligence Extraction Rate:** >70% sessions yield at least 1 piece of intel
- **API Response Time:** <3 seconds per request
- **Cost Efficiency:** Stay within Groq free tier (14,400 requests/day)

### 1.3 Constraints & Assumptions
- **Development Timeline:** 72 hours
- **Budget:** $0 (free tier only)
- **Infrastructure:** Railway (free tier)
- **LLM:** Groq Llama-3.3-70B-Versatile only
- **No Mock API Access:** Must test with synthetic data
- **Session Storage:** In-memory (acceptable for hackathon)

---

## 2. Technical Architecture

### 2.1 Tech Stack (Optimized for 3-Day Timeline)

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Backend Framework** | FastAPI | Async support, auto-docs, easy Railway deployment |
| **LLM Provider** | Groq (llama-3.3-70b-versatile) | Fast inference, good free tier, structured outputs |
| **Session Storage** | Python Dict (in-memory) | Simplest solution for short-term sessions |
| **Deployment** | Railway | Free tier, zero-config Python deployment |
| **Intelligence Extraction** | Structured Output Parsing (JSON Mode) | Reliable, no regex complexity |
| **Scam Detection** | Embedded in LLM Prompt | No separate model needed, cost-effective |

### 2.2 System Architecture

```
┌─────────────────┐
│  GUVI Platform  │
│  Mock Scammer   │
└────────┬────────┘
         │ POST /api/chat
         ▼
┌─────────────────────────────────────┐
│      FastAPI Application            │
│  ┌───────────────────────────────┐  │
│  │  1. Request Validator         │  │
│  │  2. Session Manager           │  │
│  │  3. Scam Detection Agent      │  │
│  │  4. Persona Selector          │  │
│  │  5. Conversation Manager      │  │
│  │  6. Intelligence Extractor    │  │
│  │  7. Response Generator        │  │
│  └───────────────────────────────┘  │
└────────┬────────────────────────────┘
         │ Groq API Calls
         ▼
┌─────────────────┐
│   Groq LLM      │
│ llama-3.3-70b   │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  GUVI Callback  │
│  Final Results  │
└─────────────────┘
```

### 2.3 Data Flow

1. **Incoming Request** → Validate API key & format
2. **Session Lookup** → Retrieve or create session context
3. **First-Pass Detection** → Quick scam signal check
4. **Persona Assignment** → Select appropriate victim persona
5. **LLM Generation** → Generate contextual response
6. **Intelligence Extraction** → Parse for scam artifacts (real-time)
7. **Session Update** → Store conversation + intelligence
8. **Response Delivery** → Return JSON to platform
9. **Final Callback** → When session ends, POST to GUVI endpoint

---

## 3. Core Components Specification

### 3.1 API Endpoint Design

#### Primary Endpoint: `/api/chat`
```python
# Request Headers
x-api-key: <YOUR_SECRET_API_KEY>
Content-Type: application/json

# Request Body
{
  "sessionId": "string (UUID)",
  "message": {
    "sender": "scammer | user",
    "text": "string",
    "timestamp": 1770005528731  # epoch ms
  },
  "conversationHistory": [
    {
      "sender": "scammer | user",
      "text": "string",
      "timestamp": 1770005528731
    }
  ],
  "metadata": {
    "channel": "SMS | WhatsApp | Email | Chat",
    "language": "string",
    "locale": "string"
  }
}

# Response Body
{
  "status": "success | error",
  "reply": "string"  # Agent's response as victim
}
```

#### Health Check: `/health`
```python
# Response
{
  "status": "healthy",
  "uptime": 12345,
  "active_sessions": 42
}
```

### 3.2 Session Management

```python
# In-Memory Session Store Structure
sessions = {
  "session_id": {
    "conversation_history": [],
    "scam_detected": False,
    "scam_confidence": 0.0,
    "persona": "elderly_confused",
    "intelligence": {
      "bank_accounts": [],
      "upi_ids": [],
      "phishing_links": [],
      "phone_numbers": [],
      "suspicious_keywords": []
    },
    "message_count": 0,
    "created_at": 1770005528731,
    "last_activity": 1770005528731
  }
}

# Session Lifecycle
- Created on first message
- Updated each interaction
- Auto-expire after 30 minutes of inactivity
- Callback sent when:
  - Scammer stops responding (timeout)
  - Intelligence extraction complete (success)
  - Message limit reached (15 exchanges)
```

### 3.3 Scam Detection Strategy

**Approach:** Embedded in LLM with explicit classification task

**Detection Prompt Template:**
```
You are a scam detection system. Analyze this message and respond with JSON:

Message: "{incoming_text}"
Context: {conversation_context}

Output JSON:
{
  "is_scam": true/false,
  "confidence": 0.0-1.0,
  "scam_type": "bank_fraud | upi_fraud | phishing | fake_offer | tech_support | lottery | romance | investment | other",
  "urgency_level": "low | medium | high | critical",
  "key_indicators": ["indicator1", "indicator2"]
}

Scam indicators: urgency, authority impersonation, payment requests, 
link sharing, personal info requests, threats, too-good offers.
```

**Detection Triggers:**
- First message: Always run detection
- Follow-ups: Re-evaluate if confidence <0.7
- Threshold: 0.65+ confidence = activate agent

### 3.4 Persona System (Adaptive Victim Profiles)

**Persona Selection Logic:**
```python
PERSONAS = {
  "elderly_confused": {
    "age_range": "65-80",
    "tech_skill": "very_low",
    "trust_level": "high",
    "scam_types": ["bank_fraud", "tech_support", "lottery"],
    "characteristics": [
      "Confused by technical terms",
      "Trusts authority figures",
      "Asks repetitive questions",
      "Shares personal info readily",
      "Concerned about deadlines"
    ],
    "language_style": "Simple, worried, over-polite"
  },
  
  "busy_professional": {
    "age_range": "30-45",
    "tech_skill": "medium",
    "trust_level": "medium",
    "scam_types": ["upi_fraud", "phishing", "fake_offer"],
    "characteristics": [
      "Wants quick solutions",
      "Multitasking, distracted",
      "Checks details occasionally",
      "Impatient with long explanations"
    ],
    "language_style": "Brief, direct, sometimes typos"
  },
  
  "curious_student": {
    "age_range": "18-25",
    "tech_skill": "medium-high",
    "trust_level": "medium",
    "scam_types": ["investment", "fake_offer", "romance"],
    "characteristics": [
      "Asks clarifying questions",
      "Interested in deals/opportunities",
      "Somewhat skeptical but persuadable",
      "Uses modern slang"
    ],
    "language_style": "Casual, uses emojis sometimes"
  },
  
  "desperate_job_seeker": {
    "age_range": "25-40",
    "tech_skill": "medium",
    "trust_level": "high",
    "scam_types": ["job_scam", "investment", "fake_offer"],
    "characteristics": [
      "Eager to comply",
      "Shares resume/personal details",
      "Hopeful and vulnerable",
      "Willing to pay 'registration fees'"
    ],
    "language_style": "Polite, formal, grateful"
  },
  
  "tech_naive_parent": {
    "age_range": "40-60",
    "tech_skill": "low",
    "trust_level": "high",
    "scam_types": ["bank_fraud", "upi_fraud", "phishing"],
    "characteristics": [
      "Worried about family members",
      "Doesn't understand UPI/online banking",
      "Asks 'is this safe?'",
      "Follows instructions literally"
    ],
    "language_style": "Concerned, asks many questions"
  }
}

# Selection Algorithm
def select_persona(scam_type, urgency_level, message_content):
    # Match scam type to appropriate persona
    # Higher urgency → more vulnerable personas
    # Randomize slightly to avoid detection
    pass
```

### 3.5 Conversation Management System

**Conversation Flow Stages:**

```python
class ConversationStage:
    INITIAL_HOOK = 1        # Scammer's opening (detect here)
    ENGAGEMENT = 2          # Build trust, show interest
    INFORMATION_PROBE = 3   # Scammer asks for details
    RESISTANCE = 4          # Show slight hesitation (seems human)
    GRADUAL_COMPLIANCE = 5  # Slowly give information
    INTELLIGENCE_MINING = 6 # Extract scammer's details
    PROLONGATION = 7        # Keep conversation going
    NATURAL_EXIT = 8        # End when intelligence maxed

# Stage Transition Logic
- Stay in ENGAGEMENT until scammer asks for payment/info
- Move to RESISTANCE when first sensitive request arrives
- GRADUAL_COMPLIANCE: Give partial info, ask questions back
- INTELLIGENCE_MINING: "Can you send me the link/account first?"
- Exit gracefully after 15 exchanges or 3+ intelligence pieces
```

**Conversation Context Management:**
```python
# Include in every LLM call
context = {
  "persona": selected_persona,
  "stage": current_stage,
  "conversation_history": last_5_messages,  # Limit context size
  "extracted_intelligence": current_intel,
  "scammer_tactics": identified_tactics,
  "next_objective": "what to extract next"
}
```

### 3.6 Intelligence Extraction System

**Real-Time Extraction Strategy:**

Every scammer response is analyzed with structured output:

```python
# Extraction Prompt
extraction_prompt = f"""
Analyze this scammer message for intelligence. Extract in JSON format:

Message: "{scammer_message}"

{
  "bank_accounts": ["IFSC-XXXX-XXXX format or account numbers"],
  "upi_ids": ["phone@upi or name@bankname"],
  "phishing_links": ["http://... or https://..."],
  "phone_numbers": ["+91XXXXXXXXXX or 10-digit numbers"],
  "suspicious_keywords": ["urgent", "verify", "block", etc.],
  "extraction_notes": "Brief context of what was found"
}

Rules:
- Only extract if explicitly present in text
- Normalize formats (remove spaces from account numbers)
- Flag partial matches (e.g., "send to 9876543210")
- Empty arrays if nothing found
"""

# Combine extractions across conversation
def merge_intelligence(session):
    # Deduplicate and consolidate
    # Track extraction timestamps
    # Quality score based on completeness
```

**Intelligence Quality Metrics:**
```python
intelligence_score = (
  len(bank_accounts) * 3 +      # High value
  len(upi_ids) * 2 +             # Medium value
  len(phishing_links) * 2 +      # Medium value
  len(phone_numbers) * 1 +       # Low value (may be legit)
  len(suspicious_keywords) * 0.5 # Context only
)

# Quality thresholds
MINIMUM_QUALITY_SCORE = 3  # At least 1 bank account OR 2 UPI IDs
```

### 3.7 Response Generation System

**Core Response Generation Prompt:**

```python
system_prompt = f"""
You are roleplaying as a {persona['name']} to extract scam intelligence.

PERSONA DETAILS:
- Age: {persona['age_range']}
- Tech Skill: {persona['tech_skill']}
- Personality: {persona['characteristics']}
- Language Style: {persona['language_style']}

CURRENT SITUATION:
- Stage: {conversation_stage}
- Scammer's last message: "{scammer_message}"
- Conversation so far: {brief_history}

YOUR OBJECTIVES (in order):
1. Maintain believable persona - NEVER break character
2. Keep scammer engaged - show interest, ask questions
3. Extract intelligence - bank accounts, UPI IDs, links
4. Avoid premature exposure - don't seem too eager

CONVERSATION TACTICS:
- {stage_specific_tactics[current_stage]}

RESPONSE GUIDELINES:
- Keep responses 1-3 sentences (natural SMS length)
- Show appropriate emotion (worry, curiosity, confusion)
- Ask clarifying questions that prompt info sharing
- Mirror scammer's urgency level
- Use persona-appropriate language

Generate ONLY the victim's reply text. No explanations or meta-commentary.
"""

user_prompt = f"""
Scammer said: "{scammer_message}"

Your response as {persona['name']}:
"""
```

**Response Quality Checks:**
```python
def validate_response(response, persona):
    checks = {
      "length_ok": 10 < len(response) < 200,
      "no_ai_language": not contains_ai_phrases(response),
      "persona_consistent": matches_persona_style(response, persona),
      "engagement_value": has_question_or_hook(response),
      "natural_flow": follows_conversation_context(response)
    }
    return all(checks.values())

# Regenerate if fails
```

---

## 4. LLM Optimization Strategy (Free Tier Constraints)

### 4.1 Groq API Usage Optimization

**Free Tier Limits:**
- 14,400 requests per day
- ~30 requests per minute
- Total tokens: generous but uncapped

**Optimization Tactics:**

```python
# 1. Prompt Compression
- Use abbreviations in system prompts
- Limit conversation history to last 5 messages
- Remove redundant instructions

# 2. Request Batching
- Combine scam detection + response generation in one call
- Use structured outputs to get both classification and reply

# 3. Caching Strategy
- Cache common scam patterns
- Cache persona definitions
- Reuse system prompts

# 4. Smart Rate Limiting
class RateLimiter:
    def __init__(self):
        self.request_count = 0
        self.window_start = time.time()
    
    def check_limit(self):
        # Allow 25 requests/minute (buffer for 30 limit)
        # Reset counter every minute
        pass

# 5. Fallback Responses
- Pregenerated responses for common scenarios
- Graceful degradation if rate limit hit
```

### 4.2 Multi-Task Prompt Template

```python
# Combined prompt for efficiency
combined_prompt = f"""
Task 1: Classify if this is a scam
Task 2: If scam, generate victim response
Task 3: Extract any intelligence from scammer's message

Scammer's message: "{text}"
Conversation context: {history}
Current persona: {persona}

Respond in JSON:
{{
  "scam_detection": {{
    "is_scam": true/false,
    "confidence": 0.0-1.0,
    "scam_type": "string"
  }},
  "victim_response": "string (your reply as victim)",
  "intelligence": {{
    "bank_accounts": [],
    "upi_ids": [],
    "phishing_links": [],
    "phone_numbers": []
  }}
}}
"""
# This reduces 3 API calls to 1
```

---

## 5. Deployment Architecture

### 5.1 Railway Deployment Configuration

**File Structure:**
```
honeypot-api/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Dependencies
├── Procfile               # Railway process definition
├── railway.toml           # Railway config (optional)
├── .env.example           # Environment template
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py      # API endpoints
│   │   └── validators.py  # Request validation
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py      # Settings & secrets
│   │   ├── session.py     # Session management
│   │   └── llm.py         # Groq client wrapper
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── detector.py    # Scam detection
│   │   ├── personas.py    # Persona definitions
│   │   ├── conversation.py # Conversation management
│   │   └── extractor.py   # Intelligence extraction
│   └── utils/
│       ├── __init__.py
│       ├── logger.py      # Logging setup
│       └── callbacks.py   # GUVI callback handler
└── tests/
    ├── __init__.py
    ├── test_api.py
    ├── test_detector.py
    └── mock_data.py       # Synthetic scam messages
```

**requirements.txt:**
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
groq==0.4.1
python-dotenv==1.0.0
httpx==0.26.0
```

**Procfile:**
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables (Railway):**
```
GROQ_API_KEY=<your_groq_key>
API_SECRET_KEY=<your_random_secret>
GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 5.2 Railway Setup Steps

```bash
# 1. Install Railway CLI
npm install -g railway

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Set environment variables
railway variables set GROQ_API_KEY=your_key
railway variables set API_SECRET_KEY=your_secret

# 5. Deploy
railway up

# 6. Get public URL
railway domain
```

---

## 6. Testing Strategy (No Mock API Access)

### 6.1 Synthetic Test Data

**Create comprehensive test scenarios:**

```python
# tests/mock_data.py
SYNTHETIC_SCAM_MESSAGES = {
  "bank_fraud": [
    {
      "message": "Your bank account will be blocked today. Verify immediately by calling 9876543210.",
      "expected_intel": ["9876543210"],
      "urgency": "critical"
    },
    {
      "message": "Dear customer, update your KYC details. Transfer ₹1 to 9876543210@paytm to activate account.",
      "expected_intel": ["9876543210@paytm"],
      "urgency": "high"
    }
  ],
  "upi_fraud": [
    {
      "message": "You've won ₹50,000! Claim now by sending ₹99 processing fee to winner2024@oksbi",
      "expected_intel": ["winner2024@oksbi"],
      "urgency": "medium"
    }
  ],
  "phishing": [
    {
      "message": "Click here to verify: http://bankverify.malicious.com/verify?id=12345",
      "expected_intel": ["http://bankverify.malicious.com/verify?id=12345"],
      "urgency": "high"
    }
  ],
  "tech_support": [
    {
      "message": "Microsoft detected virus on your computer. Call our support: +91-9988776655",
      "expected_intel": ["+91-9988776655"],
      "urgency": "high"
    }
  ]
}

# Multi-turn conversation test
CONVERSATION_FLOW_TEST = [
  {"sender": "scammer", "text": "Your account will be suspended. Verify now."},
  {"sender": "user", "text": "Why? What happened?"},  # AI should generate this
  {"sender": "scammer", "text": "Due to suspicious activity. Share your UPI ID to verify."},
  # AI should ask clarifying question or show hesitation
]
```

### 6.2 Testing Checklist

**Unit Tests:**
- [ ] API key validation
- [ ] Request format validation
- [ ] Session creation/retrieval
- [ ] Scam detection accuracy (>85% on test set)
- [ ] Persona selection logic
- [ ] Intelligence extraction parsing
- [ ] Response generation quality

**Integration Tests:**
- [ ] End-to-end conversation flow
- [ ] Multi-turn intelligence accumulation
- [ ] GUVI callback triggering
- [ ] Rate limiting behavior
- [ ] Session timeout handling

**Performance Tests:**
- [ ] Response time <3 seconds
- [ ] Concurrent session handling (10+ simultaneous)
- [ ] Memory usage (should stay <512MB for free tier)

**Manual Testing Scenarios:**
```bash
# Test 1: First message detection
curl -X POST https://your-app.railway.app/api/chat \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-001",
    "message": {
      "sender": "scammer",
      "text": "Your bank account will be blocked. Verify immediately.",
      "timestamp": 1770005528731
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
  }'

# Test 2: Follow-up message
curl -X POST https://your-app.railway.app/api/chat \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-001",
    "message": {
      "sender": "scammer",
      "text": "Share your UPI ID: 9876543210@paytm",
      "timestamp": 1770005535000
    },
    "conversationHistory": [
      {"sender": "scammer", "text": "Your bank account will be blocked. Verify immediately.", "timestamp": 1770005528731},
      {"sender": "user", "text": "Why will it be blocked?", "timestamp": 1770005530000}
    ],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
  }'
```

---

## 7. Evaluation Metrics & Success Criteria

### 7.1 GUVI Evaluation Metrics

Based on problem statement, scoring includes:

| Metric | Target | Weight | Measurement |
|--------|--------|--------|-------------|
| Scam Detection Accuracy | >90% | 25% | True positive rate |
| Engagement Duration | 8-15 exchanges | 20% | Message count per session |
| Intelligence Quality | Score >5 | 30% | Completeness & variety |
| API Response Time | <3 seconds | 15% | P95 latency |
| Natural Conversation | Believable | 10% | Manual review |

### 7.2 Intelligence Quality Scoring

```python
def calculate_intelligence_score(intel):
    score = 0
    
    # Bank accounts (highest value)
    score += len(intel['bank_accounts']) * 3
    
    # UPI IDs (high value)
    score += len(intel['upi_ids']) * 2
    
    # Phishing links (high value)
    score += len(intel['phishing_links']) * 2
    
    # Phone numbers (medium value)
    score += len(intel['phone_numbers']) * 1
    
    # Suspicious keywords (low value, context only)
    score += min(len(intel['suspicious_keywords']), 5) * 0.5
    
    # Bonus for variety (multiple types extracted)
    intel_types = sum([
      len(intel['bank_accounts']) > 0,
      len(intel['upi_ids']) > 0,
      len(intel['phishing_links']) > 0,
      len(intel['phone_numbers']) > 0
    ])
    if intel_types >= 3:
        score *= 1.2  # 20% bonus
    
    return round(score, 2)

# Quality thresholds
EXCELLENT = 8+   # Multiple high-value items
GOOD = 5-7       # At least 1 bank account OR 2-3 other items
ACCEPTABLE = 3-4 # Basic intelligence
POOR = <3        # Insufficient data
```

### 7.3 Engagement Quality Metrics

```python
def evaluate_engagement(session):
    metrics = {
      "message_count": len(session['conversation_history']),
      "avg_response_length": calculate_avg_length(session),
      "question_ratio": count_questions(session) / len(session['conversation_history']),
      "persona_consistency": check_consistency(session),
      "scammer_frustration_avoided": not session.get('scammer_suspicious', False)
    }
    
    # Ideal engagement
    # - 8-15 messages (not too short, not too long)
    # - Mix of questions and statements
    # - Consistent persona throughout
    # - No red flags that expose detection
    
    return metrics
```

---

## 8. Implementation Phases (3-Day Timeline)

### Day 1: Core Infrastructure (10 hours)

**Morning (4 hours):**
- [ ] Set up FastAPI project structure
- [ ] Implement API endpoint with validation
- [ ] Create session management (in-memory dict)
- [ ] Add API key authentication
- [ ] Deploy to Railway (initial version)

**Afternoon (3 hours):**
- [ ] Integrate Groq API client
- [ ] Implement basic scam detection prompt
- [ ] Test detection on synthetic data
- [ ] Achieve >85% detection accuracy

**Evening (3 hours):**
- [ ] Build persona system (5 personas)
- [ ] Create persona selection logic
- [ ] Implement basic response generation
- [ ] Test single-turn conversations

**Day 1 Milestone:** Working API that detects scams and generates basic responses

---

### Day 2: Intelligence & Conversation (10 hours)

**Morning (4 hours):**
- [ ] Implement real-time intelligence extraction
- [ ] Create structured output parsing
- [ ] Build intelligence accumulation logic
- [ ] Test extraction accuracy on mock data

**Afternoon (4 hours):**
- [ ] Develop conversation stage management
- [ ] Create multi-turn conversation prompts
- [ ] Implement context-aware responses
- [ ] Add conversation flow logic

**Evening (2 hours):**
- [ ] Implement GUVI callback functionality
- [ ] Test end-to-end conversation flows
- [ ] Add error handling and logging

**Day 2 Milestone:** Full conversation capability with intelligence extraction

---

### Day 3: Optimization & Testing (10 hours)

**Morning (3 hours):**
- [ ] Optimize prompts for cost efficiency
- [ ] Implement rate limiting
- [ ] Add response validation
- [ ] Improve persona consistency

**Afternoon (4 hours):**
- [ ] Comprehensive testing (20+ scenarios)
- [ ] Fix bugs and edge cases
- [ ] Performance optimization
- [ ] Add monitoring/logging

**Evening (3 hours):**
- [ ] Final deployment to Railway
- [ ] End-to-end testing on production
- [ ] Documentation and README
- [ ] Prepare for submission

**Day 3 Milestone:** Production-ready system meeting all requirements

---

## 9. Risk Mitigation

### 9.1 Technical Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Groq rate limit exceeded** | High | Implement request queuing, fallback responses, rate limiter with buffer |
| **Railway free tier limits** | Medium | Monitor usage, optimize memory, graceful degradation |
| **LLM hallucinations** | High | Structured outputs, validation, response quality checks |
| **Session data loss** | Medium | Accept as trade-off for simplicity; could add Redis if needed |
| **Slow response times** | High | Optimize prompts, parallel processing, caching |

### 9.2 Functional Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **False positive scam detection** | Medium | Lower threshold to 0.65, multi-turn confirmation |
| **Premature exposure** | High | Strong persona prompts, avoid eager compliance, natural hesitation |
| **Insufficient intelligence** | High | Multi-stage extraction, ask clarifying questions, prolong engagement |
| **Unnatural responses** | Medium | Persona consistency checks, response validation, varied language |

### 9.3 Timeline Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Scope creep** | High | Stick to MVP features, defer enhancements |
| **Integration issues** | Medium | Test early and often, have fallback plan |
| **Deployment problems** | High | Deploy early Day 1, iterate in production |

---

## 10. Code Implementation Examples

### 10.1 Main FastAPI Application

```python
# main.py
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

from app.core.session import SessionManager
from app.core.llm import GroqClient
from app.agents.detector import ScamDetector
from app.agents.personas import PersonaManager
from app.agents.conversation import ConversationManager
from app.agents.extractor import IntelligenceExtractor
from app.utils.callbacks import GUVICallback

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Honeypot API", version="1.0.0")

# Initialize components
session_manager = SessionManager()
groq_client = GroqClient(api_key=os.getenv("GROQ_API_KEY"))
scam_detector = ScamDetector(groq_client)
persona_manager = PersonaManager()
conversation_manager = ConversationManager(groq_client)
intelligence_extractor = IntelligenceExtractor(groq_client)
guvi_callback = GUVICallback(os.getenv("GUVI_CALLBACK_URL"))

# Request/Response Models
class Message(BaseModel):
    sender: str  # "scammer" or "user"
    text: str
    timestamp: int

class Metadata(BaseModel):
    channel: Optional[str] = "SMS"
    language: Optional[str] = "English"
    locale: Optional[str] = "IN"

class ChatRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Message] = []
    metadata: Optional[Metadata] = None

class ChatResponse(BaseModel):
    status: str
    reply: str

# Authentication
async def verify_api_key(x_api_key: str = Header(...)):
    expected_key = os.getenv("API_SECRET_KEY")
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    try:
        logger.info(f"Processing session: {request.sessionId}")
        
        # 1. Get or create session
        session = session_manager.get_or_create(request.sessionId)
        
        # 2. Update conversation history
        session['conversation_history'].append({
            "sender": request.message.sender,
            "text": request.message.text,
            "timestamp": request.message.timestamp
        })
        session['message_count'] += 1
        
        # 3. Detect scam (if not already detected)
        if not session['scam_detected']:
            detection_result = await scam_detector.analyze(
                message=request.message.text,
                history=request.conversationHistory,
                metadata=request.metadata
            )
            
            if detection_result['is_scam'] and detection_result['confidence'] >= 0.65:
                session['scam_detected'] = True
                session['scam_confidence'] = detection_result['confidence']
                session['scam_type'] = detection_result['scam_type']
                
                # Select persona based on scam type
                session['persona'] = persona_manager.select_persona(
                    scam_type=detection_result['scam_type'],
                    urgency=detection_result['urgency_level']
                )
                logger.info(f"Scam detected! Type: {detection_result['scam_type']}, Persona: {session['persona']}")
        
        # 4. Extract intelligence from scammer's message
        if session['scam_detected']:
            extracted = await intelligence_extractor.extract(request.message.text)
            
            # Merge with existing intelligence
            for key in session['intelligence']:
                session['intelligence'][key].extend(extracted.get(key, []))
                session['intelligence'][key] = list(set(session['intelligence'][key]))  # Deduplicate
        
        # 5. Generate response
        if session['scam_detected']:
            reply = await conversation_manager.generate_response(
                persona=session['persona'],
                scammer_message=request.message.text,
                conversation_history=session['conversation_history'][-5:],  # Last 5 messages
                stage=conversation_manager.determine_stage(session),
                current_intelligence=session['intelligence']
            )
        else:
            # Not detected as scam yet, respond neutrally
            reply = "Okay, can you tell me more?"
        
        # 6. Update session
        session['conversation_history'].append({
            "sender": "user",
            "text": reply,
            "timestamp": int(datetime.now().timestamp() * 1000)
        })
        session['last_activity'] = datetime.now()
        session_manager.update(request.sessionId, session)
        
        # 7. Check if conversation should end
        should_end = (
            session['message_count'] >= 15 or  # Max messages
            intelligence_extractor.calculate_score(session['intelligence']) >= 8  # High quality intel
        )
        
        if should_end and session['scam_detected']:
            # Send final callback to GUVI
            await guvi_callback.send_final_result(
                session_id=request.sessionId,
                scam_detected=True,
                total_messages=session['message_count'],
                intelligence=session['intelligence'],
                agent_notes=f"Scam type: {session['scam_type']}. Persona: {session['persona']}"
            )
            logger.info(f"Session {request.sessionId} completed. Callback sent.")
        
        return ChatResponse(status="success", reply=reply)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return ChatResponse(status="error", reply="I'm sorry, I didn't understand that.")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_sessions": len(session_manager.sessions),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
```

### 10.2 Scam Detection Agent

```python
# app/agents/detector.py
from typing import Dict, List
import json

class ScamDetector:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def analyze(self, message: str, history: List = None, metadata: Dict = None) -> Dict:
        """Detect if message is a scam attempt"""
        
        prompt = f"""You are a scam detection system. Analyze this message and respond ONLY with valid JSON.

Message: "{message}"
Channel: {metadata.get('channel', 'Unknown') if metadata else 'Unknown'}
Context: {"First message" if not history else f"{len(history)} previous messages"}

Respond with this exact JSON structure:
{{
  "is_scam": true or false,
  "confidence": 0.0 to 1.0,
  "scam_type": "bank_fraud | upi_fraud | phishing | fake_offer | tech_support | lottery | romance | investment | other",
  "urgency_level": "low | medium | high | critical",
  "key_indicators": ["indicator1", "indicator2"]
}}

Scam indicators to look for:
- Urgency/threats: "account blocked", "immediate action", "today only"
- Authority impersonation: "bank", "government", "police", "IT department"
- Payment requests: UPI IDs, bank accounts, "send money", "pay fees"
- Personal info requests: "verify", "share OTP", "confirm details"
- Links: suspicious URLs, shortened links
- Too-good offers: "won prize", "free gift", "guaranteed returns"
- Fear tactics: "legal action", "suspended", "penalty"

Be confident in detection (>0.7) if multiple indicators present.
"""
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistency
                max_tokens=200
            )
            
            # Parse JSON response
            result = json.loads(response)
            
            # Validate structure
            required_keys = ['is_scam', 'confidence', 'scam_type', 'urgency_level', 'key_indicators']
            if not all(key in result for key in required_keys):
                raise ValueError("Invalid detection response structure")
            
            return result
            
        except Exception as e:
            # Fallback detection with keyword matching
            return self._fallback_detection(message)
    
    def _fallback_detection(self, message: str) -> Dict:
        """Simple keyword-based fallback if LLM fails"""
        message_lower = message.lower()
        
        scam_keywords = [
            'account blocked', 'verify immediately', 'urgent', 'suspended',
            'upi', 'bank account', 'transfer money', 'won prize', 'claim now',
            'otp', 'cvv', 'pin', 'password', 'link', 'click here'
        ]
        
        matches = [kw for kw in scam_keywords if kw in message_lower]
        confidence = min(len(matches) * 0.25, 0.95)
        
        return {
            "is_scam": len(matches) >= 2,
            "confidence": confidence,
            "scam_type": "other",
            "urgency_level": "medium",
            "key_indicators": matches
        }
```

### 10.3 Persona Manager

```python
# app/agents/personas.py
import random
from typing import Dict

class PersonaManager:
    PERSONAS = {
        "elderly_confused": {
            "name": "elderly_confused",
            "age": "65-80",
            "tech_skill": "very_low",
            "trust_level": "high",
            "scam_types": ["bank_fraud", "tech_support", "lottery"],
            "system_prompt": """You are a 70-year-old person who is not comfortable with technology.
You are worried and confused by technical terms. You trust authority figures like banks and government.
You ask simple questions repeatedly and need reassurance.
Keep responses 1-2 sentences. Show worry. Use simple language.
Example: "Oh dear, my account is blocked? What should I do? I'm not good with these things."
"""
        },
        
        "busy_professional": {
            "name": "busy_professional",
            "age": "30-45",
            "tech_skill": "medium",
            "trust_level": "medium",
            "scam_types": ["upi_fraud", "phishing", "fake_offer"],
            "system_prompt": """You are a busy 35-year-old professional, often multitasking.
You want quick solutions and sometimes don't read everything carefully.
You're moderately tech-savvy but distracted. Occasional typos are normal.
Keep responses brief and direct.
Example: "ok but why now? can u send link quickly i m busy"
"""
        },
        
        "curious_student": {
            "name": "curious_student",
            "age": "18-25",
            "tech_skill": "medium-high",
            "trust_level": "medium",
            "scam_types": ["investment", "fake_offer", "romance"],
            "system_prompt": """You are a 22-year-old college student, somewhat tech-savvy but inexperienced.
You ask clarifying questions and are interested in deals/opportunities.
You're initially skeptical but can be convinced with good explanations.
Use casual language, occasional modern slang.
Example: "wait seriously? that sounds too good tbh. how does it work exactly?"
"""
        },
        
        "tech_naive_parent": {
            "name": "tech_naive_parent",
            "age": "40-60",
            "tech_skill": "low",
            "trust_level": "high",
            "scam_types": ["bank_fraud", "upi_fraud", "phishing"],
            "system_prompt": """You are a 50-year-old parent who doesn't understand modern banking tech.
You're concerned about doing things correctly and worried about family.
You ask many questions about safety. You follow instructions literally.
Keep responses concerned but compliant.
Example: "Is this safe? I don't use UPI much. Do I need to give my password?"
"""
        },
        
        "desperate_job_seeker": {
            "name": "desperate_job_seeker",
            "age": "25-40",
            "tech_skill": "medium",
            "trust_level": "high",
            "scam_types": ["job_scam", "investment", "fake_offer"],
            "system_prompt": """You are a 30-year-old job seeker, eager for opportunities.
You're polite, formal, and willing to comply with requests.
You show gratitude and hope. You're vulnerable to convincing offers.
Keep responses grateful and compliant.
Example: "Thank you for this opportunity! Yes, I can do that. What details do you need from me?"
"""
        }
    }
    
    def select_persona(self, scam_type: str, urgency: str = "medium") -> str:
        """Select appropriate persona based on scam type"""
        
        # Find personas that match this scam type
        matching_personas = [
            name for name, persona in self.PERSONAS.items()
            if scam_type in persona['scam_types']
        ]
        
        if not matching_personas:
            # Default to general personas
            matching_personas = ["tech_naive_parent", "busy_professional"]
        
        # Higher urgency → more vulnerable personas
        if urgency in ["critical", "high"] and "elderly_confused" in matching_personas:
            return "elderly_confused"
        
        # Random selection with slight preference for variety
        return random.choice(matching_personas)
    
    def get_persona_prompt(self, persona_name: str) -> str:
        """Get system prompt for persona"""
        return self.PERSONAS.get(persona_name, self.PERSONAS["tech_naive_parent"])["system_prompt"]
```

### 10.4 Intelligence Extractor

```python
# app/agents/extractor.py
import json
import re
from typing import Dict, List

class IntelligenceExtractor:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def extract(self, message: str) -> Dict:
        """Extract intelligence from scammer's message"""
        
        prompt = f"""Extract scam intelligence from this message. Respond ONLY with valid JSON.

Message: "{message}"

Extract these items if present:
{{
  "bank_accounts": ["Account numbers, IFSC codes, or bank details"],
  "upi_ids": ["phone@upi, name@bank format UPI IDs"],
  "phishing_links": ["http:// or https:// URLs"],
  "phone_numbers": ["+91XXXXXXXXXX or 10-digit numbers"],
  "suspicious_keywords": ["urgent", "verify", "blocked", "prize", etc.]
}}

Rules:
- Only include items explicitly present in the message
- Normalize formats (remove spaces from numbers)
- Empty arrays if nothing found
- Be thorough - check for partial mentions

Examples:
- "Send to 9876543210" → phone_numbers: ["9876543210"]
- "Pay to winner@paytm" → upi_ids: ["winner@paytm"]
- "Click http://scam.com" → phishing_links: ["http://scam.com"]
"""
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.0,  # Deterministic extraction
                max_tokens=300
            )
            
            result = json.loads(response)
            
            # Additional regex-based validation and enrichment
            result = self._enhance_with_regex(message, result)
            
            return result
            
        except Exception as e:
            # Fallback to regex-only extraction
            return self._regex_extraction(message)
    
    def _enhance_with_regex(self, message: str, llm_result: Dict) -> Dict:
        """Enhance LLM extraction with regex patterns"""
        
        # Phone number patterns (Indian)
        phone_pattern = r'(\+91[\s-]?)?[6-9]\d{9}'
        phones = re.findall(phone_pattern, message)
        llm_result['phone_numbers'].extend([p.replace('+91', '').replace('-', '').replace(' ', '') for p in phones])
        
        # UPI ID pattern
        upi_pattern = r'[\w\.\-]+@[\w]+'
        upis = re.findall(upi_pattern, message)
        llm_result['upi_ids'].extend(upis)
        
        # URL pattern
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, message)
        llm_result['phishing_links'].extend(urls)
        
        # Bank account (basic pattern)
        account_pattern = r'\b\d{9,18}\b'
        accounts = re.findall(account_pattern, message)
        llm_result['bank_accounts'].extend(accounts)
        
        # Deduplicate all lists
        for key in llm_result:
            if isinstance(llm_result[key], list):
                llm_result[key] = list(set(llm_result[key]))
        
        return llm_result
    
    def _regex_extraction(self, message: str) -> Dict:
        """Pure regex-based fallback extraction"""
        return {
            "bank_accounts": list(set(re.findall(r'\b\d{9,18}\b', message))),
            "upi_ids": list(set(re.findall(r'[\w\.\-]+@[\w]+', message))),
            "phishing_links": list(set(re.findall(r'https?://[^\s]+', message))),
            "phone_numbers": list(set(re.findall(r'(\+91[\s-]?)?[6-9]\d{9}', message))),
            "suspicious_keywords": self._extract_keywords(message)
        }
    
    def _extract_keywords(self, message: str) -> List[str]:
        """Extract common scam keywords"""
        keywords = [
            'urgent', 'immediately', 'verify', 'blocked', 'suspended', 'expired',
            'prize', 'won', 'winner', 'claim', 'free', 'gift', 'offer',
            'account', 'bank', 'upi', 'payment', 'transfer', 'send money',
            'otp', 'password', 'pin', 'cvv', 'confirm', 'update', 'kyc'
        ]
        message_lower = message.lower()
        return [kw for kw in keywords if kw in message_lower]
    
    def calculate_score(self, intelligence: Dict) -> float:
        """Calculate intelligence quality score"""
        score = 0
        score += len(intelligence.get('bank_accounts', [])) * 3
        score += len(intelligence.get('upi_ids', [])) * 2
        score += len(intelligence.get('phishing_links', [])) * 2
        score += len(intelligence.get('phone_numbers', [])) * 1
        score += min(len(intelligence.get('suspicious_keywords', [])), 5) * 0.5
        
        # Bonus for variety
        intel_types = sum([
            len(intelligence.get('bank_accounts', [])) > 0,
            len(intelligence.get('upi_ids', [])) > 0,
            len(intelligence.get('phishing_links', [])) > 0,
            len(intelligence.get('phone_numbers', [])) > 0
        ])
        if intel_types >= 3:
            score *= 1.2
        
        return round(score, 2)
```

### 10.5 Conversation Manager

```python
# app/agents/conversation.py
from typing import Dict, List
from enum import Enum

class ConversationStage(Enum):
    INITIAL_HOOK = 1
    ENGAGEMENT = 2
    INFORMATION_PROBE = 3
    RESISTANCE = 4
    GRADUAL_COMPLIANCE = 5
    INTELLIGENCE_MINING = 6
    PROLONGATION = 7

class ConversationManager:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def determine_stage(self, session: Dict) -> ConversationStage:
        """Determine conversation stage based on history"""
        msg_count = session['message_count']
        has_intel = any(len(v) > 0 for v in session['intelligence'].values())
        
        if msg_count <= 2:
            return ConversationStage.INITIAL_HOOK
        elif msg_count <= 4:
            return ConversationStage.ENGAGEMENT
        elif msg_count <= 6:
            return ConversationStage.INFORMATION_PROBE
        elif msg_count <= 8 and not has_intel:
            return ConversationStage.RESISTANCE
        elif msg_count <= 12:
            return ConversationStage.GRADUAL_COMPLIANCE if has_intel else ConversationStage.INTELLIGENCE_MINING
        else:
            return ConversationStage.PROLONGATION
    
    async def generate_response(
        self,
        persona: str,
        scammer_message: str,
        conversation_history: List[Dict],
        stage: ConversationStage,
        current_intelligence: Dict
    ) -> str:
        """Generate contextual victim response"""
        
        # Get persona system prompt
        from app.agents.personas import PersonaManager
        persona_manager = PersonaManager()
        persona_prompt = persona_manager.get_persona_prompt(persona)
        
        # Stage-specific tactics
        stage_tactics = self._get_stage_tactics(stage, current_intelligence)
        
        # Build conversation context
        history_text = "\n".join([
            f"{msg['sender']}: {msg['text']}"
            for msg in conversation_history[-5:]  # Last 5 messages
        ])
        
        # Intelligence context
        intel_context = self._build_intel_context(current_intelligence)
        
        full_prompt = f"""{persona_prompt}

CONVERSATION SO FAR:
{history_text}

LATEST SCAMMER MESSAGE:
"{scammer_message}"

CURRENT STAGE: {stage.name}
{stage_tactics}

{intel_context}

YOUR OBJECTIVES (in order):
1. Stay in character - be natural and believable
2. Keep scammer engaged - show interest, don't ghost
3. Extract information - bank accounts, UPI IDs, links
4. Don't seem suspicious - avoid being too eager or too resistant

IMPORTANT RULES:
- Keep response 1-3 sentences (natural SMS/chat length)
- Show appropriate emotion (worry, curiosity, confusion based on persona)
- Ask questions that prompt scammer to share details
- Mirror scammer's urgency but add slight hesitation
- If scammer shares payment details, ask clarifying questions
- Never break character or expose you're an AI

Generate ONLY the victim's reply. No explanations, no quotes, just the message text.
"""
        
        try:
            response = await self.llm.generate(
                prompt=full_prompt,
                temperature=0.7,  # Creative but consistent
                max_tokens=100    # Keep responses short
            )
            
            # Clean and validate response
            response = response.strip().strip('"').strip("'")
            
            # Ensure response quality
            if len(response) < 5 or len(response) > 250:
                return self._fallback_response(stage, persona)
            
            return response
            
        except Exception as e:
            return self._fallback_response(stage, persona)
    
    def _get_stage_tactics(self, stage: ConversationStage, intel: Dict) -> str:
        """Get tactics for current conversation stage"""
        
        tactics = {
            ConversationStage.INITIAL_HOOK: """
TACTICS: Show concern and ask why. Express worry but don't comply immediately.
Example: "What? Why is my account blocked? What happened?"
""",
            ConversationStage.ENGAGEMENT: """
TACTICS: Build trust, ask questions, show you're taking this seriously.
Example: "I see, that sounds serious. What do I need to do?"
""",
            ConversationStage.INFORMATION_PROBE: """
TACTICS: Scammer will ask for your info. Show slight hesitation, ask for their details first.
Example: "Before I share anything, can you confirm you're from the bank? What's your employee ID?"
""",
            ConversationStage.RESISTANCE: """
TACTICS: Show natural caution. Ask to verify through official channels.
Example: "I'm not sure about sharing that. Can I call the bank directly instead?"
""",
            ConversationStage.GRADUAL_COMPLIANCE: """
TACTICS: Slowly give in, but keep asking for their details too.
Example: "Okay, I trust you. But first, where should I send the payment? What's the account number?"
""",
            ConversationStage.INTELLIGENCE_MINING: """
TACTICS: Actively extract scammer's details. Ask for payment methods, links, contact info.
Example: "I'll do it right now. Send me the UPI ID again? And the link you mentioned?"
""",
            ConversationStage.PROLONGATION: """
TACTICS: Keep conversation alive. Report small technical issues, ask for clarification.
Example: "The link isn't working. Can you send another one? Or should I try a different payment method?"
"""
        }
        
        intel_status = "✓ Intelligence extracted" if any(len(v) > 0 for v in intel.values()) else "✗ No intelligence yet"
        return tactics.get(stage, "") + f"\n\n{intel_status}"
    
    def _build_intel_context(self, intel: Dict) -> str:
        """Build context about extracted intelligence"""
        extracted = []
        for key, values in intel.items():
            if values:
                extracted.append(f"{key}: {len(values)} items")
        
        if extracted:
            return f"EXTRACTED SO FAR: {', '.join(extracted)}\nContinue extracting more details."
        else:
            return "NO INTELLIGENCE YET: Focus on getting scammer to share bank account, UPI ID, or links."
    
    def _fallback_response(self, stage: ConversationStage, persona: str) -> str:
        """Fallback responses if LLM fails"""
        fallbacks = {
            ConversationStage.INITIAL_HOOK: "What happened? Why?",
            ConversationStage.ENGAGEMENT: "Can you explain more?",
            ConversationStage.INFORMATION_PROBE: "What details do you need?",
            ConversationStage.RESISTANCE: "I'm not sure about this. Is it safe?",
            ConversationStage.GRADUAL_COMPLIANCE: "Okay, what should I do next?",
            ConversationStage.INTELLIGENCE_MINING: "Where should I send it? Give me the details.",
            ConversationStage.PROLONGATION: "The link isn't working. Can you send again?"
        }
        return fallbacks.get(stage, "I understand. What should I do?")
```

### 10.6 GUVI Callback Handler

```python
# app/utils/callbacks.py
import httpx
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class GUVICallback:
    def __init__(self, callback_url: str):
        self.callback_url = callback_url
    
    async def send_final_result(
        self,
        session_id: str,
        scam_detected: bool,
        total_messages: int,
        intelligence: Dict,
        agent_notes: str
    ):
        """Send final intelligence report to GUVI endpoint"""
        
        payload = {
            "sessionId": session_id,
            "scamDetected": scam_detected,
            "totalMessagesExchanged": total_messages,
            "extractedIntelligence": {
                "bankAccounts": intelligence.get('bank_accounts', []),
                "upiIds": intelligence.get('upi_ids', []),
                "phishingLinks": intelligence.get('phishing_links', []),
                "phoneNumbers": intelligence.get('phone_numbers', []),
                "suspiciousKeywords": intelligence.get('suspicious_keywords', [])
            },
            "agentNotes": agent_notes
        }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    self.callback_url,
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.info(f"✓ Callback successful for session {session_id}")
                    return True
                else:
                    logger.error(f"✗ Callback failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"✗ Callback error for session {session_id}: {str(e)}")
            return False
```

### 10.7 Groq LLM Client

```python
# app/core/llm.py
from groq import AsyncGroq
import os
import logging

logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self, api_key: str):
        self.client = AsyncGroq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self.request_count = 0
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        response_format: str = None
    ) -> str:
        """Generate response from Groq"""
        
        try:
            self.request_count += 1
            
            # Prepare request parameters
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Add JSON mode if requested (for structured outputs)
            if response_format == "json":
                params["response_format"] = {"type": "json_object"}
            
            # Make API call
            response = await self.client.chat.completions.create(**params)
            
            # Extract text
            content = response.choices[0].message.content
            
            logger.info(f"Groq request #{self.request_count} completed. Tokens: {response.usage.total_tokens}")
            
            return content.strip()
            
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise
    
    async def generate_json(self, prompt: str, temperature: float = 0.1) -> str:
        """Generate JSON response specifically"""
        return await self.generate(
            prompt=prompt,
            temperature=temperature,
            response_format="json"
        )
```

### 10.8 Session Manager

```python
# app/core/session.py
from typing import Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(minutes=30)
    
    def get_or_create(self, session_id: str) -> Dict:
        """Get existing session or create new one"""
        
        # Clean up expired sessions first
        self._cleanup_expired()
        
        if session_id in self.sessions:
            logger.info(f"Retrieved existing session: {session_id}")
            return self.sessions[session_id]
        
        # Create new session
        session = {
            "session_id": session_id,
            "conversation_history": [],
            "scam_detected": False,
            "scam_confidence": 0.0,
            "scam_type": None,
            "persona": None,
            "intelligence": {
                "bank_accounts": [],
                "upi_ids": [],
                "phishing_links": [],
                "phone_numbers": [],
                "suspicious_keywords": []
            },
            "message_count": 0,
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
        
        self.sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")
        return session
    
    def update(self, session_id: str, session_data: Dict):
        """Update session data"""
        session_data['last_activity'] = datetime.now()
        self.sessions[session_id] = session_data
    
    def _cleanup_expired(self):
        """Remove sessions older than timeout"""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session['last_activity'] > self.session_timeout
        ]
        
        for sid in expired:
            del self.sessions[sid]
            logger.info(f"Cleaned up expired session: {sid}")
```

---

## 11. Deployment Checklist

### Pre-Deployment
- [ ] All dependencies in `requirements.txt`
- [ ] Environment variables configured
- [ ] Groq API key tested
- [ ] API secret key generated (use: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] Code tested locally with synthetic data

### Railway Deployment
- [ ] Create Railway account
- [ ] Install Railway CLI
- [ ] Initialize project: `railway init`
- [ ] Set environment variables
- [ ] Deploy: `railway up`
- [ ] Get public URL: `railway domain`
- [ ] Test health endpoint: `curl https://your-app.railway.app/health`
- [ ] Test chat endpoint with Postman/curl

### Post-Deployment
- [ ] Monitor logs: `railway logs`
- [ ] Test with 5+ synthetic conversations
- [ ] Verify GUVI callback triggers correctly
- [ ] Check response times (<3s)
- [ ] Monitor Groq usage (stay under free tier)

---

## 12. Monitoring & Debugging

### Logging Strategy

```python
# app/utils/logger.py
import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific log levels
    logging.getLogger("groq").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
```

### Key Metrics to Track

```python
# Add to main.py
metrics = {
    "total_sessions": 0,
    "scams_detected": 0,
    "average_messages_per_session": 0,
    "total_intelligence_extracted": 0,
    "groq_requests": 0,
    "average_response_time": 0
}

@app.get("/metrics")
async def get_metrics():
    return metrics
```

### Debug Mode

```python
# Enable verbose logging for development
if os.getenv("DEBUG", "false").lower() == "true":
    logging.getLogger().setLevel(logging.DEBUG)
```

---

## 13. Success Criteria Summary

| Criterion | Target | Priority |
|-----------|--------|----------|
| **Scam Detection Accuracy** | >90% true positive | Critical |
| **Engagement Duration** | 8-15 messages | High |
| **Intelligence Extraction** | >70% sessions with ≥1 intel | Critical |
| **API Response Time** | <3 seconds (P95) | High |
| **Groq Free Tier Compliance** | <14,400 req/day | Critical |
| **GUVI Callback Success** | 100% when session ends | Critical |
| **Persona Believability** | No obvious AI patterns | Medium |
| **System Uptime** | >99% during evaluation | High |

---

## 14. Appendices

### Appendix A: Sample Test Scenarios

```bash
# Scenario 1: Bank Fraud
curl -X POST https://your-app.railway.app/api/chat \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-bank-001",
    "message": {
      "sender": "scammer",
      "text": "Your SBI account XXXX1234 will be blocked due to KYC non-compliance. Update immediately by sending ₹1 to 9876543210@paytm",
      "timestamp": 1770005528731
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
  }'

# Expected: Scam detected, elderly_confused or tech_naive_parent persona, worried response

# Scenario 2: UPI Fraud Follow-up
curl -X POST https://your-app.railway.app/api/chat \
  -H "x-api-key": YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-bank-001",
    "message": {
      "sender": "scammer",
      "text": "Yes, pay ₹1 to verify. Send to winner2024@oksbi. Do it now to avoid penalty.",
      "timestamp": 1770005535000
    },
    "conversationHistory": [
      {"sender": "scammer", "text": "Your SBI account XXXX1234 will be blocked...", "timestamp": 1770005528731},
      {"sender": "user", "text": "Oh no! What should I do?", "timestamp": 1770005530000}
    ],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
  }'

# Expected: Extract "winner2024@oksbi", ask clarifying question, maintain persona
```

### Appendix B: Common Scam Patterns (India-specific)

| Scam Type | Common Phrases | Intelligence Target |
|-----------|----------------|---------------------|
| **Bank Fraud** | "KYC expired", "account blocked", "verify immediately" | Bank accounts, UPI IDs |
| **UPI Scam** | "won prize", "claim reward", "send ₹1 to verify" | UPI IDs (name@bank) |
| **Phishing** | "click link", "update details", "confirm account" | URLs, fake domains |
| **Tech Support** | "virus detected", "Microsoft support", "call immediately" | Phone numbers |
| **Job Scam** | "selected for job", "registration fee", "send documents" | Bank accounts, emails |
| **Investment** | "guaranteed returns", "limited offer", "double your money" | UPI IDs, bank accounts |

### Appendix C: Environment Variables Reference

```bash
# Required
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
API_SECRET_KEY=random_secret_key_32_chars_min
GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult

# Optional
PORT=8000
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false
SESSION_TIMEOUT_MINUTES=30
MAX_MESSAGES_PER_SESSION=15
INTELLIGENCE_SCORE_THRESHOLD=8
```

### Appendix D: Quick Troubleshooting Guide

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| **401 Unauthorized** | Wrong API key | Check x-api-key header matches API_SECRET_KEY |
| **Slow responses (>5s)** | Groq API latency | Optimize prompts, reduce max_tokens |
| **Rate limit errors** | Too many requests | Implement request queuing, add delays |
| **Intelligence not extracting** | LLM prompt issue | Verify JSON mode, check regex fallback |
| **Personas inconsistent** | Temperature too high | Lower to 0.6-0.7 for responses |
| **Scam not detected** | Confidence too low | Review detection prompt, lower threshold |
| **GUVI callback fails** | Network/URL issue | Check callback URL, verify payload format |
| **Memory leak** | Sessions not cleaning | Implement session expiry (already in code) |

---

## 15. Final Notes & Tips

### Development Tips for 3-Day Timeline

1. **Day 1 Focus**: Get basic API working and deployed early. Test with simple responses before adding complexity.

2. **Use Groq JSON Mode**: Enable `response_format={"type": "json_object"}` for all structured outputs (detection, extraction). This eliminates parsing errors.

3. **Start Simple**: Begin with 2 personas, expand later. Basic regex extraction is fine initially.

4. **Test Early, Test Often**: Deploy to Railway on Day 1 and test in production environment.

5. **Fallback Everything**: Have fallback responses, fallback extraction, fallback detection. Never let the API crash.

6. **Monitor Groq Usage**: Check Groq dashboard frequently to ensure you stay under free tier.

7. **Keep Prompts Short**: Shorter prompts = faster responses = more requests within rate limits.

8. **Log Everything**: You can't debug what you can't see. Log all decisions, extractions, and LLM calls.

### Cost Optimization Tactics

- **Combine Tasks**: One LLM call for detection + response + extraction instead of three separate calls
- **Cache Persona Prompts**: Don't recreate system prompts every time
- **Limit Context**: Only pass last 5 messages, not entire history
- **Smart Rate Limiting**: Buffer at 25 req/min instead of hitting 30 limit
- **Structured Outputs**: JSON mode reduces token usage vs asking for formatted text

### Winning Strategies

- **Intelligence Variety**: Extract multiple types (UPI + phone + link) scores higher than just one type
- **Natural Engagement**: Vary response lengths, occasional typos, emotion words increase believability
- **Gradual Extraction**: Don't get all intel in first exchange; spread over 8-12 messages
- **Strategic Questions**: Ask "Can you send the link again?" to get repeated intel = higher confidence
- **Callback Timing**: Send callback when intel score ≥8 OR message count =15, whichever comes first

---

## Document Version Control

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | Feb 3, 2026 | Initial PRD creation | AI Development Team |

---

**END OF PRD**

*This document provides comprehensive guidance for building an AI-powered honeypot system optimized for a 3-day hackathon timeline using Groq free tier and Railway deployment. Follow the implementation phases, use the code examples as templates, and prioritize the success criteria for maximum evaluation score.*