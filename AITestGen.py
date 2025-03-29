# fixed_test_gen.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json
import time

class FixedTestGenerator:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def extract_elements(self, url):
        print(f"\nAnalyzing {url}...")
        self.driver.get(url)
        time.sleep(3)
        
        # Accept cookies if present
        try:
            accept_buttons = self.driver.find_elements(
                By.XPATH, "//button[contains(.,'Accept') or contains(.,'Agree') or contains(.,'Allow')]")
            if accept_buttons:
                accept_buttons[0].click()
                time.sleep(1)
        except:
            pass
        
        elements = self.driver.find_elements(
            By.XPATH, "//input | //button | //a[normalize-space(text())] | //select")
        
        element_data = []
        for elem in elements:
            try:
                if elem.is_displayed() and elem.is_enabled():
                    element_data.append(self.get_element_info(elem))
            except:
                continue
        return element_data
    
    def get_element_info(self, element):
        """Extract element information while element reference is still valid"""
        elem_type = element.get_attribute('type') or ''
        elem_name = element.get_attribute('name') or element.get_attribute('id') or ''
        elem_text = element.text.strip()
        
        return {
            'tag': element.tag_name,
            'type': elem_type,
            'name': elem_name,
            'text': elem_text,
            'xpath': self.get_xpath(element),
            'score': self.calculate_score(element, elem_type, elem_name, elem_text)
        }
    
    def get_xpath(self, element):
        try:
            if element.get_attribute('id'):
                return f"//*[@id='{element.get_attribute('id')}']"
            if element.get_attribute('name'):
                return f"//*[@name='{element.get_attribute('name')}']"
            
            return self.driver.execute_script("""
                function getXPath(element) {
                    if (!element || element === document.body) return '';
                    if (element.id) return '//*[@id=\"' + element.id + '\"]';
                    
                    var siblings = element.parentNode.children;
                    if (siblings.length === 1) {
                        return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase();
                    }
                    
                    var idx = 1;
                    for (var sib = element.previousSibling; sib; sib = sib.previousSibling) {
                        if (sib.nodeType === 1 && sib.tagName === element.tagName) idx++;
                    }
                    return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + idx + ']';
                }
                return getXPath(arguments[0]);
            """, element)
        except:
            return ""
    
    def calculate_score(self, element, elem_type, elem_name, elem_text):
        """Calculate importance score using element attributes"""
        score = 0
        name_lower = elem_name.lower()
        text_lower = elem_text.lower()
        
        # Base scores by element type
        if element.tag_name == 'input':
            score += 30
            if elem_type in ['text', 'search', 'email']: score += 20
            if elem_type in ['submit', 'button']: score += 15
        elif element.tag_name == 'button':
            score += 25
        elif element.tag_name == 'a':
            score += 15
        
        # Boost scores for important keywords
        if any(kw in name_lower for kw in ['search', 'login', 'sign', 'submit']):
            score += 25
        if len(elem_text) > 3:
            score += 10
            
        return score
    
    def generate_test_cases(self, elements, site_name, max_cases=10):
        elements.sort(key=lambda x: x['score'], reverse=True)
        test_cases = []
        
        for elem in elements[:max_cases]:
            test_case = self.create_test_case(elem, site_name)
            if test_case:
                test_cases.append(test_case)
        return test_cases
    
    def create_test_case(self, element, site_name):
        """Create test case from element info"""
        if element['tag'] == 'input':
            return {
                'description': f"Test {element['name'] or 'input'} field on {site_name}",
                'type': 'input',
                'action': 'send_keys',
                'xpath': element['xpath'],
                'value': self.get_test_value(element),
                'expected': 'value_exists'
            }
        elif element['tag'] == 'button':
            return {
                'description': f"Test '{element['text'] or element['name']}' button on {site_name}",
                'type': 'button',
                'action': 'click',
                'xpath': element['xpath'],
                'expected': 'no_error'
            }
        elif element['tag'] == 'a':
            return {
                'description': f"Test '{element['text']}' link on {site_name}",
                'type': 'link',
                'action': 'click',
                'xpath': element['xpath'],
                'expected': 'no_error'
            }
        return None
    
    def get_test_value(self, element):
        """Generate appropriate test data"""
        if 'email' in element['name'].lower() or element['type'] == 'email':
            return 'test@example.com'
        elif 'phone' in element['name'].lower():
            return '1234567890'
        elif 'search' in element['name'].lower() or element['type'] == 'search':
            return 'test search'
        elif 'password' in element['name'].lower() or element['type'] == 'password':
            return 'Test@123'
        elif 'date' in element['name'].lower() or element['type'] == 'date':
            return '2023-01-01'
        else:
            return 'test input'
    
    def run(self, websites, output_file='test_cases.json'):
        all_test_cases = {}
        
        for name, url in websites.items():
            print(f"\nProcessing {name}...")
            try:
                elements = self.extract_elements(url)
                test_cases = self.generate_test_cases(elements, name)
                all_test_cases[name] = test_cases
                print(f"✅ Generated {len(test_cases)} test cases")
            except Exception as e:
                print(f"❌ Error processing {name}: {str(e)}")
                continue
        
        with open(output_file, 'w') as f:
            json.dump(all_test_cases, f, indent=2)
        
        self.driver.quit()
        total_cases = sum(len(v) for v in all_test_cases.values())
        print(f"\n🎉 Successfully generated {total_cases} total test cases")
        print(f"📁 Saved to {output_file}")
        return all_test_cases

if __name__ == "__main__":
    websites = {
        "Google": "https://www.google.com",
        "Amazon": "https://www.amazon.com",
        "Flipkart": "https://www.flipkart.com"
    }
    
    print("🚀 Starting automated test case generation...")
    generator = FixedTestGenerator()
    test_cases = generator.run(websites)