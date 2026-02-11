major_info = {
    # 基础标识 (3个)
    'special_id': item.get('special_id'),
    'code': item.get('spcode'),              # ⭐ 专业代码
    'name': item.get('name'),
    
    # 分类信息 (3个)
    'level1_name': item.get('level1_name'),  # 学历层次
    'level2_name': item.get('level2_name'),  # 学科门类
    'level3_name': item.get('level3_name'),  # 专业类别
    
    # 学位学制 (2个)
    'degree': item.get('degree'),
    'years': item.get('limit_year'),
    
    # 薪资数据 (2个) ⭐⭐⭐
    'salary_avg': item.get('salaryavg'),      # 平均年薪
    'salary_5year': item.get('fivesalaryavg'), # 5年后月薪
    
    # 性别比例 (2个) ⭐⭐
    'boy_rate': item.get('boy_rate'),
    'girl_rate': item.get('girl_rate'),
    
    # 热度数据 (4个) ⭐
    'rank': item.get('rank'),                 # 热度排名
    'view_total': item.get('view_total'),     # 总浏览
    'view_month': item.get('view_month'),     # 月浏览
    'view_week': item.get('view_week'),       # 周浏览
}
