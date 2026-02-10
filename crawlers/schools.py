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
        """获取学校完整信息（包含介绍、邮箱等所有数据）"""
        print(f"\n📡 [接口2-完整信息] school_id={school_id}")
        
        # 修复：使用GET请求，而不是POST
        url = f"https://static-data.gaokao.cn/www/2.0/school/{school_id}/info.json"
        print(f"   请求: {url}")
        
        try:
            # 使用GET方法
            response = self.session.get(url, timeout=10)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                code = result.get('code')
                print(f"   业务码: {code}")
                
                if code == '0000' and 'data' in result:
                    data = result['data']
                    
                    if isinstance(data, dict):
                        fields = list(data.keys())
                        print(f"   ✓ 返回字段({len(fields)}个)")
                        
                        # 检查关键字段
                        has_content = 'content' in data
                        has_email = 'email' in data or 'emails' in data
                        has_site = 'site' in data or 'school_site' in data
                        
                        print(f"   >>> content: {'✓' if has_content else '✗'}")
                        print(f"   >>> email: {'✓' if has_email else '✗'}")
                        print(f"   >>> site: {'✓' if has_site else '✗'}")
                        
                        if has_content:
                            content_preview = data['content'][:80] if data['content'] else "空"
                            print(f"   >>> 内容预览: {content_preview}...")
                        
                        return data
                    else:
                        print(f"   ⚠️  data类型异常: {type(data)}")
                else:
                    print(f"   ✗ 错误: code={code}, message={result.get('message')}")
            else:
                print(f"   ✗ HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"   ✗ 异常: {str(e)}")
        
        return None

    def get_enhanced_school_list(self, page=1, size=20):
        """获取增强版学校列表"""
        if page == 1:  # 只在第一页打印日志头
            print(f"\n📡 [接口3-增强列表] page={page}, size={size}")
        
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
            if page == 1:
                print(f"   使用Cookie: {cookie[:30]}...")
        else:
            if page == 1:
                print(f"   未配置Cookie")
        
        try:
            response = self.session.post(
                full_url,
                headers=headers,
                data=json.dumps(post_body),
                timeout=15
            )
            
            if page == 1:
                print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                code = result.get('code')
                
                if page == 1:
                    print(f"   业务码: {code}")
                
                if code == 0:
                    items = result.get('data', {}).get('item', [])
                    if page == 1:
                        print(f"   ✓ 第{page}页获取 {len(items)} 所学校")
                    return result
                elif code == 1010001:
                    if page == 1:
                        print(f"   ✗ 需要Cookie认证")
                else:
                    if page == 1:
                        print(f"   ✗ 错误: {result.get('message', '未知错误')}")
            else:
                if page == 1:
                    print(f"   ✗ HTTP错误")
            
        except Exception as e:
            if page == 1:
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
                
                if page > 1:  # 第2页起显示进度
                    print(f"   ✓ 第{page}页获取 {len(items)} 所学校（累计{total_fetched}所）")
                
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
    
    def crawl(self, max_pages=None, fetch_complete_info=True, fetch_enhanced=True):
        """爬取学校列表"""
        max_pages = max_pages or int(os.getenv('MAX_PAGES', '10'))
        fetch_complete_info = os.getenv('FETCH_COMPLETE_INFO', str(fetch_complete_info)).lower() == 'true'
        fetch_enhanced = os.getenv('FETCH_ENHANCED', str(fetch_enhanced)).lower() == 'true'
        
        schools = []
        print(f"\n{'='*60}")
        print(f"开始爬取学校列表（最多 {max_pages} 页）")
        print(f"完整信息: {'✓' if fetch_complete_info else '✗'} | "
              f"增强数据: {'✓' if fetch_enhanced else '✗'}")
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
                
                print(f"\n[{idx}/{len(items)}] {school_name} (ID:{school_id})")
                
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
                
                # 获取完整信息（包含content、email、website等）
                if fetch_complete_info and school_id:
                    complete_info = self.get_school_complete_info(school_id)
                    if complete_info:
                        # 提取所有有用的字段
                        school_info.update({
                            'content': complete_info.get('content'),  # 学校介绍
                            'email': complete_info.get('email'),  # 邮箱
                            'school_email': complete_info.get('school_email'),  # 学校邮箱
                            'site': complete_info.get('site'),  # 招生网
                            'school_site': complete_info.get('school_site'),  # 官网
                            'address': complete_info.get('address'),  # 地址
                            'phone': complete_info.get('phone'),  # 电话
                            'school_phone': complete_info.get('school_phone'),  # 学校电话
                            'postcode': complete_info.get('postcode'),  # 邮编
                            'logo': complete_info.get('logo'),  # logo
                            'create_date': complete_info.get('create_date'),  # 创建年份
                            'old_name': complete_info.get('old_name'),  # 曾用名
                            'area': complete_info.get('area'),  # 占地面积
                            'num_doctor': complete_info.get('num_doctor'),  # 博士点
                            'num_master': complete_info.get('num_master'),  # 硕士点
                            'num_subject': complete_info.get('num_subject'),  # 重点学科
                            'num_academician': complete_info.get('num_academician'),  # 院士数
                            'num_library': complete_info.get('num_library'),  # 图书馆藏书
                            'recommend_master_rate': complete_info.get('recommend_master_rate'),  # 保研率
                            'motto': complete_info.get('motto'),  # 校训
                            'ruanke_rank': complete_info.get('ruanke_rank'),  # 软科排名
                            'xyh_rank': complete_info.get('xyh_rank'),  # 校友会排名
                            'wsl_rank': complete_info.get('wsl_rank'),  # 武书连排名
                            'qs_rank': complete_info.get('qs_rank'),  # QS排名
                            'us_rank': complete_info.get('us_rank'),  # US排名
                        })
                        
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
            
            # 显示关键字段
            key_fields = ['school_id', 'name', 'content', 'email', 'site', 'school_site', 
                         'address', 'phone', 'motto', 'rank']
            for key in key_fields:
                if key in first_school:
                    value = first_school[key]
                    if isinstance(value, str) and len(value) > 100:
                        print(f"  {key}: {value[:100]}...")
                    else:
                        print(f"  {key}: {value}")
            
            print(f"  ... (共{len(first_school)}个字段)")
            print(f"{'='*60}")
        
        self.save_to_json(schools, 'schools.json')
        print(f"\n{'='*60}")
        print(f"🎉 学校爬取完成！共 {len(schools)} 所")
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
