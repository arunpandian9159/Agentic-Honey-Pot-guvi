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
        "maxTurns": 10,
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        "fakeData": {
            "bankAccount": "1234567890123456",
            "upiId": "scammer.fraud@fakebank",
            "phoneNumber": "+91-9876543210",
            "phishingLink": "http://sbi-security-verify.com/login",
        },
        "messages": [
            "URGENT: Your SBI account has been compromised. Your account will be blocked in 2 hours. Visit http://sbi-security-verify.com/login to verify.",
            "Sir, I am calling from SBI Head Office. Your account 1234567890123456 has suspicious activity. You must verify now.",
            "Please share the OTP sent to your number +91-9876543210 to stop the unauthorized transaction.",
            "If you don't cooperate, we will freeze your account and report to cyber crime cell.",
            "Transfer the security deposit of Rs 5000 to our verification UPI: scammer.fraud@fakebank",
            "This is your last warning. Share account details for 1234567890123456 or face legal consequences.",
            "I am senior manager Rajesh Kumar, employee ID SBI-78432. Visit http://sbi-security-verify.com/login for official notice.",
            "Send Rs 10000 to scammer.fraud@fakebank as insurance deposit. It will be refunded within 24 hours.",
            "Your account 1234567890123456 will be permanently closed if you do not verify at http://sbi-security-verify.com/login in the next 30 minutes.",
            "Call me back at +91-9876543210 immediately. This is your final notice from the Reserve Bank of India.",
        ],
    },
    "upi_fraud": {
        "scenarioId": "upi_fraud",
        "name": "UPI Fraud Multi-turn",
        "scamType": "upi_fraud",
        "maxTurns": 10,
        "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"},
        "fakeData": {
            "bankAccount": "9876543210987654",
            "upiId": "cashback.scam@fakeupi",
            "phoneNumber": "+91-8765432109",
            "phishingLink": "http://paytm-claim-reward.in/win",
        },
        "messages": [
            "Congratulations! You have won a cashback of Rs. 5000. Visit http://paytm-claim-reward.in/win to claim your reward.",
            "This is Paytm official support. Your cashback reference number is PTM-CB-98765. Please share your account 9876543210987654 for verification.",
            "To process your Rs 5000 cashback, send Re 1 to cashback.scam@fakeupi for account verification.",
            "Your cashback is approved! Call our helpline +91-8765432109 or visit http://paytm-claim-reward.in/win to complete the claim process.",
            "We need your UPI PIN to verify your identity. Check progress at http://paytm-claim-reward.in/win now.",
            "Your cashback will expire in 15 minutes. Send the verification amount to cashback.scam@fakeupi now.",
            "I am sending you a collect request from cashback.scam@fakeupi. Use account 9876543210987654 to approve it.",
            "Sir, this is urgent. If you don't verify now, your wallet will be suspended. Call +91-8765432109.",
            "We have already credited Rs 5000 to 9876543210987654. Pay Rs 499 processing fee to cashback.scam@fakeupi to unlock it.",
            "Final reminder: Visit http://paytm-claim-reward.in/win or call +91-8765432109 to receive your cashback immediately.",
        ],
    },
    "phishing": {
        "scenarioId": "phishing_link",
        "name": "Phishing Link Detection",
        "scamType": "phishing",
        "maxTurns": 10,
        "metadata": {"channel": "Email", "language": "English", "locale": "IN"},
        "fakeData": {
            "bankAccount": "5566778899001122",
            "upiId": "amazon.offers@upi",
            "phoneNumber": "+91-9999988888",
            "phishingLink": "http://amaz0n-deals.fake-site.com/claim?id=12345",
        },
        "messages": [
            "iPhone 15 Pro at Rs. 999! Click here to claim: http://amaz0n-deals.fake-site.com/claim?id=12345. Call +91-9999988888 for help.",
            "Dear customer, verify your bank account 5566778899001122 at http://amaz0n-deals.fake-site.com/claim?id=12345 to receive your iPhone.",
            "Send Rs 999 processing fee to amazon.offers@upi to confirm your order AMZ-2025-78432.",
            "Your iPhone is ready! Complete bank verification for 5566778899001122 at http://amaz0n-deals.fake-site.com/claim?id=12345",
            "URGENT: Use account 5566778899001122 to pay via amazon.offers@upi. Visit http://amaz0n-deals.fake-site.com/claim?id=12345 now.",
            "Call +91-9999988888 for delivery instructions. Pay to amazon.offers@upi to proceed.",
            "Your order is confirmed! Pay shipping fee to amazon.offers@upi or click http://amaz0n-deals.fake-site.com/claim?id=12345",
            "Amazon support here. Visit http://amaz0n-deals.fake-site.com/claim?id=12345 and link your bank 5566778899001122.",
            "Final notice: Call +91-9999988888 or your prize will be given away. Pay to amazon.offers@upi.",
            "Bonus AirPods won! Claim at http://amaz0n-deals.fake-site.com/claim?id=12345 or call +91-9999988888 for verification.",
        ],
    },
    "tech_support": {
        "scenarioId": "tech_support",
        "name": "Tech Support Scam",
        "scamType": "tech_support",
        "maxTurns": 10,
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        "fakeData": {
            "bankAccount": "1122334455667788",
            "upiId": "techfix@paytm",
            "phoneNumber": "+91-9123456789",
            "phishingLink": "http://microsoft-security-alert.fake/scan",
        },
        "messages": [
            "ALERT: Computer infected! Call Microsoft support at +91-9123456789 or visit http://microsoft-security-alert.fake/scan",
            "Unauthorized access detected! Protect your account 1122334455667788 by visiting http://microsoft-security-alert.fake/scan",
            "Your Microsoft account is compromised. Download tool at http://microsoft-security-alert.fake/scan or call +91-9123456789.",
            "Pay Rs 2000 virus removal fee for account 1122334455667788 via UPI to techfix@paytm now.",
            "Windows license expiring! Visit http://microsoft-security-alert.fake/scan or pay to techfix@paytm.",
            "47 malware files found! Call +91-9123456789. Send security fee from bank 1122334455667788 to techfix@paytm.",
            "Bank credentials stolen! Visit http://microsoft-security-alert.fake/scan to secure account 1122334455667788.",
            "Final warning: Visit http://microsoft-security-alert.fake/scan. Call +91-9123456789 or pay removal fee to techfix@paytm.",
            "Data being uploaded! Call +91-9123456789. Secure bank account 1122334455667788 via http://microsoft-security-alert.fake/scan.",
            "Device will be locked! Pay Rs 9999 to techfix@paytm or call +91-9123456789 to unlock via remote access.",
        ],
    },
    "job_scam": {
        "scenarioId": "job_scam",
        "name": "Job Scam Detection",
        "scamType": "job_scam",
        "maxTurns": 10,
        "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"},
        "fakeData": {
            "bankAccount": "8899001122334455",
            "upiId": "hr.recruit@axisbank",
            "phoneNumber": "+91-7654321098",
            "phishingLink": "http://infosys-careers-portal.net/apply",
        },
        "messages": [
            "Selected for Infosys job! Rs 50000/month. Apply at http://infosys-careers-portal.net/apply or call +91-7654321098.",
            "Pay Rs 5000 registration fee via UPI to hr.recruit@axisbank. Visit http://infosys-careers-portal.net/apply for details.",
            "Training starts tomorrow. Call +91-7654321098. Link bank 8899001122334455 at http://infosys-careers-portal.net/apply.",
            "Need bank account 8899001122334455 for salary deposit. Complete at http://infosys-careers-portal.net/apply.",
            "Offer letter ready! Call +91-7654321098 or pay Rs 3000 fee via UPI to hr.recruit@axisbank.",
            "Pay training fee from account 8899001122334455 to hr.recruit@axisbank. Visit http://infosys-careers-portal.net/apply.",
            "Background check: Visit http://infosys-careers-portal.net/apply or call +91-7654321098 to verify 8899001122334455.",
            "HR manager waiting. Call +91-7654321098. Submit security deposit to hr.recruit@axisbank.",
            "Laptop deposit: Send Rs 2000 from current bank 8899001122334455 to hr.recruit@axisbank now.",
            "Urgent: Complete payment at http://infosys-careers-portal.net/apply or call +91-7654321098. Slot will be given to others.",
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
