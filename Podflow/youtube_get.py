# Podflow/youtube_get.py
# coding: utf-8

import re
import os
import threading
from datetime import datetime
from Podflow.main import parse_app
from Podflow import gVar

from Podflow.basis import get_html_dict, http_client, vary_replace, list_merge_tidy


# 从YouTube播放列表获取更新模块
def get_youtube_html_playlists(
    youtube_key,
    youtube_value,
    guids=[""],
    direction_forward=True,
    update_size=20,
    youtube_content_ytid_original=[],
):
    idlist = []
    item = {}
    threads = []
    fail = []
    try:
        if direction_forward:
            videoid_start = guids[0]
        else:
            videoid_start = guids[-1]
    except IndexError:
        videoid_start = ""

    # 获取媒体相关信息模块
    def get_video_item(videoid, youtube_value):
        yt_Initial_Player_Response = get_html_dict(
            f"https://www.youtube.com/watch?v={videoid}",
            f"{youtube_value}|{videoid}",
            "ytInitialPlayerResponse",
        )
        if not yt_Initial_Player_Response:
            return None
        try:
            player_Microformat_Renderer = yt_Initial_Player_Response["microformat"][
                "playerMicroformatRenderer"
            ]
        except (KeyError, TypeError, IndexError, ValueError):
            player_Microformat_Renderer = {}
            fail.append(videoid)
        if player_Microformat_Renderer:
            try:
                item[videoid]["description"] = player_Microformat_Renderer[
                    "description"
                ]["simpleText"]
            except (KeyError, TypeError, IndexError, ValueError):
                item[videoid]["description"] = ""
            item[videoid]["pubDate"] = player_Microformat_Renderer["publishDate"]
            item[videoid]["image"] = player_Microformat_Renderer["thumbnail"][
                "thumbnails"
            ][0]["url"]
            try:
                fail.remove(videoid)
            except (KeyError, TypeError, IndexError, ValueError):
                pass
        else:
            return None

    yt_initial_data = get_html_dict(
        f"https://www.youtube.com/watch?v={videoid_start}&list=UULF{youtube_key[-22:]}",
        f"{youtube_value} HTML",
        "ytInitialData",
    )
    if not yt_initial_data:
        return None
    try:
        playlists = yt_initial_data["contents"]["twoColumnWatchNextResults"][
            "playlist"
        ]["playlist"]["contents"]
        main_title = yt_initial_data["contents"]["twoColumnWatchNextResults"][
            "playlist"
        ]["playlist"]["ownerName"]["simpleText"]
    except (KeyError, TypeError, IndexError, ValueError):
        return None
    if direction_forward or videoid_start == "":
        for playlist in playlists:
            videoid = playlist["playlistPanelVideoRenderer"]["videoId"]
            if (
                playlist["playlistPanelVideoRenderer"]["navigationEndpoint"][
                    "watchEndpoint"
                ]["index"]
                == update_size
            ):
                break
            if videoid not in guids:
                title = playlist["playlistPanelVideoRenderer"]["title"]["simpleText"]
                idlist.append(videoid)
                item[videoid] = {
                    "title": title,
                    "yt-dlp": True,
                }
                if videoid in youtube_content_ytid_original:
                    item[videoid]["yt-dlp"] = False
                    item_thread = threading.Thread(
                        target=get_video_item,
                        args=(
                            videoid,
                            youtube_value,
                        ),
                    )
                    item_thread.start()
                    threads.append(item_thread)
    else:
        reversed_playlists = []
        for playlist in reversed(playlists):
            videoid = playlist["playlistPanelVideoRenderer"]["videoId"]
            if videoid not in guids:
                reversed_playlists.append(playlist)
            else:
                break
        for playlist in reversed(reversed_playlists[-update_size:]):
            videoid = playlist["playlistPanelVideoRenderer"]["videoId"]
            title = playlist["playlistPanelVideoRenderer"]["title"]["simpleText"]
            idlist.append(videoid)
            item[videoid] = {
                "title": title,
                "yt-dlp": True,
            }
            if videoid in youtube_content_ytid_original:
                item[videoid]["yt-dlp"] = False
                item_thread = threading.Thread(
                    target=get_video_item,
                    args=(
                        videoid,
                        youtube_value,
                    ),
                )
                item_thread.start()
                threads.append(item_thread)
    for thread in threads:
        thread.join()
    for videoid in fail:
        get_video_item(videoid, youtube_value)
    if fail:
        if direction_forward or videoid_start == "":
            for videoid in fail:
                print(
                    f"{datetime.now().strftime('%H:%M:%S')}|{youtube_value}|{videoid} HTML无法更新, 将不获取"
                )
                idlist.remove(videoid)
                del item[videoid]
        else:
            print(
                f"{datetime.now().strftime('%H:%M:%S')}|{youtube_value} HTML有失败只更新部分"
            )
            index = len(idlist)
            for videoid in fail:
                if videoid in idlist:
                    index = min(idlist.index(videoid), index)
            idlist_fail = idlist[index:]
            idlist = idlist[:index]
            for videoid in idlist_fail:
                idlist.remove(videoid)
    return {"list": idlist, "item": item, "title": main_title}


# 获取YouTube Shorts视频列表
def get_youtube_shorts_id(youtube_key, youtube_value):
    videoIds = []
    url = f"https://www.youtube.com/channel/{youtube_key}/shorts"
    if data := get_html_dict(url, youtube_value, "ytInitialData"):
        try:
            items = data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][2][
                "tabRenderer"
            ]["content"]["richGridRenderer"]["contents"]
            for item in items:
                videoId = item["richItemRenderer"]["content"]["shortsLockupViewModel"][
                    "onTap"
                ]["innertubeCommand"]["reelWatchEndpoint"]["videoId"]
                videoIds.append(videoId)
        except (KeyError, TypeError, IndexError, ValueError):
            pass
    return videoIds


# 更新Youtube频道xml模块
def youtube_rss_update(
    youtube_key,
    youtube_value,
    pattern_youtube_varys,
    pattern_youtube404,
    pattern_youtube_error,
):
    channelid_youtube = gVar.channelid_youtube
    channelid_youtube_rss = gVar.channelid_youtube_rss
    channelid_youtube_ids_update = gVar.channelid_youtube_ids_update
    # 获取已下载媒体名称
    youtube_media = (
        ("m4a", "mp4")  # 根据 channelid_youtube 的媒体类型选择文件格式
        if channelid_youtube[youtube_value]["media"] == "m4a"
        else ("mp4",)  # 如果不是 m4a，则只选择 mp4
    )
    try:
        # 遍历指定目录下的所有文件，筛选出以 youtube_media 结尾的文件
        youtube_content_ytid_original = [
            os.path.splitext(file)[0]  # 获取文件名（不包括扩展名）
            for file in os.listdir(f"channel_audiovisual/{youtube_key}")  # 指定的目录
            if file.endswith(youtube_media)  # 筛选文件
        ]
    except Exception:
        # 如果发生异常，设置为空列表
        youtube_content_ytid_original = []
    try:
        # 获取原始XML中的内容
        original_item = gVar.xmls_original[youtube_key]
        guids = re.findall(r"(?<=<guid>).+(?=</guid>)", original_item)  # 查找所有guid
    except KeyError:
        # 如果没有找到对应的key，则guids为空
        guids = []
    # 构建 URL
    youtube_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={youtube_key}"
    youtube_response = http_client(youtube_url, youtube_value)  # 请求YouTube数据
    youtube_html_playlists = None
    youtube_channel_response = None
    if youtube_response is not None and re.search(
        pattern_youtube404, youtube_response.text, re.DOTALL
    ):
        youtube_url = f"https://www.youtube.com/channel/{youtube_key}"
        youtube_channel_response = http_client(youtube_url, f"{youtube_value} HTML")
        if youtube_channel_response is not None:
            pattern_youtube_error_mark = False
            for pattern_youtube_error_key in pattern_youtube_error:
                if pattern_youtube_error_key in youtube_channel_response.text:
                    pattern_youtube_error_mark = True
                    youtube_response = youtube_channel_response
                    break
            if not pattern_youtube_error_mark:
                # 检查响应是否有效，最多重试3次
                for _ in range(3):
                    if youtube_html_playlists := get_youtube_html_playlists(
                        youtube_key,
                        youtube_value,
                        [
                            elem
                            for elem in guids
                            if elem in youtube_content_ytid_original
                        ],  # 仅选择已下载的guids
                        True,
                        channelid_youtube[youtube_value]["update_size"],
                        youtube_content_ytid_original,
                    ):
                        break
        shorts_ytid = []
    elif youtube_response is not None and channelid_youtube[youtube_value]["NoShorts"]:
        shorts_ytid = get_youtube_shorts_id(youtube_key, youtube_value)
        gVar.video_id_failed += shorts_ytid  # 将Shorts视频添加到失败列表中
    else:
        shorts_ytid = []
    # 读取原Youtube频道xml文件并判断是否要更新
    try:
        with open(
            f"channel_id/{youtube_key}.txt",
            "r",
            encoding="utf-8",  # 以utf-8编码打开文件
        ) as file:
            youtube_content_original = file.read()  # 读取文件内容
            youtube_content_original_clean = vary_replace(
                pattern_youtube_varys, youtube_content_original
            )  # 清洗内容
    except FileNotFoundError:  # 如果文件不存在
        youtube_content_original = None
        youtube_content_original_clean = None
    if youtube_html_playlists is not None:  # 如果有新播放列表
        channelid_youtube_rss[youtube_key] = {
            "content": youtube_html_playlists,
            "type": "dict",
        }
        if youtube_html_playlists["item"]:
            channelid_youtube_ids_update[youtube_key] = youtube_value  # 更新标识
        youtube_content_ytid = youtube_html_playlists["list"]  # 获取视频ID列表
    else:
        if youtube_response is not None:
            # 如果没有新的播放列表，但响应有效
            channelid_youtube_rss[youtube_key] = {
                "content": youtube_response,
                "type": "html",
            }
            youtube_content = youtube_response.text  # 获取响应内容
            if not youtube_channel_response:
                youtube_content_clean = vary_replace(
                    pattern_youtube_varys, youtube_content
                )  # 清洗内容
                if (
                    youtube_content_clean != youtube_content_original_clean
                    and youtube_response
                ):  # 判断是否要更新
                    channelid_youtube_ids_update[youtube_key] = (
                        youtube_value  # 更新标识
                    )
        else:
            # 如果没有响应，使用原始内容
            channelid_youtube_rss[youtube_key] = {
                "content": youtube_content_original,
                "type": "text",
            }
            youtube_content = youtube_content_original
        try:
            # 从内容中提取视频ID
            youtube_content_ytid = re.findall(
                r"(?<=<id>yt:video:).{11}(?=</id>)", youtube_content
            )
        except TypeError:
            youtube_content_ytid = []  # 处理类型错误
        youtube_content_ytid = youtube_content_ytid[
            : channelid_youtube[youtube_value]["update_size"]  # 限制视频ID数量
        ]
    youtube_content_new = list_merge_tidy(youtube_content_ytid, guids)  # 合并并去重
    if youtube_content_ytid := [
        exclude
        for exclude in youtube_content_ytid
        if exclude not in youtube_content_ytid_original
        and exclude not in shorts_ytid  # 仅选择新视频ID(并且不是Shorts)
    ]:
        channelid_youtube_ids_update[youtube_key] = youtube_value  # 更新标识
        gVar.youtube_content_ytid_update[youtube_key] = (
            youtube_content_ytid  # 保存更新的视频ID
        )
    # 向后更新
    if channelid_youtube[youtube_value]["BackwardUpdate"] and guids:
        # 计算向后更新的数量
        backward_update_size = channelid_youtube[youtube_value]["last_size"] - len(
            youtube_content_new
        )
        if backward_update_size > 0:
            for _ in range(3):
                # 获取历史播放列表
                if youtube_html_backward_playlists := get_youtube_html_playlists(
                    youtube_key,
                    youtube_value,
                    guids,
                    False,
                    min(
                        backward_update_size,
                        channelid_youtube[youtube_value]["BackwardUpdate_size"],
                    ),
                    youtube_content_ytid_original,
                ):
                    break
            if youtube_html_backward_playlists:
                backward_list = youtube_html_backward_playlists[
                    "list"
                ]  # 获取向后更新的列表
                for guid in backward_list.copy():
                    if guid in youtube_content_new:
                        backward_list.remove(guid)  # 从列表中移除已更新的GUID
            if youtube_html_backward_playlists and backward_list:
                channelid_youtube_ids_update[youtube_key] = youtube_value  # 更新标识
                channelid_youtube_rss[youtube_key].update(
                    {"backward": youtube_html_backward_playlists}
                )  # 添加向后更新内容
                youtube_content_ytid_backward = []
                for guid in backward_list:
                    if guid not in youtube_content_ytid_original:
                        youtube_content_ytid_backward.append(guid)  # 收集未下载的GUID
                if youtube_content_ytid_backward:
                    gVar.youtube_content_ytid_backward_update[youtube_key] = (
                        youtube_content_ytid_backward  # 保存向后更新的ID
                    )