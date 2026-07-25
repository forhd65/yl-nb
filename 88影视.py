# -*- coding: utf-8 -*-
import requests
import re
import json
import sys
import urllib.parse
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings()
sys.path.append('.')
from base.spider import Spider


class Spider(Spider):
    def __init__(self):
        super(Spider, self).__init__()
        self.session = requests.Session()
        self.session.verify = False
        self.host = "https://www.88kan.org"
        self.name = "88影视"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': f'{self.host}/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.categories = {
            '1': '电影',
            '2': '电视剧',
            '3': '综艺',
            '4': '动漫',
        }
        self._detail_cache = {}

    def getName(self):
        return "88影视"

    def init(self, extend):
        pass

    def homeContent(self, filter):
        classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "4", "type_name": "动漫"},
        ]

        filter_dict = self._build_filters()

        try:
            videos = self._fetch_list('1', 1)
            return {
                'class': classes,
                'filters': filter_dict,
                'list': videos
            }
        except Exception as e:
            print(f'[{self.name}] 错误: 首页爬取失败 - {e}')
            return {'class': classes, 'filters': filter_dict, 'list': []}

    def homeVideoContent(self):
        try:
            videos = self._fetch_list('1', 1)
            return {'list': videos}
        except Exception as e:
            print(f'[{self.name}] 错误: 首页视频爬取失败 - {e}')
            return {'list': []}

    def _build_filters(self):
        filter_dict = {}
        for tid in ['1', '2', '3', '4']:
            filter_dict[tid] = []
        return filter_dict

    def categoryContent(self, tid, pg, filter, extend):
        try:
            videos = self._fetch_list(tid, int(pg))
            page = int(pg)
            pagecount = 9999
            limit = 20
            total = 99999
            return {
                'page': page,
                'pagecount': pagecount,
                'limit': limit,
                'total': total,
                'list': videos
            }
        except Exception as e:
            print(f'[{self.name}] 错误: 分类爬取失败 - {e}')
            return {'page': int(pg), 'pagecount': 0, 'limit': 20, 'total': 0, 'list': []}

    def _fetch_list(self, cat_id, page):
        url = f'{self.host}/api/filter?catId={cat_id}&page={page}&size=20'
        res = self.session.get(url, headers=self.headers, timeout=15)
        data = res.json()
        movies = data.get('movies', [])
        videos = []
        for m in movies:
            vod = self._parse_movie(m, cat_id)
            if vod:
                videos.append(vod)
            vod_id = f"{cat_id}_{m.get('id', '')}"
            self._detail_cache[vod_id] = (m, cat_id)
        return videos

    def _parse_movie(self, m, cat_id='1'):
        try:
            vod_id = f"{cat_id}_{m.get('id', '')}"
            title = m.get('title', '')
            if not title:
                return None
            pic = m.get('cover', '') or m.get('cdncover', '')
            if pic and pic.startswith('//'):
                pic = 'https:' + pic
            remark = ''
            pubdate = m.get('pubdate', '')
            if pubdate:
                remark = pubdate[:4]
            score = m.get('score', 0)
            if score and score > 0:
                remark = f'{remark} {score}分'.strip()
            return {
                'vod_id': vod_id,
                'vod_name': title,
                'vod_pic': pic,
                'vod_remarks': remark,
            }
        except Exception as e:
            print(f'[{self.name}] parse movie error: {e}')
            return None

    def detailContent(self, ids):
        try:
            vod_id = ids[0]
            parts = vod_id.split('_', 1)
            cat_id = parts[0] if len(parts) > 1 else '1'
            movie_id = parts[1] if len(parts) > 1 else vod_id

            detail = self._fetch_detail(cat_id, movie_id)
            if detail:
                return {'list': [detail]}

            return {'list': []}
        except Exception as e:
            print(f'[{self.name}] 错误: 详情爬取失败 - {e}')
            return {'list': []}

    def _fetch_detail(self, cat_id, movie_id):
        try:
            vod_id = f"{cat_id}_{movie_id}"
            if vod_id in self._detail_cache:
                m, cached_cat_id = self._detail_cache[vod_id]
                return self._parse_detail(m, cached_cat_id)

            page = 1
            found = None
            while page <= 10:
                url = f'{self.host}/api/filter?catId={cat_id}&page={page}&size=20'
                res = self.session.get(url, headers=self.headers, timeout=15)
                data = res.json()
                movies = data.get('movies', [])
                if not movies:
                    break
                for m in movies:
                    cached_id = f"{cat_id}_{m.get('id', '')}"
                    self._detail_cache[cached_id] = (m, cat_id)
                    if m.get('id') == movie_id:
                        found = m
                if found:
                    break
                page += 1

            if not found:
                return None

            return self._parse_detail(found, cat_id)
        except Exception as e:
            print(f'[{self.name}] fetch detail error: {e}')
            return None

    def _parse_detail(self, m, cat_id):
        try:
            vod_id = f"{cat_id}_{m.get('id', '')}"
            title = m.get('title', '')
            pic = m.get('cover', '') or m.get('cdncover', '')
            if pic and pic.startswith('//'):
                pic = 'https:' + pic

            director_list = m.get('director', [])
            director = '/'.join(director_list) if isinstance(director_list, list) else str(director_list)

            actor_list = m.get('actor', [])
            actor = '/'.join(actor_list) if isinstance(actor_list, list) else str(actor_list)

            area_list = m.get('area', [])
            area = '/'.join(area_list) if isinstance(area_list, list) else str(area_list)

            category_list = m.get('moviecategory', [])
            vod_class = '/'.join(category_list) if isinstance(category_list, list) else str(category_list)

            pubdate = m.get('pubdate', '')
            year = pubdate[:4] if pubdate else ''

            description = m.get('description', '')

            playlinks = m.get('playlinks', {})
            playlink_sites = m.get('playlink_sites', [])

            play_from_list = []
            play_url_list = []

            if playlink_sites and isinstance(playlink_sites, list):
                for site in playlink_sites:
                    if site in playlinks:
                        url = playlinks[site]
                        if url:
                            play_from_list.append(site)
                            play_url_list.append(f'正片${url}')
            elif playlinks and isinstance(playlinks, dict):
                for site, url in playlinks.items():
                    if url:
                        play_from_list.append(site)
                        play_url_list.append(f'正片${url}')

            vod_play_from = '$$$'.join(play_from_list) if play_from_list else ''
            vod_play_url = '$$$'.join(play_url_list) if play_url_list else ''

            remark = ''
            score = m.get('score', 0)
            if score and score > 0:
                remark = f'{score}分'

            return {
                'vod_id': vod_id,
                'vod_name': title,
                'vod_pic': pic,
                'vod_director': director,
                'vod_actor': actor,
                'vod_content': description,
                'vod_remarks': remark,
                'vod_year': year,
                'vod_area': area,
                'vod_class': vod_class,
                'vod_play_from': vod_play_from,
                'vod_play_url': vod_play_url,
            }
        except Exception as e:
            print(f'[{self.name}] parse detail error: {e}')
            return None

    def playerContent(self, flag, id, vipFlags):
        try:
            play_url = ''
            if id and id.startswith('http'):
                play_url = id
            elif '$' in str(id):
                parts = str(id).split('$', 1)
                if len(parts) == 2:
                    play_url = parts[1]
            else:
                play_url = id

            return {
                'parse': 1,
                'playUrl': '',
                'url': play_url,
            }
        except Exception as e:
            print(f'[{self.name}] playerContent error: {e}')
            return {
                'parse': 1,
                'playUrl': '',
                'url': str(id),
            }

    def searchContent(self, key, quick, pg):
        try:
            search_url = f'{self.host}/api/search?wd={urllib.parse.quote(key)}'
            res = self.session.get(search_url, headers=self.headers, timeout=15)
            data = res.json()
            results = data.get('results', [])
            videos = []
            if results and isinstance(results, list):
                for item in results:
                    vod = self._parse_search_item(item)
                    if vod:
                        videos.append(vod)
            return {'list': videos}
        except Exception as e:
            print(f'[{self.name}] 错误: 搜索爬取失败 - {e}')
            return {'list': []}

    def _parse_search_item(self, item):
        try:
            vod_id = item.get('id', '')
            title = item.get('title', '')
            if not title:
                return None
            pic = item.get('cover', '') or item.get('cdncover', '')
            if pic and pic.startswith('//'):
                pic = 'https:' + pic
            return {
                'vod_id': f'search_{vod_id}',
                'vod_name': title,
                'vod_pic': pic,
                'vod_remarks': '',
            }
        except Exception as e:
            return None

    def _fix_pic_url(self, url):
        if not url:
            return ''
        if url.startswith('http'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.host + url
        return url
