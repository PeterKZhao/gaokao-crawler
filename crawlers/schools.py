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
        print(f"\n📡 [接口2-详情] school_id={school_id}")
        
        payload = {
            "school_id": school_id,
            "uri": "apidata/api/gkv3/school/detail"
        }
        
        data = self.make_request(payload, retry=2)
        
        if data and 'data' in data and isinstance(data['data'], dict):
            detail_data = data['data']
            fields = list(detail_data.keys())
            print(f"   ✓ 返回字段({len(fields)}个): {', '.join(fields[:10])}{'...' if len(fields) > 10 else ''}")
            
            # 查找content相关字段
            content_fields = [k for k in fields if 'content' in k.lower() or 'intro' in k.lower() or 'desc' in k.lower()]
            if content_fields:
                for key in content_fields:
                    value = detail_data[key]
                    preview = str(value)[:80] if value else "空"
                    print(f"   >>> 发现 '{key}': {preview}...")
            else:
                print(f"   ⚠️  无content/intro相关字段")
            
            return detail_data
        else:
            print(f"   ✗ 请求失败或无数据")
            return None
    
    def get_school_static_info(self, school_id):
        """获取学校完整静态信息（包含介绍、邮箱等）"""
        urls = [
            f"https://static-data.gaokao.cn/www/2.0/school/{school_id}/info.json",
            f"https://static-data.gaokao.cn/www/2.0/school/{school_id}/info.json?a=www.gaokao.cn",
        ]
        
        for url_idx, url in enumerate(urls, 1):
            print(f"\n📡 [接口3-静态] URL{url_idx} school_id={school_id}")
            print(f"   请求: {url}")
            
            try:
                response = self.session.get(url, timeout=10)
                print(f"   状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    code = result.get('code')
                    print(f"   业务码: {code}")
                    
                    if code == 0 and 'data' in result:
                        static_data = result['data']
                        
                        if isinstance(static_data, dict):
                            fields = list(static_data.keys())
                            print(f"   ✓ 返回字段({len(fields)}个): {', '.join(fields[:15])}{'...' if len(fields) > 15 else ''}")
                            
                            # 查找content相关字段
                            content_fields = [k for k in fields if 'content' in k.lower() or 'intro' in k.lower() or 'desc' in k.lower()]
                            if content_fields:
                                for key in content_fields:
                                    value = static_data[key]
                                    preview = str(value)[:80] if value else "空"
                                    print(f"   >>> 发现 '{key}': {preview}...")
                            else:
                                print(f"   ⚠️  无content/intro相关字段")
                            
                            return static_data
                        elif isinstance(static_data, list):
                            print(f"   ⚠️  data是列表，长度: {len(static_data)}")
                        else:
                            print(f"   ⚠️  data类型异常: {type(static_data)}")
                    else:
                        print(f"   ✗ 错误: {result.get('message', '未知错误')}")
                        
            except Exception as e:
                print(f"   ✗ 异常: {str(e)}")
        
        return None
    
    def get_school_content_alternative(self, school_id):
        """尝试其他可能的接口获取学校介绍"""
        alternative_urls = [
            ("pc_special", f"https://static-data.gaokao.cn/www/2.0/schoolSpecial/{school_id}/pc_special.json"),
            ("schoolInfo", f"https://static-data.gaokao.cn/www/2.0/schoolInfo/{school_id}/info.json"),
        ]
        
        for name, url in alternative_urls:
            print(f"\n📡 [接口4-备用{name}] school_id={school_id}")
            print(f"   请求: {url}")
            
            try:
                response = self.session.get(url, timeout=10)
                print(f"   状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    code = result.get('code')
                    print(f"   业务码: {code}")
                    
                    if code == 0 and 'data' in result:
                        data = result['data']
                        if isinstance(data, dict):
                            fields = list(data.keys())
                            print(f"   ✓ 返回字段({len(fields)}个): {', '.join(fields[:10])}{'...' if len(fields) > 10 else ''}")
                            
                            # 查找content相关字段
                            for key in ['content', 'intro', 'introduction', 'school_intro', 'description']:
                                if key in data and data[key]:
                                    preview = str(data[key])[:80]
                                    print(f"   >>> 发现 '{key}': {preview}...")
                                    return data[key]
                        else:
                            print(f"   ⚠️  data类型: {type(data)}")
                    else:
                        print(f"   ✗ 错误: {result.get('message', '未知错误')}")
                else:
                    print(f"   ✗ HTTP错误")
            except Exception as e:
                print(f"   ✗ 异常: {str(e)}")
        
        return None

    def get_enhanced_school_list(self, page=1, size=20):
        """获取增强版学校列表"""
        print(f"\n📡 [接口5-增强列表] page={page}, size={size}")
        
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
            print(f"   使用Cookie: {cookie[:30]}...")
        else:
            print(f"   未配置Cookie")
        
        try:
            response = self.session.post(
                full_url,
                headers=headers,
                data=json.dumps(post_body),
                timeout=15
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                code = result.get('code')
                print(f"   业务码: {code}")
                
                if code == 0:
                    items = result.get('data', {}).get('item', [])
                    print(f"   ✓ 获取 {len(items)} 所学校")
                    if items:
                        sample = items[0]
                        fields = list(sample.keys())
                        print(f"   字段示例: {', '.join(fields[:10])}{'...' if len(fields) > 10 else ''}")
                    return result
                elif code == 1010001:
                    print(f"   ✗ 需要Cookie认证")
                else:
                    print(f"   ✗ 错误: {result.get('message', '未知错误')}")
            else:
                print(f"   ✗ HTTP错误")
            
        except Exception as e:
            print(f"   ✗ 异常: {str(e)}")
        
        return None
    
    def merge_enhanced_data(self, schools_basic, max_pages=10):
        """将增强数据合并到基础学校列表"""
        enhanced_dict = {}
        
        print(f"\n{'='*60}")
        print(f"开始获取增强版学校数据（最多{max_pages}页）")
        print(f"{'='*60}")
        
        page = 1
        total_fetched = 0
        
        while page <= max_pages:
            enhanced_data = self.get_enhanced_school_list(page=page, size=20)
            
            if enhanced_data and enhanced_data.get('code') == 0:
                items = enhanced_data.get('data', {}).get('item', [])
                
                if not items:
                    print(f"   第 {page} 页无数据，停止")
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
                
                page += 1
                self.polite_sleep(3.0, 6.0)
            else:
                if page == 1 and not os.getenv('GAOKAO_COOKIE'):
                    print(f"\n💡 提示：增强数据需要Cookie")
                    print(f"   1. 访问 www.gaokao.cn 并登录")
                    print(f"   2. F12 控制台输入: document.cookie")
                    print(f"   3. 设置 GitHub Secret: GAOKAO_COOKIE\n")
                break
        
        # 合并数据
        merged_count = 0
        for school in schools_basic:
            school_id = school.get('school_id')
            if school_id and school_id in enhanced_dict:
                school.update(enhanced_dict[school_id])
                merged_count += 1
        
        print(f"\n✓ 成功合并 {merged_count}/{len(schools_basic)} 所学校的增强数据")
        
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
        print(f"{'='*60}")
        
        for page in range(1, max_pages + 1):
            print(f"\n📡 [接口1-基础列表] page={page}, size=20")
            
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
                print(f"   ✗ 请求失败")
                break
            
            items = data['data']['item']
            if not items:
                print(f"   ✗ 无数据，停止爬取")
                break
            
            print(f"   ✓ 获取 {len(items)} 所学校")
            print(f"\n{'─'*60}")
            
            for idx, item in enumerate(items, 1):
                school_id = item.get('school_id')
                school_name = item.get('name')
                
                print(f"\n[{idx}/{len(items)}] 学校: {school_name} (ID:{school_id})")
                
                school_info = {
                    'school_id': school_id,
                    'name': school_name,
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
                        # 检查detail中是否有content
                        if 'content' in detail:
                            school_info['content'] = detail['content']
                        if 'intro' in detail:
                            school_info['intro'] = detail['intro']
                        
                        self.polite_sleep(1.0, 2.0)
                
                # 获取静态完整信息
                if fetch_static_info and school_id:
                    static_info = self.get_school_static_info(school_id)
                    if static_info:
                        # 尝试各种可能的字段名
                        for content_key in ['content', 'intro', 'introduction', 'school_intro', 'description']:
                            if content_key in static_info:
                                school_info[content_key] = static_info[content_key]
                        
                        # 其他字段
                        school_info.update({
                            'central': static_info.get('central'),
                            'school_site': static_info.get('school_site') or static_info.get('site'),
                            'emails': static_info.get('emails') or static_info.get('email'),
                            'colleges_level': static_info.get('colleges_level'),
                            'old_name': static_info.get('old_name'),
                            'create_year': static_info.get('create_date') or static_info.get('create_year'),
                            'province_id': static_info.get('province_id'),
                            'city_id': static_info.get('city_id'),
                            'town': static_info.get('town_name') or static_info.get('town'),
                            'level_name': static_info.get('level_name'),
                            'department': static_info.get('department') or static_info.get('belong'),
                        })
                        
                        # 如果还没有content，尝试备用接口
                        if not school_info.get('content') and not school_info.get('intro'):
                            alt_content = self.get_school_content_alternative(school_id)
                            if alt_content:
                                school_info['content'] = alt_content
                        
                        self.polite_sleep(2.0, 4.0)
                
                schools.append(school_info)
            
            print(f"\n{'─'*60}")
            print(f"✓ 第 {page} 页完成")
            self.polite_sleep(3.0, 6.0)
        
        # 合并增强数据
        if fetch_enhanced and schools:
            enhanced_pages = max(max_pages, (len(schools) // 20) + 2)
            schools = self.merge_enhanced_data(schools, max_pages=enhanced_pages)
        
        # 最终输出
        if schools:
            print(f"\n{'='*60}")
            print(f"📊 第一所学校的完整数据:")
            print(f"{'='*60}")
            first_school = schools[0]
            for key, value in first_school.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"  {key}: {value[:100]}...")
                else:
                    print(f"  {key}: {value}")
            print(f"{'='*60}")
        
        self.save_to_json(schools, 'schools.json')
        print(f"\n{'='*60}")
        print(f"🎉 学校爬取完成！共 {len(schools)} 所")
        print(f"{'='*60}\n")
        
        return schools

if __name__ == "__main__":
    import sys
    
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 1
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
