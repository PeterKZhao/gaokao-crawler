import time
import json
import os
from .base import BaseCrawler

class ScoreCrawler(BaseCrawler):
    def crawl(self, school_ids=None, province_id="", years=None):
        """爬取分数线数据"""
        if years is None:
            years = ["2025", "2024", "2023"]
        
        # 如果没有提供学校ID，从schools.json读取
        if school_ids is None:
            try:
                with open('data/schools.json', 'r', encoding='utf-8') as f:
                    schools_data = json.load(f)
                    schools = schools_data.get('data', [])
                    # 默认只爬取前10所学校
                    sample_count = int(os.getenv('SAMPLE_SCHOOLS', '10'))
                    school_ids = [s['school_id'] for s in schools[:sample_count] if s.get('school_id')]
                    print(f"从 schools.json 读取到 {len(school_ids)} 所学校")
            except Exception as e:
                print(f"无法读取 schools.json: {e}")
                return []
        
        all_scores = []
        
        print(f"\n{'='*60}")
        print(f"开始爬取分数线（{len(school_ids)} 所学校 × {len(years)} 年）")
        print(f"{'='*60}\n")
        
        for idx, school_id in enumerate(school_ids, 1):
            for year in years:
                # 尝试多个可能的API格式
                payloads = [
                    {
                        "school_id": school_id,
                        "province_id": province_id,
                        "year": year,
                        "uri": "apidata/api/gkv3/school/scoreline"
                    },
                    {
                        "school_id": school_id,
                        "local_province_id": province_id,
                        "year": year,
                        "uri": "apidata/api/gkv3/school/getSchoolProvinceLine"
                    }
                ]
                
                for payload in payloads:
                    data = self.make_request(payload)
                    
                    if data and 'data' in data:
                        items = data['data'].get('item', [])
                        
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
                            
                            print(f"✓ [{idx}/{len(school_ids)}] 学校ID {school_id} {year}年：{len(items)} 条")
                            break
                
                time.sleep(0.5)
            
            time.sleep(1)
        
        self.save_to_json(all_scores, 'scores.json')
        print(f"\n{'='*60}")
        print(f"分数线爬取完成！共 {len(all_scores)} 条")
        print(f"{'='*60}\n")
        
        return all_scores

if __name__ == "__main__":
    crawler = ScoreCrawler()
    crawler.crawl()
