"""
测试使用requests模拟浏览器访问
"""
import requests
from bs4 import BeautifulSoup
import json

def test_requests_scraping():
    """测试requests直接获取"""
    print("="*60)
    print("测试: 使用requests直接爬取")
    print("="*60)
    
    session = requests.Session()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.gaokao.cn/',
        'Connection': 'keep-alive',
    }
    
    url = "https://www.gaokao.cn/school/search?page=1"
    
    try:
        print(f"正在请求: {url}")
        response = session.get(url, headers=headers, timeout=10)
        
        print(f"状态码: {response.status_code}")
        print(f"内容长度: {len(response.text)}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        # 保存HTML
        with open('debug_requests_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"✓ HTML已保存到 debug_requests_page.html")
        
        # 解析
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找学校项
        school_items = soup.find_all('div', class_='school-search_schoolItem__3q7R2')
        print(f"\n找到学校项: {len(school_items)} 个")
        
        if school_items:
            print("\n✓ 成功！可以直接使用requests")
            # 测试提取第一所学校
            item = school_items[0]
            name = item.find('h3', class_='school-search_schoolName__1L7pc')
            tags_div = item.find('div', class_='school-search_tags__ZPsHs')
            
            if name:
                print(f"  学校名: {name.get_text()[:50]}")
            if tags_div:
                tags = [tag.get_text() for tag in tags_div.find_all('span')]
                print(f"  标签: {tags}")
            
            return True
        else:
            print("\n✗ 未找到学校项，页面可能是动态加载")
            print("\n页面中的所有class（前20个）:")
            all_divs = soup.find_all('div')[:20]
            for div in all_divs:
                class_name = div.get('class')
                if class_name:
                    print(f"  - {class_name}")
            
            return False
            
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False

if __name__ == "__main__":
    test_requests_scraping()
