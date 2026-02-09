import requests
import time
import json
from bs4 import BeautifulSoup
from .base import BaseCrawler

class SchoolTagsScraper(BaseCrawler):
    """从掌上高考搜索页面爬取学校标签"""
    
    def __init__(self):
        super().__init__()
        self.search_url = "https://www.gaokao.cn/school/search"
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "referer": "https://www.gaokao.cn/",
        }
    
    def scrape_page_tags(self, page_num):
        """爬取某一页的学校标签"""
        schools_with_tags = []
        
        params = {
            "page": page_num,
        }
        
        try:
            response = requests.get(
                self.search_url,
                headers=self.headers,
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找所有学校项
                school_items = soup.find_all('div', class_='school-search_schoolItem__3q7R2')
                
                if not school_items:
                    print(f"  第{page_num}页未找到学校项，可能需要使用Selenium")
                    return None
                
                for item in school_items:
                    try:
                        # 提取学校名称
                        name_elem = item.find('h3', class_='school-search_schoolName__1L7pc')
                        if name_elem:
                            school_name = name_elem.find('em').text if name_elem.find('em') else name_elem.text.strip()
                        else:
                            continue
                        
                        # 提取标签
                        tags_div = item.find('div', class_='school-search_tags__ZPsHs')
                        tags = []
                        if tags_div:
                            tag_spans = tags_div.find_all('span')
                            tags = [tag.text.strip() for tag in tag_spans]
                        
                        schools_with_tags.append({
                            'name': school_name,
                            'tags': tags
                        })
                    
                    except Exception as e:
                        print(f"  解析学校项出错: {e}")
                        continue
                
                print(f"✓ 第{page_num}页：获取{len(schools_with_tags)}所学校的标签")
                return schools_with_tags
            
            else:
                print(f"✗ 第{page_num}页请求失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"✗ 第{page_num}页爬取出错: {e}")
            return None
    
    def scrape_all_tags(self, max_pages=150):
        """爬取所有页面的学校标签（约2958所学校/20 = 148页）"""
        all_schools_tags = {}
        
        print(f"\n{'='*60}")
        print(f"开始爬取学校标签（共约{max_pages}页）")
        print(f"{'='*60}\n")
        
        for page in range(1, max_pages + 1):
            schools = self.scrape_page_tags(page)
            
            if schools is None:
                print(f"第{page}页爬取失败，请检查网页结构")
                break
            
            if not schools:
                print(f"第{page}页无数据，爬取完成")
                break
            
            # 存储到字典中，以学校名为key
            for school in schools:
                all_schools_tags[school['name']] = school['tags']
            
            time.sleep(2)  # 适当延时
            
            # 每10页保存一次（防止中断丢失数据）
            if page % 10 == 0:
                self.save_tags_dict(all_schools_tags, 'school_tags_temp.json')
                print(f"  已保存临时数据（共{len(all_schools_tags)}所学校）\n")
        
        # 最终保存
        self.save_tags_dict(all_schools_tags, 'school_tags.json')
        
        print(f"\n{'='*60}")
        print(f"标签爬取完成！共{len(all_schools_tags)}所学校")
        print(f"{'='*60}\n")
        
        return all_schools_tags
    
    def save_tags_dict(self, tags_dict, filename):
        """保存标签字典"""
        filepath = f'data/{filename}'
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(tags_dict, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scraper = SchoolTagsScraper()
    # 先测试1页
    scraper.scrape_all_tags(max_pages=1)
