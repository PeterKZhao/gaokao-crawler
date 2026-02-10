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
        
        # 1. 按字母排序（保留所有参数，包括空值）
        sorted_keys = sorted(params.keys())
        
        # 2. 构建查询字符串（包含空值）
        query_string = '&'.join([f"{k}={params[k]}" for k in sorted_keys])
        
        print(f"[DEBUG] 待签名字符串: {query_string}")
        
        # 3. HmacSHA1
        hmac_result = hmac.new(
            secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        # 4. Base64编码
        base64_result = base64.b64encode(hmac_result).decode('utf-8')
        
        # 5. MD5
        final_signature = hashlib.md5(base64_result.encode('utf-8')).hexdigest()
        
        print(f"[DEBUG] 生成签名: {final_signature}")
        
        return final_signature
    
    def get_school_detail(self, school_id):
        """获取学校详细信息"""
        payload = {
            "school_id": school_id,
            "uri": "apidata/api/gkv3/school/detail"
        }
        
        data = self.make_request(payload, retry=2)
        
        if data and 'data' in data:
            detail = data['data']
            if isinstance(detail, dict):
                return detail
        return None
    
    def get_enhanced_school_list(self, page=1, size=20, local_type_id=""):
        """
        获取增强版学校列表（包含label_list等新字段）
        """
        # 手动构建URL，避免自动编码问题
        base_url = "https://api-gaokao.zjzw.cn/apidata/web"
        
        # 构建参数字典用于签名（不包含signsafe）
        params_for_sign = {
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
            "uri": "v1/school/lists"
        }
        
        # 生成签名
        signsafe = self.generate_signsafe(params_for_sign)
        
        # 手动构建URL，保持斜杠不被编码
        sorted_keys = sorted(params_for_sign.keys())
        query_parts = []
        for k in sorted_keys:
            # 对于uri参数，不编码斜杠
            if k == 'uri':
                query_parts.append(f"{k}={params_for_sign[k]}")
            else:
                query_parts.append(f"{k}={params_for_sign[k]}")
        
        query_parts.append(f"signsafe={signsafe}")
        full_url = f"{base_url}?{'&'.join(query_parts)}"
        
        print(f"[DEBUG] 完整URL: {full_url}")
        
        try:
            # 直接使用完整URL发送POST请求
            response = self.session.post(
                full_url,
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
            
            print(f"[DEBUG] 实际请求URL: {response.url}")
            print(f"[DEBUG] 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"[DEBUG] 响应code: {result.get('code')}, message: {result.get('message')}")
                return result
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
                
                if page == 1:
                    print("\n[提示] 增强数据获取失败，将只保存基础数据")
                break
        
        merged_count = 0
        for school in schools_basic:
            school_id = school.get('school_id')
            if school_id and school_id in enhanced_dict:
                school.update(enhanced_dict[school_id])
                merged_count += 1
        
        if merged_count > 0:
            print(f"\n✓ 成功合并 {merged_count}/{len(schools_basic)} 所学校的增强数据")
            print(f"  (增强数据库共{len(enhanced_dict)}所，基础数据{len(schools_basic)}所)\n")
        
        return schools_basic
    
    def crawl(self, max_pages=None, fetch_detail=True, fetch_enhanced=True):
        """爬取学校列表"""
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
                        if detail and isinstance(detail, dict):
                            school_info.update({
                                'logo': detail.get('logo'),
                                'img': detail.get('img'),
                                'address': detail.get('address'),
                                'phone': detail.get('phone'),
                                'email': detail.get('email'),
                                'website': detail.get('site'),
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
    fetch_detail = sys.argv[2].lower() == 'true' if len(sys.argv) > 2 else False
    fetch_enhanced = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else True
    
    crawler = SchoolCrawler()
    crawler.crawl(max_pages=max_pages, fetch_detail=fetch_detail, fetch_enhanced=fetch_enhanced)
