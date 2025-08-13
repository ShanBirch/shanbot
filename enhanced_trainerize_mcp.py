#!/usr/bin/env python3
"""
Enhanced Trainerize MCP Tool - Zero Cost Alternative to $250/month API
Provides near-API performance using advanced Selenium automation
"""

import asyncio
import json
import logging
import os
import time
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import pickle
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import google.generativeai as genai

# You'll need to install: pip install mcp-server
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    print("MCP not available. Running in standalone mode.")
    MCP_AVAILABLE = False
    # Create dummy TextContent for type hints when MCP is not available

    class TextContent:
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text


class EnhancedTrainerizeMCP:
    """
    Enhanced Selenium-based Trainerize automation with MCP interface
    Zero cost alternative to expensive API access
    """

    def __init__(self, gemini_api_key: str, max_browsers: int = 3):
        if MCP_AVAILABLE:
            self.server = Server("enhanced-trainerize")

        self.gemini_api_key = gemini_api_key
        self.max_browsers = max_browsers
        self.driver_pool = []
        self.driver_states = {}
        self.cache_dir = Path("trainerize_cache")
        self.cache_dir.mkdir(exist_ok=True)

        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel(
            'gemini-2.0-flash-thinking-exp-01-21')

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        if MCP_AVAILABLE:
            self.setup_tools()

    def setup_tools(self):
        """Register all MCP tools for Trainerize automation"""

        @self.server.call_tool()
        async def initialize_browser_pool(username: str, password: str) -> List[TextContent]:
            """Initialize multiple browser instances with login"""
            return await self._initialize_browser_pool(username, password)

        @self.server.call_tool()
        async def extract_client_data(client_name: str, data_types: str, use_cache: bool = True) -> List[TextContent]:
            """Extract comprehensive client data with fallback strategies"""
            return await self._extract_client_data(client_name, data_types.split(','), use_cache)

        @self.server.call_tool()
        async def parallel_client_analysis(client_list: str, analysis_type: str) -> List[TextContent]:
            """Analyze multiple clients in parallel using browser pool"""
            return await self._parallel_client_analysis(client_list, analysis_type)

        @self.server.call_tool()
        async def comprehensive_client_report(client_name: str, days_back: int = 30) -> List[TextContent]:
            """Generate comprehensive client progress report"""
            return await self._comprehensive_client_report(client_name, days_back)

        @self.server.call_tool()
        async def cleanup_browsers() -> List[TextContent]:
            """Clean up all browser instances"""
            return await self._cleanup_browsers()

    async def _initialize_browser_pool(self, username: str, password: str) -> List[TextContent]:
        """Initialize multiple browser instances for parallel processing"""
        try:
            self.logger.info(
                f"Initializing {self.max_browsers} browser instances...")

            success_count = 0
            for i in range(self.max_browsers):
                try:
                    driver = self._create_browser_instance(f"instance_{i}")
                    if await self._login_browser(driver, username, password):
                        self.driver_pool.append(driver)
                        self.driver_states[id(driver)] = {
                            'logged_in': True,
                            'available': True,
                            'current_client': None,
                            'last_activity': datetime.now(),
                            'instance_id': f"instance_{i}"
                        }
                        success_count += 1
                        self.logger.info(
                            f"Browser instance {i} initialized successfully")
                    else:
                        driver.quit()
                        self.logger.error(
                            f"Failed to login browser instance {i}")
                except Exception as e:
                    self.logger.error(
                        f"Error creating browser instance {i}: {e}")

            return [TextContent(
                type="text",
                text=f"Successfully initialized {success_count}/{self.max_browsers} browser instances"
            )]

        except Exception as e:
            self.logger.error(f"Error initializing browser pool: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    def _create_browser_instance(self, instance_id: str) -> webdriver.Chrome:
        """Create a single browser instance with optimized settings"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--silent")
        chrome_options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Create unique temp directory for each instance
        temp_dir = tempfile.mkdtemp(prefix=f"trainerize_{instance_id}_")
        chrome_options.add_argument(f"--user-data-dir={temp_dir}")

        # Use your existing ChromeDriver path
        chromedriver_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chromedriver-137\chromedriver-win64\chromedriver.exe"
        service = ChromeService(executable_path=chromedriver_path)

        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)

        return driver

    async def _login_browser(self, driver: webdriver.Chrome, username: str, password: str) -> bool:
        """Login a browser instance to Trainerize"""
        try:
            driver.get("https://www.trainerize.com/login.aspx")
            wait = WebDriverWait(driver, 20)

            # First email entry
            email_field = wait.until(
                EC.presence_of_element_located((By.ID, "t_email")))
            email_field.clear()
            email_field.send_keys(username)

            find_me_button = driver.find_element(
                By.CLASS_NAME, "tz-button--secondary")
            find_me_button.click()
            time.sleep(3)

            # Second login page - try multiple selectors
            email_selectors = [
                (By.ID, "emailInput"),
                (By.CSS_SELECTOR, "input[placeholder='Email']"),
                (By.CSS_SELECTOR, "input[type='email']")
            ]

            email_field_second = None
            for selector_type, selector_value in email_selectors:
                try:
                    email_field_second = wait.until(
                        EC.element_to_be_clickable((selector_type, selector_value)))
                    break
                except TimeoutException:
                    continue

            if not email_field_second:
                return False

            email_field_second.clear()
            email_field_second.send_keys(username)

            # Password field
            password_selectors = [
                (By.ID, "passInput"),
                (By.CSS_SELECTOR, "input[type='password']")
            ]

            password_field = None
            for selector_type, selector_value in password_selectors:
                try:
                    password_field = driver.find_element(
                        selector_type, selector_value)
                    break
                except NoSuchElementException:
                    continue

            if not password_field:
                return False

            password_field.clear()
            password_field.send_keys(password)

            # Sign in button
            sign_in_selectors = [
                (By.CSS_SELECTOR, "[data-testid='signIn-button']"),
                (By.XPATH, "//button[contains(text(), 'SIGN IN')]"),
                (By.CSS_SELECTOR, "button[type='submit']")
            ]

            sign_in_button = None
            for selector_type, selector_value in sign_in_selectors:
                try:
                    sign_in_button = wait.until(
                        EC.element_to_be_clickable((selector_type, selector_value)))
                    break
                except TimeoutException:
                    continue

            if not sign_in_button:
                return False

            driver.execute_script("arguments[0].click();", sign_in_button)
            time.sleep(5)

            # Verify login success
            current_url = driver.current_url
            return "dashboard" in current_url.lower() or "clients" in current_url.lower()

        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False

    async def _extract_client_data(self, client_name: str, data_types: List[str], use_cache: bool) -> List[TextContent]:
        """Extract client data using multiple fallback strategies"""
        try:
            # Check cache first
            if use_cache:
                cached_data = self._get_cached_data(client_name, data_types)
                if cached_data:
                    return [TextContent(type="text", text=f"Cache hit: {json.dumps(cached_data, indent=2)}")]

            # Get available browser
            driver = self._get_available_browser()
            if not driver:
                return [TextContent(type="text", text="No available browser instances")]

            try:
                # Navigate to client
                if not await self._navigate_to_client(driver, client_name):
                    return [TextContent(type="text", text=f"Failed to navigate to client: {client_name}")]

                extracted_data = {}

                # Extract each data type
                for data_type in data_types:
                    self.logger.info(
                        f"Extracting {data_type} for {client_name}")

                    # Try screenshot analysis for graphs
                    if data_type in ['bodyweight', 'nutrition', 'sleep', 'steps']:
                        result = await self._extract_via_screenshot(driver, data_type)
                        if result and result != "No data":
                            extracted_data[data_type] = result
                            continue

                    # Try DOM extraction
                    result = await self._extract_via_dom(driver, data_type)
                    if result and result != "No data":
                        extracted_data[data_type] = result
                    else:
                        extracted_data[data_type] = "Extraction failed"

                # Cache the results
                if use_cache:
                    self._cache_data(client_name, extracted_data)

                return [TextContent(type="text", text=json.dumps(extracted_data, indent=2))]

            finally:
                # Always release browser
                self._release_browser(driver)

        except Exception as e:
            self.logger.error(f"Error extracting client data: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _extract_via_screenshot(self, driver: webdriver.Chrome, data_type: str) -> str:
        """Extract data using screenshot analysis"""
        try:
            # Navigate to appropriate section
            navigation_success = False
            if data_type == 'bodyweight':
                navigation_success = await self._navigate_to_bodyweight_graph(driver)
            elif data_type == 'nutrition':
                navigation_success = await self._navigate_to_nutrition_graph(driver)
            elif data_type == 'sleep':
                navigation_success = await self._navigate_to_sleep_graph(driver)
            elif data_type == 'steps':
                navigation_success = await self._navigate_to_steps_graph(driver)

            if not navigation_success:
                return "Navigation failed"

            # Take screenshot
            screenshot_path = self._take_screenshot(driver, data_type)
            if not screenshot_path:
                return "Screenshot failed"

            try:
                # Analyze with Gemini
                analysis = await self._analyze_screenshot_with_gemini(screenshot_path, data_type)
                return analysis
            finally:
                # Clean up screenshot
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)

        except Exception as e:
            self.logger.error(f"Screenshot extraction failed: {e}")
            return f"Error: {str(e)}"

    async def _extract_via_dom(self, driver: webdriver.Chrome, data_type: str) -> str:
        """Extract data directly from DOM elements"""
        try:
            # Simple DOM extraction for basic data
            if data_type == 'workout_count':
                elements = driver.find_elements(
                    By.XPATH, "//span[contains(text(), 'workout')]")
                if elements:
                    return elements[0].text

            return "No DOM data found"

        except Exception as e:
            return f"DOM extraction error: {str(e)}"

    def _take_screenshot(self, driver: webdriver.Chrome, data_type: str) -> Optional[str]:
        """Take screenshot for analysis"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{data_type}_{timestamp}.png"
            filepath = self.cache_dir / filename

            # Scroll to ensure graph is visible
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)

            driver.save_screenshot(str(filepath))
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Screenshot error: {e}")
            return None

    async def _analyze_screenshot_with_gemini(self, screenshot_path: str, data_type: str) -> str:
        """Analyze screenshot using Gemini Vision"""
        try:
            with open(screenshot_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()

            prompts = {
                'bodyweight': "Analyze this bodyweight graph. Extract starting weight, current weight, trend, and any numerical data visible.",
                'nutrition': "Analyze this nutrition graph. Extract calories, protein, carbs, fats data for recent days.",
                'sleep': "Analyze this sleep graph. Extract sleep hours and patterns for recent days.",
                'steps': "Analyze this steps graph. Extract daily step counts and averages."
            }

            prompt = prompts.get(
                data_type, f"Analyze this {data_type} graph from Trainerize fitness app.")

            response = self.gemini_model.generate_content([
                prompt,
                {"inline_data": {"mime_type": "image/png", "data": image_data}}
            ])

            return response.text

        except Exception as e:
            return f"Screenshot analysis error: {str(e)}"

    # Navigation methods (simplified versions of your existing code)
    async def _navigate_to_client(self, driver: webdriver.Chrome, client_name: str) -> bool:
        """Navigate to specific client"""
        try:
            # Navigate to clients page
            driver.get("https://www.trainerize.com/app/trainer/clients")
            wait = WebDriverWait(driver, 10)

            # Search for client
            search_box = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[placeholder*='Search']")))
            search_box.clear()
            search_box.send_keys(client_name)
            time.sleep(2)

            # Click on client
            client_link = wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//a[contains(text(), '{client_name}')]")))
            client_link.click()
            time.sleep(3)

            return True

        except Exception as e:
            self.logger.error(f"Navigation to client failed: {e}")
            return False

    async def _navigate_to_bodyweight_graph(self, driver: webdriver.Chrome) -> bool:
        """Navigate to bodyweight graph"""
        try:
            # Click on Progress tab
            progress_tab = driver.find_element(
                By.XPATH, "//a[contains(text(), 'Progress')]")
            progress_tab.click()
            time.sleep(2)

            # Click on bodyweight/biometrics
            bodyweight_section = driver.find_element(
                By.XPATH, "//a[contains(text(), 'Biometrics')]")
            bodyweight_section.click()
            time.sleep(3)

            return True

        except Exception as e:
            self.logger.error(f"Navigation to bodyweight graph failed: {e}")
            return False

    async def _navigate_to_nutrition_graph(self, driver: webdriver.Chrome) -> bool:
        """Navigate to nutrition graph"""
        try:
            # Click on Progress tab then Nutrition
            progress_tab = driver.find_element(
                By.XPATH, "//a[contains(text(), 'Progress')]")
            progress_tab.click()
            time.sleep(2)

            nutrition_section = driver.find_element(
                By.XPATH, "//a[contains(text(), 'Nutrition')]")
            nutrition_section.click()
            time.sleep(3)

            return True

        except Exception as e:
            self.logger.error(f"Navigation to nutrition graph failed: {e}")
            return False

    async def _navigate_to_sleep_graph(self, driver: webdriver.Chrome) -> bool:
        """Navigate to sleep graph"""
        try:
            # Similar navigation pattern
            progress_tab = driver.find_element(
                By.XPATH, "//a[contains(text(), 'Progress')]")
            progress_tab.click()
            time.sleep(2)

            sleep_section = driver.find_element(
                By.XPATH, "//a[contains(text(), 'Sleep')]")
            sleep_section.click()
            time.sleep(3)

            return True

        except Exception as e:
            self.logger.error(f"Navigation to sleep graph failed: {e}")
            return False

    async def _navigate_to_steps_graph(self, driver: webdriver.Chrome) -> bool:
        """Navigate to steps graph"""
        try:
            progress_tab = driver.find_element(
                By.XPATH, "//a[contains(text(), 'Progress')]")
            progress_tab.click()
            time.sleep(2)

            steps_section = driver.find_element(
                By.XPATH, "//a[contains(text(), 'Activity')]")
            steps_section.click()
            time.sleep(3)

            return True

        except Exception as e:
            self.logger.error(f"Navigation to steps graph failed: {e}")
            return False

    # Browser pool management
    def _get_available_browser(self) -> Optional[webdriver.Chrome]:
        """Get an available browser from the pool"""
        for driver in self.driver_pool:
            driver_id = id(driver)
            if driver_id in self.driver_states:
                state = self.driver_states[driver_id]
                if state.get('available', True):
                    state['available'] = False
                    state['last_activity'] = datetime.now()
                    return driver
        return None

    def _release_browser(self, driver: webdriver.Chrome):
        """Release browser back to pool"""
        driver_id = id(driver)
        if driver_id in self.driver_states:
            self.driver_states[driver_id]['available'] = True
            self.driver_states[driver_id]['current_client'] = None

    # Caching methods
    def _get_cached_data(self, client_name: str, data_types: List[str]) -> Optional[dict]:
        """Retrieve cached data if available and fresh"""
        try:
            cache_key = self._generate_cache_key(client_name, data_types)
            cache_file = self.cache_dir / f"{cache_key}.pkl"

            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)

                # Check if cache is still fresh (30 minutes)
                if datetime.now() - cached_data['timestamp'] < timedelta(minutes=30):
                    self.logger.info(f"Cache hit for {client_name}")
                    return cached_data['data']
                else:
                    cache_file.unlink()

            return None

        except Exception as e:
            self.logger.error(f"Cache retrieval error: {e}")
            return None

    def _cache_data(self, client_name: str, data: dict):
        """Cache extracted data"""
        try:
            cache_key = self._generate_cache_key(
                client_name, list(data.keys()))
            cache_file = self.cache_dir / f"{cache_key}.pkl"

            cache_data = {
                'timestamp': datetime.now(),
                'client_name': client_name,
                'data': data
            }

            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)

            self.logger.info(f"Data cached for {client_name}")

        except Exception as e:
            self.logger.error(f"Cache storage error: {e}")

    def _generate_cache_key(self, client_name: str, data_types: List[str]) -> str:
        """Generate unique cache key"""
        key_string = f"{client_name}_{sorted(data_types)}"
        return hashlib.md5(key_string.encode()).hexdigest()

    async def _parallel_client_analysis(self, client_list: str, analysis_type: str) -> List[TextContent]:
        """Analyze multiple clients in parallel"""
        try:
            clients = json.loads(client_list)
            results = []

            # Process clients in batches based on available browsers
            batch_size = len(self.driver_pool)
            for i in range(0, len(clients), batch_size):
                batch = clients[i:i + batch_size]
                batch_results = []

                for j, client in enumerate(batch):
                    if j < len(self.driver_pool):
                        driver = self.driver_pool[j]
                        try:
                            result = await self._analyze_single_client(driver, client, analysis_type)
                            batch_results.append({
                                'client': client,
                                'status': 'success',
                                'data': result
                            })
                        except Exception as e:
                            batch_results.append({
                                'client': client,
                                'status': 'error',
                                'error': str(e)
                            })

                results.extend(batch_results)

            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        except Exception as e:
            return [TextContent(type="text", text=f"Parallel analysis error: {str(e)}")]

    async def _analyze_single_client(self, driver: webdriver.Chrome, client_name: str, analysis_type: str) -> dict:
        """Analyze a single client"""
        try:
            await self._navigate_to_client(driver, client_name)

            if analysis_type == "weekly_summary":
                data = await self._extract_client_data(client_name, ['bodyweight', 'nutrition', 'workouts'], False)
                return {"type": "weekly_summary", "data": data[0].text if data else "No data"}
            else:
                return {"error": f"Unknown analysis type: {analysis_type}"}

        except Exception as e:
            return {"error": str(e)}

    async def _comprehensive_client_report(self, client_name: str, days_back: int) -> List[TextContent]:
        """Generate comprehensive client report"""
        try:
            # Get all available data types
            data_types = ['bodyweight', 'nutrition', 'sleep', 'steps']
            comprehensive_data = {}

            for data_type in data_types:
                try:
                    result = await self._extract_client_data(client_name, [data_type], use_cache=True)
                    comprehensive_data[data_type] = result[0].text if result else "No data"
                except Exception as e:
                    comprehensive_data[data_type] = f"Error: {str(e)}"

            # Generate AI summary
            ai_summary = await self._generate_ai_summary(client_name, comprehensive_data)
            comprehensive_data['ai_summary'] = ai_summary

            return [TextContent(type="text", text=json.dumps(comprehensive_data, indent=2))]

        except Exception as e:
            return [TextContent(type="text", text=f"Report generation error: {str(e)}")]

    async def _generate_ai_summary(self, client_name: str, data: dict) -> str:
        """Generate AI summary of client data"""
        try:
            prompt = f"""
            Generate a concise fitness progress summary for {client_name} based on this data:
            
            {json.dumps(data, indent=2)}
            
            Include:
            1. Key highlights
            2. Areas needing attention
            3. Recommendations
            
            Keep it professional and actionable.
            """

            response = self.gemini_model.generate_content(prompt)
            return response.text

        except Exception as e:
            return f"AI summary error: {str(e)}"

    async def _cleanup_browsers(self) -> List[TextContent]:
        """Clean up all browser instances"""
        try:
            cleanup_count = 0
            for driver in self.driver_pool:
                try:
                    driver.quit()
                    cleanup_count += 1
                except:
                    pass

            self.driver_pool.clear()
            self.driver_states.clear()

            return [TextContent(type="text", text=f"Cleaned up {cleanup_count} browser instances")]

        except Exception as e:
            return [TextContent(type="text", text=f"Cleanup error: {str(e)}")]

# Standalone usage (without MCP)


class StandaloneTrainerizeAutomation:
    """
    Standalone version for direct usage without MCP
    """

    def __init__(self, gemini_api_key: str, username: str, password: str):
        self.enhanced_mcp = EnhancedTrainerizeMCP(gemini_api_key)
        self.username = username
        self.password = password
        self.initialized = False

    async def initialize(self):
        """Initialize browser pool"""
        if not self.initialized:
            result = await self.enhanced_mcp._initialize_browser_pool(self.username, self.password)
            self.initialized = True
            return result

    async def extract_client_data(self, client_name: str, data_types: List[str], use_cache: bool = True):
        """Extract client data"""
        if not self.initialized:
            await self.initialize()

        return await self.enhanced_mcp._extract_client_data(client_name, data_types, use_cache)

    async def parallel_analysis(self, client_list: List[str], analysis_type: str = "weekly_summary"):
        """Analyze multiple clients in parallel"""
        if not self.initialized:
            await self.initialize()

        return await self.enhanced_mcp._parallel_client_analysis(json.dumps(client_list), analysis_type)

    async def comprehensive_report(self, client_name: str, days_back: int = 30):
        """Generate comprehensive report"""
        if not self.initialized:
            await self.initialize()

        return await self.enhanced_mcp._comprehensive_client_report(client_name, days_back)

    async def cleanup(self):
        """Cleanup resources"""
        return await self.enhanced_mcp._cleanup_browsers()

# Usage example


async def example_usage():
    """Example of how to use the Enhanced Trainerize MCP Tool"""

    # Your credentials
    gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"

    # Initialize
    automation = StandaloneTrainerizeAutomation(
        gemini_api_key, username, password)

    try:
        # Initialize browser pool
        print("Initializing browser pool...")
        init_result = await automation.initialize()
        print(init_result[0].text)

        # Extract data for a single client
        print("\nExtracting client data...")
        client_data = await automation.extract_client_data(
            "Alice Forster",
            ['bodyweight', 'nutrition', 'sleep'],
            use_cache=True
        )
        print(client_data[0].text)

        # Parallel analysis of multiple clients
        print("\nParallel client analysis...")
        clients = ["Alice Forster", "Shannon Birch", "Kelly Smith"]
        parallel_results = await automation.parallel_analysis(clients, "weekly_summary")
        print(parallel_results[0].text)

        # Comprehensive report
        print("\nGenerating comprehensive report...")
        report = await automation.comprehensive_report("Alice Forster", days_back=30)
        print(report[0].text)

    finally:
        # Always cleanup
        await automation.cleanup()

if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
