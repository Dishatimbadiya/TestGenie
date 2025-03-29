# test_executor.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.support import expected_conditions as EC
import json
import time
from colorama import init, Fore

# Initialize colorama
init(autoreset=True)

class TestExecutor:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)  # Increased wait time
        self.test_results = []

    def execute_test_case(self, site_name, test_case):
        try:
            print(f"\nRunning test: {test_case['description']}")
            
            # Navigate to the website
            if site_name == "Google":
                self.driver.get("https://www.google.com/ncr")  # /ncr prevents country redirect
            elif site_name == "Amazon":
                self.driver.get("https://www.amazon.com")
            elif site_name == "Flipkart":
                self.driver.get("https://www.flipkart.com")
            
            time.sleep(3)  # Allow page to load
            
            # Accept cookies if present
            try:
                cookie_button = self.driver.find_element(By.XPATH, "//button[contains(.,'Accept') or contains(.,'I agree')]")
                cookie_button.click()
                time.sleep(2)
            except:
                pass
            
            element = self.wait.until(EC.presence_of_element_located((By.XPATH, test_case["xpath"])))
            
            # Scroll to element before interacting
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            if test_case["type"] == "input" and test_case["action"] == "send_keys":
                element.clear()
                element.send_keys(test_case["value"])
                
                if test_case["expected"] == "value_exists":
                    actual_value = element.get_attribute("value")
                    if actual_value == test_case["value"]:
                        self.record_result(True, test_case["description"])
                    else:
                        self.record_result(False, test_case["description"], f"Expected value '{test_case['value']}', got '{actual_value}'")
            
            elif test_case["type"] in ["button", "link"] and test_case["action"] == "click":
                # Use JavaScript click as a fallback
                try:
                    element.click()
                except:
                    self.driver.execute_script("arguments[0].click();", element)
                
                time.sleep(3)  # Increased wait time after click
                
                if test_case["expected"] == "no_error":
                    if "404" not in self.driver.title.lower() and "error" not in self.driver.title.lower():
                        self.record_result(True, test_case["description"])
                    else:
                        self.record_result(False, test_case["description"], "Error page detected after click")
        
        except Exception as e:
            error_msg = str(e).split('\n')[0]  # Take only first line of error
            self.record_result(False, test_case["description"], error_msg)
    
    def record_result(self, passed, description, error_msg=None):
        result = {
            "passed": passed,
            "description": description,
            "error": error_msg
        }
        self.test_results.append(result)
        
        if passed:
            print(Fore.GREEN + "✅ Test Passed")
        else:
            print(Fore.RED + f"❌ Test Failed: {error_msg}")
    
    def run_tests_from_file(self, filename):
        with open(filename, "r") as f:
            test_cases = json.load(f)
        
        total_tests = 0
        passed_tests = 0
        
        for site_name, cases in test_cases.items():
            print(Fore.CYAN + f"\n===== Testing {site_name} =====")
            for test_case in cases:
                self.execute_test_case(site_name, test_case)
                total_tests += 1
                if self.test_results[-1]["passed"]:
                    passed_tests += 1
        
        # Print summary
        print(Fore.YELLOW + "\n===== TEST SUMMARY =====")
        print(Fore.WHITE + f"Total Tests: {total_tests}")
        print(Fore.GREEN + f"Passed: {passed_tests}")
        print(Fore.RED + f"Failed: {total_tests - passed_tests}")
        print(Fore.WHITE + f"Success Rate: {(passed_tests/total_tests)*100:.2f}%")
        
        return self.test_results
    
    def close(self):
        self.driver.quit()

def main():
    executor = TestExecutor()
    try:
        executor.run_tests_from_file("test_cases.json")
    finally:
        executor.close()

if __name__ == "__main__":
    main()