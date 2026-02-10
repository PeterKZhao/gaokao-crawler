import time
import os
import json
import requests
from .base import BaseCrawler


class SchoolCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        # 读取“页码 -> signsafe”的映射（由你从前端抓包得到）
        # 例：{"1":"d47a...","2":"fcfb..."}
        self.enhanced_signsafe_map = {}
        raw = os.getenv("ENHANCED_SIGNSAFE_MAP", "").strip()
        if raw:
            try:
                self.enhanced_signsafe_map = json.loads(raw)
            except Exception as e:
                print(f"⚠ ENHANCED_SIGNSAFE_MAP 不是合法JSON，将忽略：{e}")

        # 增强接口固定参数（你贴的URL里 local_type_id=2073）
        self.enhanced_local_type_id = os.getenv("ENHANCED_LOCAL_TYPE_ID", "2073").strip()

    def get_school_detail(self, school_id):
        payload = {
            "school_id": school_id,
            "uri": "apidata/api/gkv3/school/detail"
        }
        data = self.make_request(payload, retry=2)
        if data and "data" in data:
            return data["data"]
        return None

    def request_enhanced_page(self, page: int, size: int = 20):
        """
        调用增强接口（v1/school/lists）。
        关键点：
        - 方法：POST（你抓包确认）
        - 参数：放在 querystring（params）里
        - body：不传/传空都行（这里传空字符串）
        - signsafe：必须与你抓包一致，否则会失败
        """
        signsafe = self.enhanced_signsafe_map.get(str(page)) or self.enhanced_signsafe_map.get(page)
        if not signsafe:
            print(f"⚠ 未提供第{page}页 signsafe，跳过该页（请更新 ENHANCED_SIGNSAFE_MAP）")
            return None

        url = "https://api-gaokao.zjzw.cn/apidata/web"
        params = {
            "autosign": "",
            "keyword": "",
            "local_type_id": self.enhanced_local_type_id,
            "page": str(page),
            "platform": "2",
            "province_id": "",
            "ranktype": "",
            "request_type": "1",
            "size": str(size),
            "spe_ids": "",
            "top_school_id": "",
            "uri": "v1/school/lists",
            "signsafe": signsafe,
        }

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            # 不要强行写 content-type=application/json（避免服务端按JSON解析body）
            "origin": "https://www.gaokao.cn",
            "referer": "https://www.gaokao.cn/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            r = requests.post(url, params=params, headers=headers, data="", timeout=15)
            if r.status_code != 200:
                print(f"✗ 增强接口HTTP失败 page={page} status={r.status_code}")
                print(f"  url={r.url}")
                return None
            return r.json()
        except Exception as e:
            print(f"✗ 增强接口请求异常 page={page}: {e}")
            return None

    def merge_enhanced_data(self, schools_basic, max_pages: int):
        """
        将增强接口字段合并到 schools_basic（按 school_id 对齐）。
        """
        enhanced_dict = {}

        print(f"\n{'='*60}")
        print("开始获取增强版学校数据...")
        print(f"{'='*60}\n")

        for page in range(1, max_pages + 1):
            data = self.request_enhanced_page(page=page, size=20)
            if not data:
                break

            if data.get("code") != 0:
                print(f"✗ 增强数据第 {page} 页：{data.get('message')}")
                break

            items = (data.get("data") or {}).get("item") or []
            if not items:
                print(f"✓ 增强数据第 {page} 页无数据，停止")
                break

            for item in items:
                sid = item.get("school_id")
                if sid is None:
                    continue
                enhanced_dict[int(sid)] = {
                    "label_list": item.get("label_list", []),
                    "attr_list": item.get("attr_list", []),
                    "recommend_master_level": item.get("recommend_master_level"),
                    "is_top": item.get("is_top"),
                    "hightitle": item.get("hightitle"),
                }

            print(f"✓ 增强数据第 {page} 页：{len(items)} 所")
            time.sleep(0.8)

        merged = 0
        for s in schools_basic:
            sid = s.get("school_id")
            if sid is None:
                continue
            key = int(sid)
            if key in enhanced_dict:
                s.update(enhanced_dict[key])
                merged += 1

        print(f"\n✓ 成功合并 {merged}/{len(schools_basic)} 所学校的增强数据")
        print(f"  (增强数据覆盖学校数：{len(enhanced_dict)})\n")

        return schools_basic

    def crawl(self, max_pages=None, fetch_detail=True, fetch_enhanced=True):
        if max_pages is None:
            max_pages = int(os.getenv("MAX_PAGES", "10"))

        fetch_detail = os.getenv("FETCH_DETAIL", str(fetch_detail)).lower() == "true"
        fetch_enhanced = os.getenv("FETCH_ENHANCED", str(fetch_enhanced)).lower() == "true"

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
            if not (data and "data" in data and "item" in data["data"]):
                print(f"✗ 第 {page} 页：请求失败")
                break

            items = data["data"]["item"] or []
            if not items:
                print(f"第 {page} 页无数据，停止爬取")
                break

            for item in items:
                sid = item.get("school_id")
                school_info = {
                    "school_id": sid,
                    "name": item.get("name"),
                    "province": item.get("province_name"),
                    "city": item.get("city_name"),
                    "county": item.get("county_name"),
                    "type": item.get("type_name"),
                    "level": item.get("level_name"),
                    "belong": item.get("belong"),
                    "rank": item.get("rank"),
                    "dual_class": item.get("dual_class_name"),
                    "f985": item.get("f985"),
                    "f211": item.get("f211"),
                    "is_dual_class": item.get("dual_class"),
                    "central": item.get("central"),
                    "nature": item.get("nature_name"),
                    "view_month": item.get("view_month"),
                    "view_total": item.get("view_total"),
                    "view_week": item.get("view_week"),
                    "alumni": item.get("alumni"),
                    "city_id": item.get("city_id"),
                    "county_id": item.get("county_id"),
                    "province_id": item.get("province_id"),
                    "type_id": item.get("type"),
                    "level_id": item.get("level"),
                }

                if fetch_detail and sid:
                    detail = self.get_school_detail(sid)
                    if detail:
                        school_info.update({
                            "logo": detail.get("logo"),
                            "img": detail.get("img"),
                            "address": detail.get("address"),
                            "postcode": detail.get("postcode"),
                            "phone": detail.get("phone"),
                            "email": detail.get("email"),
                            "website": detail.get("site"),
                            "tags": detail.get("tags"),
                            "feature": detail.get("feature"),
                            "school_feature": detail.get("school_feature"),
                            "academician": detail.get("academician"),
                            "national_feature": detail.get("national_feature"),
                            "key_discipline": detail.get("key_discipline"),
                            "master_degree": detail.get("master_degree"),
                            "doctor_degree": detail.get("doctor_degree"),
                            "recruit": detail.get("recruit"),
                            "admission_brochure": detail.get("admissions_brochure"),
                            "history": detail.get("content"),
                            "found_time": detail.get("create_date"),
                            "area": detail.get("area"),
                            "student_num": detail.get("student_num"),
                            "teacher_num": detail.get("teacher_num"),
                            "motto": detail.get("motto"),
                            "anniversary": detail.get("anniversary"),
                            "old_name": detail.get("old_name"),
                            "dorm_condition": detail.get("dorm_condition"),
                            "canteen_condition": detail.get("canteen_condition"),
                            "is_985": detail.get("f985"),
                            "is_211": detail.get("f211"),
                            "is_double_first_class": detail.get("dual_class"),
                            "has_graduate_school": detail.get("graduate_school"),
                            "has_independent_enrollment": detail.get("independent_enrollment"),
                            "subject_evaluate": detail.get("subject_evaluate"),
                            "dual_class_disciplines": detail.get("dual_class_name_dict"),
                        })
                        time.sleep(0.3)

                schools.append(school_info)

            print(f"✓ 第 {page} 页：获取 {len(items)} 所学校" + (" (含详情)" if fetch_detail else ""))
            time.sleep(0.8)

        if fetch_enhanced and schools:
            # 你基础 schools 爬了多少页，就用同样页数去拉增强页（签名映射也通常按页准备）
            schools = self.merge_enhanced_data(schools, max_pages=max_pages)

        self.save_to_json(schools, "schools.json")
        print(f"\n{'='*60}")
        print(f"学校爬取完成！共 {len(schools)} 所")
        print(f"{'='*60}\n")
        return schools


if __name__ == "__main__":
    crawler = SchoolCrawler()
    crawler.crawl()
