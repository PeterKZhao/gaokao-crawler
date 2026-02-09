import requests
import json
import time
from datetime import datetime

class GaoKaoCrawler:
    def __init__(self):
        self.base_url = "https://api.zjzw.cn/web/api/"
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.gaokao.cn",
            "referer": "https://www.gaokao.cn/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def get_schools(self, max_pages=10):
        """获取大学列表"""
        schools = []
        
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
            
            try:
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and 'item' in data['data']:
                        items = data['data']['item']
                        for item in items:
                            school_info = {
                                'school_id': item.get('school_id'),
                                'name': item.get('name'),
                                'province': item.get('province_name'),
                                'type': item.get('type_name'),
                                'rank': item.get('rank')
                            }
                            schools.append(school_info)
                        print(f"第{page}页爬取成功，获取{len(items)}所学校")
                    else:
                        print(f"第{page}页无数据")
                        break
                else:
                    print(f"第{page}页请求失败: {response.status_code}")
                
                time.sleep(1)  # 避免请求过快
                
            except Exception as e:
                print(f"第{page}页爬取出错: {str(e)}")
                continue
        
        return schools
    
    def save_to_json(self, data, filename):
        """保存数据到JSON文件"""
        with open(f'data/{filename}', 'w', encoding='utf-8') as f:
            json.dump({
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'count': len(data),
                'data': data
            }, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 data/{filename}")

if __name__ == "__main__":
    # 测试第一步：获取大学列表
    crawler = GaoKaoCrawler()
    print("开始爬取大学列表...")
    schools = crawler.get_schools(max_pages=5)  # 先测试5页
    crawler.save_to_json(schools, 'schools.json')
    print(f"共爬取 {len(schools)} 所大学")
