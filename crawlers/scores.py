import time
import json
import os
from .base import BaseCrawler

class ScoreCrawler(BaseCrawler):
    
    def __init__(self):
        super().__init__()
        self._first_logged = False
    
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
        print(f"开始爬取分数线")
        print(f"学校数: {len(school_ids)} | 年份: {', '.join(years)}")
        print(f"{'='*60}\n")
        
        for idx, school_id in enumerate(school_ids, 1):
            school_score_count = 0
            
            print(f"\n[{idx}/{len(school_ids)}] 学校ID: {school_id}")
            
            for year in years:
                print(f"\n   📡 [分数线接口] school_id={school_id}, year={year}")
                
                payload = {
                    "school_id": school_id,
                    "province_id": province_id,
                    "year": year,
                    "uri": "apidata/api/gkv3/school/scoreline"
                }
                
                data = self.make_request(payload, retry=5)
                
                # 检查数据有效性
                if not data:
                    print(f"      ✗ 请求失败")
                    continue
                
                # 检查错误码
                code = data.get('code')
                print(f"      业务码: {code}")
                
                if code != '0000' and code != 0:
                    print(f"      ⚠️  API错误: {data.get('message')}")
                    continue
                
                if 'data' not in data:
                    print(f"      ✗ 响应中无data字段")
                    continue
                
                # 处理不同的数据结构
                data_content = data['data']
                
                # 首次显示响应结构
                if not self._first_logged:
                    print(f"\n      {'─'*50}")
                    print(f"      首次响应数据结构:")
                    print(f"      {'─'*50}")
                    print(f"      data类型: {type(data_content).__name__}")
                    
                    if isinstance(data_content, str):
                        print(f"      data是字符串，长度: {len(data_content)}")
                        print(f"      尝试解析JSON...")
                    elif isinstance(data_content, dict):
                        print(f"      data是字典，包含键: {list(data_content.keys())}")
                    elif isinstance(data_content, list):
                        print(f"      data是列表，长度: {len(data_content)}")
                
                # 如果 data 是字符串，尝试解析
                if isinstance(data_content, str):
                    try:
                        data_content = json.loads(data_content)
                        if not self._first_logged:
                            print(f"      ✓ JSON解析成功")
                            print(f"      解析后类型: {type(data_content).__name__}")
                    except:
                        print(f"      ✗ JSON解析失败")
                        continue
                
                # 如果 data 是字典，提取 item
                items = []
                if isinstance(data_content, dict):
                    items = data_content.get('item', [])
                    if not self._first_logged:
                        print(f"      提取items字段，找到: {len(items)} 项")
                elif isinstance(data_content, list):
                    items = data_content
                    if not self._first_logged:
                        print(f"      data本身就是列表: {len(items)} 项")
                
                # 首次显示分数线字段
                if not self._first_logged and items and isinstance(items, list) and len(items) > 0:
                    sample = items[0]
                    if isinstance(sample, dict):
                        fields = list(sample.keys())
                        print(f"\n      分数线数据字段({len(fields)}个):")
                        print(f"      {'─'*50}")
                        for i, field in enumerate(fields, 1):
                            value = sample[field]
                            value_type = type(value).__name__
                            # 显示值的预览
                            if value is None:
                                preview = "None"
                            elif isinstance(value, str):
                                preview = f'"{value[:25]}..."' if len(value) > 25 else f'"{value}"'
                            elif isinstance(value, (list, dict)):
                                preview = f"{value_type}({len(value)}项)"
                            else:
                                preview = str(value)
                            print(f"      {i:2}. {field:25} = {preview}")
                        print(f"      {'─'*50}\n")
                        self._first_logged = True
                
                if items and isinstance(items, list):
                    for item in items:
                        score_info = {
                            # 基础标识
                            'school_id': school_id,
                            'year': year,
                            
                            # 地区信息
                            'province': item.get('province_name') or item.get('local_province_name'),
                            
                            # 录取批次和类型
                            'batch': item.get('local_batch_name'),
                            'type': item.get('local_type_name'),
                            
                            # 专业信息
                            'major': item.get('spname') or item.get('special_name'),
                            'major_code': item.get('spcode'),
                            
                            # 分数信息
                            'min_score': item.get('min'),
                            'avg_score': item.get('average') or item.get('avg'),
                            'max_score': item.get('max'),
                            'min_section': item.get('min_section'),
                            'proscore': item.get('proscore'),
                            
                            # 招生人数
                            'enrollment_count': item.get('sg_info') or item.get('zs_num'),
                        }
                        all_scores.append(score_info)
                    
                    school_score_count += len(items)
                    print(f"      ✓ {year}年: 获取 {len(items)} 条分数线")
                else:
                    print(f"      ⚠️  {year}年: 无分数线数据")
                
                self.polite_sleep(3.0, 6.0)
            
            if school_score_count > 0:
                print(f"   ✅ 学校ID {school_id}：共 {school_score_count} 条分数线")
            else:
                print(f"   ⚠️  学校ID {school_id}：无分数线数据")
            
            # 学校间更长延迟
            if idx < len(school_ids):
                self.polite_sleep(5.0, 8.0)
        
        # 保存数据
        self.save_to_json(all_scores, 'scores.json')
        
        print(f"\n{'='*60}")
        print(f"✅ 分数线爬取完成！")
        print(f"   总计: {len(all_scores)} 条分数线")
        if all_scores:
            print(f"   字段数: {len(all_scores[0].keys())}")
            # 统计覆盖的省份
            provinces = set(s.get('province') for s in all_scores if s.get('province'))
            print(f"   覆盖省份: {len(provinces)} 个")
            # 统计年份分布
            year_counts = {}
            for score in all_scores:
                y = score.get('year')
                year_counts[y] = year_counts.get(y, 0) + 1
            print(f"   年份分布: {dict(sorted(year_counts.items(), reverse=True))}")
        print(f"{'='*60}\n")
        
        return all_scores

if __name__ == "__main__":
    crawler = ScoreCrawler()
    crawler.crawl()
