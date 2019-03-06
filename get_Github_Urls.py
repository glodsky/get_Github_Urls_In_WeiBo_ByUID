# -*- coding: utf-8 -*-

import urllib.request
import json
import time
import datetime
import random
import os
import sqlite3
  
 
proxy_addr="175.155.138.182:1133"
DBNAME = ""
 
def use_proxy(url):
    global proxy_addr
    req=urllib.request.Request(url)
    req.add_header("User-Agent","Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0")
    proxy=urllib.request.ProxyHandler({'http':proxy_addr})
    opener=urllib.request.build_opener(proxy,urllib.request.HTTPHandler)
    urllib.request.install_opener(opener)
    data=urllib.request.urlopen(req).read().decode('utf-8','ignore')
    return data
 
def get_containerid(url):
    data=use_proxy(url)
    content=json.loads(data).get('data')
    ok = json.loads(data).get('ok')
    if ok == 1:
        tabs = content.get('tabsInfo').get('tabs')
        for data in tabs:
            if(data.get('tab_type')=='weibo'):
                containerid=data.get('containerid')
                return containerid        
        return 0
    else:
        print("error At : %s\n data:%s"%(url,data))
        return 0

#获取微博大V账号的用户基本信息，如：微博昵称、微博地址、微博头像、关注人数、粉丝数、性别、等级等
def get_userInfo(id):
    url='https://m.weibo.cn/api/container/getIndex?type=uid&value='+id
    data=use_proxy(url)
    content=json.loads(data).get('data')
    profile_image_url=content.get('userInfo').get('profile_image_url')
    description=content.get('userInfo').get('description')
    profile_url=content.get('userInfo').get('profile_url')
    verified=content.get('userInfo').get('verified')
    guanzhu=content.get('userInfo').get('follow_count')
    name=content.get('userInfo').get('screen_name')
    fensi=content.get('userInfo').get('followers_count')
    gender=content.get('userInfo').get('gender')
    urank=content.get('userInfo').get('urank')
    print("微博昵称："+name+"\n"+"微博主页地址："+profile_url+"\n"+"微博头像地址："+profile_image_url+"\n"+"是否认证："+str(verified)+"\n"+"微博说明："+description+"\n"+"关注人数："+str(guanzhu)+"\n"+"粉丝数："+str(fensi)+"\n"+"性别："+gender+"\n"+"微博等级："+str(urank)+"\n")


def get_detailContent(detail_url):
    try:
        data=use_proxy(detail_url) 
        if not data.find('微博正文 - 微博HTML5版'):
            return '[该条已经被和谐咯] '
        content = json.loads(data).get('data')
        longTextContent=content.get('longTextContent')
        return longTextContent
    except Exception as e:
        print(e)
        return '[该条已经被和谐咯]' 
       
 
def format_createdDate(targetDate):
    create_at   = targetDate
    if create_at.find("小时前") != -1 : # 最近二天 格式
        before_hours = int( create_at.split("小")[0] )
        create_at = (datetime.datetime.now()+datetime.timedelta(hours= -before_hours )).strftime("%Y-%m-%d")
    elif create_at.find("分钟前")!= -1:
        create_at = datetime.datetime.now().strftime("%Y-%m-%d")
    elif create_at.find("昨天") != -1 :
        create_at = (datetime.datetime.now()+datetime.timedelta(days= -1 )).strftime("%Y-%m-%d")
    else:
        which = create_at.split('-')
        if(len(which) == 2 ):      # 今年的 都是 '11-09' 之类的格式         
            year = time.strftime('%Y',time.localtime(time.time()))
            create_at = "%s-%s"%(year,create_at)
        elif(len(which)== 3 ):    # 去年的  都是 '2017-11-09' 之类的格式
            pass
        else:
            pass
    return create_at
    

def get_weibo(uid,file,keyword=[]):
    global DBNAME
    count = 0
    i=1
    local_json_data = []
    
    while True:
        url='https://m.weibo.cn/api/container/getIndex?type=uid&value='+uid
        containerid = get_containerid(url)
        if containerid != 0:
            weibo_url='https://m.weibo.cn/api/container/getIndex?type=uid&value='+uid+'&containerid='+ str(containerid) +'&page='+str(i)
        else:
            break
        
        try:
            pdata=json.loads(use_proxy(weibo_url))            
            ok = pdata.get('ok')
            msg =pdata.get('msg')
            if ok == 0:
                print("msg: %s\n"%msg)
                break
            
            content = pdata.get('data')
            cards=content.get('cards')
            cards_len = len(cards)
            if(cards_len>0):
                for j in range(cards_len):
                    print("-----正在爬取第"+str(i)+"页，第"+str(j+1)+"条微博------")
                    card_type=cards[j].get('card_type')
                    if(card_type==9):
                        mblog=cards[j].get('mblog')
                        attitudes_count=mblog.get('attitudes_count')
                        comments_count=mblog.get('comments_count')
                        created_at=mblog.get('created_at')
                        created_at= format_createdDate(created_at)
                        reposts_count=mblog.get('reposts_count')
                        scheme=cards[j].get('scheme')
                        isLongText = bool(mblog.get('isLongText'))
                        if (not isLongText):
                            text=mblog.get('text')
                        else:
                            idstr = mblog.get('idstr')
                            detail_url = 'https://m.weibo.cn/statuses/extend?id='+str(idstr)
                            text = get_detailContent(detail_url)
                        if len(text)<=0:
                            continue
                        else:
                            #过滤出感兴趣的部分 并保存到文件中
                            if keyword != []:
                                i_s = text.find(keyword[0])
                                i_e = 0
                                if i_s > 0 :
                                    i_e = text.find(keyword[1])
                                    filters_result = text[i_s:i_e]
                                    new_content = "https://" + filters_result.replace("%2F","/") + "\n"
                                    if len(new_content) > len("https://"):
                                        with open(file,'a') as fn:
                                            fn.write(new_content)
                                            fn.close()
                            
                        count = count + 1                        
         
 
                            
            i+=1
            if(i% 3 == 0 ):
                sleeptimes = random.randint(1,5)
                print("Sleep times at %s  Senconds"%sleeptimes)
                time.sleep(sleeptimes)
        except Exception as e:
            print(e)            
 
            
    print('>>>>>>>>>>>>>>>>>>>')
    print('共计：%s'%count)

def main():
    global DBNAME 
    id_list = ['5182526927'] #
    keyword = ["github.com",'" class=""><span class']  # 过滤出 github项目
    for uid in id_list:
        DBNAME = "%s_%s.db"%("data",uid)
        create_table(DBNAME) 
        file="%s_%s_%s.txt"%(keyword[0] , uid , datetime.datetime.now().strftime('%Y%m%d'))
        get_userInfo(uid)
        get_weibo(uid,file,keyword)
        
if __name__=="__main__":
    main()


    

