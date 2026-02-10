import time
import os
import hashlib
import hmac
import base64
from .base import BaseCrawler

class SchoolCrawler(BaseCrawler):
    
    def generate_signsafe(self, params):
        """
        生成signsafe签名
        算法：MD5(Base64(HmacSHA1(参数字符串, 密钥)))
        """
        secret = "D23ABC@#56"
        
        # 1. 过滤空参数并按字母排序
        filtered = {k: v for k, v in params.items() if v}
        sorted_keys = sorted(filtered.keys())
        query_string = '&'.join([f"{k}={filtered[k]}" for k in sorted_keys])
        
        # 2. HmacSHA1
        hmac_result = hmac.new(
            secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        # 3. Base64编码
        base64_result = base64.b64encode(hmac_result).decode('utf-8')
        
        # 4. MD5
        final_signature = hashlib.md5(base64_result.encode('utf-8')).hexdigest()
        
        return final_signature
    
    def get_school_detail(self, school_id):
        """获取学校详细信息"""
        payload = {
            "school_id": school_id,
            "uri": "apidata/api/gkv3/school/detail"
        }
        
        data = self.make_request(payload, retry=2)
        
        if data and 'data' in data:
            return data['data']
        return None
    
    def get_enhanced_school_list(self, page=1, size=20, local_type_id=""):
        """
        获取增强版学校列表（包含label_list等新字段）
        """
        enhanced_url = "https://api-gaokao.zjzw.cn/apidata/web"
        
        # 构建参数
        params = {
            "autosign": "",
            "keyword": "",
            "local_type_id": str(local_type_id) if local_type_id else "",
            "page": str(page),
            "platform": "2",
            "province_id": "",
            "ranktype": "",
            "request_type": "1",
            "size": str(size),
            "spe_ids": "",
            "top_school_id": "",
            "uri": "v1/school/lists",
        }
        
        # 生成签名
        signsafe = self.generate_signsafe(params)
        params["signsafe"] = signsafe
        
        try:
            response = self.session.post(
                enhanced_url,
                params=params,
                json={},
                headers={
                    "accept": "application/json, text/plain, */*",
                    "accept-language": "zh-CN,zh;q=0.9",
                    "content-type": "application/json",
                    "origin": "https://www.gaokao.cn",
                    "referer": "https://www.gaokao.cn/",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"增强接口请求失败，状态码: {response.status_code}")
                
        except Exception as e:
            print(f"增强接口请求出错: {str(e)}")
        
        return None
    
    def merge_enhanced_data(self, schools_basic, max_pages=None):
        """将增强数据合并到基础学校列表"""
        enhanced_dict = {}
        
        if max_pages is None:
            max_pages = 10
        
        print(f"\n{'='*60}")
        print(f"开始获取增强版学校数据...")
        print(f"{'='*60}\n")
        
        page = 1
        total_fetched = 0
        
        while page <= max_pages:
            enhanced_data = self.get_enhanced_school_list(page=page, size=20)
            
            if enhanced_data and enhanced_data.get('code') == 0:
                items = enhanced_data.get('data', {}).get('item', [])
                
                if not items:
                    print(f"✓ 增强数据第 {page} 页无数据，已完成")
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
                        total_fetched += 1
                
                print(f"✓ 增强数据第 {page} 页：获取 {len(items)} 所学校（累计{total_fetched}所）")
                time.sleep(1)
                page += 1
            else:
                error_msg = enhanced_data.get('message', '未知错误') if enhanced_data else '请求失败'
                print(f"✗ 增强数据第 {page} 页：{error_msg}")
                break
        
        # 合并数据
        merged_count = 0
        for school in schools_basic:
            school_id = school.get('school_id')
            if school_id and school_id in enhanced_dict:
                school.update(enhanced_dict[school_id])
                merged_count += 1
        
        print(f"\n✓ 成功合并 {merged_count}/{len(schools_basic)} 所学校的增强数据")
        print(f"  (增强数据库共{len(enhanced_dict)}所，基础数据{len(schools_basic)}所)\n")
        
        return schools_basic
    
    def crawl(self, max_pages=None, fetch_detail=True, fetch_enhanced=True):
        """
        爬取学校列表
        :param max_pages: 最大页数
        :param fetch_detail: 是否获取详细信息
        :param fetch_enhanced: 是否获取增强数据（label_list等新字段）
        """
        if max_pages is None:
            max_pages = int(os.getenv('MAX_PAGES', '10'))
        
        fetch_detail = os.getenv('FETCH_DETAIL', str(fetch_detail)).lower() == 'true'
        fetch_enhanced = os.getenv('FETCH_ENHANCED', str(fetch_enhanced)).lower() == 'true'
        
        schools = []
        print(f"\n{'='*60}")
        print(f"开始爬取学校列表（最多 {max_pages} 页）")
        print(f"详细信息模式: {'开启' if fetch_detail else '关闭'}")
        print(f"增强数据模式: {'开启' if fetch_enhanced else '关闭'}")
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
                    
                    school_info = {
                        'school_id': school_id,
                        'name': item.get('name'),
                        'province': item.get('province_name'),
                        'city': item.get('city_name'),
                        'county': item.get('county_name'),
                        'type': item.get('type_name'),
                        'level': item.get('level_name'),
                        'belong': item.get('belong'),
                        'rank': item.get('rank'),
                        'dual_class': item.get('dual_class_name'),
                        'f985': item.get('f985'),
                        'f211': item.get('f211'),
                        'is_dual_class': item.get('dual_class'),
                        'central': item.get('central'),
                        'nature': item.get('nature_name'),
                        'view_month': item.get('view_month'),
                        'view_total': item.get('view_total'),
                        'view_week': item.get('view_week'),
                        'alumni': item.get('alumni'),
                        'city_id': item.get('city_id'),
                        'county_id': item.get('county_id'),
                        'province_id': item.get('province_id'),
                        'type_id': item.get('type'),
                        'level_id': item.get('level'),
                    }
                    
                    if fetch_detail and school_id:
                        detail = self.get_school_detail(school_id)
                        if detail:
                            school_info.update({
                                'logo': detail.get('logo'),
                                'img': detail.get('img'),
                                'address': detail.get('address'),
                                'postcode': detail.get('postcode'),
                                'phone': detail.get('phone'),
                                'email': detail.get('email'),
                                'website': detail.get('site'),
                                'tags': detail.get('tags'),
                                'feature': detail.get('feature'),
                                'school_feature': detail.get('school_feature'),
                                'academician': detail.get('academician'),
                                'national_feature': detail.get('national_feature'),
                                'key_discipline': detail.get('key_discipline'),
                                'master_degree': detail.get('master_degree'),
                                'doctor_degree': detail.get('doctor_degree'),
                                'recruit': detail.get('recruit'),
                                'admission_brochure': detail.get('admissions_brochure'),
                                'history': detail.get('content'),
                                'found_time': detail.get('create_date'),
                                'area': detail.get('area'),
                                'student_num': detail.get('student_num'),
                                'teacher_num': detail.get('teacher_num'),
                                'motto': detail.get('motto'),
                                'anniversary': detail.get('anniversary'),
                                'old_name': detail.get('old_name'),
                                'dorm_condition': detail.get('dorm_condition'),
                                'canteen_condition': detail.get('canteen_condition'),
                                'is_985': detail.get('f985'),
                                'is_211': detail.get('f211'),
                                'is_double_first_class': detail.get('dual_class'),
                                'has_graduate_school': detail.get('graduate_school'),
                                'has_independent_enrollment': detail.get('independent_enrollment'),
                                'subject_evaluate': detail.get('subject_evaluate'),
                                'dual_class_disciplines': detail.get('dual_class_name_dict'),
                            })
                            time.sleep(0.5)
                    
                    schools.append(school_info)
                
                print(f"✓ 第 {page} 页：获取 {len(items)} 所学校" + 
                      (" (含详情)" if fetch_detail else ""))
            else:
                print(f"✗ 第 {page} 页：请求失败")
                break
            
            time.sleep(1)
        
        if fetch_enhanced and schools:
            enhanced_pages = max(max_pages, (len(schools) // 20) + 2)
            schools = self.merge_enhanced_data(schools, max_pages=enhanced_pages)
        
        self.save_to_json(schools, 'schools.json')
        print(f"\n{'='*60}")
        print(f"学校爬取完成！共 {len(schools)} 所")
        print(f"{'='*60}\n")
        
        return schools

if __name__ == "__main__":
    import sys
    
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    fetch_detail = sys.argv[2].lower() == 'true' if len(sys.argv) > 2 else True
    fetch_enhanced = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else True
    
    crawler = SchoolCrawler()
    crawler.crawl(max_pages=max_pages, fetch_detail=fetch_detail, fetch_enhanced=fetch_enhanced)
