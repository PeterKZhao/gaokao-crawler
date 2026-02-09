import requests
import json
import time
import os
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
                        if not items:
                            print(f"第{page}页无数据，停止爬取")
                            break
                        
                        for item in items:
                            school_info = {
                                'school_id': item.get('school_id'),
                                'name': item.get('name'),
                                'province': item.get('province_name'),
                                'type': item.get('type_name'),
                                'rank': item.get('rank'),
                                'level': item.get('level_name'),
                                'dual_class': item.get('dual_class_name')
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

    def get_majors(self):
        """获取专业列表"""
        majors = []
        page = 1
        
        while True:
            payload = {
                "keyword": "",
                "page": page,
                "size": 30,
                "uri": "apidata/api/gkv3/major/lists"
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
                        if not items:
                            print(f"专业第{page}页无数据，爬取完成")
                            break
                        
                        for item in items:
                            major_info = {
                                'special_id': item.get('special_id'),
                                'code': item.get('code'),
                                'name': item.get('name'),
                                'level1_name': item.get('level1_name'),
                                'level2_name': item.get('level2_name'),
                                'level3_name': item.get('level3_name'),
                                'degree': item.get('degree'),
                                'years': item.get('years')
                            }
                            majors.append(major_info)
                        print(f"专业第{page}页爬取成功，获取{len(items)}个专业")
                        page += 1
                    else:
                        break
                else:
                    print(f"专业第{page}页请求失败: {response.status_code}")
                    break
                
                time.sleep(1)
                
            except Exception as e:
                print(f"专业第{page}页爬取出错: {str(e)}")
                break
        
        return majors

    def get_school_scores(self, school_id, province_id="", year="2025"):
        """获取学校专业分数线和招生计划"""
        scores = []
        
        payload = {
            "school_id": school_id,
            "province_id": province_id,
            "year": year,
            "uri": "apidata/api/gkv3/school/scoreline"
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
                        score_info = {
                            'school_id': school_id,
                            'year': year,
                            'province': item.get('province_name'),
                            'major': item.get('spname'),
                            'major_code': item.get('spcode'),
                            'batch': item.get('local_batch_name'),
                            'type': item.get('local_type_name'),
                            'min_score': item.get('min'),
                            'avg_score': item.get('avg'),
                            'max_score': item.get('max'),
                            'min_section': item.get('min_section'),
                            'proscore': item.get('proscore'),
                            'sg_info': item.get('sg_info'),
                            'plan_count': item.get('sg_info')
                        }
                        scores.append(score_info)
                    return scores
            return []
            
        except Exception as e:
            print(f"学校{school_id}分数线爬取出错: {str(e)}")
            return []
    
    def crawl_all_scores(self, schools, sample_count=5):
        """批量爬取学校分数线（测试模式：只爬取部分学校）"""
        all_scores = []
        
        # 只爬取前sample_count所学校进行测试
        sample_schools = schools[:sample_count]
        
        print(f"\n开始爬取{len(sample_schools)}所学校的分数线...")
        for idx, school in enumerate(sample_schools, 1):
            school_id = school.get('school_id')
            school_name = school.get('name')
            
            print(f"[{idx}/{len(sample_schools)}] 正在爬取: {school_name} (ID: {school_id})")
            
            scores = self.get_school_scores(school_id)
            if scores:
                all_scores.extend(scores)
                print(f"  → 获取到{len(scores)}条分数线数据")
            else:
                print(f"  → 无分数线数据")
            
            time.sleep(2)  # 增加延时避免请求过快
        
        return all_scores
    
    def save_to_json(self, data, filename):
        """保存数据到JSON文件"""
        filepath = f'data/{filename}'
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'count': len(data),
                'data': data
            }, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 {filepath}")

if __name__ == "__main__":
    crawler = GaoKaoCrawler()
    
    # 从环境变量读取配置（用于GitHub Actions）
    max_pages = int(os.getenv('MAX_PAGES', '5'))  # 默认5页
    crawl_scores = os.getenv('CRAWL_SCORES', 'false').lower() == 'true'
    
    # 第一步：获取大学列表
    print("=" * 60)
    print("第一步：爬取大学列表")
    print("=" * 60)
    schools = crawler.get_schools(max_pages=max_pages)
    crawler.save_to_json(schools, 'schools.json')
    print(f"✓ 共爬取 {len(schools)} 所大学\n")
    
    # 第二步：获取专业列表
    print("=" * 60)
    print("第二步：爬取专业列表")
    print("=" * 60)
    majors = crawler.get_majors()
    crawler.save_to_json(majors, 'majors.json')
    print(f"✓ 共爬取 {len(majors)} 个专业\n")
    
    # 第三步：获取分数线（可选）
    if crawl_scores and schools:
        print("=" * 60)
        print("第三步：爬取分数线和招生计划")
        print("=" * 60)
        scores = crawler.crawl_all_scores(schools, sample_count=5)
        crawler.save_to_json(scores, 'scores.json')
        print(f"✓ 共爬取 {len(scores)} 条分数线数据\n")
    else:
        print("=" * 60)
        print("第三步：跳过分数线爬取（可手动开启）")
        print("=" * 60)
        # 保存空的scores文件
        crawler.save_to_json([], 'scores.json')
    
    print("\n" + "=" * 60)
    print("✓ 所有爬取任务完成！")
    print("=" * 60)
