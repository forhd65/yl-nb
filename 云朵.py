"""
@header({
  searchable: 1,
  filterable: 1,
  quickSearch: 1,
  title: '云朵影视',
  lang: 'hipy',
})
"""
# -*- coding: utf-8 -*-
import re
import json
import urllib3
import requests
from urllib.parse import quote

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from base.spider import Spider as BaseSpider


X_CLIENT = '8f3d2a1c7b6e5d4c9a0b1f2e3d4c5b6a'
WEB_SIGN = 'yda81x6d9ad3c4s'

PARSE_MAP = {
    'JD4K': 'https://fgsrg.hzqingshan.com/player/?url=',
    'JD2K': 'https://fgsrg.hzqingshan.com/player/?url=',
    'YYNB': 'https://zzrs.mfdyvip.com/player/?url=',
}


class Spider(BaseSpider):
    def init(self, extend=""):
        self.session = requests.Session()
        self.host = 'https://ds3xy2yunsa.xyz'
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': self.host + '/',
            'X-Client': X_CLIENT,
            'web-sign': WEB_SIGN,
        })
        self.categories = [
            {'type_id': '1', 'type_name': '电影'},
            {'type_id': '2', 'type_name': '剧集'},
            {'type_id': '3', 'type_name': '动漫'},
            {'type_id': '4', 'type_name': '综艺'},
        ]
        self.category_map = {
            '1': '电影',
            '2': '剧集',
            '3': '动漫',
            '4': '综艺',
        }

    def getName(self):
        return '云朵影视'

    def _api_get(self, path, params=None):
        try:
            url = self.host + path
            headers = dict(self.session.headers)
            headers['Referer'] = self.host + '/'
            r = self.session.get(url, params=params, headers=headers, timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print('[云朵影视] API请求错误: {}'.format(e))
        return None

    def homeContent(self, filter):
        result = {"class": self.categories}
        try:
            data = self._api_get('/api.php/web/index/home')
            if data and data.get('code') == 200 and data.get('data'):
                home_data = data['data']
                cats = home_data.get('categories', [])
                videos = []
                seen = set()
                for cat in cats:
                    for v in cat.get('videos', []):
                        vid = str(v.get('vod_id', ''))
                        if vid and vid not in seen:
                            seen.add(vid)
                            videos.append({
                                'vod_id': vid,
                                'vod_name': v.get('vod_name', ''),
                                'vod_pic': v.get('vod_pic', ''),
                                'vod_remarks': v.get('vod_remarks', ''),
                            })
                if videos:
                    result['list'] = videos
        except Exception as e:
            print('[云朵影视] 首页错误: {}'.format(e))
        return result

    def homeVideoContent(self):
        result = {"list": []}
        try:
            data = self._api_get('/api.php/web/index/home')
            if data and data.get('code') == 200 and data.get('data'):
                home_data = data['data']
                cats = home_data.get('categories', [])
                videos = []
                seen = set()
                for cat in cats:
                    for v in cat.get('videos', []):
                        vid = str(v.get('vod_id', ''))
                        if vid and vid not in seen:
                            seen.add(vid)
                            videos.append({
                                'vod_id': vid,
                                'vod_name': v.get('vod_name', ''),
                                'vod_pic': v.get('vod_pic', ''),
                                'vod_remarks': v.get('vod_remarks', ''),
                            })
                result['list'] = videos
        except Exception as e:
            print('[云朵影视] 首页推荐错误: {}'.format(e))
        return result

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg and str(pg).isdigit() else 1
        result = {"list": [], "page": page, "pagecount": 1, "limit": 24, "total": 0}
        try:
            type_name = self.category_map.get(str(tid), '电影')
            params = {
                'type_name': type_name,
                'type_id': int(tid),
                'page': page,
                'sort': 'hits',
            }
            data = self._api_get('/api.php/web/filter/vod', params=params)
            if data and data.get('code') == 200 and data.get('data'):
                items = data['data']
                videos = []
                for v in items:
                    video = {
                        'vod_id': str(v.get('vod_id', '')),
                        'vod_name': v.get('vod_name', ''),
                        'vod_pic': v.get('vod_pic', ''),
                        'vod_remarks': v.get('vod_remarks', ''),
                        'vod_actor': v.get('vod_actor', ''),
                    }
                    if isinstance(video['vod_actor'], list):
                        video['vod_actor'] = ','.join(video['vod_actor'])
                    videos.append(video)
                result['list'] = videos
                result['pagecount'] = page + 1 if len(videos) >= 24 else page
                result['total'] = 99999 if len(videos) >= 24 else len(videos)
        except Exception as e:
            print('[云朵影视] 分类错误: {}'.format(e))
        return result

    def detailContent(self, ids):
        result = {"list": []}
        vid = ids[0]
        try:
            data = self._api_get('/api.php/web/vod/get_detail', params={'vod_id': vid})
            if not data or data.get('code') != 200 or not data.get('data'):
                return result
            
            vod_data = data['data'][0]
            vod = {
                'vod_id': str(vod_data.get('vod_id', vid)),
                'vod_name': vod_data.get('vod_name', ''),
                'vod_pic': vod_data.get('vod_pic', ''),
                'vod_director': vod_data.get('vod_director', ''),
                'vod_actor': vod_data.get('vod_actor', ''),
                'vod_year': str(vod_data.get('vod_year', '')),
                'vod_area': '',
                'vod_remarks': vod_data.get('vod_remarks', ''),
                'vod_content': '',
                'vod_play_from': '',
                'vod_play_url': '',
            }

            area = vod_data.get('vod_area', '')
            if isinstance(area, list):
                vod['vod_area'] = ','.join(area)
            else:
                vod['vod_area'] = str(area)

            content = vod_data.get('vod_content', '')
            if content:
                content = re.sub(r'<[^>]+>', '', content).strip()
                vod['vod_content'] = content

            play_from = []
            play_url = []
            
            agg_data = self._api_get('/api.php/web/internal/search_aggregate', params={'vod_id': vid})
            if agg_data and agg_data.get('code') == 200 and agg_data.get('data'):
                for item in agg_data['data']:
                    site_name = item.get('site_name', '')
                    site_key = item.get('site_key', '')
                    pf = item.get('vod_play_from', '')
                    pu = item.get('vod_play_url', '')
                    decode_status = item.get('decode_status', 0)
                    
                    if not pf or not pu:
                        continue
                    
                    if decode_status == 0 and '.m3u8' in pu:
                        play_from.append(site_name if site_name else pf)
                        play_url.append(pu)
            
            if not play_from:
                orig_from = vod_data.get('vod_play_from', '')
                orig_url = vod_data.get('vod_play_url', '')
                if orig_from and orig_url:
                    from_list = orig_from.split('$$$')
                    url_list = orig_url.split('$$$')
                    for pf, pu in zip(from_list, url_list):
                        if pf and pu:
                            play_from.append(pf.strip())
                            play_url.append(pu.strip())
            
            vod['vod_play_from'] = '$$$'.join(play_from)
            vod['vod_play_url'] = '$$$'.join(play_url)

            result['list'].append(vod)
        except Exception as e:
            print('[云朵影视] 详情错误: {}'.format(e))
        return result

    def playerContent(self, flag, id, vipFlags):
        result = {"parse": 0, "playUrl": "", "url": "", "header": ""}
        try:
            if id and id.startswith('http') and '.m3u8' in id:
                result['parse'] = 0
                result['url'] = id
                result['header'] = json.dumps({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': self.host + '/'
                }, ensure_ascii=False)
            elif flag in PARSE_MAP:
                parse_url = PARSE_MAP[flag] + id
                result['parse'] = 1
                result['url'] = parse_url
                result['header'] = json.dumps({
                    'User-Agent': self.session.headers['User-Agent'],
                    'Referer': self.host + '/'
                }, ensure_ascii=False)
            else:
                play_url = self.host + '/play/' + id
                result['parse'] = 1
                result['url'] = play_url
                result['header'] = json.dumps({
                    'User-Agent': self.session.headers['User-Agent'],
                    'Referer': self.host + '/'
                }, ensure_ascii=False)
        except Exception as e:
            print('[云朵影视] 播放错误: {}'.format(e))
        return result

    def searchContent(self, key, quick, pg="1"):
        return self.searchContentPage(key, quick, pg)

    def searchContentPage(self, key, quick, pg):
        page = int(pg) if pg and str(pg).isdigit() else 1
        result = {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}
        try:
            params = {
                'wd': key,
                'page': page,
                'limit': 20,
            }
            data = self._api_get('/api.php/web/search/index', params=params)
            if data and data.get('code') == 200 and data.get('data'):
                items = data['data']
                videos = []
                for v in items:
                    video = {
                        'vod_id': str(v.get('vod_id', '')),
                        'vod_name': v.get('vod_name', ''),
                        'vod_pic': v.get('vod_pic', ''),
                        'vod_remarks': v.get('vod_remarks', ''),
                        'vod_actor': v.get('vod_actor', ''),
                    }
                    if isinstance(video['vod_actor'], list):
                        video['vod_actor'] = ','.join(video['vod_actor'])
                    videos.append(video)
                result['list'] = videos
                result['pagecount'] = page + 1 if len(videos) >= 20 else page
                result['total'] = 99999 if len(videos) >= 20 else len(videos)
        except Exception as e:
            print('[云朵影视] 搜索错误: {}'.format(e))
        return result

    def localProxy(self, param=''):
        return {}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False
