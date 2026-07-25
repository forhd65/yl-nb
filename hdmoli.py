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
        self.host = "https://www.hdmoli.me"
        self.name = "HDmoli"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': f'{self.host}/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

    def getName(self):
        return "HDmoli影视"

    def init(self, extend):
        pass

    def homeContent(self, filter):
        classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "剧集"},
            {"type_id": "4", "type_name": "动画"},
        ]

        filter_dict = self._build_filters()

        try:
            res = self.session.get(self.host, headers=self.headers, timeout=15)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            videos = self._parse_list(soup)
            return {
                'class': classes,
                'filters': filter_dict,
                'list': videos
            }
        except Exception as e:
            print(f'[{self.name}] 错误: 首页爬取失败 - {e}')
            return {'class': classes, 'filters': filter_dict, 'list': []}

    def _build_filters(self):
        filter_dict = {}

        types_map = {
            '1': ['动作', '喜剧', '爱情', '科幻', '恐怖', '剧情', '战争'],
            '2': ['国产剧', '港台剧', '日韩剧', '海外剧'],
            '4': ['国产动漫', '日韩动漫', '港台动漫', '欧美动漫'],
        }

        class_list = [
            '爱情', '奇幻', '喜剧', '动作', '科幻', '武侠', '冒险', '惊悚',
            '恐怖', '犯罪', '动画', '剧情', '悬疑', '战争', '家庭', '运动',
            '灾难', '传记', '历史', '短片', '西部', '纪录片', '歌舞', '古装',
            '音乐', '剧情片', '儿童', '真人秀'
        ]

        areas = [
            '大陆', '香港', '台湾', '日本', '美国', '英国', '韩国', '西班牙',
            '泰国', '法国', '丹麦', '智利', '土耳其', '德国', '瑞典', '印度',
            '新西兰', '爱尔兰', '比利时', '希腊', '澳大利亚', '芬兰', '巴西',
            '俄罗斯', '加拿大', '意大利', '其它'
        ]

        languages = [
            '国语', '粤语', '日语', '英语', '韩语', '夏威夷语', '法语', '德语',
            '丹麦语', '西班牙语', '耳其语', '印地语', '芬兰语', '四川乐山话',
            '俄语', '意大利语', '汉语普通话', '闽南语', '其它'
        ]

        years = [str(y) for y in range(2026, 2010, -1)]

        letters = [chr(ord('A') + i) for i in range(26)] + ['0-9']

        orders = [
            {'n': '时间', 'v': 'time'},
            {'n': '人气', 'v': 'hits'},
            {'n': '评分', 'v': 'score'}
        ]

        for tid in ['1', '2', '4']:
            type_list = [{'n': '全部', 'v': tid}] + [{'n': t, 'v': t} for t in types_map.get(tid, [])]
            class_type_list = [{'n': '全部', 'v': ''}] + [{'n': c, 'v': c} for c in class_list]
            area_list = [{'n': '全部', 'v': ''}] + [{'n': a, 'v': a} for a in areas]
            lang_list = [{'n': '全部', 'v': ''}] + [{'n': l, 'v': l} for l in languages]
            year_list = [{'n': '全部', 'v': ''}] + [{'n': y, 'v': y} for y in years]
            letter_list = [{'n': '全部', 'v': ''}] + [{'n': l, 'v': l} for l in letters]

            filter_dict[tid] = [
                {'key': 'cateId', 'name': '类型', 'value': type_list},
                {'key': 'class', 'name': '剧情', 'value': class_type_list},
                {'key': 'area', 'name': '地区', 'value': area_list},
                {'key': 'lang', 'name': '语言', 'value': lang_list},
                {'key': 'year', 'name': '年份', 'value': year_list},
                {'key': 'letter', 'name': '字母', 'value': letter_list},
                {'key': 'by', 'name': '排序', 'value': orders},
            ]
        return filter_dict

    def categoryContent(self, tid, pg, filter, extend):
        try:
            pg = int(pg) if pg else 1
            cateId = extend.get('cateId', tid)
            area = extend.get('area', '')
            by = extend.get('by', '')
            class_type = extend.get('class', '')
            lang = extend.get('lang', '')
            letter = extend.get('letter', '')
            year = extend.get('year', '')

            url = f'{self.host}/show/{cateId}-{area}-{by}-{class_type}-{lang}-{letter}---{pg}---{year}.html'

            res = self.session.get(url, headers=self.headers, timeout=15)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            videos = self._parse_list(soup)

            return {
                'page': pg,
                'pagecount': 999,
                'limit': 30,
                'total': 30 * 999,
                'list': videos
            }
        except Exception as e:
            print(f'[{self.name}] 错误: 分类爬取失败 - {e}')
            return {'page': int(pg) if pg else 1, 'pagecount': 0, 'limit': 30, 'total': 0, 'list': []}

    def _parse_list(self, soup):
        videos = []
        seen = set()

        items = soup.select('.myui-vodlist__thumb')
        if not items:
            items = soup.select('.lazyload')

        for item in items:
            try:
                href = item.get('href', '')
                m = re.search(r'/movie/index(\d+)\.html', href)
                if not m:
                    continue

                vod_id = m.group(1)
                if vod_id in seen:
                    continue
                seen.add(vod_id)

                vod_pic = ''
                for attr in ['data-original', 'data-src', 'src']:
                    vod_pic = item.get(attr, '')
                    if vod_pic and vod_pic.startswith('http'):
                        break

                vod_name = item.get('title', '')
                if not vod_name:
                    img = item.find('img')
                    if img:
                        vod_name = img.get('alt', '')
                if not vod_name:
                    vod_name = item.get_text(strip=True)

                remark = ''
                pic_text = item.select_one('.pic-text')
                if pic_text:
                    remark = pic_text.get_text(strip=True)
                pic_tag = item.select_one('.pic-tag')
                if pic_tag:
                    tag_text = pic_tag.get_text(strip=True)
                    if remark:
                        remark = f'{remark}|{tag_text}'
                    else:
                        remark = tag_text

                videos.append({
                    'vod_id': vod_id,
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
                    'vod_remarks': remark,
                })
            except Exception as e:
                continue

        return videos

    def detailContent(self, ids):
        try:
            vod_id = ids
            url = f'{self.host}/movie/index{vod_id}.html'
            res = self.session.get(url, headers=self.headers, timeout=15)
            res.encoding = 'utf-8'
            text = res.text
            soup = BeautifulSoup(text, 'html.parser')

            vod = {
                'vod_id': vod_id,
                'vod_name': '',
                'vod_pic': '',
                'vod_director': '',
                'vod_actor': '',
                'vod_content': '',
                'vod_remarks': '',
                'vod_year': '',
                'vod_area': '',
                'vod_lang': '',
                'vod_class': '',
                'vod_play_from': '',
                'vod_play_url': '',
            }

            title_el = soup.select_one('h1')
            if title_el:
                vod['vod_name'] = title_el.get_text(strip=True)

            img_el = soup.select_one('.myui-vodlist__thumb img, .myui-content__thumb img')
            if img_el:
                for attr in ['data-original', 'data-src', 'src']:
                    pic = img_el.get(attr, '')
                    if pic and pic.startswith('http'):
                        vod['vod_pic'] = pic
                        break

            info_el = soup.select_one('.myui-content__detail')
            if info_el:
                info_text = info_el.get_text()

                m = re.search(r'导演[：:]\s*([^\n]+)', info_text)
                if m:
                    director = m.group(1).strip()
                    director = re.sub(r'^[/、,，]+|[/、,，]+$', '', director)
                    vod['vod_director'] = director

                m = re.search(r'演员[：:]\s*([^\n]+)', info_text)
                if m:
                    actor = m.group(1).strip()
                    actor = re.sub(r'^[/、,，]+|[/、,，]+$', '', actor)
                    vod['vod_actor'] = actor

                m = re.search(r'分类[：:]\s*([^\n]+)', info_text)
                if m:
                    vod['vod_class'] = m.group(1).strip()

                m = re.search(r'地区[：:]\s*([^\n]+)', info_text)
                if m:
                    vod['vod_area'] = m.group(1).strip()

                m = re.search(r'语言[：:]\s*([^\n]+)', info_text)
                if m:
                    vod['vod_lang'] = m.group(1).strip()

                m = re.search(r'年份[：:]\s*([^\n]+)', info_text)
                if m:
                    vod['vod_year'] = m.group(1).strip()

                m = re.search(r'更新[：:]\s*([^\n]+)', info_text)
                if m:
                    vod['vod_remarks'] = m.group(1).strip()

            content_el = soup.select_one('.col-pd, .vod_content, .detail-content')
            if content_el:
                content = content_el.get_text(strip=True)
                if content.startswith('简介：') or content.startswith('剧情介绍：'):
                    content = content.split('：', 1)[1] if '：' in content else content
                vod['vod_content'] = content

            play_from_list = []
            play_url_list = []

            tab_items = soup.select('.nav-tabs li a')
            sort_lists = soup.select('.sort-list')

            if tab_items and sort_lists:
                for idx, tab in enumerate(tab_items):
                    source_name = tab.get_text(strip=True)
                    source_name = re.sub(r'\d+$', '', source_name)
                    if not source_name:
                        source_name = f'线路{idx+1}'
                    play_from_list.append(source_name)

                    urls = []
                    if idx < len(sort_lists):
                        sl = sort_lists[idx]
                        links = sl.find_all('a', href=re.compile(r'/play/\d+-\d+-\d+\.html'))
                        for a in links:
                            ep_title = a.get_text(strip=True)
                            href = a.get('href', '')
                            ep_m = re.search(r'/play/(\d+-\d+-\d+)\.html', href)
                            if ep_m:
                                urls.append(f'{ep_title}${ep_m.group(1)}')

                    play_url_list.append('#'.join(urls))
            else:
                all_links = soup.find_all('a', href=re.compile(r'/play/(\d+)-(\d+)-(\d+)\.html'))
                if all_links:
                    play_lines = {}
                    for a in all_links:
                        href = a.get('href', '')
                        ep_m = re.search(r'/play/(\d+)-(\d+)-(\d+)\.html', href)
                        if ep_m:
                            sid = ep_m.group(2)
                            if sid not in play_lines:
                                play_lines[sid] = []
                            ep_title = a.get_text(strip=True)
                            ep_id = f'{ep_m.group(1)}-{sid}-{ep_m.group(3)}'
                            play_lines[sid].append(f'{ep_title}${ep_id}')

                    for sid, urls in sorted(play_lines.items(), key=lambda x: int(x[0])):
                        play_from_list.append(f'线路{sid}')
                        play_url_list.append('#'.join(urls))

            vod['vod_play_from'] = '$$$'.join(play_from_list)
            vod['vod_play_url'] = '$$$'.join(play_url_list)

            return {'list': [vod]}
        except Exception as e:
            print(f'[{self.name}] 错误: 详情爬取失败 - {e}')
            return {'list': []}

    def _extract_json(self, text, key):
        idx = text.find(key)
        if idx < 0:
            return None
        start = text.find('{', idx)
        if start < 0:
            return None
        depth = 0
        in_str = False
        escape = False
        for i in range(start, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == '\\':
                escape = True
                continue
            if c == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        return None

    def playerContent(self, flag, id, vipFlags):
        try:
            m = re.match(r'(\d+)-(\d+)-(\d+)', id)
            if m:
                vid = m.group(1)
                sid = m.group(2)
                nid = m.group(3)
                play_url = f'{self.host}/play/{vid}-{sid}-{nid}.html'
            else:
                play_url = f'{self.host}/play/{id}.html'

            headers = dict(self.headers)
            headers['Referer'] = f'{self.host}/'
            res = self.session.get(play_url, headers=headers, timeout=15)
            res.encoding = 'utf-8'
            text = res.text

            json_str = self._extract_json(text, 'player_aaaa')
            if json_str:
                player_data = json.loads(json_str)
                real_url = player_data.get('url', '')
                encrypt = player_data.get('encrypt', 0)
                from_type = player_data.get('from', '')

                if real_url:
                    play_headers = {
                        'User-Agent': self.headers['User-Agent'],
                        'Referer': f'{self.host}/',
                    }

                    if '网盘' in flag or from_type in ['quark', 'baidu', 'uc']:
                        return {
                            'parse': 1,
                            'url': real_url,
                            'header': play_headers,
                        }
                    else:
                        return {
                            'parse': 0,
                            'url': real_url,
                            'header': play_headers,
                        }

            return {'parse': 0, 'url': ''}
        except Exception as e:
            print(f'[{self.name}] 错误: 播放解析失败 - {e}')
            return {'parse': 0, 'url': ''}

    def searchContent(self, key, quick, pg):
        try:
            pg = int(pg) if pg else 1
            url = f'{self.host}/search/{urllib.parse.quote(key)}----------{pg}---.html'
            res = self.session.get(url, headers=self.headers, timeout=20)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            videos = self._parse_list(soup)
            return {'list': videos}
        except Exception as e:
            print(f'[{self.name}] 错误: 搜索失败 - {e}')
            return {'list': []}

    def isVideoFormat(self, url):
        pass

    def proxyContent(self, url):
        pass

    def localProxy(self, param):
        pass


if __name__ == '__main__':
    s = Spider()
    print('Name:', s.getName())

    print('\n=== 首页测试 ===')
    result = s.homeContent(False)
    print(f'分类数: {len(result.get("class", []))}')
    print(f'列表数: {len(result.get("list", []))}')
    if result.get('list'):
        print(f'第一个: {result["list"][0]}')

    print('\n=== 分类测试 ===')
    cat = s.categoryContent('1', '1', False, {})
    print(f'分类列表数: {len(cat.get("list", []))}')
    if cat.get('list'):
        print(f'第一个: {cat["list"][0]}')

    print('\n=== 搜索测试 ===')
    search = s.searchContent('剑', False, 1)
    print(f'搜索结果数: {len(search.get("list", []))}')
    if search.get('list'):
        print(f'第一个: {search["list"][0]}')

    print('\n=== 详情测试 ===')
    if result.get('list'):
        vid = result['list'][0]['vod_id']
        detail = s.detailContent(vid)
        if detail.get('list'):
            v = detail['list'][0]
            print(f'标题: {v["vod_name"]}')
            print(f'封面: {v["vod_pic"]}')
            print(f'导演: {v["vod_director"]}')
            print(f'主演: {v["vod_actor"]}')
            print(f'状态: {v["vod_remarks"]}')
            print(f'线路数: {len(v["vod_play_from"].split("$$$")) if v["vod_play_from"] else 0}')
            print(f'线路: {v["vod_play_from"]}')
            urls_preview = v['vod_play_url'].split("$$$")
            for i, u in enumerate(urls_preview):
                print(f'  线路{i}前3个: {u.split("#")[:3]}')

            print('\n=== 播放测试 ===')
            if v['vod_play_url']:
                first_line = v['vod_play_url'].split('$$$')[0]
                first_ep = first_line.split('#')[0]
                ep_id = first_ep.split('$')[1] if '$' in first_ep else ''
                flag = v['vod_play_from'].split('$$$')[0]
                print(f'测试线路: {flag}, id: {ep_id}')
                player = s.playerContent(flag, ep_id, [])
                print(f'播放结果: {player}')
