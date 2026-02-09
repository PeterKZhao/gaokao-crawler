import requests
import json
import time
from datetime import datetime

class BaseCrawler:
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
    
    def make_request(self, payload, retry=3):
        """统一的请求方法"""
        for attempt in range(retry):
            try:
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=15
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"请求失败，状态码: {response.status_code}")
                    
            except Exception as e:
                print(f"请求出错 (尝试 {attempt + 1}/{retry}): {str(e)}")
                if attempt < retry - 1:
                    time.sleep(2)
        
        return None
    
    def save_to_json(self, data, filename):
        """保存数据到JSON文件"""
        filepath = f'data/{filename}'
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'count': len(data),
                'data': data
            }, f, ensure_ascii=False, indent=2)
        print(f"✓ 数据已保存到 {filepath}")
