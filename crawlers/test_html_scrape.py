import requests
from bs4 import BeautifulSoup

def test_html_scrape():
    """测试能否直接爬取HTML"""
    url = "https://www.gaokao.cn/school/search?page=1"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.gaokao.cn/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    response = requests.get(url, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"返回内容长度: {len(response.text)}")
    
    # 保存HTML查看
    with open('test_page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("HTML已保存到 test_page.html")
    
    # 尝试解析
    soup = BeautifulSoup(response.text, 'html.parser')
    school_items = soup.find_all('div', class_='school-search_schoolItem__3q7R2')
    
    print(f"\n找到 {len(school_items)} 个学校项")
    
    if school_items:
        print("\n成功！可以直接爬取HTML")
        # 测试提取清华的标签
        for item in school_items[:1]:
            name = item.find('h3', class_='school-search_schoolName__1L7pc')
            if name:
                print(f"学校: {name.text.strip()}")
            
            tags_div = item.find('div', class_='school-search_tags__ZPsHs')
            if tags_div:
                tags = [tag.text for tag in tags_div.find_all('span')]
                print(f"标签: {tags}")
    else:
        print("\n失败！页面是动态加载的，需要使用Selenium")

if __name__ == "__main__":
    test_html_scrape()
