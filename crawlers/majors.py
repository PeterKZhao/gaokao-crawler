import time
from .base import BaseCrawler

class MajorCrawler(BaseCrawler):
    def crawl(self):
        """爬取专业列表"""
        majors = []
        page = 1
        
        print(f"\n{'='*60}")
        print(f"开始爬取专业列表")
        print(f"{'='*60}\n")
        
        while True:
            # 尝试多个可能的API格式
            payloads = [
                {
                    "keyword": "",
                    "page": page,
                    "size": 30,
                    "type": "",
                    "uri": "apidata/api/gkv3/special/lists"  # 可能的API路径1
                },
                {
                    "page": page,
                    "size": 30,
                    "uri": "apidata/api/gk/special/page"  # 可能的API路径2
                },
                {
                    "keyword": "",
                    "level1": "",
                    "level2": "",
                    "level3": "",
                    "page": page,
                    "size": 30,
                    "uri": "apidata/api/gkv3/special/lists"  # 可能的API路径3
                }
            ]
            
            success = False
            for idx, payload in enumerate(payloads):
                data = self.make_request(payload)
                
                if data and 'data' in data:
                    # 尝试多种数据结构
                    items = None
                    if 'item' in data['data']:
                        items = data['data']['item']
                    elif 'items' in data['data']:
                        items = data['data']['items']
                    elif isinstance(data['data'], list):
                        items = data['data']
                    
                    if items and len(items) > 0:
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
                        
                        print(f"✓ 第 {page} 页：获取 {len(items)} 个专业（使用API格式{idx+1}）")
                        success = True
                        break
            
            if not success:
                if page == 1:
                    print(f"✗ 所有API格式都失败，可能需要更新API参数")
                else:
                    print(f"第 {page} 页无数据，爬取完成")
                break
            
            page += 1
            time.sleep(1)
            
            # 安全上限
            if page > 200:
                print("已达到最大页数限制")
                break
        
        self.save_to_json(majors, 'majors.json')
        print(f"\n{'='*60}")
        print(f"专业爬取完成！共 {len(majors)} 个")
        print(f"{'='*60}\n")
        
        return majors

if __name__ == "__main__":
    crawler = MajorCrawler()
    crawler.crawl()
