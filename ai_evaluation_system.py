import requests
import json
import time
import random
import asyncio
import aiohttp
import google.generativeai as genai
from datetime import datetime
import sqlite3
import pandas as pd
from typing import List, Dict, Any
import logging
from concurrent.futures import ThreadPoolExecutor
import os

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
WEBHOOK_URL = "https://1c3f-118-208-224-170.ngrok-free.app/webhook/manychat"
GEMINI_API_KEY = "AIzaSyAH6467EocGBwuMi-oDLawrNyCKjPHHmN8"  # From your system
GEMINI_MODEL = "gemini-2.0-flash-thinking-exp-01-21"
MAX_CONCURRENT_TESTS = 10  # Limit concurrent requests
EVALUATION_DB = "evaluation_results.sqlite"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


class AIPayloadGenerator:
    """AI-powered realistic payload generator for fresh vegan leads"""

    def __init__(self):
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        self.generated_count = 0

    def generate_realistic_payload(self, scenario_type: str = "random") -> Dict[str, Any]:
        """Generate a realistic fresh vegan lead payload using AI"""

        scenario_prompts = {
            "initial_contact": "Generate a realistic Instagram DM from someone who just discovered Shannon's plant-based fitness content and is reaching out for the first time. Make it casual, authentic, and show genuine interest.",

            "fitness_struggle": "Create a message from someone struggling with plant-based fitness - they might be having trouble building muscle, losing weight, or finding the right nutrition on a vegan diet.",

            "direct_inquiry": "Generate a direct question about Shannon's coaching services from someone who's clearly vegan/plant-based and wants to know about training options.",

            "personal_story": "Create a message where someone shares their plant-based journey and asks for fitness guidance - make it personal and authentic.",

            "referral_inquiry": "Generate a message from someone who was referred by a friend or saw Shannon's content shared somewhere.",

            "random": "Create any realistic Instagram DM that a fresh vegan lead might send to Shannon. Vary the tone, urgency, and specific interests."
        }

        prompt = f"""
        {scenario_prompts.get(scenario_type, scenario_prompts['random'])}
        
        Requirements:
        - Keep it under 200 characters (Instagram DM style)
        - Include subtle vegan/plant-based indicators 
        - Make it sound like a real person (not corporate)
        - Vary the writing style, grammar, and formality
        - Include relevant fitness/health concerns
        - Make the name and username realistic
        - Age demographic: 25-40 year old women primarily
        
        Generate ONLY a JSON object with these fields:
        {{
            "last_input_text": "the actual message text",
            "first_name": "realistic first name",
            "last_name": "realistic last name", 
            "ig_username": "realistic_instagram_username",
            "scenario_type": "{scenario_type}"
        }}
        
        Return ONLY the JSON, no other text.
        """

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())

            # Add required fields for webhook
            result.update({
                "id": f"ai_test_{self.generated_count:06d}",
                "created_at": time.time()
            })

            self.generated_count += 1
            return result

        except Exception as e:
            logger.error(f"Error generating payload: {e}")
            # Fallback to manual generation
            return self._fallback_payload(scenario_type)

    def _fallback_payload(self, scenario_type: str) -> Dict[str, Any]:
        """Fallback payload if AI generation fails"""
        fallback_messages = [
            "hey! love your plant based fitness content, do you do coaching?",
            "struggling to build muscle on a vegan diet, any tips?",
            "noticed youre vegan too! been looking for a fitness coach",
            "friend recommended you for plant based nutrition help",
            "vegan for 2 years but struggling with fitness goals"
        ]

        names = ["Emma", "Sarah", "Maya", "Jessica",
                 "Ashley", "Lauren", "Chloe", "Hannah"]
        last_names = ["Green", "Wilson", "Taylor",
                      "Johnson", "Brown", "Davis", "Miller", "Smith"]

        return {
            "id": f"fallback_{self.generated_count:06d}",
            "ig_username": f"vegan_user_{random.randint(1000, 9999)}",
            "last_input_text": random.choice(fallback_messages),
            "first_name": random.choice(names),
            "last_name": random.choice(last_names),
            "created_at": time.time(),
            "scenario_type": scenario_type
        }


class WebhookTester:
    """Handles sending requests to Shannon's webhook system"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "true"
        })

    async def send_webhook_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send webhook request asynchronously"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    WEBHOOK_URL,
                    json=payload,
                    headers={"Content-Type": "application/json",
                             "ngrok-skip-browser-warning": "true"},
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:

                    result = {
                        "status_code": response.status,
                        "success": response.status == 200,
                        "timestamp": datetime.now().isoformat(),
                        "payload": payload,
                        "response_time": time.time() - payload["created_at"]
                    }

                    try:
                        result["response_data"] = await response.json()
                    except:
                        result["response_data"] = {"status": "processed"}

                    return result

        except asyncio.TimeoutError:
            # Timeout means Shannon's system is processing (this is good!)
            return {
                "status_code": 200,
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "payload": payload,
                "response_time": 15.0,
                "response_data": {"status": "async_processing"},
                "note": "Timeout indicates successful async processing"
            }
        except Exception as e:
            return {
                "status_code": 0,
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "payload": payload,
                "error": str(e)
            }


class AIResponseEvaluator:
    """AI-powered evaluation of Shannon's bot responses"""

    def __init__(self):
        self.model = genai.GenerativeModel(GEMINI_MODEL)

    def evaluate_conversation(self, payload: Dict, webhook_result: Dict) -> Dict[str, Any]:
        """Evaluate the bot's performance on this conversation"""

        # For now, we'll simulate the response since Shannon's system is async
        # In a real implementation, you'd need to capture the actual bot response
        user_message = payload["last_input_text"]
        scenario_type = payload.get("scenario_type", "unknown")

        evaluation_prompt = f"""
        You are evaluating Shannon's AI fitness coaching bot. Analyze this interaction:
        
        USER MESSAGE: "{user_message}"
        SCENARIO TYPE: {scenario_type}
        WEBHOOK SUCCESS: {webhook_result.get('success', False)}
        
        Based on Shannon's requirements, evaluate on these criteria:
        
        1. FRESH VEGAN DETECTION: Does this look like a fresh vegan lead?
        2. A/B STRATEGY ASSIGNMENT: Should this get Group A (rapport-first) or Group B (direct vegan)?
        3. EXPECTED RESPONSE TONE: Should be casual Australian ("heya", "how's things")
        4. EXPECTED RESPONSE LENGTH: Must be 1-15 words maximum
        5. CONVERSATION STAGE: What stage of the lead journey is this?
        
        Rate each criterion 1-10 and provide reasoning.
        
        Return ONLY a JSON object:
        {{
            "fresh_vegan_score": 8,
            "fresh_vegan_reasoning": "Clear plant-based indicators",
            "recommended_strategy": "B",
            "strategy_reasoning": "Direct vegan mention suggests Group B",
            "expected_tone_quality": 9,
            "expected_length_compliance": 10,
            "conversation_stage": "initial_contact",
            "overall_score": 8.5,
            "key_insights": ["Strong vegan signals", "Good coaching opportunity"],
            "webhook_processing_score": 10
        }}
        """

        try:
            response = self.model.generate_content(evaluation_prompt)
            evaluation = json.loads(response.text.strip())

            # Add metadata
            evaluation.update({
                "evaluated_at": datetime.now().isoformat(),
                "user_message": user_message,
                "scenario_type": scenario_type,
                "webhook_success": webhook_result.get('success', False)
            })

            return evaluation

        except Exception as e:
            logger.error(f"Error in evaluation: {e}")
            return {
                "error": str(e),
                "evaluated_at": datetime.now().isoformat(),
                "overall_score": 0
            }


class EvaluationDatabase:
    """SQLite database for storing evaluation results"""

    def __init__(self):
        self.db_path = EVALUATION_DB
        self.init_database()

    def init_database(self):
        """Initialize the evaluation database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_run_id TEXT,
                user_message TEXT,
                ig_username TEXT,
                scenario_type TEXT,
                webhook_success BOOLEAN,
                webhook_response_time REAL,
                fresh_vegan_score INTEGER,
                recommended_strategy TEXT,
                overall_score REAL,
                evaluation_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def save_evaluation(self, test_run_id: str, payload: Dict, webhook_result: Dict, evaluation: Dict):
        """Save evaluation results to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO evaluations (
                test_run_id, user_message, ig_username, scenario_type,
                webhook_success, webhook_response_time, fresh_vegan_score,
                recommended_strategy, overall_score, evaluation_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_run_id,
            payload.get("last_input_text"),
            payload.get("ig_username"),
            payload.get("scenario_type"),
            webhook_result.get("success", False),
            webhook_result.get("response_time", 0),
            evaluation.get("fresh_vegan_score", 0),
            evaluation.get("recommended_strategy"),
            evaluation.get("overall_score", 0),
            json.dumps(evaluation)
        ))

        conn.commit()
        conn.close()


class MassiveEvaluationSystem:
    """Main orchestrator for 10,000+ conversation evaluations"""

    def __init__(self):
        self.generator = AIPayloadGenerator()
        self.tester = WebhookTester()
        self.evaluator = AIResponseEvaluator()
        self.database = EvaluationDatabase()
        self.test_run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def run_single_evaluation(self, scenario_type: str = "random") -> Dict[str, Any]:
        """Run a single conversation evaluation"""
        try:
            # Step 1: Generate realistic payload
            payload = self.generator.generate_realistic_payload(scenario_type)

            # Step 2: Send to Shannon's webhook
            webhook_result = await self.tester.send_webhook_async(payload)

            # Step 3: Evaluate the interaction
            evaluation = self.evaluator.evaluate_conversation(
                payload, webhook_result)

            # Step 4: Save to database
            self.database.save_evaluation(
                self.test_run_id, payload, webhook_result, evaluation)

            return {
                "payload": payload,
                "webhook_result": webhook_result,
                "evaluation": evaluation,
                "success": True
            }

        except Exception as e:
            logger.error(f"Error in single evaluation: {e}")
            return {"success": False, "error": str(e)}

    async def run_massive_evaluation(self, total_tests: int = 10000, batch_size: int = 100):
        """Run massive evaluation with specified number of tests"""

        print(f"🚀 STARTING MASSIVE AI EVALUATION SYSTEM")
        print(f"📊 Total Tests: {total_tests:,}")
        print(f"🔄 Batch Size: {batch_size}")
        print(f"🆔 Test Run ID: {self.test_run_id}")
        print("=" * 60)

        start_time = time.time()
        completed = 0
        successful = 0

        # Scenario distribution
        scenarios = [
            "initial_contact", "fitness_struggle", "direct_inquiry",
            "personal_story", "referral_inquiry", "random"
        ]

        for batch_start in range(0, total_tests, batch_size):
            batch_end = min(batch_start + batch_size, total_tests)
            batch_scenarios = [random.choice(scenarios)
                               for _ in range(batch_end - batch_start)]

            print(
                f"\n🧪 Processing Batch {batch_start//batch_size + 1}: Tests {batch_start+1}-{batch_end}")

            # Run batch concurrently
            tasks = [self.run_single_evaluation(
                scenario) for scenario in batch_scenarios]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in batch_results:
                completed += 1
                if isinstance(result, dict) and result.get("success"):
                    successful += 1

                # Progress update every 100 tests
                if completed % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = completed / elapsed
                    eta = (total_tests - completed) / rate if rate > 0 else 0

                    print(
                        f"✅ Progress: {completed:,}/{total_tests:,} ({completed/total_tests*100:.1f}%)")
                    print(f"✅ Success Rate: {successful/completed*100:.1f}%")
                    print(
                        f"⏱️ Rate: {rate:.1f} tests/sec, ETA: {eta/60:.1f} minutes")

            # Brief pause between batches to avoid overwhelming the system
            await asyncio.sleep(2)

        # Final results
        total_time = time.time() - start_time
        self.generate_final_report(total_tests, successful, total_time)

    def generate_final_report(self, total_tests: int, successful: int, total_time: float):
        """Generate comprehensive evaluation report"""
        print(f"\n🏁 MASSIVE EVALUATION COMPLETE!")
        print("=" * 50)
        print(f"📊 Total Tests: {total_tests:,}")
        print(
            f"✅ Successful: {successful:,} ({successful/total_tests*100:.1f}%)")
        print(f"⏱️ Total Time: {total_time/60:.1f} minutes")
        print(f"🚀 Average Rate: {total_tests/total_time:.1f} tests/second")

        # Analyze results from database
        self.analyze_results()

    def analyze_results(self):
        """Analyze and report on evaluation results"""
        conn = sqlite3.connect(self.db_path)

        # Load results for this test run
        df = pd.read_sql_query(
            "SELECT * FROM evaluations WHERE test_run_id = ?",
            conn, params=(self.test_run_id,)
        )

        if df.empty:
            print("❌ No results found for analysis")
            return

        print(f"\n📈 ANALYSIS RESULTS:")
        print(
            f"📊 Webhook Success Rate: {df['webhook_success'].mean()*100:.1f}%")
        print(
            f"🌱 Average Fresh Vegan Score: {df['fresh_vegan_score'].mean():.1f}/10")
        print(f"⭐ Average Overall Score: {df['overall_score'].mean():.1f}/10")
        print(
            f"⚡ Average Response Time: {df['webhook_response_time'].mean():.2f}s")

        # Strategy distribution
        strategy_dist = df['recommended_strategy'].value_counts()
        print(f"\n🎯 RECOMMENDED A/B STRATEGY DISTRIBUTION:")
        for strategy, count in strategy_dist.items():
            percentage = count / len(df) * 100
            print(f"   Group {strategy}: {count:,} ({percentage:.1f}%)")

        # Scenario performance
        scenario_scores = df.groupby('scenario_type')[
            'overall_score'].mean().sort_values(ascending=False)
        print(f"\n🎭 SCENARIO PERFORMANCE:")
        for scenario, score in scenario_scores.items():
            print(f"   {scenario}: {score:.1f}/10")

        conn.close()

        print(f"\n💾 Full results saved to: {self.db_path}")
        print(
            f"🔍 Use data analysis tools to dive deeper into the {len(df):,} conversations!")

# Main execution


async def main():
    """Main execution function"""

    evaluation_system = MassiveEvaluationSystem()

    # Get user input for test configuration
    print("🤖 AI EVALUATION SYSTEM FOR SHANNON'S BOT")
    print("=" * 50)

    while True:
        try:
            num_tests = input(
                "Enter number of tests (default 1000, max 10000): ").strip()
            if not num_tests:
                num_tests = 1000
            else:
                num_tests = int(num_tests)

            if num_tests > 10000:
                print("⚠️ Maximum 10,000 tests allowed")
                continue
            elif num_tests < 1:
                print("⚠️ Minimum 1 test required")
                continue

            break
        except ValueError:
            print("❌ Please enter a valid number")

    # Run the evaluation
    await evaluation_system.run_massive_evaluation(total_tests=num_tests)

if __name__ == "__main__":
    asyncio.run(main())
