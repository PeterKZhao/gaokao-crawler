import time
import json
import os
from .base import BaseCrawler

class PlanCrawler(BaseCrawler):
    
    def __init__(self):
        super().__init__()
        self._first_logged = False
        
        # 省份ID映射（中国34个省级行政区）
        self.province_dict = {
            # 华北地区
            '11': '北京',
            '12': '天津',
            '13': '河北',
            '14': '山西',
            '15': '内蒙古',
            
            # 东北地区
            '21': '辽宁',
            '22': '吉林',
            '23': '黑龙江',
            
            # 华东地区
            '31': '上海',
            '32': '江苏',
            '33': '浙江',
            '34': '安徽',
            '35': '福建',
            '36': '江西',
            '37': '山东',
            
            # 华中地区
            '41': '河南',
            '42': '湖北',
            '43': '湖南',
            
            # 华南地区
            '44': '广东',
            '45': '广西',
            '46': '海南',
            
            # 西南地区
            '50': '重庆',
            '51': '四川',
            '52': '贵州',
            '53': '云南',
            '54': '西藏',
            
            # 西北地区
            '61': '陕西',
            '62': '甘肃',
            '63': '青海',
            '64': '宁夏',
            '65': '新疆',
            
            # 港澳台地区（高考数据可能不包含）
            '71': '台湾',
            '81': '香港',
            '82': '澳门',
        }
    
    def get_plan_data(self, school_id, year, province_id):
        """获取指定学校、年份、省份的招生计划数据"""
        url = f"https://static-data.gaokao.cn/www/2.0/schoolspecialplan/{school_id}/{year}/{province_id}.json"
        
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == '0000' and 'data' in result:
                    return result['data']
            elif response.status_code == 404:
                return 'no_data'  # 该省份无招生
        except Exception as e:
            # 静默处理异常，避免过多日志
            pass
        
        return None
    
    def parse_years(self, years_input):
        """解析年份参数，支持多种格式"""
        if isinstance(years_input, list):
            return years_input
        
        if isinstance(years_input, str):
            if '-' in years_input:
                start, end = years_input.split('-')
                return [str(y) for y in range(int(start), int(end) + 1)]
            elif ',' in years_input:
                return [y.strip() for y in years_input.split(',')]
            else:
                return [years_input]
        
        return years_input
    
    def crawl(self, school_ids=None, years=None, province_ids=None):
        """爬取招生计划数据"""
        # 年份控制优先级：
        # 1. 函数参数 years
        # 2. 环境变量 PLAN_YEARS
        # 3. 默认值 ["2025", "2024", "2023"]
        if years is None:
            years_env = os.getenv('PLAN_YEARS', '2025,2024,2023')
            years = self.parse_years(years_env)
        else:
            years = self.parse_years(years)
        
        province_ids = province_ids or list(self.province_dict.keys())
        
        # 从schools.json读取学校ID
        if school_ids is None:
            try:
                with open('data/schools.json', 'r', encoding='utf-8') as f:
                    schools_data = json.load(f)
                    
                    # 处理不同的数据结构
                    if isinstance(schools_data, list):
                        schools = schools_data
                    elif isinstance(schools_data, dict):
                        schools = schools_data.get('data', [])
                        if not schools:
                            schools = [schools_data]
                    else:
                        print(f"⚠️  schools.json 数据格式错误: {type(schools_data)}")
                        return []
                    
                    sample_count = int(os.getenv('SAMPLE_SCHOOLS', '3'))
                    school_ids = [s['school_id'] for s in schools[:sample_count] if isinstance(s, dict) and s.get('school_id')]
                    
                    if not school_ids:
                        print("⚠️  未找到有效的学校ID")
                        return []
                    
                    print(f"从 schools.json 读取到 {len(school_ids)} 所学校")
                    
            except FileNotFoundError:
                print("⚠️  未找到 schools.json，请先运行学校爬虫")
                return []
            except Exception as e:
                print(f"⚠️  读取 schools.json 失败: {e}")
                import traceback
                traceback.print_exc()
                return []
        
        all_plans = []
        
        print(f"\n{'='*60}")
        print(f"开始爬取招生计划")
        print(f"学校数: {len(school_ids)} | 年份: {', '.join(years)} | 省份: {len(province_ids)} 个")
        print(f"{'='*60}\n")
        
        for idx, school_id in enumerate(school_ids, 1):
            school_plan_count = 0
            
            print(f"\n[{idx}/{len(school_ids)}] 学校ID: {school_id}")
            
            for year in years:
                year_count = 0
                
                for province_id in province_ids:
                    province_name = self.province_dict.get(province_id, f'省份{province_id}')
                    
                    # 只在第一所学校第一个年份第一个省份显示详细日志
                    show_detail = (idx == 1 and year == years[0] and province_id == province_ids[0])
                    
                    if show_detail:
                        print(f"\n   📡 [招生计划接口] school_id={school_id}, year={year}, province={province_name}")
                        print(f"      URL: https://static-data.gaokao.cn/www/2.0/schoolspecialplan/{school_id}/{year}/{province_id}.json")
                    
                    data = self.get_plan_data(school_id, year, province_id)
                    
                    # 首次显示响应结构
                    if not self._first_logged and data and data != 'no_data':
                        print(f"\n      {'─'*50}")
                        print(f"      首次响应数据结构:")
                        print(f"      {'─'*50}")
                        print(f"      data类型: {type(data).__name__}")
                        
                        if isinstance(data, dict):
                            print(f"      data包含键: {list(data.keys())}")
                            
                            # 查找第一个有数据的类型
                            sample_item = None
                            for plan_type, plan_info in data.items():
                                if isinstance(plan_info, dict):
                                    items = plan_info.get('item', [])
                                    if items:
                                        sample_item = items[0]
                                        print(f"      招生类型: {plan_type}")
                                        print(f"      该类型数据条数: {len(items)}")
                                        break
                            
                            if sample_item and isinstance(sample_item, dict):
                                fields = list(sample_item.keys())
                                print(f"\n      招生计划数据字段({len(fields)}个):")
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
                        continue
                    elif data and isinstance(data, dict):
                        for plan_type, plan_info in data.items():
                            if not isinstance(plan_info, dict):
                                continue
                                
                            items = plan_info.get('item', [])
                            
                            for item in items:
                                if not isinstance(item, dict):
                                    continue
                                    
                                plan_record = {
                                    # 基础标识
                                    'school_id': school_id,
                                    'year': year,
                                    'province_id': province_id,
                                    'province': province_name,
                                    
                                    # 招生类型
                                    'plan_type': plan_type,  # 普通类、中外合作等
                                    'batch': item.get('local_batch_name'),  # 招生批次
                                    'type': item.get('type'),  # 科类
                                    
                                    # 专业信息
                                    'major': item.get('sp_name') or item.get('spname'),
                                    'major_code': item.get('spcode'),
                                    'major_group': item.get('sg_name'),  # 专业组名称
                                    'major_group_code': item.get('sg_code'),  # 专业组代码
                                    'major_group_info': item.get('sg_info'),  # 专业组要求/选考科目
                                    
                                    # 学科分类
                                    'level1_name': item.get('level1_name'),
                                    'level2_name': item.get('level2_name'),
                                    'level3_name': item.get('level3_name'),
                                    
                                    # 招生人数
                                    'plan_number': item.get('num') or item.get('plan_num'),  # 计划招生人数
                                    
                                    # 学制和学费
                                    'years': item.get('length') or item.get('years'),  # 学制
                                    'tuition': item.get('tuition'),  # 学费
                                    
                                    # 其他信息
                                    'note': item.get('note') or item.get('remark'),  # 备注
                                }
                                all_plans.append(plan_record)
                                year_count += 1
                                school_plan_count += 1
                    
                    if show_detail:
                        print(f"      ✓ {province_name}: 获取数据")
                    
                    self.polite_sleep(1.5, 3.0)
                
                if year_count > 0:
                    print(f"   ✓ {year}年: 获取 {year_count} 条招生计划")
                else:
                    print(f"   ⚠️  {year}年: 无招生计划数据")
            
            if school_plan_count > 0:
                print(f"   ✅ 学校ID {school_id}：共 {school_plan_count} 条招生计划")
            else:
                print(f"   ⚠️  学校ID {school_id}：无招生计划数据")
            
            if idx < len(school_ids):
                self.polite_sleep(4.0, 7.0)
        
        self.save_to_json(all_plans, 'plans.json')
        
        print(f"\n{'='*60}")
        print(f"✅ 招生计划爬取完成！")
        print(f"   总计: {len(all_plans)} 条招生计划")
        if all_plans:
            print(f"   字段数: {len(all_plans[0].keys())}")
            # 统计覆盖的省份
            provinces = set(p.get('province') for p in all_plans if p.get('province'))
            print(f"   覆盖省份: {len(provinces)} 个 - {', '.join(sorted(provinces))}")
            # 统计年份分布
            year_counts = {}
            for plan in all_plans:
                y = plan.get('year')
                year_counts[y] = year_counts.get(y, 0) + 1
            print(f"   年份分布: {dict(sorted(year_counts.items(), reverse=True))}")
            # 统计总招生人数
            total_enrollment = sum(int(p.get('plan_number', 0) or 0) for p in all_plans if p.get('plan_number'))
            print(f"   总招生人数: {total_enrollment}")
        print(f"{'='*60}\n")
        
        return all_plans

if __name__ == "__main__":
    import sys
    
    # 支持命令行参数
    years_arg = sys.argv[1] if len(sys.argv) > 1 else None
    
    crawler = PlanCrawler()
    crawler.crawl(years=years_arg)
