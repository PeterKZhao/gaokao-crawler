import requests
import time
import json
from bs4 import BeautifulSoup

class SchoolTagsScraper:
    """从掌上高考HTML页面爬取所有学校的标签"""
    
    def __init__(self):
        self.base_url = "https://www.gaokao.cn/school/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.gaokao.cn/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
    
    def scrape_page(self, page_num):
        """爬取指定页的学校标签"""
        url = f"{self.base_url}?page={page_num}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                print(f"✗ 第{page_num}页请求失败: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            school_items = soup.find_all('div', class_='school-search_schoolItem__3q7R2')
            
            if not school_items:
                return []
            
            schools = []
            for item in school_items:
                try:
                    # 提取学校名称
                    name_elem = item.find('h3', class_='school-search_schoolName__1L7pc')
                    if not name_elem:
                        continue
                    
                    # 清理名称（可能有<em>标签）
                    school_name = name_elem.get_text().split('\n')[0].strip()
                    
                    # 提取标签
                    tags = []
                    tags_div = item.find('div', class_='school-search_tags__ZPsHs')
                    if tags_div:
                        tag_spans = tags_div.find_all('span')
                        tags = [tag.get_text().strip() for tag in tag_spans if tag.get_text().strip()]
                    
                    schools.append({
                        'name': school_name,
                        'tags': tags
                    })
                
                except Exception as e:
                    print(f"  解析学校项出错: {e}")
                    continue
            
            print(f"✓ 第{page_num}页: {len(schools)}所学校")
            return schools
        
        except Exception as e:
            print(f"✗ 第{page_num}页出错: {e}")
            return None
    
    def scrape_all(self, max_pages=150):
        """爬取所有学校的标签（约150页）"""
        all_tags = {}
        
        print(f"\n{'='*60}")
        print(f"开始爬取学校标签")
        print(f"{'='*60}\n")
        
        for page in range(1, max_pages + 1):
            schools = self.scrape_page(page)
            
            if schools is None:
                print(f"第{page}页失败，重试...")
                time.sleep(3)
                schools = self.scrape_page(page)
                if schools is None:
                    print(f"第{page}页重试失败，跳过")
                    continue
            
            if not schools:
                print(f"第{page}页无数据，爬取完成")
                break
            
            # 保存标签
            for school in schools:
                all_tags[school['name']] = school['tags']
            
            # 每10页保存一次
            if page % 10 == 0:
                self.save_tags(all_tags, 'data/school_tags_temp.json')
                print(f"  💾 已保存临时数据（{len(all_tags)}所学校）\n")
            
            time.sleep(2)  # 避免请求过快
        
        # 最终保存
        self.save_tags(all_tags, 'data/school_tags.json')
        
        print(f"\n{'='*60}")
        print(f"✓ 完成！共爬取 {len(all_tags)} 所学校的标签")
        print(f"{'='*60}\n")
        
        return all_tags
    
    def save_tags(self, tags_dict, filepath):
        """保存标签字典"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(tags_dict, f, ensure_ascii=False, indent=2)
        print(f"  已保存到 {filepath}")

if __name__ == "__main__":
    import sys
    scraper = SchoolTagsScraper()
    
    # 先测试3页
    test_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    scraper.scrape_all(max_pages=test_pages)
