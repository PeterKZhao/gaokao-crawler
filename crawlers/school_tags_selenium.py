from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import time
import json

class SchoolTagsSeleniumScraper:
    """使用Selenium爬取学校标签"""
    
    def __init__(self, headless=True):
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=options)
        self.base_url = "https://www.gaokao.cn/school/search"
    
    def scrape_page(self, page_num):
        """爬取指定页"""
        url = f"{self.base_url}?page={page_num}"
        
        try:
            self.driver.get(url)
            
            # 等待学校列表加载
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "school-search_schoolItem__3q7R2"))
            )
            
            # 等待额外时间确保内容加载完成
            time.sleep(2)
            
            # 获取所有学校项
            school_items = self.driver.find_elements(By.CLASS_NAME, "school-search_schoolItem__3q7R2")
            
            schools = []
            for item in school_items:
                try:
                    # 学校名称
                    name_elem = item.find_element(By.CLASS_NAME, "school-search_schoolName__1L7pc")
                    school_name = name_elem.text.split('\n')[0].strip()
                    
                    # 标签
                    tags = []
                    try:
                        tags_div = item.find_element(By.CLASS_NAME, "school-search_tags__ZPsHs")
                        tag_elements = tags_div.find_elements(By.TAG_NAME, "span")
                        tags = [tag.text.strip() for tag in tag_elements if tag.text.strip()]
                    except:
                        pass
                    
                    schools.append({
                        'name': school_name,
                        'tags': tags
                    })
                
                except Exception as e:
                    continue
            
            print(f"✓ 第{page_num}页: {len(schools)}所学校")
            return schools
        
        except TimeoutException:
            print(f"✗ 第{page_num}页超时")
            return None
        except Exception as e:
            print(f"✗ 第{page_num}页出错: {e}")
            return None
    
    def scrape_all(self, max_pages=150):
        """爬取所有页面"""
        all_tags = {}
        
        print(f"\n{'='*60}")
        print(f"使用Selenium爬取学校标签")
        print(f"{'='*60}\n")
        
        for page in range(1, max_pages + 1):
            schools = self.scrape_page(page)
            
            if schools is None:
                print(f"第{page}页失败，重试...")
                time.sleep(5)
                schools = self.scrape_page(page)
                if schools is None:
                    continue
            
            if not schools:
                print(f"第{page}页无数据，完成")
                break
            
            for school in schools:
                all_tags[school['name']] = school['tags']
            
            # 每10页保存
            if page % 10 == 0:
                self.save_tags(all_tags, 'data/school_tags_temp.json')
                print(f"  💾 已保存（{len(all_tags)}所学校）\n")
            
            time.sleep(3)
        
        self.save_tags(all_tags, 'data/school_tags.json')
        self.driver.quit()
        
        print(f"\n{'='*60}")
        print(f"✓ 完成！共 {len(all_tags)} 所学校")
        print(f"{'='*60}\n")
        
        return all_tags
    
    def save_tags(self, tags_dict, filepath):
        """保存标签"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(tags_dict, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import sys
    scraper = SchoolTagsSeleniumScraper(headless=True)
    
    test_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    scraper.scrape_all(max_pages=test_pages)
