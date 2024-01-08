import json
import requests
from xhs_utils.xhs_util import get_headers, get_params, js, check_cookies, get_note_data, handle_note_info, norm_str, check_and_create_path, save_comments_detail, save_note_detail, download_media, handle_note_comments_info

class OneNote:
    def __init__(self, cookies=None):
        if cookies is None:
            self.cookies = check_cookies()
        else:
            self.cookies = cookies
        self.feed_url = 'https://edith.xiaohongshu.com/api/sns/web/v1/feed'
        self.detail_url = 'https://www.xiaohongshu.com/explore/'
        self.comment_url = 'https://edith.xiaohongshu.com/api/sns/web/v2/comment/page?note_id='
        self.headers = get_headers()
        self.params = get_params()

    # 单个视频
    def get_one_note_info(self, url):
        note_id = url.split('/')[-1]
        data = get_note_data(note_id)
        data = json.dumps(data, separators=(',', ':'))
        ret = js.call('get_xs', '/api/sns/web/v1/feed', data, self.cookies['a1'])
        self.headers['x-s'], self.headers['x-t'] = ret['X-s'], str(ret['X-t'])
        response = requests.post(self.feed_url, headers=self.headers, cookies=self.cookies, data=data)
        res = response.json()
        try:
            data = res['data']['items'][0]
        except Exception as e:
            print(f'笔记 {note_id} 不允许查看')
            return
        note = handle_note_info(data)
        return note

    def get_one_note_comments_info(self, url):
        note_id = url.split('/')[-1]
        
        all_comments = []
        comment_url = self.comment_url + str(note_id) + '&cursor=&top_comment_id=&image_formats=jpg,webp,avif'
        
        while True:
            response = requests.get(comment_url, headers=self.headers, cookies=self.cookies)
            res = response.json()
            try:
                data = res['data']['comments']
            except Exception as e:
                print(f'not comments in note: {note_id}')
                return
            
            for comment in data:
                note = handle_note_comments_info(comment)
                all_comments.append(note)

            if 'cursor' in res['data']:
                comment_url = self.comment_url + str(note_id) + '&cursor=' + str(res['data']['cursor']) + '&top_comment_id=&image_formats=jpg,webp,avif'
            else:
                break
        return all_comments
    

    def save_one_note_info(self, url, need_cover=False, info='', dir_path='datas'):
        note = self.get_one_note_info(url)
        if note is None:
            return
        nickname =  norm_str(note.nickname) if note is not None and getattr(note, 'nickname') else '未知用户'
        user_id = note.user_id
        title = norm_str(note.title)
        if title.strip() == '':
            title = f'无标题'
        path = f'./{dir_path}/{nickname}_{user_id}/{title}_{note.note_id}'
        exist = check_and_create_path(path)
        if exist and not need_cover:
            print(f'用户: {nickname}, 标题: {title} 本地已存在，跳过保存')
            return note
        note_comments = self.get_one_note_comments_info(url)
        save_comments_detail(path, note_comments)
        save_note_detail(path, note)
        note_type = note.note_type
        if note_type == 'normal':
            for img_index, img in enumerate(note.image_list):
                img_url = img['info_list'][1]['url']
                download_media(path, f'image_{img_index}', img_url, 'image', f'第{img_index}张图片')

        # not downloading video
        # elif note_type == 'video':
        #     img_url = note.image_list[0]['info_list'][1]['url']
        #     download_media(path, 'cover', img_url, 'image', '视频封面')
        #     video_url = note.video_addr
        #     download_media(path, 'video', video_url, 'video')
        
        print(f'用户: {nickname}, {info}标题: {title} 笔记保存成功')
        print('===================================================================')
        return note
        # except:
        #     print(f'笔记 {url} 保存失败')
        #     return

    def main(self, url_list):
        for url in url_list:
            try:
                self.save_one_note_info(url)
            except:
                print(f'笔记 {url} 保存失败')
                continue

if __name__ == '__main__':
    one_note = OneNote()
    url_list = [
        'https://www.xiaohongshu.com/explore/64356527000000001303282b',
        # 'https://www.xiaohongshu.com/explore/63d625f8000000001d01042c',
        # 'https://www.xiaohongshu.com/explore/61ac8820000000002103a8aa',
        # 'https://www.xiaohongshu.com/explore/62d2699c000000001200f101',
        # 'https://www.xiaohongshu.com/explore/637f0938000000001f012d15',
    ]
    one_note.main(url_list)

