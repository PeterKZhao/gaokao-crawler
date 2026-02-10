import time
import json
from .base import BaseCrawler

class MajorCrawler(BaseCrawler):
    def crawl(self, max_pages=200):
        """爬取专业列表"""
        majors = []
        page = 1
        
        print(f"\n{'='*60}")
        print(f"开始爬取专业列表")
        print(f"{'='*60}\n")
        
        while page <= max_pages:
            payload = {
                "keyword": "",
                "page": page,
                "size": 30,
                "level1": "",
                "level2": "",
                "level3": "",
                "uri": "apidata/api/gkv3/special/lists"
            }
            
            data = self.make_request(payload)
            
            if not data or 'data' not in data:
                print(f"✗ 第 {page} 页：请求失败")
                if page == 1:
                    print("⚠️  API 可能已更改，请检查参数")
                break
            
            # 处理不同的数据结构
            data_content = data['data']
            
            # 如果 data 是字符串，尝试解析
            if isinstance(data_content, str):
                try:
                    data_content = json.loads(data_content)
                except Exception as e:
                    print(f"✗ 第 {page} 页：数据解析失败 - {str(e)}")
                    break
            
            # 提取 items
            items = []
            if isinstance(data_content, dict):
                items = data_content.get('item') or data_content.get('items') or []
            elif isinstance(data_content, list):
                items = data_content
            
            if not items:
                print(f"第 {page} 页无数据，爬取完成")
                break
            
            for item in items:
                major_info = {
                    'special_id': item.get('special_id') or item.get('id'),
                    'code': item.get('code') or item.get('special_code'),
                    'name': item.get('name') or item.get('special_name'),
                    'level1_name': item.get('level1_name'),
                    'level2_name': item.get('level2_name'),
                    'level3_name': item.get('level3_name'),
                    'degree': item.get('degree'),
                    'years': item.get('years') or item.get('limit_year')
                }
                majors.append(major_info)
            
            print(f"✓ 第 {page} 页：获取 {len(items)} 个专业")
            
            # 每10页显示进度
            if page % 10 == 0:
                print(f"📊 进度：已爬取 {len(majors)} 个专业...")
            
            page += 1
            self.polite_sleep()
        
        self.save_to_json(majors, 'majors.json')
        print(f"\n{'='*60}")
        print(f"专业爬取完成！共 {len(majors)} 个")
        print(f"{'='*60}\n")
        
        return majors

if __name__ == "__main__":
    crawler = MajorCrawler()
    crawler.crawl()
