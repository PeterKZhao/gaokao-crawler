"""
Selenium调试测试脚本
用于在GitHub Actions中诊断问题
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import time

def test_selenium_basic():
    """测试Selenium基本功能"""
    print("="*60)
    print("测试1: Selenium基础功能")
    print("="*60)
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    try:
        driver = webdriver.Chrome(options=options)
        print("✓ Chrome驱动初始化成功")
        
        # 测试访问百度
        driver.get("https://www.baidu.com")
        print(f"✓ 测试页面访问成功，标题: {driver.title}")
        
        driver.quit()
        return True
    except Exception as e:
        print(f"✗ 基础测试失败: {e}")
        return False

def test_gaokao_page():
    """测试掌上高考页面"""
    print("\n" + "="*60)
    print("测试2: 访问掌上高考搜索页")
    print("="*60)
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        url = "https://www.gaokao.cn/school/search?page=1"
        
        print(f"正在访问: {url}")
        driver.get(url)
        
        print(f"✓ 页面加载完成")
        print(f"  页面标题: {driver.title}")
        print(f"  当前URL: {driver.current_url}")
        
        # 保存页面源码
        page_source = driver.page_source
        with open('debug_page_source.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        print(f"✓ 页面源码已保存到 debug_page_source.html ({len(page_source)} 字符)")
        
        # 等待页面加载
        time.sleep(5)
        print("✓ 等待5秒后...")
        
        # 尝试查找学校项
        print("\n尝试查找学校列表元素...")
        
        possible_classes = [
            "school-search_schoolItem__3q7R2",
            "schoolItem",
            "school-item",
            "school_item"
        ]
        
        for class_name in possible_classes:
            try:
                elements = driver.find_elements(By.CLASS_NAME, class_name)
                print(f"  class='{class_name}': 找到 {len(elements)} 个元素")
                if elements:
                    print(f"    第一个元素的文本: {elements[0].text[:100]}")
            except Exception as e:
                print(f"  class='{class_name}': 未找到 ({e})")
        
        # 尝试通过CSS选择器查找
        print("\n尝试通过CSS选择器查找...")
        try:
            items = driver.find_elements(By.CSS_SELECTOR, "div[class*='schoolItem']")
            print(f"  找到包含'schoolItem'的div: {len(items)} 个")
        except Exception as e:
            print(f"  CSS选择器失败: {e}")
        
        # 截图
        try:
            screenshot_path = 'debug_screenshot.png'
            driver.save_screenshot(screenshot_path)
            print(f"✓ 截图已保存到 {screenshot_path}")
        except Exception as e:
            print(f"✗ 截图失败: {e}")
        
        # 输出页面部分HTML
        print("\n页面body的前2000字符:")
        print("-" * 60)
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            print(body.get_attribute('innerHTML')[:2000])
        except Exception as e:
            print(f"获取body失败: {e}")
        print("-" * 60)
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"✗ 掌上高考页面测试失败: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return False

def test_wait_strategies():
    """测试不同的等待策略"""
    print("\n" + "="*60)
    print("测试3: 不同的等待策略")
    print("="*60)
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.gaokao.cn/school/search?page=1")
        
        # 策略1: 等待body加载
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("✓ 策略1: body已加载")
        except TimeoutException:
            print("✗ 策略1: body加载超时")
        
        # 策略2: 等待特定class
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "school-search_schoolItem__3q7R2"))
            )
            print("✓ 策略2: 找到学校列表元素")
        except TimeoutException:
            print("✗ 策略2: 未找到学校列表元素（可能是动态加载）")
        
        # 策略3: 执行JavaScript检查
        try:
            time.sleep(3)
            result = driver.execute_script("""
                var items = document.querySelectorAll('[class*="schoolItem"]');
                return {
                    count: items.length,
                    classes: items.length > 0 ? items[0].className : 'none'
                };
            """)
            print(f"✓ 策略3: JavaScript查询结果: {result}")
        except Exception as e:
            print(f"✗ 策略3: JavaScript执行失败: {e}")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"✗ 等待策略测试失败: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Selenium调试测试开始")
    print("="*60 + "\n")
    
    results = []
    
    # 测试1
    results.append(("Selenium基础功能", test_selenium_basic()))
    
    # 测试2
    results.append(("掌上高考页面访问", test_gaokao_page()))
    
    # 测试3
    results.append(("等待策略", test_wait_strategies()))
    
    # 总结
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)
    for name, success in results:
        status = "✓ 成功" if success else "✗ 失败"
        print(f"{name}: {status}")
    print("="*60 + "\n")
