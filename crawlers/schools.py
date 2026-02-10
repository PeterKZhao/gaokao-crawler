import time
import os
import hashlib
import hmac
import base64
import json
from .base import BaseCrawler

class SchoolCrawler(BaseCrawler):
    
    def generate_signsafe(self, params):
        """生成signsafe签名"""
        secret = "D23ABC@#56"
        sorted_keys = sorted(params.keys())
        query_string = '&'.join([f"{k}={params[k]}" for k in sorted_keys])
        sign_string = f"api-gaokao.zjzw.cn/apidata/web?{query_string}"
        
        hmac_result = hmac.new(
            secret.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        base64_result = base64.b64encode(hmac_result).decode('utf-8')
        final_signature = hashlib.md5(base64_result.encode('utf-8')).hexdigest()
        
        return final_signature
    
    def get_school_complete_info(self, school_id):
        """获取学校完整信息"""
        url = f"https://static-data.gaokao.cn/www/2.0/school/{school_id}/info.json"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == '0000' and 'data' in result:
                    return result['data']
        except Exception as e:
            print(f"⚠️  获取完整信息失败 (ID:{school_id}): {str(e)}")
        
        return None

    def get_enhanced_school_list(self, page=1, size=20):
        """获取增强版学校列表"""
        base_url = "https://api-gaokao.zjzw.cn/apidata/web"
        cookie = os.getenv('GAOKAO_COOKIE', '')
        
        params = {
            "autosign": "",
            "keyword": "",
            "local_type_id": "2073",
            "page": str(page),
            "platform": "2",
            "province_id": "",
            "ranktype": "",
            "request_type": "1",
            "size": str(size),
            "spe_ids": "",
            "top_school_id": "",
            "uri": "v1/school/lists"
        }
        
        signsafe = self.generate_signsafe(params)
        query_string = '&'.join([f"{k}={params[k]}" for k in sorted(params.keys())])
        full_url = f"{base_url}?{query_string}&signsafe={signsafe}"
        
        post_body = {
            "autosign": "",
            "keyword": "",
            "local_type_id": 2073,
            "page": int(page),
            "platform": "2",
            "province_id": "",
            "ranktype": "",
            "request_type": 1,
            "signsafe": signsafe,
            "size": int(size),
            "spe_ids": "",
            "top_school_id": "",
            "uri": "v1/school/lists"
        }
        
        headers = self.headers.copy()
        if cookie:
            headers["cookie"] = cookie
        
        try:
            response = self.session.post(
                full_url,
                headers=headers,
                data=json.dumps(post_body),
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    return result
        except Exception as e:
            if page == 1:
                print(f"⚠️  增强数据请求失败: {str(e)}")
        
        return None
    
    def merge_enhanced_data(self, schools_basic, max_pages=10):
        """将增强数据合并到基础学校列表"""
        enhanced_dict = {}
        page = 1
        
        print(f"正在获取增强数据...")
        
        while page <= max_pages:
            enhanced_data = self.get_enhanced_school_list(page=page, size=20)
            
            if enhanced_data and enhanced_data.get('code') == 0:
                items = enhanced_data.get('data', {}).get('item', [])
                
                if not items:
                    break
                
                for item in items:
                    school_id = item.get('school_id')
                    if school_id:
                        enhanced_dict[school_id] = {
                            'label_list': item.get('label_list', []),
                            'recommend_master_level': item.get('recommend_master_level'),
                            'is_top': item.get('is_top'),
                            'attr_list': item.get('attr_list', []),
                            'hightitle': item.get('hightitle')
                        }
                
                page += 1
                self.polite_sleep(3.0, 6.0)
            else:
                if page == 1 and not os.getenv('GAOKAO_COOKIE'):
                    print(f"💡 提示：设置GAOKAO_COOKIE环境变量可获取更多数据")
                break
        
        # 合并数据
        merged_count = 0
        for school in schools_basic:
            school_id = school.get('school_id')
            if school_id and school_id in enhanced_dict:
                school.update(enhanced_dict[school_id])
                merged_count += 1
        
        print(f"✓ 合并增强数据: {merged_count}/{len(schools_basic)} 所学校")
        
        return schools_basic
    
    def crawl(self, max_pages=None, fetch_complete_info=True, fetch_enhanced=True):
        """爬取学校列表"""
        max_pages = max_pages or int(os.getenv('MAX_PAGES', '10'))
        fetch_complete_info = os.getenv('FETCH_COMPLETE_INFO', str(fetch_complete_info)).lower() == 'true'
        fetch_enhanced = os.getenv('FETCH_ENHANCED', str(fetch_enhanced)).lower() == 'true'
        
        schools = []
        print(f"\n{'='*60}")
        print(f"开始爬取学校数据")
        print(f"页数: {max_pages} | 完整信息: {'✓' if fetch_complete_info else '✗'} | 增强数据: {'✓' if fetch_enhanced else '✗'}")
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
            
            if not data or 'data' not in data or 'item' not in data['data']:
                print(f"✗ 第 {page} 页请求失败")
                break
            
            items = data['data']['item']
            if not items:
                print(f"✗ 第 {page} 页无数据")
                break
            
            print(f"第 {page} 页: 获取 {len(items)} 所学校", end='', flush=True)
            
            for idx, item in enumerate(items, 1):
                school_id = item.get('school_id')
                
                # 从基础列表提取字段
                school_info = {
                    # 基础标识
                    'school_id': school_id,
                    'name': item.get('name'),
                    
                    # 地理位置
                    'province': item.get('province_name'),
                    'city': item.get('city_name'),
                    'county': item.get('county_name'),
                    
                    # 学校属性
                    'type': item.get('type_name'),
                    'level': item.get('level_name'),
                    'nature': item.get('nature_name'),
                    'belong': item.get('belong'),
                    
                    # 排名与标识
                    'rank': item.get('rank'),
                    'f985': item.get('f985'),
                    'f211': item.get('f211'),
                    'dual_class': item.get('dual_class_name'),
                    'is_dual_class': item.get('dual_class'),
                    
                    # 统计数据
                    'view_total': item.get('view_total'),
                }
                
                # 获取完整信息（128个字段）
                if fetch_complete_info and school_id:
                    complete_info = self.get_school_complete_info(school_id)
                    if complete_info:
                        school_info.update({
                            # 学校介绍
                            'content': complete_info.get('content'),
                            'motto': complete_info.get('motto'),
                            'old_name': complete_info.get('old_name'),
                            
                            # 联系方式
                            'email': complete_info.get('email'),
                            'school_email': complete_info.get('school_email'),
                            'phone': complete_info.get('phone'),
                            'school_phone': complete_info.get('school_phone'),
                            'address': complete_info.get('address'),
                            'postcode': complete_info.get('postcode'),
                            
                            # 网站链接
                            'site': complete_info.get('site'),  # 招生网
                            'school_site': complete_info.get('school_site'),  # 官网
                            
                            # 建校信息
                            'create_date': complete_info.get('create_date'),
                            'area': complete_info.get('area'),  # 占地面积
                            
                            # 学科实力
                            'num_doctor': complete_info.get('num_doctor'),  # 博士点
                            'num_master': complete_info.get('num_master'),  # 硕士点
                            'num_subject': complete_info.get('num_subject'),  # 重点学科
                            'num_academician': complete_info.get('num_academician'),  # 院士
                            'num_library': complete_info.get('num_library'),  # 图书馆藏书
                            
                            # 升学数据
                            'recommend_master_rate': complete_info.get('recommend_master_rate'),  # 保研率
                            'upgrading_rate': complete_info.get('upgrading_rate'),  # 升学率
                            
                            # 排名数据
                            'ruanke_rank': complete_info.get('ruanke_rank'),  # 软科排名
                            'xyh_rank': complete_info.get('xyh_rank'),  # 校友会排名
                            'wsl_rank': complete_info.get('wsl_rank'),  # 武书连排名
                            'qs_rank': complete_info.get('qs_rank'),  # QS排名
                            'us_rank': complete_info.get('us_rank'),  # US排名
                            'qs_world': complete_info.get('qs_world'),  # QS世界排名
                            
                            # 其他详细信息
                            'label_list_detail': complete_info.get('label_list'),  # 详细标签
                            'attr_list_detail': complete_info.get('attr_list'),  # 详细属性
                            'dualclass': complete_info.get('dualclass'),  # 双一流学科列表
                            'special': complete_info.get('special'),  # 特色专业列表
                            'province_score_min': complete_info.get('province_score_min'),  # 各省最低分
                            'rank_detail': complete_info.get('rank'),  # 详细排名字典
                        })
                        
                        self.polite_sleep(2.0, 4.0)
                
                schools.append(school_info)
                
                # 进度显示
                if idx % 5 == 0:
                    print('.', end='', flush=True)
            
            print(f" ✓")
            self.polite_sleep(3.0, 6.0)
        
        # 合并增强数据
        if fetch_enhanced and schools:
            enhanced_pages = max(max_pages, (len(schools) // 20) + 2)
            schools = self.merge_enhanced_data(schools, max_pages=enhanced_pages)
        
        # 保存数据
        self.save_to_json(schools, 'schools.json')
        
        print(f"\n{'='*60}")
        print(f"✅ 爬取完成！共 {len(schools)} 所学校")
        if schools:
            # 统计字段数
            field_count = len(schools[0].keys())
            has_content = bool(schools[0].get('content'))
            has_email = bool(schools[0].get('email'))
            print(f"   字段数: {field_count}")
            print(f"   学校介绍: {'✓' if has_content else '✗'}")
            print(f"   联系邮箱: {'✓' if has_email else '✗'}")
        print(f"{'='*60}\n")
        
        return schools

if __name__ == "__main__":
    import sys
    
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    fetch_complete_info = sys.argv[2].lower() == 'true' if len(sys.argv) > 2 else True
    fetch_enhanced = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else True
    
    crawler = SchoolCrawler()
    crawler.crawl(
        max_pages=max_pages, 
        fetch_complete_info=fetch_complete_info,
        fetch_enhanced=fetch_enhanced
    )
