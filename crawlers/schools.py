import time
import os
from .base import BaseCrawler

class SchoolCrawler(BaseCrawler):
    
    def get_school_detail_static(self, school_id):
        """从静态JSON接口获取学校详细信息（数据最全）"""
        url = f"https://static-data.gaokao.cn/www/2.0/school/{school_id}/info.json"
        
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "origin": "https://www.gaokao.cn",
            "referer": "https://www.gaokao.cn/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            import requests
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    return data['data']
        except Exception as e:
            print(f"  静态接口请求失败: {str(e)}")
        
        return None
    
    def parse_tags(self, detail_data):
        """解析并提取所有标签"""
        tags_list = []
        
        if not detail_data:
            return tags_list
        
        # 1. 基础标签
        if detail_data.get('f985') == '1':
            tags_list.append('985')
        if detail_data.get('f211') == '1':
            tags_list.append('211')
        
        # 2. 双一流
        dual_class = detail_data.get('dual_class_name')
        if dual_class and dual_class != '无':
            tags_list.append('双一流')
        
        # 3. 特殊标签（从school_tag字段解析）
        school_tag = detail_data.get('school_tag', '')
        if school_tag:
            # school_tag可能是字符串或数组
            if isinstance(school_tag, str):
                tag_items = school_tag.split(',')
            elif isinstance(school_tag, list):
                tag_items = school_tag
            else:
                tag_items = []
            
            for tag in tag_items:
                tag = str(tag).strip()
                if tag and tag not in tags_list:
                    tags_list.append(tag)
        
        # 4. 从tag字段解析（可能存在的另一个标签字段）
        if 'tag' in detail_data and detail_data['tag']:
            tags = detail_data['tag']
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, dict) and 'name' in tag:
                        tag_name = tag['name']
                    else:
                        tag_name = str(tag)
                    
                    if tag_name and tag_name not in tags_list:
                        tags_list.append(tag_name)
            elif isinstance(tags, str):
                tag_items = tags.split(',')
                for tag in tag_items:
                    tag = tag.strip()
                    if tag and tag not in tags_list:
                        tags_list.append(tag)
        
        # 5. 特殊属性标签
        if detail_data.get('is_qg') == '1':
            tags_list.append('强基')
        if detail_data.get('has_101_plan') == '1' or '101' in str(detail_data.get('feature', '')):
            tags_list.append('101计划')
        if detail_data.get('is_c9') == '1' or 'C9' in str(detail_data.get('feature', '')):
            tags_list.append('C9')
        
        # 6. 联盟和特色标签（从feature或其他字段提取）
        feature_str = str(detail_data.get('feature', '')) + str(detail_data.get('school_feature', ''))
        
        # 定义可能的联盟和特色标签
        known_tags = [
            'C9', '华五', '中坚九校', 'E9', '卓越大学联盟',
            '机械五虎', '电气四虎', '建筑老八校', '两电一邮',
            '国防七子', '五院四系', '外语四校', '龙头高校',
            '强基', '101计划', '111计划', '2011计划',
            '珠峰计划', '卓越工程师', '卓越医生', '卓越法律',
            '中西部高校基础能力建设工程', '小211',
            '省部共建', '部省合建'
        ]
        
        for known_tag in known_tags:
            if known_tag in feature_str and known_tag not in tags_list:
                tags_list.append(known_tag)
        
        return tags_list
    
    def crawl(self, max_pages=None, fetch_detail=True):
        """
        爬取学校列表
        :param max_pages: 最大页数
        :param fetch_detail: 是否获取详细信息（会慢很多但数据更全）
        """
        if max_pages is None:
            max_pages = int(os.getenv('MAX_PAGES', '10'))
        
        fetch_detail = os.getenv('FETCH_DETAIL', str(fetch_detail)).lower() == 'true'
        
        schools = []
        print(f"\n{'='*60}")
        print(f"开始爬取学校列表（最多 {max_pages} 页）")
        print(f"详细信息模式: {'开启（含完整标签）' if fetch_detail else '关闭'}")
        print(f"{'='*60}\n")
        
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
            
            data = self.make_request(payload)
            
            if data and 'data' in data and 'item' in data['data']:
                items = data['data']['item']
                if not items:
                    print(f"第 {page} 页无数据，停止爬取")
                    break
                
                for item in items:
                    school_id = item.get('school_id')
                    school_name = item.get('name')
                    
                    # 基础信息
                    school_info = {
                        'school_id': school_id,
                        'name': school_name,
                        'province': item.get('province_name'),
                        'city': item.get('city_name'),
                        'county': item.get('county_name'),
                        'type': item.get('type_name'),
                        'level': item.get('level_name'),
                        'belong': item.get('belong'),
                        'nature': item.get('nature_name'),
                        'rank': item.get('rank'),
                        
                        # 基础标签
                        'f985': item.get('f985'),
                        'f211': item.get('f211'),
                        'dual_class': item.get('dual_class_name'),
                    }
                    
                    # 如果开启详情模式，获取完整信息和标签
                    if fetch_detail and school_id:
                        detail = self.get_school_detail_static(school_id)
                        if detail:
                            # 解析标签
                            tags_list = self.parse_tags(detail)
                            
                            school_info.update({
                                # 标签（最重要）
                                'tags': tags_list,  # 完整标签数组
                                'tags_text': ', '.join(tags_list),  # 标签文本
                                
                                # Logo和图片
                                'logo': detail.get('logo'),
                                'logo_url': f"https://static-data.gaokao.cn{detail.get('logo')}" if detail.get('logo') else None,
                                
                                # 详细地址
                                'address': detail.get('address'),
                                'postcode': detail.get('postcode'),
                                
                                # 联系方式
                                'phone': detail.get('phone'),
                                'email': detail.get('email'),
                                'website': detail.get('site'),
                                
                                # 学校特色
                                'feature': detail.get('feature'),
                                'school_feature': detail.get('school_feature'),
                                'school_tag': detail.get('school_tag'),  # 原始标签数据
                                
                                # 排名信息
                                'ruanke_rank': detail.get('ruanke_rank') or detail.get('rank', {}).get('ruanke_rank'),
                                'qs_world': detail.get('qs_world') or detail.get('rank', {}).get('qs_world'),
                                'us_rank': detail.get('us_rank') or detail.get('rank', {}).get('us_rank'),
                                'xyh_rank': detail.get('xyh_rank'),
                                'wsl_rank': detail.get('wsl_rank'),
                                
                                # 学科和专业
                                'num_subject': detail.get('num_subject'),  # 国家重点学科数
                                'num_master': detail.get('num_master'),  # 硕士点
                                'num_doctor': detail.get('num_doctor'),  # 博士点
                                'num_academician': detail.get('num_academician'),  # 院士数
                                'national_feature': detail.get('national_feature'),
                                'key_discipline': detail.get('key_discipline'),
                                
                                # 双一流学科
                                'dual_class_disciplines': detail.get('dual_class_name_dict'),
                                
                                # 历史和规模
                                'create_date': detail.get('create_date'),
                                'old_name': detail.get('old_name'),
                                'area': detail.get('area'),  # 占地面积
                                'student_num': detail.get('student_num'),
                                'teacher_num': detail.get('teacher_num'),
                                
                                # 其他
                                'motto': detail.get('motto'),
                                'content': detail.get('content'),  # 学校简介
                                'view_total': detail.get('view_total'),  # 人气值
                            })
                            
                            print(f"  ✓ {school_name}: {len(tags_list)} 个标签 {tags_list}")
                        else:
                            school_info['tags'] = []
                            school_info['tags_text'] = ''
                            print(f"  ✗ {school_name}: 详情获取失败")
                        
                        time.sleep(0.8)  # 详情请求需要延时
                    
                    schools.append(school_info)
                
                print(f"✓ 第 {page} 页：获取 {len(items)} 所学校")
            else:
                print(f"✗ 第 {page} 页：请求失败")
                break
            
            time.sleep(1)
        
        self.save_to_json(schools, 'schools.json')
        print(f"\n{'='*60}")
        print(f"学校爬取完成！共 {len(schools)} 所")
        print(f"{'='*60}\n")
        
        return schools

if __name__ == "__main__":
    import sys
    
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    fetch_detail = sys.argv[2].lower() == 'true' if len(sys.argv) > 2 else True
    
    crawler = SchoolCrawler()
    crawler.crawl(max_pages=max_pages, fetch_detail=fetch_detail)
