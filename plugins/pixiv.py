from nonebot import on_command, CommandSession, permission, helpers
from urllib.request import HTTPError
from pixivpy3 import *
import requests
import random
import re
import os


# 初始化参数
_USERNAME = 'Pixiv的用户名'
_PASSWORD = 'Pixiv的密码'
_USERID = '用于获取书签列表的PixivID，可以填一个收藏setu比较多的人的'
_CQP_IMG_URL = '酷Q存储图片的文件夹，例如.../data/image/，image后面一定要加个/'
_PROXIES = {'https': '你的代理地址'}
headers = {
    'Referer': 'https://app-api.pixiv.net',
    'User-Agent': 'User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36"'
    }


api = AppPixivAPI()

def init_api():
    global api
    api = AppPixivAPI(proxies=_PROXIES, verify=False)
    token = api.login(_USERNAME, _PASSWORD)
    api = AppPixivAPI()
    api.set_auth(token.response.access_token)
    # 这里使用了 pixivlite 提供的 api，不需要使用代理，如果要使用 app-api.pixiv.net 删除下面这行
    api.set_api_proxy('http://app-api.pixivlite.com')

init_api()


# 命令帮助
async def send_help(session: CommandSession):
    await session.send('=====CQ Pixiv Illusts=====\n' +
                 '命令帮助（如果 <参数> 缺省，默认发送 1 张图片）：\n' +
                 '/pixiv day <参数>\t获取 Pixiv 日榜 <参数> 张图片\n' +
                 '/pixiv week <参数>\t获取 Pixiv 周榜 <参数> 张图片\n' +
                 '/pixiv mon <参数>\t获取 Pixiv 月榜 <参数> 张图片\n' +
                 '/pixiv user <id> <参数>\t随机获取 PID=<id> 的 <参数> 张图片\n'
                 '/pixiv bookmark <参数>\t随机获取 <参数> 张收藏的图片\n' +
                 '如果是第一次下载图片可能会花费些许时间，请耐心等待。')


# 下载作品
def download_illusts(illusts):
    img_namelist = []
    for illust in illusts:
        # 因为多页作品只取第一页
        if illust.page_count > 1:
            img_url = illust.meta_pages[0].image_urls.original
        else:
            img_url = illust.meta_single_page.original_image_url
        img_name = img_url.split('/')[-1]
        img_namelist.append(img_name)

        if not os.path.exists(_CQP_IMG_URL + img_name):
            print('[CQ Pixiv DEBUG] Downloading ' + img_name + '(' + img_url + ')')
            try:
                # 此处获取的 Pixiv 原图地址并没有被墙，如果不需要使用代理可以直接删去下面的 proxies=_PROXIES
                img = requests.get(img_url, headers=headers, timeout=10, proxies=_PROXIES)
                with open(_CQP_IMG_URL + img_name, 'wb') as f:
                    f.write(img.content)
            except HTTPError as e:
                print(e.reason)
            print('[CQ Pixiv DEBUG] Download successfully')
        else:
            print('[CQ Pixiv DEBUG] ' + img_name + ' has existed')
    return img_namelist


# 获取作品列表
def get_illusts(session):
    ill_type = session.get('type')
    res = api.illust_ranking(mode='day')
    # 这里用了模糊匹配，带有
    if re.match('week', ill_type):
        res = api.illust_ranking(mode='week')
    if re.match('mon', ill_type):
        res = api.illust_ranking(mode='month')
    if re.match('bookmark', ill_type):
        res = api.user_bookmarks_illust(user_id=_USERID, restrict='public')
    if re.match('user', ill_type):
        res = api.user_illusts(int(session.state['id']))
    return res


# 插件主函数
@on_command('pixiv', permission=permission.EVERYBODY, only_to_me=False)
async def pixiv(session: CommandSession):
    ill_type = session.get('type')
    if len(ill_type) is 0:
        await send_help(session)
    else:
        try:
            illusts = get_illusts(session).illusts
        except:
            init_api()
            illusts = get_illusts(session).illusts

        img_namelist = download_illusts(illusts)
        message = ''

        if session.state['amount'] is None:
            rd_idx = random.randint(0, len(img_namelist)-1)
            message += '[' + illusts[rd_idx].title + ']\n(By ' + illusts[rd_idx].user.name + \
                       ', id=' + str(illusts[rd_idx].user.id) + ')\n[CQ:image,file=' + img_namelist[rd_idx] + ']'
        else:
            # Pixiv API 最多一次获取 30 张图片
            if int(session.state['amount']) > 30:
                message = '数量参数不能大于 30，请重新输入指令。'
            else:
                if int(session.state['amount']) > len(img_namelist):
                    session.state['amount'] = len(img_namelist)
                for idx in range(1, int(session.state['amount'])+1):
                    message += str(idx) + '.' + '[' + illusts[idx-1].title + ']\n(By ' + illusts[idx-1].user.name + \
                                ', id=' + str(illusts[idx-1].user.id) + ')\n[CQ:image,file=' +  img_namelist[idx-1] + ']\n'

        await session.send(message)


# 命令参数预处理
@pixiv.args_parser
async def _(session: CommandSession):
    args = session.current_arg_text.strip().split(' ')
    session.state['type'] = args[0]
    if len(args) > 1:
        if re.match('user', args[0]):
            session.state['id'] = args[1]
            session.state['amount'] = args[2]
        else:
            session.state['amount'] = args[1]
    else:
        session.state['amount'] = None
