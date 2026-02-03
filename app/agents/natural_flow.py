"""
Natural Conversation Flow Manager for AI Honeypot.
Provides contextual instructions for natural conversation progression.
"""

import random
from typing import Dict, List


class NaturalConversationFlow:
    """Manages natural conversation progression."""
    
    def __init__(self):
        self.conversation_memory = {}
    
    def get_contextual_instructions(
        self,
        session: Dict,
        persona: Dict,
        message_number: int
    ) -> str:
        """Generate dynamic, context-aware instructions for LLM."""
        
        # Analyze conversation so far
        history = session.get("conversation_history", [])
        scammer_tactics = self._analyze_scammer_tactics(history)
        victim_state = self._determine_victim_state(session, message_number)
        
        instructions = f"""
CONVERSATION CONTEXT (Message #{message_number}):

SCAMMER TACTICS DETECTED:{scammer_tactics}

YOUR CURRENT EMOTIONAL STATE: {victim_state["emotion"]}
YOUR CURRENT UNDERSTANDING LEVEL: {victim_state["comprehension"]}

NATURAL RESPONSE GUIDELINES FOR THIS MESSAGE:
{self._get_message_specific_guidance(message_number, victim_state, persona)}

VARIATION REQUIREMENTS:
- This is message #{message_number} - your responses should feel different from earlier
- {self._get_variation_requirement(message_number, persona)}
- Balance: {victim_state["balance_instruction"]}

REMEMBER:
- Real people don't always understand everything immediately
- Real people sometimes forget what was said earlier
- Real people have varying moods and energy levels
- Real people make mistakes and correct themselves
"""
        
        return instructions
    
    def _analyze_scammer_tactics(self, history: List[Dict]) -> str:
        """Analyze what the scammer is doing."""
        scammer_messages = [msg for msg in history if msg.get("sender") == "scammer"]
        if not scammer_messages:
            return "\n- Initial contact - scammer is establishing trust"
        
        recent = scammer_messages[-1].get("text", "").lower()
        
        tactics = []
        if any(word in recent for word in ["urgent", "immediately", "now", "today"]):
            tactics.append("Using urgency tactics")
        
        if any(word in recent for word in ["account", "bank", "blocked", "suspended"]):
            tactics.append("Impersonating authority (bank)")
        
        if any(word in recent for word in ["send", "pay", "transfer", "upi"]):
            tactics.append("Requesting payment/details")
        
        if "http" in recent or "link" in recent or "click" in recent:
            tactics.append("Sharing phishing links")
        
        if any(word in recent for word in ["job", "selected", "salary", "offer"]):
            tactics.append("Job scam tactics")
        
        if any(word in recent for word in ["prize", "winner", "lottery", "won"]):
            tactics.append("Prize/lottery scam")
        
        if not tactics:
            tactics.append("Building trust / Information gathering")
        
        return "\n- " + "\n- ".join(tactics)
    
    def _determine_victim_state(self, session: Dict, message_number: int) -> Dict:
        """Determine victim's current psychological state."""
        has_intel = any(len(v) > 0 for v in session.get("intelligence", {}).values())
        
        if message_number <= 2:
            return {
                "emotion": "Confused / Concerned / Surprised",
                "comprehension": "Just learned about the issue",
                "balance_instruction": "Show initial reaction - confusion, worry, or curiosity"
            }
        elif message_number <= 5:
            return {
                "emotion": "Seeking clarity / Building trust or suspicion",
                "comprehension": "Understanding the situation but still questioning",
                "balance_instruction": "Ask clarifying questions, show you're trying to understand"
            }
        elif message_number <= 8:
            if has_intel:
                return {
                    "emotion": "Cautiously complying / Reluctant but convinced",
                    "comprehension": "Mostly understands but still has doubts",
                    "balance_instruction": "Show you're being persuaded but still ask for details"
                }
            else:
                return {
                    "emotion": "Skeptical / Hesitant",
                    "comprehension": "Understanding but not trusting",
                    "balance_instruction": "Express doubt, ask for proof or verification"
                }
        else:
            return {
                "emotion": "Compliant but occasionally confused",
                "comprehension": "Mostly onboard but details still confuse you",
                "balance_instruction": "Go along with it but ask for clarification on technical steps"
            }
    
    def _get_message_specific_guidance(
        self,
        message_number: int,
        victim_state: Dict,
        persona: Dict
    ) -> str:
        """Get specific guidance for this message number."""
        
        if message_number == 1:
            return """
- This is your FIRST response - show immediate emotional reaction
- Don't overthink it - real people react instinctively
- Short response is fine (even one word like "What?!" or "Why?")
- Express confusion, worry, or surprise naturally
"""
        
        elif message_number == 2:
            return """
- You're processing the information now
- Ask for clarification on what confused you
- Show that you're taking this seriously
- Can be slightly longer than first message
"""
        
        elif message_number in [3, 4, 5]:
            return """
- You're in the "understanding" phase
- Ask questions that help you grasp the situation
- Show mix of concern and curiosity
- This is where you might start asking about their process/details
"""
        
        elif message_number in [6, 7, 8]:
            return """
- You're being persuaded (or showing skepticism)
- If they've asked for payment/info: show slight hesitation but interest
- Good time to ask "How do I know this is real?" type questions
- But don't be TOO skeptical - stay convinceable
"""
        
        else:
            return """
- You've been talking a while - feel free to show fatigue or impatience
- Can ask "Wait, what was that again?" - real people lose track
- Mix compliance with occasional confusion
- Keep extracting their details: "Send me that link again?"
"""
    
    def _get_variation_requirement(self, message_number: int, persona: Dict) -> str:
        """Specific variation requirements for this message."""
        
        variations = [
            "Try a different sentence structure than your last message",
            "Vary your message length - don't be consistent",
            "If you used a question last time, try a statement this time (or vice versa)",
            "Change your opening style from previous messages",
            "Show a different aspect of your personality",
            "React differently than you did in earlier messages"
        ]
        
        persona_specific = {
            "elderly_confused": [
                "Don't start with 'oh dear' this time - try a different opening or no opening",
                "Vary between short confused questions and longer worried explanations",
                "Sometimes mention a specific family member, sometimes don't"
            ],
            "busy_professional": [
                "Alternate between very short (1-3 words) and slightly longer responses",
                "Mix heavy abbreviations with occasional full words",
                "Sometimes mention being busy, sometimes don't"
            ],
            "curious_student": [
                "Rotate through different slang terms - don't repeat the same ones",
                "Mix skeptical responses with interested ones",
                "Vary between all lowercase and occasional capital for emphasis"
            ],
            "tech_naive_parent": [
                "Vary between asking about safety and asking for step-by-step help",
                "Sometimes mention family, sometimes don't",
                "Mix formal language with confused questions"
            ],
            "desperate_job_seeker": [
                "Vary gratitude levels - sometimes very thankful, sometimes just eager",
                "Don't always mention being unemployed",
                "Mix formal language with eager compliance"
            ]
        }
        
        base_variation = random.choice(variations)
        persona_name = persona.get("name", "")
        
        if persona_name in persona_specific:
            persona_variation = random.choice(persona_specific[persona_name])
            return f"{base_variation}\n- {persona_variation}"
        
        return base_variation


def get_stage_guidance(message_number: int) -> str:
    """Get simple stage guidance for prompts."""
    if message_number <= 2:
        return "Show concern, ask why"
    elif message_number <= 5:
        return "Build trust, ask for their details"
    elif message_number <= 8:
        return "Show hesitation, request their payment info"
    elif message_number <= 12:
        return "Slowly comply, ask for account/UPI again"
    else:
        return "Report issues with their link, prolong conversation"
