import time
import json
import os
from .base import BaseCrawler

class ScoreCrawler(BaseCrawler):
    
    def __init__(self):
        super().__init__()
        self._first_logged = False
        
        # 省份ID映射（部分示例）
        self.province_dict = {
            '11': '北京', '12': '天津', '13': '河北', '14': '山西', '15': '内蒙古',
            '21': '辽宁', '22': '吉林', '23': '黑龙江',
            '31': '上海', '32': '江苏', '33': '浙江', '34': '安徽', '35': '福建',
            '36': '江西', '37': '山东',
            '41': '河南', '42': '湖北', '43': '湖南', '44': '广东', '45': '广西',
            '46': '海南',
            '50': '重庆', '51': '四川', '52': '贵州', '53': '云南', '54': '西藏',
            '61': '陕西', '62': '甘肃', '63': '青海', '64': '宁夏', '65': '新疆'
        }
    
    def get_score_data(self, school_id, year, province_id):
        """获取指定学校、年份、省份的分数线数据"""
        url = f"https://static-data.gaokao.cn/www/2.0/schoolspecialscore/{school_id}/{year}/{province_id}.json"
        
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == '0000' and 'data' in result:
                    return result['data']
            elif response.status_code == 404:
                return 'no_data'  # 该省份无招生
        except Exception as e:
            print(f"         ⚠️  请求异常: {str(e)}")
        
        return None
    
    def crawl(self, school_ids=None, years=None, province_ids=None):
        """爬取分数线数据"""
        years = years or ["2025", "2024", "2023"]
        province_ids = province_ids or list(self.province_dict.keys())
        
        # 从schools.json读取学校ID
        if school_ids is None:
            try:
                with open('data/schools.json', 'r', encoding='utf-8') as f:
                    schools_data = json.load(f)
                    sample_count = int(os.getenv('SAMPLE_SCHOOLS', '3'))
                    school_ids = [s['school_id'] for s in schools_data[:sample_count] if s.get('school_id')]
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
        print(f"学校数: {len(school_ids)} | 年份: {', '.join(years)} | 省份: {len(province_ids)} 个")
        print(f"{'='*60}\n")
        
        for idx, school_id in enumerate(school_ids, 1):
            school_score_count = 0
            
            print(f"\n[{idx}/{len(school_ids)}] 学校ID: {school_id}")
            
            for year in years:
                year_count = 0
                
                for province_id in province_ids:
                    province_name = self.province_dict.get(province_id, f'省份{province_id}')
                    
                    # 只在第一所学校第一个年份第一个省份显示详细日志
                    show_detail = (idx == 1 and year == years[0] and province_id == province_ids[0])
                    
                    if show_detail:
                        print(f"\n   📡 [分数线接口] school_id={school_id}, year={year}, province={province_name}")
                        print(f"      URL: https://static-data.gaokao.cn/www/2.0/schoolspecialscore/{school_id}/{year}/{province_id}.json")
                    
                    data = self.get_score_data(school_id, year, province_id)
                    
                    # 首次显示响应结构
                    if not self._first_logged and data and data != 'no_data':
                        print(f"\n      {'─'*50}")
                        print(f"      首次响应数据结构:")
                        print(f"      {'─'*50}")
                        print(f"      data类型: {type(data).__name__}")
                        print(f"      data包含键: {list(data.keys())}")
                        
                        # 查找第一个有数据的类型
                        sample_item = None
                        for major_type, major_info in data.items():
                            items = major_info.get('item', [])
                            if items:
                                sample_item = items[0]
                                print(f"      招生类型: {major_type}")
                                print(f"      该类型数据条数: {len(items)}")
                                break
                        
                        if sample_item:
                            fields = list(sample_item.keys())
                            print(f"\n      分数线数据字段({len(fields)}个):")
                            print(f"      {'─'*50}")
                            for i, field in enumerate(fields, 1):
                                value = sample_item[field]
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
                    
                    # 处理数据
                    if data == 'no_data':
                        # 该省份无招生，不记录
                        continue
                    elif data and isinstance(data, dict):
                        # 遍历所有招生类型（普通类、中外合作等）
                        for major_type, major_info in data.items():
                            items = major_info.get('item', [])
                            
                            for item in items:
                                score_info = {
                                    # 基础标识
                                    'school_id': school_id,
                                    'year': year,
                                    'province_id': province_id,
                                    'province': province_name,
                                    
                                    # 招生类型
                                    'major_type': major_type,  # 普通类、中外合作等
                                    'batch': item.get('local_batch_name'),  # 招生批次
                                    'type': item.get('type'),  # 科类
                                    'recruit_type': item.get('zslx_name'),  # 录取类型
                                    
                                    # 专业信息
                                    'major': item.get('sp_name') or item.get('spname'),
                                    'major_code': item.get('spcode'),
                                    'major_group': item.get('sg_name'),  # 专业组名称
                                    'major_group_info': item.get('sg_info'),  # 专业组要求
                                    
                                    # 学科分类
                                    'level1_name': item.get('level1_name'),
                                    'level2_name': item.get('level2_name'),
                                    'level3_name': item.get('level3_name'),
                                    
                                    # 分数信息
                                    'min_score': item.get('min'),
                                    'max_score': item.get('max'),
                                    'avg_score': item.get('average') or item.get('avg'),
                                    'min_rank': item.get('min_section'),  # 最低位次
                                    'proscore': item.get('proscore'),  # 省控线
                                    
                                    # 招生人数
                                    'enrollment': item.get('lq_num') or item.get('sg_info'),
                                }
                                all_scores.append(score_info)
                                year_count += 1
                                school_score_count += 1
                    
                    # 控制频率
                    if show_detail:
                        print(f"      ✓ {province_name}: 获取数据")
                    
                    self.polite_sleep(1.5, 3.0)
                
                if year_count > 0:
                    print(f"   ✓ {year}年: 获取 {year_count} 条分数线")
                else:
                    print(f"   ⚠️  {year}年: 无分数线数据")
            
            if school_score_count > 0:
                print(f"   ✅ 学校ID {school_id}：共 {school_score_count} 条分数线")
            else:
                print(f"   ⚠️  学校ID {school_id}：无分数线数据")
            
            # 学校间更长延迟
            if idx < len(school_ids):
                self.polite_sleep(4.0, 7.0)
        
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
