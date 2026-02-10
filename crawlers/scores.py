import time
import json
import os
from .base import BaseCrawler

class ScoreCrawler(BaseCrawler):
    def crawl(self, school_ids=None, province_id="", years=None):
        """爬取分数线数据"""
        years = years or ["2025", "2024", "2023"]
        
        # 从schools.json读取学校ID
        if school_ids is None:
            try:
                with open('data/schools.json', 'r', encoding='utf-8') as f:
                    schools_data = json.load(f)
                    schools = schools_data.get('data', [])
                    sample_count = int(os.getenv('SAMPLE_SCHOOLS', '10'))
                    school_ids = [s['school_id'] for s in schools[:sample_count] if s.get('school_id')]
                    print(f"从 schools.json 读取到 {len(school_ids)} 所学校")
            except FileNotFoundError:
                print("⚠️  未找到 schools.json，请先运行学校爬虫")
                return []
            except Exception as e:
                print(f"⚠️  读取 schools.json 失败: {e}")
                return []
        
        all_scores = []
        
        print(f"\n{'='*60}")
        print(f"开始爬取分数线（{len(school_ids)} 所学校 × {len(years)} 年）")
        print(f"{'='*60}\n")
        
        for idx, school_id in enumerate(school_ids, 1):
            school_score_count = 0
            for year in years:
                payload = {
                    "school_id": school_id,
                    "province_id": province_id,
                    "year": year,
                    "uri": "apidata/api/gkv3/school/scoreline"
                }
                
                data = self.make_request(payload)
                
                # 检查数据有效性
                if not data or 'data' not in data:
                    continue
                
                # 处理不同的数据结构
                data_content = data['data']
                
                # 如果 data 是字符串，尝试解析
                if isinstance(data_content, str):
                    try:
                        data_content = json.loads(data_content)
                    except:
                        print(f"⚠️  [{idx}/{len(school_ids)}] 学校ID {school_id} {year}年：数据格式异常")
                        continue
                
                # 如果 data 是字典，提取 item
                if isinstance(data_content, dict):
                    items = data_content.get('item', [])
                # 如果 data 直接是列表
                elif isinstance(data_content, list):
                    items = data_content
                else:
                    continue
                
                if items:
                    for item in items:
                        score_info = {
                            'school_id': school_id,
                            'year': year,
                            'province': item.get('province_name') or item.get('local_province_name'),
                            'batch': item.get('local_batch_name'),
                            'type': item.get('local_type_name'),
                            'major': item.get('spname') or item.get('special_name'),
                            'major_code': item.get('spcode'),
                            'min_score': item.get('min'),
                            'avg_score': item.get('average') or item.get('avg'),
                            'max_score': item.get('max'),
                            'min_section': item.get('min_section'),
                            'proscore': item.get('proscore'),
                            'enrollment_count': item.get('sg_info') or item.get('zs_num')
                        }
                        all_scores.append(score_info)
                    
                    school_score_count += len(items)
                
                self.polite_sleep(0.3, 0.8)
            
            if school_score_count > 0:
                print(f"✓ [{idx}/{len(school_ids)}] 学校ID {school_id}：{school_score_count} 条分数线")
            else:
                print(f"⚠️  [{idx}/{len(school_ids)}] 学校ID {school_id}：无分数线数据")
            
            self.polite_sleep()
        
        self.save_to_json(all_scores, 'scores.json')
        print(f"\n{'='*60}")
        print(f"分数线爬取完成！共 {len(all_scores)} 条")
        print(f"{'='*60}\n")
        
        return all_scores

if __name__ == "__main__":
    crawler = ScoreCrawler()
    crawler.crawl()
