# Podflow/Netscape.py
# coding: utf-8

from datetime import datetime
from Podflow.basis import file_save
from http.cookiejar import LoadError
from http.cookiejar import MozillaCookieJar

# 生成Netscape_HTTP_Cookie模块
def bulid_Netscape_HTTP_Cookie(file_name, cookie={}):
    if "bilibili" in file_name:
        cookie_jar = f'''# Netscape HTTP Cookie File
# This file is generated by yt-dlp.  Do not edit.

.bilibili.com	TRUE	/	FALSE	0	SESSDATA	{cookie.get("SESSDATA", "")}
.bilibili.com	TRUE	/	FALSE	0	bili_jct	{cookie.get("bili_jct", "")}
.bilibili.com	TRUE	/	FALSE	0	DedeUserID	{cookie.get("DedeUserID", "")}
.bilibili.com	TRUE	/	FALSE	0	DedeUserID__ckMd5	{cookie.get("DedeUserID__ckMd5", "")}
.bilibili.com	TRUE	/	FALSE	0	sid	{cookie.get("sid", "")}
.bilibili.com	TRUE	/	FALSE	0	buvid3	{cookie.get("buvid3", "")}
.bilibili.com	TRUE	/	FALSE	0	b_nut	{cookie.get("b_nut", "")}'''
    elif "youtube" in file_name:
        cookie_jar = f'''# Netscape HTTP Cookie File
# This file is generated by yt-dlp.  Do not edit.

.youtube.com	TRUE	/	TRUE	0	__Secure-3PSID	{cookie.get("__Secure-3PSID", "")}
.youtube.com	TRUE	/	TRUE	0	__Secure-1PSIDTS	{cookie.get("__Secure-1PSIDTS", "")}
.youtube.com	TRUE	/	TRUE	0	SAPISID	{cookie.get("SAPISID", "")}
.youtube.com	TRUE	/	TRUE	0	__Secure-1PSIDCC	{cookie.get("__Secure-1PSIDCC", "")}
.youtube.com	TRUE	/	TRUE	0	SSID	{cookie.get("SSID", "")}
.youtube.com	TRUE	/	TRUE	0	__Secure-1PAPISID	{cookie.get("__Secure-1PAPISID", "")}
.youtube.com	TRUE	/	TRUE	0	__Secure-1PSID	{cookie.get("__Secure-1PSID", "")}
.youtube.com	TRUE	/	TRUE	0	__Secure-3PAPISID	{cookie.get("__Secure-3PAPISID", "")}
.youtube.com	TRUE	/	TRUE	0	__Secure-3PSIDCC	{cookie.get("__Secure-3PSIDCC", "")}
.youtube.com	TRUE	/	TRUE	0	__Secure-3PSIDTS	{cookie.get("__Secure-3PSIDTS", "")}
.youtube.com	TRUE	/	TRUE	0	LOGIN_INFO	{cookie.get("LOGIN_INFO", "")}
.youtube.com	TRUE	/	FALSE	0	PREF	{cookie.get("PREF", "")}
.youtube.com	TRUE	/	TRUE	0	YSC	{cookie.get("YSC", "")}
.youtube.com	TRUE	/	TRUE	0	VISITOR_INFO1_LIVE	{cookie.get("VISITOR_INFO1_LIVE", "")}
.youtube.com	TRUE	/	TRUE	0	VISITOR_PRIVACY_METADATA	{cookie.get("VISITOR_PRIVACY_METADATA", "")}'''
    else:
        cookie_jar = '''# Netscape HTTP Cookie File
# This file is generated by yt-dlp.  Do not edit.'''
    file_save(cookie_jar, f"{file_name}.txt", "channel_data")

# 将Netscape转Dict模块
def get_cookie_dict(file):
    parts = file.split('/')
    try:
        # 加载Netscape格式的cookie文件
        cookie_jar = MozillaCookieJar(file)
        cookie_jar.load(ignore_discard=True)
        # 将cookie转换为字典
        cookie_dict = {}
        for cookie in cookie_jar:
            cookie_dict[cookie.name] = cookie.value
        return cookie_dict
    except FileNotFoundError :
        print(f"{datetime.now().strftime('%H:%M:%S')}|{parts[-1]}文件不存在")
        return None
    except LoadError:
        print(f"{datetime.now().strftime('%H:%M:%S')}|{parts[-1]}文件错误")
        return None