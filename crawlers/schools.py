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
    
    def get_school_detail(self, school_id):
        """获取学校详细信息（通过API）"""
        payload = {
            "school_id": school_id,
            "uri": "apidata/api/gkv3/school/detail"
        }
        
        data = self.make_request(payload, retry=2)
        
        if data and 'data' in data and isinstance(data['data'], dict):
            return data['data']
        return None
    
    def get_school_static_info(self, school_id):
        """获取学校完整静态信息（包含介绍、邮箱等）"""
        # 方式1：带参数的URL
        url = f"https://static-data.gaokao.cn/www/2.0/school/{school_id}/info.json?a=www.gaokao.cn"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                result = response.json()
                
                # 打印第一次获取的数据结构（仅首次调试）
                if not hasattr(self, '_debug_printed'):
                    print(f"\n🔍 调试信息 - 学校ID {school_id} 的静态接口返回字段：")
                    if result.get('code') == 0 and 'data' in result:
                        print(f"   可用字段: {list(result['data'].keys())[:20]}")  # 显示前20个字段
                        # 检查是否有content字段
                        if 'content' in result['data']:
                            content_preview = result['data']['content'][:100] if result['data']['content'] else "空"
                            print(f"   ✓ 找到content字段: {content_preview}...")
                        else:
                            print(f"   ✗ 没有content字段")
                    self._debug_printed = True
                
                if result.get('code') == 0 and 'data' in result:
                    return result['data']
                    
        except Exception as e:
            print(f"⚠️  获取学校静态信息失败 (ID: {school_id}): {str(e)}")
        
        return None
    
    def get_school_content(self, school_id):
        """专门获取学校介绍内容（尝试多个可能的接口）"""
        
        # 方法1: 通过主API获取
        payload = {
            "school_id": school_id,
            "uri": "apidata/api/gkv3/school/detail"
        }
        
        data = self.make_request(payload, retry=2)
        if data and 'data' in data:
            detail_data = data['data']
            # 检查是否有content相关字段
            if 'content' in detail_data:
                return detail_data['content']
            if 'intro' in detail_data:
                return detail_data['intro']
            if 'introduction' in detail_data:
                return detail_data['introduction']
        
        # 方法2: 尝试另一个静态接口
        try:
            url = f"https://static-data.gaokao.cn/www/2.0/schoolSpecial/{school_id}/pc_special.json"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0 and 'data' in result:
                    if 'content' in result['data']:
                        return result['data']['content']
        except:
            pass
        
        return None

    def get_enhanced_school_list(self, page=1, size=20):
        """获取增强版学校列表"""
        base_url = "https://api-gaokao.zjzw.cn/apidata/web"
        cookie = os.getenv('GAOKAO_COOKIE', '')
        
        # 构建参数
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
        
        # 构建URL
        query_string = '&'.join([f"{k}={params[k]}" for k in sorted(params.keys())])
        full_url = f"{base_url}?{query_string}&signsafe={signsafe}"
        
        # POST body（数字类型）
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
                elif result.get('code') == 1010001 and not cookie:
                    print(f"⚠️  增强API需要Cookie认证")
                else:
                    print(f"⚠️  API返回错误: code={result.get('code')}, message={result.get('message')}")
            
        except Exception as e:
            print(f"⚠️  增强数据请求失败: {str(e)}")
        
        return None
    
    def merge_enhanced_data(self, schools_basic, max_pages=10):
        """将增强数据合并到基础学校列表"""
        enhanced_dict = {}
        
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
                    print(f"✓ 增强数据第 {page} 页无数据")
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
                page += 1
                self.polite_sleep(3.0, 6.0)
            else:
                if page == 1 and not os.getenv('GAOKAO_COOKIE'):
                    print("\n💡 提示：增强数据需要Cookie")
                    print("   1. 访问 www.gaokao.cn 并登录")
                    print("   2. F12 控制台输入: document.cookie")
                    print("   3. 设置环境变量: export GAOKAO_COOKIE='你的cookie'\n")
                break
        
        # 合并数据
        merged_count = 0
        for school in schools_basic:
            school_id = school.get('school_id')
            if school_id and school_id in enhanced_dict:
                school.update(enhanced_dict[school_id])
                merged_count += 1
        
        if merged_count > 0:
            print(f"\n✓ 成功合并 {merged_count}/{len(schools_basic)} 所学校的增强数据\n")
        
        return schools_basic
    
    def crawl(self, max_pages=None, fetch_detail=True, fetch_enhanced=True, fetch_static_info=True):
        """爬取学校列表"""
        max_pages = max_pages or int(os.getenv('MAX_PAGES', '10'))
        fetch_detail = os.getenv('FETCH_DETAIL', str(fetch_detail)).lower() == 'true'
        fetch_enhanced = os.getenv('FETCH_ENHANCED', str(fetch_enhanced)).lower() == 'true'
        fetch_static_info = os.getenv('FETCH_STATIC_INFO', str(fetch_static_info)).lower() == 'true'
        
        schools = []
        print(f"\n{'='*60}")
        print(f"开始爬取学校列表（最多 {max_pages} 页）")
        print(f"详细信息: {'✓' if fetch_detail else '✗'} | "
              f"增强数据: {'✓' if fetch_enhanced else '✗'} | "
              f"完整信息: {'✓' if fetch_static_info else '✗'}")
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
                print(f"✗ 第 {page} 页：请求失败")
                break
            
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
                    'nature': item.get('nature_name'),
                    'view_total': item.get('view_total'),
                }
                
                # 获取API详细信息
                if fetch_detail and school_id:
                    detail = self.get_school_detail(school_id)
                    if detail:
                        school_info.update({
                            'logo': detail.get('logo'),
                            'img': detail.get('img'),
                            'address': detail.get('address'),
                            'phone': detail.get('phone'),
                            'email': detail.get('email'),
                            'website': detail.get('site'),
                        })
                        self.polite_sleep(1.0, 2.0)
                
                # 获取静态完整信息（包含介绍等）
                if fetch_static_info and school_id:
                    static_info = self.get_school_static_info(school_id)
                    if static_info:
                        school_info.update({
                            'content': static_info.get('content'),  # 学校介绍
                            'introduction': static_info.get('intro') or static_info.get('introduction'),  # 备用字段
                            'central': static_info.get('central'),  # 是否部属
                            'school_site': static_info.get('school_site'),  # 官网
                            'emails': static_info.get('emails') or static_info.get('email'),  # 邮箱
                            'colleges_level': static_info.get('colleges_level'),  # 院校层次
                            'old_name': static_info.get('old_name'),  # 曾用名
                            'create_year': static_info.get('create_date') or static_info.get('create_year'),  # 创建年份
                            'province_id': static_info.get('province_id'),
                            'city_id': static_info.get('city_id'),
                            'town': static_info.get('town_name') or static_info.get('town'),  # 所在镇/街道
                            'level_name': static_info.get('level_name'),
                            'department': static_info.get('department') or static_info.get('belong'),  # 主管部门
                            'member': static_info.get('member'),  # 学校成员资格
                            'area': static_info.get('area'),  # 占地面积
                            'num_doctor': static_info.get('num_doctor'),  # 博士点
                            'num_master': static_info.get('num_master'),  # 硕士点
                            'num_subject': static_info.get('num_subject'),  # 重点学科
                            'ruanke_rank': static_info.get('ruanke_rank'),  # 软科排名
                            'xyh_rank': static_info.get('xyh_rank'),  # 校友会排名
                            'wsl_rank': static_info.get('wsl_rank'),  # 武书连排名
                        })
                        
                        # 如果没有content，尝试专门获取
                        if not school_info.get('content'):
                            content = self.get_school_content(school_id)
                            if content:
                                school_info['content'] = content
                        
                        self.polite_sleep(2.0, 4.0)
                
                schools.append(school_info)
            
            info_str = ""
            if fetch_detail:
                info_str += "(含详情)"
            if fetch_static_info:
                info_str += "(含完整信息)"
            
            print(f"✓ 第 {page} 页：获取 {len(items)} 所学校 {info_str}")
            self.polite_sleep(3.0, 6.0)
        
        # 合并增强数据
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
    
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 1  # 默认1页用于测试
    fetch_detail = sys.argv[2].lower() == 'true' if len(sys.argv) > 2 else True
    fetch_enhanced = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else True
    fetch_static_info = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else True
    
    crawler = SchoolCrawler()
    crawler.crawl(
        max_pages=max_pages, 
        fetch_detail=fetch_detail, 
        fetch_enhanced=fetch_enhanced,
        fetch_static_info=fetch_static_info
    )
