#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
韩剧TV TVBox Python Spider (纯标准库版)
网站地址: https://hanjuk.com/
仅使用Python标准库，无需安装第三方包
"""

import re
import json
import ssl
import urllib.request
import urllib.parse
import html as html_mod

try:
    from base.spider import Spider as BaseSpider
except ImportError:
    class BaseSpider:
        def init(self, extend=""): pass
        def getName(self): return ""
        def homeContent(self, filter): return {}
        def homeVideoContent(self): return {}
        def categoryContent(self, tid, pg, filter, extend): return {}
        def detailContent(self, ids): return {}
        def searchContent(self, key, quick, pg="1"): return {}
        def playerContent(self, flag, id, vipFlags): return {}


class Spider(BaseSpider):
    BASE_URL = "https://hanjuk.com"
    WECHAT_INFO = '微信公众号"源力软件汇"'
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    CATEGORIES = [
        {"type_id": 1, "type_name": "电影"},
        {"type_id": 2, "type_name": "电视剧"},
        {"type_id": 3, "type_name": "综艺"},
        {"type_id": 4, "type_name": "动漫"},
    ]

    def init(self, extend=""):
        pass

    def getName(self):
        return "韩剧TV"

    def getHtml(self, url):
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, headers={"User-Agent": self.UA})
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                data = resp.read()
                for enc in ["utf-8", "gbk", "gb2312", "latin-1"]:
                    try:
                        return data.decode(enc)
                    except Exception:
                        continue
                return data.decode("utf-8", errors="replace")
        except Exception:
            return ""

    def clean(self, text):
        if not text:
            return ""
        text = html_mod.unescape(str(text))
        return re.sub(r"\s+", " ", text).strip()

    def attr_val(self, tag_html, attr):
        m = re.search(rf'{attr}\s*=\s*["\']([^"\']*)["\']', tag_html)
        return m.group(1) if m else ""

    def homeContent(self, filter):
        return {"class": self.CATEGORIES, "filters": {}}

    def homeVideoContent(self):
        result = {"list": []}
        html = self.getHtml(self.BASE_URL)
        if not html:
            return result

        videos = []
        seen = set()

        for item in re.finditer(r'<a[^>]*href="/nf-detail/(\d+)\.html"[^>]*>(.*?)</a>', html, re.S):
            vid = item.group(1)
            block = item.group(2)
            if not vid or vid in seen:
                continue
            seen.add(vid)

            name = ""
            title_m = re.search(r'<div[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</div>', block, re.S)
            if title_m:
                name = self.clean(title_m.group(1))
            if not name:
                title_m = re.search(r'title="([^"]+)"', item.group(0))
                if title_m:
                    name = self.clean(title_m.group(1))
            if not name:
                continue

            pic = ""
            src_m = re.search(r'<img[^>]*data-original="([^"]+)"', block)
            if not src_m:
                src_m = re.search(r'<img[^>]*src="([^"]+)"', block)
            if not src_m:
                src_m = re.search(r'<img[^>]*src="([^"]+)"', item.group(0))
            if src_m:
                pic = src_m.group(1)

            score = ""
            score_m = re.search(r'<div[^>]*class="[^"]*score[^"]*"[^>]*>([\d.]+)</div>', block)
            if score_m:
                score = score_m.group(1)

            remarks = ""
            remarks_m = re.search(r'<div[^>]*class="[^"]*role[^"]*"[^>]*>(.*?)</div>', block)
            if remarks_m:
                remarks = self.clean(remarks_m.group(1))

            videos.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": pic,
                "vod_score": score,
                "vod_remarks": remarks,
                "vod_content": self.WECHAT_INFO,
            })

        result["list"] = videos[:30]
        return result

    def categoryContent(self, tid, pg, filter, extend):
        result = {"list": [], "page": str(pg), "pagecount": "1", "total": "0"}
        cat = None
        for c in self.CATEGORIES:
            if c["type_id"] == int(tid):
                cat = c
                break
        if not cat:
            return result

        page = int(pg) if str(pg).isdigit() else 1
        if page <= 1:
            url = f"{self.BASE_URL}/nf-type/{tid}.html"
        else:
            url = f"{self.BASE_URL}/nf-type/{tid}-{page}.html"

        html = self.getHtml(url)
        if not html:
            return result

        videos = []
        seen = set()

        for item in re.finditer(r'<a[^>]*href="/nf-detail/(\d+)\.html"[^>]*>(.*?)</a>', html, re.S):
            vid = item.group(1)
            block = item.group(2)
            if not vid or vid in seen:
                continue
            seen.add(vid)

            name = ""
            title_m = re.search(r'<div[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</div>', block, re.S)
            if title_m:
                name = self.clean(title_m.group(1))
            if not name:
                title_m = re.search(r'title="([^"]+)"', item.group(0))
                if title_m:
                    name = self.clean(title_m.group(1))
            if not name:
                continue

            pic = ""
            src_m = re.search(r'<img[^>]*data-original="([^"]+)"', block)
            if not src_m:
                src_m = re.search(r'<img[^>]*src="([^"]+)"', block)
            if not src_m:
                src_m = re.search(r'<img[^>]*src="([^"]+)"', item.group(0))
            if src_m:
                pic = src_m.group(1)

            score = ""
            score_m = re.search(r'<div[^>]*class="[^"]*score[^"]*"[^>]*>([\d.]+)</div>', block)
            if score_m:
                score = score_m.group(1)

            remarks = ""
            remarks_m = re.search(r'<div[^>]*class="[^"]*role[^"]*"[^>]*>(.*?)</div>', block)
            if remarks_m:
                remarks = self.clean(remarks_m.group(1))

            videos.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": pic,
                "vod_score": score,
                "vod_remarks": remarks,
                "type_id": str(cat["type_id"]),
                "type_name": cat["type_name"],
            })

        pagecount = "1"
        page_m = re.search(r'page=(\d+)&', html)
        if page_m:
            pagecount = str(max(int(page_m.group(1)), page))
        else:
            next_m = re.search(r'下一页', html)
            if next_m:
                pagecount = str(page + 1)

        result["list"] = videos
        result["pagecount"] = pagecount
        result["total"] = str(int(pagecount) * len(videos)) if videos else "0"
        return result

    def detailContent(self, ids):
        result = {"list": []}
        vid = ids[0] if isinstance(ids, list) and ids else ids
        url = f"{self.BASE_URL}/nf-detail/{vid}.html"
        html = self.getHtml(url)
        if not html:
            return result

        vod = {"vod_id": str(vid)}

        hm = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        vod["vod_name"] = self.clean(hm.group(1)) if hm else ""

        pm = re.search(r'<img[^>]*data-original="(https?://[^"]+)"', html)
        if not pm:
            pm = re.search(r'<img[^>]*src="(https?://[^"]+)"', html)
        vod["vod_pic"] = pm.group(1) if pm else ""

        vod["vod_class"] = ""
        vod["vod_area"] = ""
        vod["vod_year"] = ""
        vod["vod_remarks"] = ""
        vod["vod_actor"] = ""
        vod["vod_director"] = ""
        vod["vod_lang"] = ""

        for link in re.finditer(r'<a[^>]*class="[^"]*tag[^"]*"[^>]*href="/nf-show/\d+/class/[^"]*">([^<]+)</a>', html):
            if vod["vod_class"]:
                vod["vod_class"] += " "
            vod["vod_class"] += self.clean(link.group(1))

        year_m = re.search(r'<a[^>]*class="[^"]*tag[^"]*"[^>]*href="/nf-show/\d+/year/(\d+)\.html">(\d+)</a>', html)
        if year_m:
            vod["vod_year"] = year_m.group(1)

        area_m = re.search(r'<a[^>]*class="[^"]*tag[^"]*"[^>]*href="/nf-show/\d+/area/[^"]*">([^<]+)</a>', html)
        if area_m:
            vod["vod_area"] = self.clean(area_m.group(1))

        for dm in re.finditer(r'<div[^>]*class="[^"]*director[^"]*"[^>]*>(.*?)</div>', html, re.S):
            text = dm.group(1)
            name_m = re.search(r'<div[^>]*class="[^"]*name[^"]*"[^>]*>(.*?)</div>', text)
            if name_m:
                label = self.clean(name_m.group(1))
                value = self.clean(text.replace(name_m.group(0), ""))
                if "导演" in label:
                    vod["vod_director"] = value
                elif "主演" in label:
                    vod["vod_actor"] = value
                elif "更新" in label:
                    vod["vod_remarks"] = value

        for item in re.finditer(r'<div[^>]*class="[^"]*item[^"]*"[^>]*>(.*?)</div>', html, re.S):
            text = self.clean(item.group(1))
            if "语言" in text:
                lang_m = re.search(r'语言[：:]\s*(\S+)', text)
                if lang_m:
                    vod["vod_lang"] = lang_m.group(1)
            elif "上映时间" in text:
                ym = re.search(r'上映时间[：:]\s*(\d+)', text)
                if ym and not vod["vod_year"]:
                    vod["vod_year"] = ym.group(1)
            elif "地区" in text:
                am = re.search(r'地区[：:]\s*(\S+)', text)
                if am and not vod["vod_area"]:
                    vod["vod_area"] = am.group(1)

        if not vod["vod_actor"]:
            actor_m = re.search(r'og:video:actor" content="([^"]+)"', html)
            if actor_m:
                vod["vod_actor"] = self.clean(actor_m.group(1))

        if not vod["vod_director"]:
            director_m = re.search(r'og:video:director" content="([^"]+)"', html)
            if director_m:
                vod["vod_director"] = self.clean(director_m.group(1))

        desc_m = re.search(r'简介[：:]\s*(<[^>]+>)?\s*([^<]+)', html)
        if desc_m:
            vod["vod_content"] = self.WECHAT_INFO + "\n" + self.clean(desc_m.group(2))
        else:
            vod["vod_content"] = self.WECHAT_INFO

        play_sources = []
        play_url_groups = []

        source_names = {}
        for sm in re.finditer(r'href="#(playlist\d+)".*?swiper-slide-text[^>]*>([^<]+)', html):
            name = sm.group(2).replace('<span class="play-num-badge">', '').replace('</span>', '')
            source_names[sm.group(1)] = self.clean(name)

        for pm in re.finditer(r'<div[^>]*id="(playlist\d+)"[^>]*class="[^"]*tab-pane[^"]*">(.*?)</div>', html, re.S):
            pane_id = pm.group(1)
            pane_html = pm.group(2)
            source_name = source_names.get(pane_id, "极速在线")
            episodes = []
            for am in re.finditer(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', pane_html):
                ep_href = am.group(1)
                ep_name = self.clean(am.group(2))
                if ep_name and ep_href:
                    full_url = self.BASE_URL + ep_href if ep_href.startswith("/") else ep_href
                    episodes.append(f"{ep_name}${full_url}")
            if episodes:
                play_sources.append(source_name)
                play_url_groups.append("#".join(episodes))

        if not play_url_groups:
            for link in re.finditer(r'<a[^>]*href="/nf-play/(\d+-\d+-\d+)\.html"[^>]*>([^<]+)</a>', html):
                ep_name = self.clean(link.group(2))
                ep_url = f"{self.BASE_URL}/nf-play/{link.group(1)}.html"
                play_url_groups.append(f"{ep_name}${ep_url}")
            if play_url_groups:
                play_sources.append("极速在线")

        vod["vod_play_from"] = "$$$".join(play_sources) if play_sources else "极速在线"
        vod["vod_play_url"] = "$$$".join(play_url_groups) if play_url_groups else ""
        vod["type_id"] = "1"
        vod["type_name"] = "韩剧"

        result["list"] = [vod]
        return result

    def searchContent(self, key, quick, pg="1"):
        try:
            return self._do_search(key, quick, pg)
        except Exception:
            return {"list": [], "page": str(pg), "pagecount": "1", "total": "0"}

    def _do_search(self, key, quick, pg="1"):
        result = {"list": [], "page": str(pg), "pagecount": "1", "total": "0"}
        pg = int(pg) if str(pg).isdigit() else 1
        
        search_urls = [
            f"{self.BASE_URL}/vodsearch{urllib.parse.quote(key)}.html",
            f"{self.BASE_URL}/vodsearch.html?wd={urllib.parse.quote(key)}",
            f"{self.BASE_URL}/nf-show/15/class/{urllib.parse.quote(key)}.html",
            f"{self.BASE_URL}/nf-show/15/area/{urllib.parse.quote(key)}.html",
        ]
        
        html = ""
        for url in search_urls:
            html = self.getHtml(url)
            if html and len(html) > 500:
                break

        if not html or len(html) <= 500:
            return result

        videos = []
        seen = set()

        for item in re.finditer(r'<a[^>]*href="/nf-detail/(\d+)\.html"[^>]*>(.*?)</a>', html, re.S):
            vid = item.group(1)
            block = item.group(2)
            if not vid or vid in seen:
                continue
            seen.add(vid)

            name = ""
            title_m = re.search(r'<div[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</div>', block, re.S)
            if title_m:
                name = self.clean(re.sub(r'<[^>]+>', '', title_m.group(1)))
            if not name:
                title_attr_m = re.search(r'title="([^"]+)"', item.group(0))
                if title_attr_m:
                    name = self.clean(title_attr_m.group(1))
            if not name:
                text_only = re.sub(r'<[^>]+>', '', block)
                name = self.clean(text_only)
            if not name:
                continue

            pic = ""
            src_m = re.search(r'<img[^>]*data-original="([^"]+)"', block)
            if not src_m:
                src_m = re.search(r'<img[^>]*src="([^"]+)"', block)
            if not src_m:
                src_m = re.search(r'<img[^>]*data-original="([^"]+)"', item.group(0))
            if not src_m:
                src_m = re.search(r'<img[^>]*src="([^"]+)"', item.group(0))
            if src_m:
                pic = src_m.group(1)

            score = ""
            score_m = re.search(r'<div[^>]*class="[^"]*score[^"]*"[^>]*>([\d.]+)</div>', block)
            if not score_m:
                score_m = re.search(r'([\d.]+)\s*分', block)
            if score_m:
                score = score_m.group(1)

            remarks = ""
            remarks_m = re.search(r'<div[^>]*class="[^"]*role[^"]*"[^>]*>(.*?)</div>', block)
            if not remarks_m:
                remarks_m = re.search(r'<span[^>]*class="[^"]*role[^"]*"[^>]*>(.*?)</span>', block)
            if remarks_m:
                remarks = self.clean(re.sub(r'<[^>]+>', '', remarks_m.group(1)))

            videos.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": pic,
                "vod_score": score,
                "vod_remarks": remarks,
                "type_id": "1",
                "type_name": "韩剧",
            })

        pagecount = "1"
        next_m = re.search(r'下一页', html)
        if next_m:
            pagecount = str(pg + 1)

        result["list"] = videos
        result["pagecount"] = pagecount
        result["total"] = str(int(pagecount) * len(videos)) if videos else "0"
        return result

    def playerContent(self, flag, id, vipFlags):
        return {"url": id, "parse": "1", "header": "", "playUrl": "", "subtitle": ""}