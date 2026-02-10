import time
import json
import os
from .base import BaseCrawler

class ScoreCrawler(BaseCrawler):
    def crawl(self, school_ids=None, province_id="", years=None, debug=True):
        """爬取分数线数据"""
        years = years or ["2025", "2024", "2023"]
        
        # 从环境变量读取调试模式
        debug = os.getenv('DEBUG_MODE', str(debug)).lower() == 'true'
        
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
        if debug:
            print(f"🔍 调试模式已开启")
        print(f"{'='*60}\n")
        
        for idx, school_id in enumerate(school_ids, 1):
            school_score_count = 0
            
            # 只在第一所学校显示详细调试信息
            show_debug = debug and idx == 1
            
            for year in years:
                payload = {
                    "school_id": school_id,
                    "province_id": province_id,
                    "year": year,
                    "uri": "apidata/api/gkv3/school/scoreline"
                }
                
                if show_debug:
                    print(f"\n🔍 调试信息 - 学校ID {school_id} {year}年")
                    print(f"   请求payload: {json.dumps(payload, ensure_ascii=False)}")
                
                data = self.make_request(payload)
                
                if show_debug:
                    print(f"   响应状态: {'成功' if data else '失败'}")
                    if data:
                        print(f"   响应结构: {list(data.keys())}")
                        print(f"   完整响应: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
                
                # 检查数据有效性
                if not data:
                    if show_debug:
                        print(f"   ❌ 响应为空")
                    continue
                
                if 'data' not in data:
                    if show_debug:
                        print(f"   ❌ 响应中无'data'字段")
                    continue
                
                # 处理不同的数据结构
                data_content = data['data']
                
                if show_debug:
                    print(f"   data类型: {type(data_content).__name__}")
                    if isinstance(data_content, str):
                        print(f"   data内容（前200字符）: {data_content[:200]}")
                    elif isinstance(data_content, dict):
                        print(f"   data字典键: {list(data_content.keys())}")
                    elif isinstance(data_content, list):
                        print(f"   data列表长度: {len(data_content)}")
                
                # 如果 data 是字符串，尝试解析
                if isinstance(data_content, str):
                    try:
                        data_content = json.loads(data_content)
                        if show_debug:
                            print(f"   ✓ 字符串成功解析为: {type(data_content).__name__}")
                    except Exception as e:
                        print(f"⚠️  [{idx}/{len(school_ids)}] 学校ID {school_id} {year}年：JSON解析失败 - {str(e)}")
                        if show_debug:
                            print(f"   原始字符串: {data_content}")
                        continue
                
                # 如果 data 是字典，提取 item
                items = []
                if isinstance(data_content, dict):
                    items = data_content.get('item', [])
                    if not items and show_debug:
                        print(f"   ⚠️  字典中无'item'字段，可用字段: {list(data_content.keys())}")
                        # 尝试其他可能的字段名
                        for key in ['items', 'list', 'data', 'result']:
                            if key in data_content:
                                items = data_content.get(key, [])
                                print(f"   尝试使用字段'{key}': {len(items) if isinstance(items, list) else '非列表'}")
                                break
                # 如果 data 直接是列表
                elif isinstance(data_content, list):
                    items = data_content
                else:
                    if show_debug:
                        print(f"   ❌ 未知的data类型: {type(data_content)}")
                    continue
                
                if show_debug:
                    print(f"   提取到的items数量: {len(items) if isinstance(items, list) else '非列表'}")
                
                if items and isinstance(items, list):
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
                    
                    if show_debug:
                        print(f"   ✓ 成功提取 {len(items)} 条分数线")
                        print(f"   示例数据: {json.dumps(items[0], ensure_ascii=False, indent=2)[:300]}...")
                
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
