import time
import json
import os
from .base import BaseCrawler

class SchoolScoreCrawler(BaseCrawler):
    
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
    
    def get_school_info(self, school_id):
        """获取学校详细信息（包含各省最低分）"""
        url = f"https://static-data.gaokao.cn/www/2.0/school/{school_id}/info.json"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == '0000' and 'data' in result:
                    return result['data']
        except Exception as e:
            print(f"      ⚠️  获取学校信息失败 (ID:{school_id}): {str(e)}")
        
        return None
    
    def crawl(self, school_ids=None):
        """爬取大学最低分数线数据"""
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
                    
                    sample_count = int(os.getenv('SAMPLE_SCHOOLS', '999999'))
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
        
        all_school_scores = []
        
        print(f"\n{'='*60}")
        print(f"开始爬取大学最低分数线")
        print(f"学校数: {len(school_ids)}")
        print(f"{'='*60}\n")
        
        for idx, school_id in enumerate(school_ids, 1):
            print(f"[{idx}/{len(school_ids)}] 学校ID: {school_id}", end='', flush=True)
            
            school_info = self.get_school_info(school_id)
            
            if not school_info:
                print(f" ✗ 无数据")
                continue
            
            school_name = school_info.get('name', '未知')
            province_score_min = school_info.get('province_score_min', {})
            
            # 首次显示数据结构
            if not self._first_logged and province_score_min:
                print(f"\n\n   📡 [学校最低分接口] school_id={school_id}")
                print(f"      URL: https://static-data.gaokao.cn/www/2.0/school/{school_id}/info.json")
                print(f"\n      {'─'*50}")
                print(f"      首次响应数据结构:")
                print(f"      {'─'*50}")
                print(f"      学校名称: {school_name}")
                print(f"      province_score_min 类型: {type(province_score_min).__name__}")
                print(f"      包含省份数: {len(province_score_min)}")
                
                # 显示第一个省份的数据样例
                if province_score_min:
                    sample_province_id = list(province_score_min.keys())[0]
                    sample_data = province_score_min[sample_province_id]
                    print(f"\n      样例数据（省份ID: {sample_province_id}）:")
                    print(f"      {'─'*50}")
                    if isinstance(sample_data, dict):
                        for key, value in sample_data.items():
                            print(f"         {key:20} = {value}")
                    print(f"      {'─'*50}\n")
                
                self._first_logged = True
            
            if not province_score_min:
                print(f" ⚠️  {school_name} - 无分数线数据")
                continue
            
            score_count = 0
            
            # 解析各省分数线
            for province_id, score_data in province_score_min.items():
                if not isinstance(score_data, dict):
                    continue
                
                province_name = self.province_dict.get(province_id, f'省份{province_id}')
                
                school_score_record = {
                    # 学校信息
                    'school_id': school_id,
                    'school_name': school_name,
                    
                    # 地区信息
                    'province_id': province_id,
                    'province': province_name,
                    
                    # 分数信息
                    'type': score_data.get('type'),  # 科类（1=文科,2=理科,3=综合等）
                    'type_name': self.get_type_name(score_data.get('type')),  # 科类名称
                    'min_score': score_data.get('min'),  # 最低分
                    'year': score_data.get('year'),  # 年份
                    
                    # 其他信息
                    'batch': score_data.get('batch'),  # 批次
                    'min_rank': score_data.get('min_section'),  # 最低位次
                }
                
                all_school_scores.append(school_score_record)
                score_count += 1
            
            print(f" ✓ {school_name} - {score_count} 个省份")
            
            # 进度显示
            if idx % 10 == 0:
                print(f"\n   已完成 {idx}/{len(school_ids)} 所学校，累计 {len(all_school_scores)} 条数据\n")
            
            self.polite_sleep(2.0, 4.0)
        
        # 保存数据
        self.save_to_json(all_school_scores, 'school_scores.json')
        
        print(f"\n{'='*60}")
        print(f"✅ 大学最低分数线爬取完成！")
        print(f"   总计: {len(all_school_scores)} 条分数线")
        if all_school_scores:
            print(f"   字段数: {len(all_school_scores[0].keys())}")
            # 统计学校数
            schools = set(s.get('school_id') for s in all_school_scores if s.get('school_id'))
            print(f"   学校数: {len(schools)} 所")
            # 统计覆盖的省份
            provinces = set(s.get('province') for s in all_school_scores if s.get('province'))
            print(f"   覆盖省份: {len(provinces)} 个")
            # 统计年份分布
            year_counts = {}
            for score in all_school_scores:
                y = score.get('year')
                if y:
                    year_counts[y] = year_counts.get(y, 0) + 1
            if year_counts:
                print(f"   年份分布: {dict(sorted(year_counts.items(), reverse=True))}")
        print(f"{'='*60}\n")
        
        return all_school_scores
    
    def get_type_name(self, type_code):
        """科类代码转名称"""
        type_map = {
            '1': '文科',
            '2': '理科',
            '3': '综合',
            '4': '物理类',
            '5': '历史类',
        }
        return type_map.get(str(type_code), f'类型{type_code}')

if __name__ == "__main__":
    crawler = SchoolScoreCrawler()
    crawler.crawl()
