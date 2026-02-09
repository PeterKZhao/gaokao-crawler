import time
import os
from .base import BaseCrawler

class SchoolCrawler(BaseCrawler):
    def crawl(self, max_pages=None):
        """爬取学校列表"""
        if max_pages is None:
            max_pages = int(os.getenv('MAX_PAGES', '10'))
        
        schools = []
        print(f"\n{'='*60}")
        print(f"开始爬取学校列表（最多 {max_pages} 页）")
        print(f"{'='*60}\n")
        
        for page in range(1, max_pages + 1):
            payload = {
                "keyword": "",
                "page": page,
                "province_id": "",
                "ranktype": "",
                "request_type": 1,
                "size": 20,
                "type": "",
                "uri": "apidata/api/gkv3/school/lists"
            }
            
            data = self.make_request(payload)
            
            if data and 'data' in data and 'item' in data['data']:
                items = data['data']['item']
                if not items:
                    print(f"第 {page} 页无数据，停止爬取")
                    break
                
                for item in items:
                    school_info = {
                        'school_id': item.get('school_id'),
                        'name': item.get('name'),
                        'province': item.get('province_name'),
                        'city': item.get('city_name'),
                        'type': item.get('type_name'),
                        'level': item.get('level_name'),
                        'dual_class': item.get('dual_class_name'),
                        'rank': item.get('rank'),
                        'belong': item.get('belong')
                    }
                    schools.append(school_info)
                
                print(f"✓ 第 {page} 页：获取 {len(items)} 所学校")
            else:
                print(f"✗ 第 {page} 页：请求失败")
                break
            
            time.sleep(1)
        
        self.save_to_json(schools, 'schools.json')
        print(f"\n{'='*60}")
        print(f"学校爬取完成！共 {len(schools)} 所")
        print(f"{'='*60}\n")
        
        return schools

if __name__ == "__main__":
    crawler = SchoolCrawler()
    crawler.crawl(max_pages=5)
