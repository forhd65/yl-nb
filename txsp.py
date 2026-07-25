"""
@header({
  searchable: 1,
  filterable: 0,
  quickSearch: 1,
  title: '腾讯视频',
  lang: 'hipy',
})
"""
# -*- coding: utf-8 -*-
import re
import json
import sys
import requests
from urllib.parse import quote

sys.path.append('..')
from base.spider import Spider


class Spider(Spider):
    def init(self, extend=""):
        self.host = "https://v.qq.com"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.61 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": self.host + "/",
        })

    def getName(self):
        return '腾讯视频'

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def homeContent(self, filter):
        return {"class": [
            {'type_id': 'movie', 'type_name': '电影'},
            {'type_id': 'tv', 'type_name': '电视剧'},
            {'type_id': 'variety', 'type_name': '综艺'},
            {'type_id': 'cartoon', 'type_name': '动漫'},
            {'type_id': 'documentary', 'type_name': '纪录片'},
            {'type_id': 'kids', 'type_name': '少儿'},
            {'type_id': 'sports', 'type_name': '体育'},
            {'type_id': 'music', 'type_name': '音乐'},
        ]}

    def homeVideoContent(self):
        items = self._get_movie_list('movie', 1)
        if not items:
            items = self._get_hot_list()
        return {"list": items[:30]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg and str(pg).isdigit() else 1
        
        channel_map = {
            'movie': 'movie',
            'tv': 'tv',
            'variety': 'variety',
            'cartoon': 'cartoon',
            'documentary': 'documentary',
            'kids': 'kids',
            'sports': 'sports',
            'music': 'music',
        }
        channel = channel_map.get(tid, tid)
        
        items = self._get_movie_list(channel, page)
        
        page_count = page + 10
        return {"list": items, "page": page, "pagecount": page_count, "limit": 30, "total": 99999}

    def detailContent(self, ids):
        result = {"list": []}
        vid = ids[0]
        try:
            detail_api = f'https://node.video.qq.com/x/api/float_vinfo2?cid={vid}'
            rsp = self.session.get(detail_api, timeout=10)
            data = rsp.json()
            
            if 'c' not in data:
                url = f'{self.host}/x/cover/{vid}.html'
                rsp = self.session.get(url, timeout=10)
                html = rsp.content.decode('utf-8', errors='replace')
                return self._parse_detail_html(html, vid)

            info = data['c']
            
            vod_name = info.get('title', '')
            vod_pic = info.get('pic', '')
            vod_director = ','.join(info.get('dir', []))
            vod_actor = ','.join(info.get('nam', []))
            vod_year = info.get('year', '')
            vod_content = info.get('description', '')
            vod_remarks = data.get('rec', '')
            
            vod_area = ''
            vod_type = ','.join(info.get('typ', []))
            
            video_ids = info.get('video_ids', [])
            
            play_urls = []
            if video_ids:
                if len(video_ids) == 1:
                    real_vid = video_ids[0]
                    play_urls.append(f'在线播放${self.host}/x/play.html?vid={real_vid}')
                else:
                    play_urls = self._get_playlist_items(vid, video_ids)
            
            if not play_urls and video_ids:
                real_vid = video_ids[0]
                play_urls.append(f'在线播放${self.host}/x/play.html?vid={real_vid}')
            
            if not play_urls:
                play_urls.append(f'在线播放${self.host}/x/cover/{vid}.html')

            vod = {
                "vod_id": vid,
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_director": vod_director,
                "vod_actor": vod_actor,
                "vod_year": vod_year,
                "vod_area": vod_area,
                "vod_remarks": vod_remarks,
                "vod_content": vod_content,
                "vod_play_from": '腾讯视频',
                "vod_play_url": '#'.join(play_urls),
            }
            result['list'].append(vod)
        except Exception as e:
            print(f'detailContent error: {e}')
            try:
                url = f'{self.host}/x/cover/{vid}.html'
                rsp = self.session.get(url, timeout=10)
                html = rsp.content.decode('utf-8', errors='replace')
                return self._parse_detail_html(html, vid)
            except:
                pass
        return result

    def playerContent(self, flag, id, vipFlags):
        result = {"jx": 1, "parse": 1, "playUrl": "", "url": "", "header": ""}
        try:
            real_vid = None
            cid = None
            
            if id.startswith('http'):
                url = id
                vid_match = re.search(r'/cover/([^/]+)/([^/]+)\.html', url)
                if vid_match:
                    cid = vid_match.group(1)
                    real_vid = vid_match.group(2)
                elif '/play.html?vid=' in url:
                    vid_match = re.search(r'vid=([^&]+)', url)
                    if vid_match:
                        real_vid = vid_match.group(1)
                else:
                    vid_match2 = re.search(r'/cover/([^/]+)\.html', url)
                    if vid_match2:
                        cid = vid_match2.group(1)
            
            elif id.startswith('/'):
                vid_match = re.search(r'/cover/([^/]+)/([^/]+)\.html', id)
                if vid_match:
                    cid = vid_match.group(1)
                    real_vid = vid_match.group(2)
                else:
                    vid_match2 = re.search(r'/cover/([^/]+)\.html', id)
                    if vid_match2:
                        cid = vid_match2.group(1)
            elif id.startswith('s'):
                real_vid = id
            else:
                cid = id
            
            if not real_vid and cid:
                try:
                    detail_api = f'https://node.video.qq.com/x/api/float_vinfo2?cid={cid}'
                    rsp = self.session.get(detail_api, timeout=5)
                    data = rsp.json()
                    if 'c' in data and data['c'].get('video_ids'):
                        real_vid = data['c']['video_ids'][0]
                except:
                    pass
            
            if real_vid:
                url = f'https://m.v.qq.com/play.html?vid={real_vid}'
                if cid:
                    url += f'&cid={cid}'
            else:
                url = f'{self.host}/x/cover/{cid}.html' if cid else id
            
            result["url"] = url
            result["parse"] = 1
            result["header"] = ""
        except Exception as e:
            print(f'playerContent error: {e}')
            url = id if id.startswith('http') else f'{self.host}/x/cover/{id}.html'
            result["url"] = url
        return result

    def searchContent(self, key, quick, pg="1"):
        return self.searchContentPage(key, quick, pg)

    def searchContentPage(self, key, quick, pg):
        page = int(pg) if pg and str(pg).isdigit() else 1
        items = []
        try:
            search_api = f'https://pbaccess.video.qq.com/trpc.videosearch.smartboxServer.HttpRountRecall/Smartbox?query={quote(key)}&appID=3172&appKey=lGhFIPeD3HsO9xEp&pageNum={page-1}&pageSize=10'
            rsp = self.session.get(search_api, timeout=10)
            data = rsp.json()
            
            if data.get('data', {}).get('smartboxItemList'):
                for item in data['data']['smartboxItemList'][:10]:
                    cid = item.get('basicDoc', {}).get('id', '')
                    if cid:
                        detail_url = f'https://node.video.qq.com/x/api/float_vinfo2?cid={cid}'
                        try:
                            detail_rsp = self.session.get(detail_url, timeout=5)
                            detail_data = detail_rsp.json()
                            info = detail_data.get('c', {})
                            items.append({
                                "vod_id": cid,
                                "vod_name": info.get('title', ''),
                                "vod_pic": info.get('pic', ''),
                                "vod_remarks": detail_data.get('rec', ''),
                            })
                        except:
                            pass
        except Exception as e:
            print(f'searchContentPage error: {e}')
            try:
                search_url = f'{self.host}/x/search/?q={quote(key)}&stag=fypage'
                rsp = self.session.get(search_url, timeout=10)
                html = rsp.content.decode('utf-8', errors='replace')
                items = self._parse_search_result(html)
            except:
                pass
        return {"list": items, "page": page, "pagecount": 9999, "limit": 20, "total": 99999}

    def localProxy(self, param=''):
        return {}

    def _get_movie_list(self, channel, page):
        items = []
        try:
            url = f'{self.host}/x/bu/pagesheet/list?_all=1&append=1&channel={channel}&listpage=1&offset={(page-1)*21}&pagesize=21&iarea=-1&sort=75'
            rsp = self.session.get(url, timeout=10)
            html = rsp.content.decode('utf-8', errors='replace')
            
            items = self._parse_api_response(html)
            
            if not items:
                url2 = f'{self.host}/channel/{channel}?page={page}'
                rsp2 = self.session.get(url2, timeout=10)
                html2 = rsp2.content.decode('utf-8', errors='replace')
                items = self._parse_html_list(html2)
        except Exception as e:
            print(f'_get_movie_list error: {e}')
        return items

    def _get_hot_list(self):
        items = []
        try:
            url = f'{self.host}/channel/movie'
            rsp = self.session.get(url, timeout=10)
            html = rsp.content.decode('utf-8', errors='replace')
            items = self._parse_html_list(html)
        except Exception as e:
            print(f'_get_hot_list error: {e}')
        return items

    def _get_playlist_items(self, cid, video_ids):
        play_urls = []
        try:
            chunks = [video_ids[i:i+30] for i in range(0, len(video_ids), 30)]
            for chunk in chunks:
                ids_str = ','.join(chunk)
                union_url = f'https://union.video.qq.com/fcgi-bin/data?otype=json&tid=1804&appid=20001238&appkey=6c03bbe9658448a4&union_platform=1&idlist={ids_str}'
                rsp = self.session.get(union_url, timeout=10)
                text = rsp.text
                
                if text.startswith('QZOutputJson='):
                    text = text[len('QZOutputJson='):]
                
                text = text.strip()
                if 'QZOutputJson=' in text:
                    parts = text.split('QZOutputJson=')
                    for part in parts:
                        part = part.strip()
                        if part:
                            try:
                                data = json.loads(part)
                                if 'results' in data:
                                    for item in data['results']:
                                        fields = item.get('fields', {})
                                        vid = fields.get('vid', '')
                                        title = fields.get('title', '')
                                        if vid:
                                            if not title:
                                                title = f'第{len(play_urls)+1}集'
                                            play_urls.append(f'{title}${self.host}/x/play.html?vid={vid}')
                            except:
                                continue
                else:
                    try:
                        data = json.loads(text)
                        if 'results' in data:
                            for item in data['results']:
                                fields = item.get('fields', {})
                                vid = fields.get('vid', '')
                                title = fields.get('title', '')
                                if vid:
                                    if not title:
                                        title = f'第{len(play_urls)+1}集'
                                    play_urls.append(f'{title}${self.host}/x/play.html?vid={vid}')
                    except:
                        pass
        except Exception as e:
            print(f'_get_playlist_items error: {e}')
        
        if not play_urls:
            for i, vid in enumerate(video_ids[:50]):
                play_urls.append(f'第{i+1}集${self.host}/x/play.html?vid={vid}')
        
        return play_urls

    def _parse_api_response(self, html):
        videos = []
        seen = set()
        try:
            if not html:
                return videos

            card_patterns = [
                r'<a[^>]*href="([^"]*cover/([^"]+)\.html)"[^>]*>([^<]+)</a>',
            ]
            
            cards = []
            for pat in card_patterns:
                cards = re.findall(pat, html)
                if cards:
                    break

            if not cards:
                return videos

            pic_pattern = r'<img[^>]*src="([^"]*vcover[^"]*)"[^>]*>'
            pic_urls = re.findall(pic_pattern, html)

            remark_pattern = r'<span[^>]*class="[^"]*remark[^"]*"[^>]*>([^<]+)</span>'
            remarks = re.findall(remark_pattern, html)
            
            idx = 0
            for full_url, vid, title in cards:
                if vid in seen:
                    continue
                seen.add(vid)

                title = title.strip()
                if not title or len(title) < 2:
                    title = f'视频_{vid[:8]}'

                pic = ''
                for pic_url in pic_urls:
                    if vid in pic_url:
                        pic = pic_url
                        break
                if not pic:
                    pic = f'https://vcover-vt-pic.puui.qpic.cn/vcover_vt_pic/0/{vid}/220'

                remark = remarks[idx] if idx < len(remarks) else ''
                idx += 1

                videos.append({
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": remark,
                })

        except Exception as e:
            print(f'_parse_api_response error: {e}')
        return videos

    def _parse_html_list(self, html):
        videos = []
        seen = set()
        try:
            if not html:
                return videos

            figure_patterns = [
                r'<figure[^>]*>(.*?)</figure>',
            ]
            
            figures = []
            for pat in figure_patterns:
                figures = re.findall(pat, html, re.S | re.I)
                if figures:
                    break

            if not figures:
                a_patterns = [
                    r'<a[^>]*href="/x/cover/([^"]+)\.html"[^>]*>',
                ]
                for pat in a_patterns:
                    links = re.findall(pat, html)
                    if links:
                        for vid in links[:30]:
                            if vid in seen:
                                continue
                            seen.add(vid)
                            title = ''
                            pic = f'https://vcover-vt-pic.puui.qpic.cn/vcover_vt_pic/0/{vid}/220'
                            videos.append({
                                "vod_id": vid,
                                "vod_name": title,
                                "vod_pic": pic,
                                "vod_remarks": '',
                            })
                        break
                return videos

            for figure in figures:
                m_link = re.search(r'href="/x/cover/([^"]+)\.html"', figure)
                if not m_link:
                    continue

                vid = m_link.group(1)
                if vid in seen:
                    continue
                seen.add(vid)

                title = ''
                m_title = re.search(r'title="([^"]+)"', figure)
                if m_title:
                    title = m_title.group(1).strip()
                if not title:
                    m_title = re.search(r'<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</span>', figure, re.I)
                    if m_title:
                        title = m_title.group(1).strip()
                if not title:
                    m_title = re.search(r'<strong[^>]*>([^<]+)</strong>', figure)
                    if m_title:
                        title = m_title.group(1).strip()
                if not title or len(title) < 2:
                    continue

                pic = ''
                m_pic = re.search(r'src="(https?://[^"]+)"', figure)
                if m_pic:
                    pic = m_pic.group(1).strip()
                if not pic:
                    pic = f'https://vcover-vt-pic.puui.qpic.cn/vcover_vt_pic/0/{vid}/220'

                remark = ''
                m_remark = re.search(r'<span[^>]*class="[^"]*remark[^"]*"[^>]*>([^<]+)</span>', figure, re.I)
                if m_remark:
                    remark = m_remark.group(1).strip()

                videos.append({
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": remark,
                })

        except Exception as e:
            print(f'_parse_html_list error: {e}')
        return videos

    def _parse_search_result(self, html):
        items = []
        seen = set()
        try:
            result_items = re.findall(r'<div[^>]*class="result_item_v"[^>]*>(.*?)</div>', html, re.S)
            for item in result_items:
                m_title = re.search(r'<a[^>]*title="([^"]+)"[^>]*>([^<]+)</a>', item)
                m_link = re.search(r'<a[^>]*href="([^"]*)"[^>]*>', item)
                m_img = re.search(r'<img[^>]*src="([^"]+)"[^>]*>', item)
                
                if m_link and m_link.group(1):
                    href = m_link.group(1)
                    vid_match = re.search(r'/cover/([^/]+)\.html', href)
                    if vid_match:
                        vid = vid_match.group(1)
                        if vid in seen:
                            continue
                        seen.add(vid)
                        
                        title = m_title.group(1).strip() if m_title else ''
                        pic = m_img.group(1).strip() if m_img else f'https://vcover-vt-pic.puui.qpic.cn/vcover_vt_pic/0/{vid}/220'
                        
                        items.append({
                            "vod_id": vid,
                            "vod_name": title,
                            "vod_pic": pic,
                            "vod_remarks": '',
                        })
        except Exception as e:
            print(f'_parse_search_result error: {e}')
        return items

    def _parse_detail_html(self, html, vid):
        result = {"list": []}
        try:
            vod_name = ''
            m_name = re.search(r'<h1[^>]*class="video_title"[^>]*>([^<]+)</h1>', html)
            if not m_name:
                m_name = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
            if m_name:
                vod_name = m_name.group(1).strip()
            if not vod_name:
                m_name = re.search(r'<title>([^<]+)</title>', html)
                if m_name:
                    vod_name = m_name.group(1).strip().split('-')[0].strip()

            vod_pic = ''
            m_pic = re.search(r'property="og:image"\s+content="([^"]+)"', html)
            if m_pic:
                vod_pic = m_pic.group(1).strip()
            if not vod_pic:
                pic_url = f'https://vcover-vt-pic.puui.qpic.cn/vcover_vt_pic/0/{vid}/220'
                vod_pic = pic_url

            vod_director = ''
            vod_actor = ''
            vod_year = ''
            vod_area = ''
            vod_content = ''
            vod_remarks = ''

            info_pattern = r'<li[^>]*><span[^>]*>([^<]+)</span>\s*<span[^>]*>([^<]+)</span></li>'
            infos = re.findall(info_pattern, html)
            for key, val in infos:
                key = key.strip()
                val = val.strip()
                if key == '导演':
                    vod_director = val
                elif key == '主演':
                    vod_actor = val
                elif key == '年份':
                    vod_year = val
                elif key == '地区':
                    vod_area = val

            m_content = re.search(r'剧情简介[^>]*>[\s\S]*?(<p[^>]*>[\s\S]*?</p>)', html)
            if not m_content:
                m_content = re.search(r'<div[^>]*class="desc"[^>]*>[\s\S]*?(<p[^>]*>[\s\S]*?</p>)', html)
            if m_content:
                vod_content = re.sub(r'<[^>]+>', '', m_content.group(1)).strip()

            m_remarks = re.search(r'(更新至[^<]+|HD|4K|全集)', html)
            if m_remarks:
                vod_remarks = m_remarks.group(1).strip()

            play_urls = [f'在线播放${self.host}/x/cover/{vid}.html']

            vod = {
                "vod_id": vid,
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_director": vod_director,
                "vod_actor": vod_actor,
                "vod_year": vod_year,
                "vod_area": vod_area,
                "vod_remarks": vod_remarks,
                "vod_content": vod_content,
                "vod_play_from": '腾讯视频',
                "vod_play_url": '#'.join(play_urls),
            }
            result['list'].append(vod)
        except Exception as e:
            print(f'_parse_detail_html error: {e}')
        return result