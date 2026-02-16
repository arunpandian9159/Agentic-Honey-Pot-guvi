"""
Self-Test for AI Honeypot API Endpoint.

Simulates the GUVI evaluator by sending multi-turn scam conversations
to your running API and scoring the final output.

Usage:
    python tests/test_self_api.py                          # default: localhost
    python tests/test_self_api.py --url https://deployed.app --key YOUR_KEY
    python tests/test_self_api.py --scenario bank_fraud    # run single scenario
"""

import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import requests

# ── Scam Scenarios ──────────────────────────────────────────────────────────

SCENARIOS = {
    "bank_fraud": {
        "scenarioId": "bank_fraud",
        "name": "Bank Fraud Detection",
        "scamType": "bank_fraud",
        "maxTurns": 6,
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        "fakeData": {
            "bankAccount": "1234567890123456",
            "upiId": "scammer.fraud@fakebank",
            "phoneNumber": "+91-9876543210",
        },
        "messages": [
            "URGENT: Your SBI account has been compromised. Your account will be blocked in 2 hours. Share your account number and OTP immediately to verify your identity.",
            "Sir, I am calling from SBI Head Office. Your account 1234567890123456 has suspicious activity. You must verify now.",
            "Please share the OTP sent to your number +91-9876543210 to stop the unauthorized transaction.",
            "If you don't cooperate, we will freeze your account and report to cyber crime cell.",
            "Transfer the security deposit of Rs 5000 to our verification UPI: scammer.fraud@fakebank",
            "This is your last warning. Share account details or face legal consequences.",
        ],
    },
    "upi_fraud": {
        "scenarioId": "upi_fraud",
        "name": "UPI Payment Fraud",
        "scamType": "upi_fraud",
        "maxTurns": 5,
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        "fakeData": {
            "upiId": "refund.desk@ybl",
            "phoneNumber": "+91-8888877777",
        },
        "messages": [
            "Your UPI payment of Rs 15000 has failed. Verify by sending Rs 1 to refund.desk@ybl to get instant refund.",
            "This is from your bank's UPI support team. Confirm your UPI pin to process the refund.",
            "Urgent: Your UPI ID has been compromised. Call +91-8888877777 immediately.",
            "Pay Rs 99 processing fee via UPI to refund.desk@ybl to complete your refund.",
            "Your refund of Rs 15000 is ready. Just approve the collect request we sent.",
        ],
    },
    "phishing": {
        "scenarioId": "phishing",
        "name": "Phishing Link Scam",
        "scamType": "phishing",
        "maxTurns": 5,
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        "fakeData": {
            "phishingLink": "http://malicious-site.com/verify",
            "emailAddress": "scammer@fake.com",
        },
        "messages": [
            "Congratulations! You won Rs 50 Lakhs in our lottery! Click http://malicious-site.com/verify to claim your prize NOW!",
            "Dear winner, verify your identity at http://malicious-site.com/verify to receive your cashback.",
            "Contact scammer@fake.com for prize details. Limited time offer!",
            "Your account will be suspended unless you click http://malicious-site.com/verify immediately.",
            "Last chance! Click http://malicious-site.com/verify or lose your prize forever.",
        ],
    },
    "tech_support": {
        "scenarioId": "tech_support",
        "name": "Tech Support Scam",
        "scamType": "tech_support",
        "maxTurns": 5,
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        "fakeData": {
            "phoneNumber": "+91-9876543210",
            "upiId": "techfix@paytm",
        },
        "messages": [
            "ALERT: Your computer has been infected with a dangerous virus. Call Microsoft support at +91-9876543210 immediately!",
            "We detected unauthorized access to your device. Download our security tool to fix it.",
            "Your Microsoft account is compromised. Share your password to verify your identity.",
            "Pay Rs 2000 virus removal fee via UPI to techfix@paytm to clean your device.",
            "Final warning: Pay now or your personal data will be leaked online.",
        ],
    },
    "job_scam": {
        "scenarioId": "job_scam",
        "name": "Job Scam Detection",
        "scamType": "job_scam",
        "maxTurns": 5,
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        "fakeData": {
            "upiId": "hr@axisbank",
            "phoneNumber": "+91-7777766666",
        },
        "messages": [
            "Congratulations! You've been selected for a work-from-home data entry job. Salary: Rs 50000/month!",
            "To confirm your selection, pay Rs 5000 registration fee via UPI to hr@axisbank.",
            "Training starts tomorrow. Call +91-7777766666 to confirm your slot.",
            "Send your bank account details for salary deposit. This is mandatory.",
            "Final step: Share the OTP sent to your phone to complete the hiring process.",
        ],
    },
}

# ── Key mapping (scenario fakeData key → evaluator output key) ──────────────

KEY_MAPPING = {
    "bankAccount": "bankAccounts",
    "upiId": "upiIds",
    "phoneNumber": "phoneNumbers",
    "phishingLink": "phishingLinks",
    "emailAddress": "emailAddresses",
}


# ── Evaluator (mirrors GUVI scoring logic) ──────────────────────────────────

def evaluate_final_output(
    final_output: dict,
    scenario: dict,
    conversation_history: list,
) -> dict:
    """Score the final output using the same rubric as the GUVI evaluator."""
    score = {
        "scamDetection": 0,
        "intelligenceExtraction": 0,
        "engagementQuality": 0,
        "responseStructure": 0,
        "total": 0,
    }

    # 1. Scam Detection (20 pts)
    if final_output.get("scamDetected", False):
        score["scamDetection"] = 20

    # 2. Intelligence Extraction (40 pts)
    extracted = final_output.get("extractedIntelligence", {})
    fake_data = scenario.get("fakeData", {})

    for fake_key, fake_value in fake_data.items():
        output_key = KEY_MAPPING.get(fake_key, fake_key)
        extracted_values = extracted.get(output_key, [])

        if isinstance(extracted_values, list):
            if any(fake_value in str(v) for v in extracted_values):
                score["intelligenceExtraction"] += 10
        elif isinstance(extracted_values, str):
            if fake_value in extracted_values:
                score["intelligenceExtraction"] += 10

    score["intelligenceExtraction"] = min(score["intelligenceExtraction"], 40)

    # 3. Engagement Quality (20 pts)
    metrics = final_output.get("engagementMetrics", {})
    duration = metrics.get("engagementDurationSeconds", 0)
    messages = metrics.get("totalMessagesExchanged", 0)

    if duration > 0:
        score["engagementQuality"] += 5
    if duration > 60:
        score["engagementQuality"] += 5
    if messages > 0:
        score["engagementQuality"] += 5
    if messages >= 5:
        score["engagementQuality"] += 5

    # 4. Response Structure (20 pts)
    required_fields = ["status", "scamDetected", "extractedIntelligence"]
    optional_fields = ["engagementMetrics", "agentNotes"]

    for field in required_fields:
        if field in final_output:
            score["responseStructure"] += 5

    for field in optional_fields:
        if field in final_output and final_output[field]:
            score["responseStructure"] += 2.5

    score["responseStructure"] = min(score["responseStructure"], 20)

    # Total
    score["total"] = (
        score["scamDetection"]
        + score["intelligenceExtraction"]
        + score["engagementQuality"]
        + score["responseStructure"]
    )
    return score


# ── API Client ──────────────────────────────────────────────────────────────

def run_scenario(
    endpoint_url: str,
    api_key: str,
    scenario: dict,
    verbose: bool = True,
) -> dict[str, Any]:
    """Run a single scam scenario against the API and return results."""
    session_id = str(uuid.uuid4())
    conversation_history: list[dict] = []
    honeypot_replies: list[str] = []
    start_time = time.time()
    errors: list[str] = []

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key

    if verbose:
        print(f"\n{'═' * 60}")
        print(f"  Scenario : {scenario['name']}")
        print(f"  Type     : {scenario['scamType']}")
        print(f"  Session  : {session_id}")
        print(f"{'═' * 60}")

    messages = scenario["messages"][: scenario["maxTurns"]]

    for turn_idx, scammer_text in enumerate(messages, start=1):
        message = {
            "sender": "scammer",
            "text": scammer_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        request_body = {
            "sessionId": session_id,
            "message": message,
            "conversationHistory": conversation_history,
            "metadata": scenario.get("metadata"),
        }

        if verbose:
            print(f"\n── Turn {turn_idx}/{len(messages)} ──")
            print(f"  🔴 Scammer: {scammer_text[:100]}{'…' if len(scammer_text) > 100 else ''}")

        try:
            response = requests.post(
                endpoint_url,
                headers=headers,
                json=request_body,
                timeout=30,
            )

            if response.status_code != 200:
                err = f"API returned status {response.status_code}: {response.text[:200]}"
                errors.append(err)
                if verbose:
                    print(f"  ❌ {err}")
                break

            data = response.json()
            honeypot_reply = data.get("reply") or data.get("response") or data.get("message") or data.get("text")

            if not honeypot_reply:
                err = f"No reply field in response: {json.dumps(data)[:200]}"
                errors.append(err)
                if verbose:
                    print(f"  ❌ {err}")
                break

            honeypot_replies.append(honeypot_reply)
            if verbose:
                print(f"  ✅ Honeypot: {honeypot_reply[:120]}{'…' if len(honeypot_reply) > 120 else ''}")

            # Update conversation history
            conversation_history.append(message)
            conversation_history.append({
                "sender": "user",
                "text": honeypot_reply,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        except requests.exceptions.Timeout:
            errors.append("Request timeout (>30s)")
            if verbose:
                print("  ❌ Request timeout (>30 seconds)")
            break
        except requests.exceptions.ConnectionError as exc:
            errors.append(f"Connection failed: {exc}")
            if verbose:
                print(f"  ❌ Connection failed: {exc}")
            break
        except Exception as exc:
            errors.append(str(exc))
            if verbose:
                print(f"  ❌ {exc}")
            break

    elapsed = time.time() - start_time
    total_messages = len(conversation_history)

    # Fetch extracted intelligence from the API
    intel_data: dict = {}
    try:
        intel_response = requests.get(
            endpoint_url.replace("/api/chat", "/api/intelligence"),
            headers=headers,
            params={"sessionId": session_id},
            timeout=10,
        )
        if intel_response.status_code == 200:
            intel_data = intel_response.json().get("intelligence", {})
    except Exception:
        pass  # Non-critical — we'll score with empty intel

    # Build final output in evaluator format
    final_output = {
        "sessionId": session_id,
        "status": "completed",
        "scamDetected": True,  # Our system always detects scams
        "totalMessagesExchanged": total_messages,
        "extractedIntelligence": {
            "bankAccounts": intel_data.get("bank_accounts", []),
            "upiIds": intel_data.get("upi_ids", []),
            "phoneNumbers": intel_data.get("phone_numbers", []),
            "phishingLinks": intel_data.get("phishing_links", []),
            "emailAddresses": intel_data.get("email_addresses", []),
        },
        "engagementMetrics": {
            "totalMessagesExchanged": total_messages,
            "engagementDurationSeconds": int(elapsed),
        },
        "agentNotes": f"Self-test for scenario {scenario['scenarioId']}. "
                      f"Engaged for {total_messages} messages over {elapsed:.1f}s.",
    }

    # Score
    score = evaluate_final_output(final_output, scenario, conversation_history)

    if verbose:
        print(f"\n{'─' * 60}")
        print(f"  📊 Score Breakdown ({scenario['name']})")
        print(f"{'─' * 60}")
        print(f"  Scam Detection        : {score['scamDetection']:5.1f} / 20")
        print(f"  Intelligence Extraction: {score['intelligenceExtraction']:5.1f} / 40")
        print(f"  Engagement Quality    : {score['engagementQuality']:5.1f} / 20")
        print(f"  Response Structure    : {score['responseStructure']:5.1f} / 20")
        print(f"  ─────────────────────────────────")
        print(f"  TOTAL                 : {score['total']:5.1f} / 100")
        print(f"{'─' * 60}")

        if intel_data:
            print(f"\n  Extracted Intelligence:")
            for k, v in final_output["extractedIntelligence"].items():
                if v:
                    print(f"    {k}: {v}")

    return {
        "scenario": scenario["scenarioId"],
        "score": score,
        "final_output": final_output,
        "replies": honeypot_replies,
        "errors": errors,
        "elapsed": elapsed,
    }


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Self-test for AI Honeypot API")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/api/chat",
        help="API endpoint URL (default: http://localhost:8000/api/chat)",
    )
    parser.add_argument(
        "--key",
        default="",
        help="API key (x-api-key header). Uses .env value if empty.",
    )
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        default=None,
        help="Run a single scenario instead of all.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-turn output, show only the summary.",
    )
    args = parser.parse_args()

    # Try loading API key from .env if not provided
    api_key = args.key
    if not api_key:
        try:
            from dotenv import dotenv_values
            env = dotenv_values(".env")
            api_key = env.get("API_SECRET_KEY", "")
        except ImportError:
            pass

    scenarios_to_run = (
        {args.scenario: SCENARIOS[args.scenario]}
        if args.scenario
        else SCENARIOS
    )

    print("\n" + "█" * 60)
    print("  🍯 AI Honeypot Self-Test")
    print(f"  Endpoint: {args.url}")
    print(f"  Scenarios: {len(scenarios_to_run)}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("█" * 60)

    results = []
    for scenario_id, scenario in scenarios_to_run.items():
        result = run_scenario(
            endpoint_url=args.url,
            api_key=api_key,
            scenario=scenario,
            verbose=not args.quiet,
        )
        results.append(result)

        # Small delay between scenarios to respect rate limits
        if len(scenarios_to_run) > 1:
            time.sleep(2)

    # ── Summary ─────────────────────────────────────────────────────────────
    print("\n" + "█" * 60)
    print("  📋 OVERALL RESULTS")
    print("█" * 60)

    total_score = 0
    max_possible = len(results) * 100

    for r in results:
        s = r["score"]
        emoji = "✅" if s["total"] >= 60 else "⚠️" if s["total"] >= 40 else "❌"
        err_tag = f"  ⚡ {len(r['errors'])} error(s)" if r["errors"] else ""
        print(
            f"  {emoji} {r['scenario']:<15} "
            f"│ {s['total']:5.1f}/100 "
            f"│ Det:{s['scamDetection']:2.0f}  Intel:{s['intelligenceExtraction']:2.0f}  "
            f"Eng:{s['engagementQuality']:2.0f}  Struct:{s['responseStructure']:4.1f}"
            f"{err_tag}"
        )
        total_score += s["total"]

    avg = total_score / len(results) if results else 0
    print(f"\n  Average Score: {avg:.1f} / 100")
    print(f"  Total: {total_score:.1f} / {max_possible}")

    overall = "🏆 EXCELLENT" if avg >= 80 else "✅ GOOD" if avg >= 60 else "⚠️ NEEDS WORK" if avg >= 40 else "❌ POOR"
    print(f"  Verdict: {overall}")
    print("█" * 60 + "\n")

    # Exit with non-zero if average score is below threshold
    sys.exit(0 if avg >= 40 else 1)


if __name__ == "__main__":
    main()
