import time
import os
import json
from .base import BaseCrawler

class SchoolCrawler(BaseCrawler):
    
    def __init__(self):
        super().__init__()
        # 加载标签数据
        self.tags_dict = self.load_tags_dict()
    
    def load_tags_dict(self):
        """加载标签字典"""
        try:
            with open('data/school_tags.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            print("⚠ 未找到标签数据文件，标签将为空")
            return {}
    
    def get_school_detail_static(self, school_id):
        """从静态JSON接口获取学校详细信息"""
        url = f"https://static-data.gaokao.cn/www/2.0/school/{school_id}/info.json"
        
        headers = {
            "accept": "application/json, text/plain, */*",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            import requests
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    return data['data']
        except Exception as e:
            pass
        
        return None
    
    def crawl(self, max_pages=None, fetch_detail=True):
        """爬取学校列表"""
        if max_pages is None:
            max_pages = int(os.getenv('MAX_PAGES', '10'))
        
        fetch_detail = os.getenv('FETCH_DETAIL', str(fetch_detail)).lower() == 'true'
        
        schools = []
        print(f"\n{'='*60}")
        print(f"开始爬取学校列表（最多 {max_pages} 页）")
        print(f"标签数据: {'已加载' if self.tags_dict else '未加载'}")
        print(f"详细信息: {'开启' if fetch_detail else '关闭'}")
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
                    school_id = item.get('school_id')
                    school_name = item.get('name')
                    
                    # 基础信息
                    school_info = {
                        'school_id': school_id,
                        'name': school_name,
                        'province': item.get('province_name'),
                        'city': item.get('city_name'),
                        'county': item.get('county_name'),
                        'type': item.get('type_name'),
                        'level': item.get('level_name'),
                        'belong': item.get('belong'),
                        'nature': item.get('nature_name'),
                        'rank': item.get('rank'),
                        'f985': item.get('f985'),
                        'f211': item.get('f211'),
                        'dual_class': item.get('dual_class_name'),
                    }
                    
                    # 从标签字典获取标签
                    tags = self.tags_dict.get(school_name, [])
                    school_info['tags'] = tags
                    school_info['tags_text'] = ', '.join(tags)
                    
                    # 获取详细信息
                    if fetch_detail and school_id:
                        detail = self.get_school_detail_static(school_id)
                        if detail:
                            school_info.update({
                                'logo': detail.get('logo'),
                                'address': detail.get('address'),
                                'phone': detail.get('phone'),
                                'email': detail.get('email'),
                                'website': detail.get('site'),
                                'motto': detail.get('motto'),
                                # ... 其他字段
                            })
                        time.sleep(0.8)
                    
                    print(f"  ✓ {school_name}: {tags}")
                    schools.append(school_info)
                
                print(f"✓ 第 {page} 页：获取 {len(items)} 所学校")
            else:
                print(f"✗ 第 {page} 页：请求失败")
                break
            
            time.sleep(1)
        
        self.save_to_json(schools, 'schools.json')
        print(f"\n{'='*60}")
        print(f"完成！共 {len(schools)} 所学校")
        print(f"{'='*60}\n")
        
        return schools

if __name__ == "__main__":
    import sys
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    fetch_detail = sys.argv[2].lower() == 'true' if len(sys.argv) > 2 else True
    
    crawler = SchoolCrawler()
    crawler.crawl(max_pages=max_pages, fetch_detail=fetch_detail)
