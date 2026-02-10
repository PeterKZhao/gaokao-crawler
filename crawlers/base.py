import requests
import json
import time
import random
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
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def make_request(self, payload, retry=3, delay=1):
        """统一的请求方法"""
        for attempt in range(retry):
            try:
                response = self.session.post(
                    self.base_url,
                    json=payload,
                    timeout=15
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"⚠️  请求失败，状态码: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"⚠️  请求超时 (尝试 {attempt + 1}/{retry})")
            except requests.exceptions.RequestException as e:
                print(f"⚠️  请求出错 (尝试 {attempt + 1}/{retry}): {str(e)}")
            
            if attempt < retry - 1:
                time.sleep(delay * (attempt + 1))
        
        return None
    
    def polite_sleep(self, min_delay=0.5, max_delay=1.5):
        """随机延迟，模拟人类行为"""
        time.sleep(random.uniform(min_delay, max_delay))
    
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
