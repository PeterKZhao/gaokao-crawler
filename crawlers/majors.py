import time
import json
import os
from .base import BaseCrawler

class MajorCrawler(BaseCrawler):
    
    def __init__(self):
        super().__init__()
        self._first_logged = False
    
    def crawl(self, max_pages=200):
        """爬取专业列表"""
        majors = []
        page = 1
        
        print(f"\n{'='*60}")
        print(f"开始爬取专业目录")
        print(f"最大页数: {max_pages}")
        print(f"{'='*60}\n")
        
        while page <= max_pages:
            print(f"\n📡 [专业列表接口] page={page}, size=30")
            
            payload = {
                "keyword": "",
                "page": page,
                "size": 30,
                "level1": "",
                "level2": "",
                "level3": "",
                "uri": "apidata/api/gkv3/special/lists"
            }
            
            data = self.make_request(payload, retry=5)
            
            if not data:
                print(f"   ✗ 第 {page} 页：请求失败")
                if page == 1:
                    print(f"   ⚠️  API 可能已更改，请检查参数")
                break
            
            # 显示响应状态码
            code = data.get('code')
            print(f"   业务码: {code}")
            
            if code != '0000' and code != 0:
                if page == 1:
                    print(f"   ⚠️  API返回错误: code={code}, message={data.get('message')}")
                continue
            
            if 'data' not in data:
                print(f"   ✗ 响应中无data字段")
                break
            
            # 处理不同的数据结构
            data_content = data['data']
            
            # 首次显示响应结构
            if not self._first_logged:
                print(f"\n   {'─'*55}")
                print(f"   首次响应数据结构:")
                print(f"   {'─'*55}")
                print(f"   data类型: {type(data_content).__name__}")
                
                if isinstance(data_content, str):
                    print(f"   data是字符串，长度: {len(data_content)}")
                    print(f"   尝试解析JSON...")
                elif isinstance(data_content, dict):
                    print(f"   data是字典，包含键: {list(data_content.keys())}")
                elif isinstance(data_content, list):
                    print(f"   data是列表，长度: {len(data_content)}")
            
            # 如果 data 是字符串，尝试解析
            if isinstance(data_content, str):
                try:
                    data_content = json.loads(data_content)
                    if not self._first_logged:
                        print(f"   ✓ JSON解析成功")
                        print(f"   解析后类型: {type(data_content).__name__}")
                except Exception as e:
                    print(f"   ✗ 第 {page} 页：数据解析失败 - {str(e)}")
                    break
            
            # 提取 items
            items = []
            if isinstance(data_content, dict):
                items = data_content.get('item') or data_content.get('items') or []
                if not self._first_logged:
                    print(f"   提取items字段，找到: {len(items)} 项")
            elif isinstance(data_content, list):
                items = data_content
                if not self._first_logged:
                    print(f"   data本身就是列表: {len(items)} 项")
            
            if not items:
                print(f"   第 {page} 页无数据，爬取完成")
                break
            
            # 首次显示专业字段
            if not self._first_logged and items:
                sample = items[0]
                fields = list(sample.keys())
                print(f"\n   专业数据字段({len(fields)}个):")
                print(f"   {'─'*55}")
                for i, field in enumerate(fields, 1):
                    value = sample[field]
                    value_type = type(value).__name__
                    # 显示值的预览
                    if value is None:
                        preview = "None"
                    elif isinstance(value, str):
                        preview = f'"{value[:30]}..."' if len(value) > 30 else f'"{value}"'
                    elif isinstance(value, (list, dict)):
                        preview = f"{value_type}({len(value)}项)"
                    else:
                        preview = str(value)
                    print(f"   {i:2}. {field:20} = {preview}")
                print(f"   {'─'*55}\n")
                self._first_logged = True
            
            # 处理每个专业 - 保存完整字段
            for item in items:
                major_info = {
                    # 基础标识
                    'special_id': item.get('special_id'),
                    'code': item.get('spcode'),  # ⭐ 修正：使用spcode而不是code
                    'name': item.get('name'),
                    
                    # 分类信息
                    'level1_name': item.get('level1_name'),  # 学历层次
                    'level2_name': item.get('level2_name'),  # 学科门类
                    'level3_name': item.get('level3_name'),  # 专业类别
                    
                    # 学位学制
                    'degree': item.get('degree'),
                    'years': item.get('limit_year'),
                    
                    # 薪资数据 ⭐⭐⭐
                    'salary_avg': item.get('salaryavg'),      # 平均年薪
                    'salary_5year': item.get('fivesalaryavg'), # 5年后月薪
                    
                    # 性别比例 ⭐⭐
                    'boy_rate': item.get('boy_rate'),
                    'girl_rate': item.get('girl_rate'),
                    
                    # 热度数据 ⭐
                    'rank': item.get('rank'),                 # 热度排名
                    'view_total': item.get('view_total'),     # 总浏览量
                    'view_month': item.get('view_month'),     # 月浏览量
                    'view_week': item.get('view_week'),       # 周浏览量
                }
                majors.append(major_info)
            
            print(f"   ✓ 第 {page} 页：获取 {len(items)} 个专业（累计 {len(majors)} 个）")
            
            # 每10页显示进度
            if page % 10 == 0:
                print(f"\n   📊 进度：已爬取 {len(majors)} 个专业...")
            
            page += 1
            self.polite_sleep(3.0, 6.0)
        
        # 保存数据
        self.save_to_json(majors, 'majors.json')
        
        print(f"\n{'='*60}")
        print(f"✅ 专业爬取完成！")
        print(f"   总计: {len(majors)} 个专业")
        if majors:
            print(f"   字段数: {len(majors[0].keys())}")
            # 统计专业分类
            level1_set = set(m.get('level1_name') for m in majors if m.get('level1_name'))
            print(f"   学历层次: {len(level1_set)} 个")
            
            # 统计有薪资数据的专业
            has_salary = sum(1 for m in majors if m.get('salary_avg'))
            print(f"   有薪资数据: {has_salary} 个 ({has_salary*100//len(majors)}%)")
        print(f"{'='*60}\n")
        
        return majors

if __name__ == "__main__":
    crawler = MajorCrawler()
    crawler.crawl()
