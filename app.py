# element_extractor.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
# Add these imports at the top
from selenium.webdriver.chrome.options import Options

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    return webdriver.Chrome(options=chrome_options)

def extract_elements(driver, url, site_name):
    print(f"\nExtracting elements from {site_name} ({url})...")
    driver.get(url)
    time.sleep(5)  # Increased wait time
    
    # Accept cookies if present (helps with click interceptions)
    try:
        cookie_button = driver.find_element(By.XPATH, "//button[contains(.,'Accept') or contains(.,'I agree')]")
        cookie_button.click()
        time.sleep(4)
    except:
        pass

    elements = {
        "input_fields": [],
        "buttons": [],
        "links": [],
        "dropdowns": []
    }
    
    # Extract input fields
    inputs = driver.find_elements(By.TAG_NAME, "input")
    for input_element in inputs:
        if input_element.is_displayed():
            input_type = input_element.get_attribute("type") or "text"
            input_name = input_element.get_attribute("name") or input_element.get_attribute("id") or "unnamed_input"
            elements["input_fields"].append({
                "type": input_type,
                "name": input_name,
                "xpath": get_xpath(driver, input_element)
            })
    
    # Extract buttons
    buttons = driver.find_elements(By.XPATH, "//button | //input[@type='button'] | //input[@type='submit']")
    for button in buttons:
        if button.is_displayed():
            button_text = button.text or button.get_attribute("value") or button.get_attribute("aria-label") or "unnamed_button"
            elements["buttons"].append({
                "name": button_text,
                "xpath": get_xpath(driver, button)
            })
    
    # Extract links
    links = driver.find_elements(By.TAG_NAME, "a")
    for link in links:
        if link.is_displayed() and link.text.strip():
            elements["links"].append({
                "text": link.text.strip(),
                "xpath": get_xpath(driver, link)
            })
    
    # Extract dropdowns
    selects = driver.find_elements(By.TAG_NAME, "select")
    for select in selects:
        if select.is_displayed():
            select_name = select.get_attribute("name") or select.get_attribute("id") or "unnamed_select"
            elements["dropdowns"].append({
                "name": select_name,
                "xpath": get_xpath(driver, select)
            })
    
    return elements

def get_xpath(driver, element):
    # JavaScript to generate XPath
    script = """
    function getElementXPath(element) {
        if (element.id !== '')
            return '//*[@id=\"' + element.id + '\"]';
        if (element === document.body)
            return element.tagName.toLowerCase();

        var ix = 0;
        var siblings = element.parentNode.childNodes;
        for (var i = 0; i < siblings.length; i++) {
            var sibling = siblings[i];
            if (sibling === element)
                return getElementXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
            if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                ix++;
        }
    }
    return getElementXPath(arguments[0]);
    """
    return driver.execute_script(script, element)

def generate_test_cases(elements, site_name):
    test_cases = []
    
    # Test case for input fields
    for input_field in elements["input_fields"][:2]:  # Limit to 2 input fields per site
        if input_field["type"].lower() in ["text", "search"]:
            test_cases.append({
                "description": f"Verify {input_field['name']} input field on {site_name}",
                "type": "input",
                "action": "send_keys",
                "xpath": input_field["xpath"],
                "value": "test search" if "search" in input_field["name"].lower() else "test input",
                "expected": "value_exists"
            })
    
    # Test case for buttons
    for button in elements["buttons"][:2]:  # Limit to 2 buttons per site
        test_cases.append({
            "description": f"Verify '{button['name']}' button on {site_name}",
            "type": "button",
            "action": "click",
            "xpath": button["xpath"],
            "expected": "no_error"
        })
    
    # Test case for links
    if elements["links"]:
        test_cases.append({
            "description": f"Verify '{elements['links'][0]['text']}' link on {site_name}",
            "type": "link",
            "action": "click",
            "xpath": elements["links"][0]["xpath"],
            "expected": "no_error"
        })
    
    return test_cases

def main():
    websites = {
        "Google": "https://www.google.com",
        "Amazon": "https://www.amazon.com",
        "Flipkart": "https://www.flipkart.com"
    }
    
    driver = webdriver.Chrome()
    all_test_cases = {}
    
    try:
        for site_name, url in websites.items():
            elements = extract_elements(driver, url, site_name)
            test_cases = generate_test_cases(elements, site_name)
            all_test_cases[site_name] = test_cases
            
            print(f"Generated {len(test_cases)} test cases for {site_name}")
            
        # Save test cases to JSON file
        with open("web_test_cases.json", "w") as f:
            json.dump(all_test_cases, f, indent=4)
            
        print("\nSuccessfully generated test cases in 'web_test_cases.json'")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()