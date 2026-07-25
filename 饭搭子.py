"""
@header({
  searchable: 1,
  filterable: 1,
  quickSearch: 1,
  title: '饭搭子影视',
  lang: 'hipy',
})
"""
# -*- coding: utf-8 -*-
import re
import json
import urllib3
from urllib.parse import quote, urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def init(self, extend=""):
        self.host_list = [
            "https://fdzys.net",
            "https://fdzys666.xyz",
            "https://fff666.site",
        ]
        self.host = self.host_list[0]
        self.host_index = 0
        self.web_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
        }
        self.categories = [
            {'type_id': 'movie', 'type_name': '电影'},
            {'type_id': 'tv', 'type_name': '电视剧'},
            {'type_id': 'dongman', 'type_name': '动漫'},
            {'type_id': 'zongyi', 'type_name': '综艺'},
            {'type_id': 'tiyu', 'type_name': '体育'},
            {'type_id': 'duanju', 'type_name': '短剧'},
        ]

    def getName(self):
        return '饭搭子影视'

    def _fetch(self, url):
        try:
            if url.startswith('http'):
                headers = dict(self.web_headers)
                rsp = self.fetch(url, headers=headers)
                if rsp and rsp.text:
                    return rsp.text
                return ''
            for i in range(len(self.host_list)):
                idx = (self.host_index + i) % len(self.host_list)
                host = self.host_list[idx]
                try:
                    full_url = host + url
                    headers = dict(self.web_headers)
                    headers["Referer"] = host + "/"
                    rsp = self.fetch(full_url, headers=headers)
                    if rsp and rsp.text and len(rsp.text) > 1000:
                        if idx != self.host_index:
                            self.host_index = idx
                            self.host = host
                            self.web_headers["Referer"] = host + "/"
                        return rsp.text
                except:
                    continue
            return ''
        except:
            return ''

    def _parse_vod_list(self, html):
        result = []
        seen = set()
        try:
            pattern = r'<div[^>]+class="[^"]*content-card[^"]*"[^>]*>.*?<img[^>]+data-src="([^"]+)"[^>]+alt="([^"]*)"[^>]*>.*?</div>\s*</div>\s*</a>'
            matches = re.findall(pattern, html, re.S)
            for img, title in matches:
                m_href = re.search(r'<a[^>]+href="([^"]+)"[^>]*>\s*<div[^>]+class="[^"]*content-card', html[max(0, html.find(img)-500):html.find(img)+50], re.S)
                href = ''
                if not m_href:
                    img_idx = html.find(img)
                    before = html[max(0, img_idx-1000):img_idx]
                    all_a = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>', before)
                    if all_a:
                        href = all_a[-1]
                else:
                    href = m_href.group(1)
                
                if not href or not re.search(r'/(?:movie|tv|dongman|zongyi|tiyu|duanju)/', href):
                    continue
                if href in seen:
                    continue
                seen.add(href)
                
                vod_id = self._extract_vod_id(href)
                if not vod_id:
                    continue
                
                result.append({
                    "vod_id": vod_id,
                    "vod_name": title.strip() if title else '',
                    "vod_pic": img if img.startswith('http') else urljoin(self.host, img),
                    "vod_remarks": '',
                })
        except Exception as e:
            print('_parse_vod_list error: {}'.format(e))
        
        if len(result) < 5:
            try:
                card_pattern = r'<div[^>]+class="[^"]*card-box[^"]*"[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>.*?data-src="([^"]+)"[^>]+alt="([^"]*)"[^>]*>'
                matches2 = re.findall(card_pattern, html, re.S)
                for href, img, title in matches2:
                    if not re.search(r'/(?:movie|tv|dongman|zongyi|tiyu|duanju)/', href):
                        continue
                    if href in seen:
                        continue
                    seen.add(href)
                    vod_id = self._extract_vod_id(href)
                    if not vod_id:
                        continue
                    result.append({
                        "vod_id": vod_id,
                        "vod_name": title.strip() if title else '',
                        "vod_pic": img if img.startswith('http') else urljoin(self.host, img),
                        "vod_remarks": '',
                    })
            except Exception as e:
                print('_parse_vod_list fallback error: {}'.format(e))
        
        return result

    def _extract_vod_id(self, url):
        try:
            m = re.search(r'/(?:movie|tv|dongman|zongyi|tiyu|duanju)/([^/?#]+)', url)
            if m:
                slug = m.group(1)
                cat = ''
                if '/movie/' in url:
                    cat = 'movie'
                elif '/tv/' in url:
                    cat = 'tv'
                elif '/dongman/' in url:
                    cat = 'dongman'
                elif '/zongyi/' in url:
                    cat = 'zongyi'
                elif '/tiyu/' in url:
                    cat = 'tiyu'
                elif '/duanju/' in url:
                    cat = 'duanju'
                return '{}__{}'.format(cat, slug)
        except:
            pass
        return ''

    def _parse_detail(self, html, vod_id):
        try:
            vod = {
                "vod_id": vod_id,
                "vod_name": "",
                "vod_pic": "",
                "vod_director": "",
                "vod_actor": "",
                "vod_year": "",
                "vod_area": "",
                "vod_remarks": "",
                "vod_content": "",
                "vod_play_from": "",
                "vod_play_url": "",
            }

            ld_json_matches = re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S)
            for ld_text in ld_json_matches:
                try:
                    ld_data = json.loads(ld_text.strip())
                    if ld_data.get('@type') == 'VideoObject':
                        if not vod["vod_name"]:
                            vod["vod_name"] = ld_data.get('name', '')
                        if not vod["vod_pic"]:
                            vod["vod_pic"] = ld_data.get('thumbnailUrl', '')
                        if not vod["vod_content"]:
                            vod["vod_content"] = ld_data.get('description', '')
                        if not vod["vod_director"]:
                            director = ld_data.get('director', {})
                            if isinstance(director, dict):
                                vod["vod_director"] = director.get('name', '')
                            elif isinstance(director, list) and director:
                                names = [d.get('name', '') for d in director if isinstance(d, dict) and d.get('name')]
                                if names:
                                    vod["vod_director"] = ','.join(names)
                        if not vod["vod_actor"]:
                            actors = ld_data.get('actor', [])
                            if isinstance(actors, list):
                                actor_names = [a.get('name', '') for a in actors if isinstance(a, dict) and a.get('name')]
                                if actor_names:
                                    vod["vod_actor"] = ','.join(actor_names)
                        upload_date = ld_data.get('uploadDate', '')
                        if upload_date and str(upload_date).isdigit() and not vod["vod_year"]:
                            try:
                                import datetime
                                dt = datetime.datetime.fromtimestamp(int(upload_date))
                                vod["vod_year"] = str(dt.year)
                            except:
                                pass
                        break
                except:
                    continue

            m_player = re.search(r'var player_aaaa=({.*?})</script>', html, re.S)
            player_data = {}
            if m_player:
                try:
                    player_data = json.loads(m_player.group(1))
                except:
                    pass
            
            vod_data = player_data.get('vod_data', {})
            if vod_data:
                vod["vod_name"] = vod_data.get('vod_name', '')
                vod["vod_actor"] = vod_data.get('vod_actor', '')
                vod["vod_director"] = vod_data.get('vod_director', '')
                vod["vod_class"] = vod_data.get('vod_class', '')

            m_name = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
            if m_name and not vod["vod_name"]:
                vod["vod_name"] = re.sub(r'<[^>]+>', '', m_name.group(1)).strip()

            if not vod["vod_name"]:
                m_title = re.search(r'<title>([^<_]+)', html)
                if m_title:
                    vod["vod_name"] = m_title.group(1).strip()

            m_pic = re.search(r'property="og:image"[^>]*content="([^"]+)"', html)
            if m_pic:
                vod["vod_pic"] = m_pic.group(1)

            if not vod["vod_pic"]:
                m_pic2 = re.search(r'data-src="([^"]+)"[^>]*class="[^"]*detail[^"]*"', html)
                if m_pic2:
                    vod["vod_pic"] = m_pic2.group(1)

            if vod["vod_pic"] and not vod["vod_pic"].startswith('http'):
                vod["vod_pic"] = urljoin(self.host, vod["vod_pic"])

            if not vod["vod_director"]:
                m_dir = re.search(r'导演.*?<(?:span|div)[^>]*>(.*?)</(?:span|div)>', html, re.S)
                if m_dir:
                    directors = re.findall(r'>([^<]+)</a>', m_dir.group(1))
                    if directors:
                        vod["vod_director"] = ','.join(directors)

            if not vod["vod_actor"]:
                m_act = re.search(r'(?:主演|演员).*?<(?:span|div)[^>]*>(.*?)</(?:span|div)>', html, re.S)
                if m_act:
                    actors = re.findall(r'>([^<]+)</a>', m_act.group(1))
                    if actors:
                        vod["vod_actor"] = ','.join(actors)

            if not vod["vod_year"]:
                m_year = re.search(r'(?:年份|上映|首播).*?(\d{4})', html, re.S)
                if not m_year:
                    m_year_title = re.search(r'<title>[^<]*(\d{4})[^<]*</title>', html)
                    if m_year_title:
                        y = m_year_title.group(1)
                        if 1900 <= int(y) <= 2100:
                            vod["vod_year"] = y
                if m_year and not vod["vod_year"]:
                    y = m_year.group(1)
                    if 1900 <= int(y) <= 2100:
                        vod["vod_year"] = y

            m_area = re.search(r'地区.*?<(?:span|div)[^>]*>(.*?)</(?:span|div)>', html, re.S)
            if m_area:
                areas = re.findall(r'>([^<]+)</a>', m_area.group(1))
                if areas:
                    vod["vod_area"] = ','.join(areas)

            m_content = re.search(r'(?:简介|剧情).*?<(?:span|div|p)[^>]*class="[^"]*(?:content|desc|detail|intro)[^"]*"[^>]*>(.*?)</(?:span|div|p)>', html, re.S)
            if m_content:
                vod["vod_content"] = re.sub(r'<[^>]+>', '', m_content.group(1)).strip()

            if not vod["vod_content"]:
                m_desc = re.search(r'name="description"[^>]*content="([^"]+)"', html)
                if m_desc:
                    vod["vod_content"] = m_desc.group(1)

            route_names = []
            seen_sids = set()
            route_items = re.findall(r'<li[^>]*class="[^"]*player_name[^"]*"[^>]*data-sid="(\d+)"[^>]*>.*?<a[^>]*>(.*?)</a>', html, re.S)
            for sid, text in route_items:
                if sid in seen_sids:
                    continue
                name = re.sub(r'<[^>]+>', '', text).strip()
                if name:
                    route_names.append((sid, name))
                    seen_sids.add(sid)
            
            if not route_names:
                route_pattern2 = r'data-sid="(\d+)".*?<span>([^<]+云|[^<]+线路|[^<]+播放源)</span>'
                routes2 = re.findall(route_pattern2, html, re.S)
                for sid, name in routes2:
                    if sid in seen_sids:
                        continue
                    route_names.append((sid, name.strip()))
                    seen_sids.add(sid)

            play_from_list = []
            play_url_list = []

            cat = vod_id.split('__')[0] if '__' in vod_id else 'movie'
            slug = vod_id.split('__')[1] if '__' in vod_id else vod_id

            for sid, route_name in route_names[:15]:
                ep_list = []
                seen_eps = set()
                playlist_pattern = r'id="playlist{}"[^>]*>(.*?)</div>\s*</div>\s*</div>'.format(sid)
                ep_m = re.search(playlist_pattern, html, re.S)
                if ep_m:
                    ep_html = ep_m.group(1)
                    ep_links = re.findall(r'<div[^>]+class="[^"]*listitem[^"]*"[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', ep_html, re.S)
                    for ep_href, ep_text in ep_links:
                        ep_name = re.sub(r'<[^>]+>', '', ep_text).strip()
                        if not ep_name or ep_name in seen_eps:
                            continue
                        if int(sid) > 1:
                            if ('sid=' + sid) not in ep_href:
                                continue
                        else:
                            if 'sid=' in ep_href:
                                continue
                        seen_eps.add(ep_name)
                        ep_nid = ''
                        clean_href = ep_href.split('?')[0]
                        parts = clean_href.rstrip('/').split('/')
                        if parts:
                            ep_nid = parts[-1]
                        else:
                            ep_nid = ep_name
                        ep_id = '{}__{}__{}__{}'.format(cat, slug, sid, ep_nid)
                        ep_list.append('{}${}'.format(ep_name, ep_id))
                
                if not ep_list:
                    ep_id = '{}__{}__{}__1'.format(cat, slug, sid)
                    ep_list.append('正片${}'.format(ep_id))

                if ep_list:
                    play_from_list.append(route_name)
                    play_url_list.append('#'.join(ep_list))

            vod["vod_play_from"] = '$$$'.join(play_from_list)
            vod["vod_play_url"] = '$$$'.join(play_url_list)

            return vod
        except Exception as e:
            print('_parse_detail error: {}'.format(e))
            return None

    def _get_m3u8_url(self, player_data):
        try:
            url = player_data.get('url', '')
            from_name = player_data.get('from', '')
            
            if not url:
                return ''
            
            if '.m3u8' in url:
                return url
            
            if 'share' in url or 'dytt' in from_name:
                try:
                    headers = dict(self.web_headers)
                    headers["Referer"] = self.host + "/"
                    rsp = self.fetch(url, headers=headers)
                    if rsp and rsp.text:
                        m = re.search(r'const url\s*=\s*["\']([^"\']+)["\']', rsp.text)
                        if m:
                            m3u8_path = m.group(1)
                            full_url = urljoin(url, m3u8_path)
                            return full_url
                except:
                    pass
            
            return url
        except Exception as e:
            print('_get_m3u8_url error: {}'.format(e))
            return ''

    def homeContent(self, filter):
        return {"class": self.categories}

    def homeVideoContent(self):
        html = self._fetch('/')
        items = self._parse_vod_list(html)
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg and str(pg).isdigit() else 1
        if page <= 1:
            url = '/{}'.format(tid)
        else:
            url = '/{}/?page={}'.format(tid, page)
        
        html = self._fetch(url)
        items = self._parse_vod_list(html)
        
        page_count = page if len(items) < 30 else page + 1
        return {"list": items, "page": page, "pagecount": page_count, "limit": 30, "total": 99999}

    def detailContent(self, ids):
        result = {"list": []}
        try:
            vid = ids[0]
            parts = vid.split('__')
            if len(parts) < 2:
                return result
            
            cat = parts[0]
            slug = parts[1]
            
            detail_url = '/{}/{}'.format(cat, slug)
            html = self._fetch(detail_url)
            if not html:
                return result
            
            vod = self._parse_detail(html, vid)
            if vod:
                result['list'].append(vod)
        except Exception as e:
            print('detailContent error: {}'.format(e))
        return result

    def playerContent(self, flag, id, vipFlags):
        result = {"parse": 0, "playUrl": "", "url": "", "header": ""}
        try:
            parts = id.split('__')
            if len(parts) < 4:
                return result
            
            cat = parts[0]
            slug = parts[1]
            sid = parts[2]
            nid = parts[3]
            
            play_url = '/{}/{}/{}?sid={}'.format(cat, slug, nid, sid)
            html = self._fetch(play_url)
            if not html:
                return result
            
            m_player = re.search(r'var player_aaaa=({.*?})</script>', html, re.S)
            if not m_player:
                return result
            
            player_data = json.loads(m_player.group(1))
            m3u8_url = self._get_m3u8_url(player_data)
            
            if m3u8_url:
                result["url"] = m3u8_url
                result["parse"] = 0
                result["header"] = json.dumps({
                    "User-Agent": self.web_headers.get("User-Agent", ""),
                    "Referer": self.host + "/",
                    "Origin": self.host,
                    "Accept": "*/*",
                })
        except Exception as e:
            print('playerContent error: {}'.format(e))
        return result

    def searchContent(self, key, quick, pg="1"):
        return self.searchContentPage(key, quick, pg)

    def searchContentPage(self, key, quick, pg):
        page = int(pg) if pg and str(pg).isdigit() else 1
        items = []
        search_urls = [
            '/yu-{}-xianguan-de-yingpian-shippin-zhibo'.format(quote(key)),
            '/index.php?m=vod-search&wd={}&page={}'.format(quote(key), page),
            '/index.php?m=vod-search&wd={}'.format(quote(key)),
        ]
        for url in search_urls:
            html = self._fetch(url)
            if html:
                items = self._parse_vod_list(html)
                if items:
                    break
        return {"list": items, "page": page, "pagecount": 9999, "limit": 20, "total": 99999}

    def localProxy(self, params):
        try:
            if not isinstance(params, dict):
                return None
            url = params.get('url', '')
            ptype = params.get('type', '')
            
            if not url:
                return None
            
            need_referer = False
            if ptype in ['m3u8', 'ts', 'media', 'key']:
                need_referer = True
            
            if need_referer:
                header = params.get('header', {})
                if not isinstance(header, dict):
                    header = {}
                header["Referer"] = self.host + "/"
                header["Origin"] = self.host
                header["User-Agent"] = self.web_headers.get("User-Agent", "")
                header["Accept"] = "*/*"
                
                return {
                    'url': url,
                    'header': header,
                    'param': params.get('param', ''),
                    'type': ptype
                }
        except Exception as e:
            print('localProxy error: {}'.format(e))
        return None

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False
