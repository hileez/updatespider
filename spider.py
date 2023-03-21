# -*- coding:utf-8 -*-
# @Time : 2021/10/19 23:57
# @Author: ZhenLi
# @File : spider.py

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.scrolledtext as ScrolledText
from tkinter import messagebox
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv,time,datetime,re,webbrowser,json,sys
import threading,sqlite3
# import winsound #windows音频播放

def spider(rule):
    """
    网络爬虫
    :param rule:爬取规则
    :return:爬取结果（二维数组）
    """
    print('\r\nSpider request:' + rule['name'] + '---------------------------------|')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'
    }
    data = []
    for link in rule['urls']:
        urls = create_url(link)
        print('Request Urls:')
        print(urls)
        for url_data in urls:
            if rule['type'] == 'get':
                response = requests.get(url_data['url'], headers=headers)
            elif rule['type'] == 'post':
                jobdata = json.loads(url_data['data'])
                response = requests.post(url_data['url'], jobdata, headers=headers)
            response.encoding = rule['encoding']

            # # 源码保存为html文件
            # f = open(f"html\{rule['name']}.html", 'w', encoding=rule['encoding'])
            # f.write(response.text)

            # 请求错误结束闭关提示
            if response.status_code != 200:
                print('\r\nRequest Error ' + response.status_code + '\r\n')
                continue

            if rule['response'] == 'json':
                jobject = json.loads(clear_json(clear_str(response.text)))
                # 根据path路径获取需要循环的项
                keyarr = rule['path'].replace(' ', '').split('>')
                for key in keyarr:
                    jobject = jobject[key]
                # 循环提取数组数据
                for row in jobject:
                    parse_data = {}
                    for parse in rule['parse']:
                        if 'key_from' in parse.keys() and parse['key_from'] != '':
                            val = row[parse['key_from']]
                        # 类型数据处理
                        val = data_format(parse['data_type'], val, url_data['url'])
                        # 替换模板标签
                        val = parse['value'].replace('{$val}', str(val))
                        parse_data[parse['key']] = val
                    print(parse_data)
                    data.append(parse_data)

            if rule['response'] == 'html':
                soup = BeautifulSoup(response.text, 'lxml')
                parse_data = []
                for parse in rule['parse']:
                    if parse['selector'] == '':
                        # 无选择器，直接根据类型转换数据
                        val = data_format(parse['data_type'], parse['value'], url_data['url'])
                        for row in parse_data:
                            row[parse['key']] = val
                        continue
                    sel_data = soup.select(parse['selector'])

                    if len(sel_data) == 0:
                        print('\r\nSelector Error\r\n')
                        break
                    for index, dom in enumerate(sel_data):
                        # 提取目标数据
                        if len(parse_data) < len(sel_data):
                            parse_data.append({})
                        if 'attr' in parse.keys():
                            val = dom[parse['attr']]
                        else:
                            dom = BeautifulSoup(clear_str(str(dom)), 'lxml')
                            val = dom.string
                        # 类型数据处理
                        val = data_format(parse['data_type'], val, url_data['url'])
                        # 替换模板标签
                        val = parse['value'].replace('{$val}', str(val))
                        # 添加到临时字典
                        parse_data[index][parse['key']] = val
                # 添加到主字典
                for list in parse_data:
                    data.append(list)
                print('Request Result:')
                print(parse_data)
    return data


def create_url(link):
    """
    根据爬虫规则生成URL
    :param link: url规则
    :return: url数组
    """
    urls = []
    for lk_index, link_key in enumerate(link.keys()):
        # 正则匹配字符串替换的字符
        for_data = re.findall(r'\[(.*?)\]', link[link_key])
        if for_data:
            for int_arr in for_data:
                for_int = int_arr.split(',')
                if len(for_int) == 3:
                    for number in for_int:
                        if number.isdigit() == False:
                            break
                    else:
                        # 根据参数循环生成url
                        for i in range(int(for_int[0]), int(for_int[1]), int(for_int[2])):
                            index = int(i / int(for_int[2]))
                            if len(urls) > index:
                                # urls数组中存在则修改
                                if link_key in urls[index].keys():
                                    urls[index][link_key] = urls[index][link_key].replace('[' + int_arr + ']', str(i))
                                else:
                                    urls[index][link_key] = link[link_key].replace('[' + int_arr + ']', str(i))
                            else:
                                # urls中不存在则添加
                                if lk_index == 0:
                                    # 首项添加
                                    urls.append({link_key: link[link_key].replace('[' + int_arr + ']', str(i))})
                                else:
                                    # 首项无生成参数[int,int,int],则后面项目生成添加到urls，需补齐前项
                                    arr = {}
                                    for l_index, l_key in enumerate(link.keys()):
                                        if l_index < lk_index:
                                            arr[l_key] = link[l_key]
                                        else:
                                            break
                                    arr[link_key] = link[link_key].replace('[' + int_arr + ']', str(i))
                                    urls.append(arr)
    if len(urls) == 0:
        urls.append(link)
    return urls


def clear_str(str):
    """
    字符串删除多余字符
    :param str:
    :return:
    """
    str = str.replace('\r\n', '')
    str = str.replace('\n', '')
    str = str.replace(' ', '')
    str = str.replace('\t', '')
    str = str.strip('(').strip(')')
    str = str.strip('（').strip('）')
    # html存在br换行，BeautifulSoup无法获取数据
    str = str.replace('<br/>', '')
    str = str.replace('</br>', '')
    str = str.replace('<br>', '')
    return str


def clear_json(jsonstr):
    """
    清理json字符串的{}两侧多余字符，便于将字符串转json数组
    :param jsonstr:json字符串
    :return:清理结果
    """
    if jsonstr.find('{') >= 0 and jsonstr.rfind('}') >= 0:
        jsonstr = jsonstr[jsonstr.find('{'):len(jsonstr)]
        jsonstr = jsonstr[0:jsonstr.rfind('}') + 1]
    return jsonstr


def data_format(type, val='', url=''):
    """
    # 数据结果根据类型转换为对应数据
    比如时间戳根据datatime类型转换为日期
    :param type: 目标数据类型
    :param val: 待转换数据
    :param url: 用于相对地址转绝对地址的源URL
    :return: 转换结果
    """
    # 转换为字符类型
    val = str(val)
    # 类型数据处理
    if type == 'url' and url != '':
        val = urljoin(url, val)
    elif type == 'string':
        val = clear_str(val)
    elif type == 'datetime':
        val = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(val)))
    elif type == 'now':
        val = datetime.datetime.now().strftime('%Y-%m-%d %T')
    return val


def csv_save(filepath, data):
    """
    数据写入CSV文件
    :param filepath:文件路径
    :param data:待写入数据
    """
    fw = open(filepath, 'a+', newline='', encoding='utf-8')
    csv_writer = csv.writer(fw)
    for row in data:
        insert_data = []
        for val in row.values():
            insert_data.append(val)
        csv_writer.writerow(insert_data)
    fw.close()


class Splite():
    """
    sqlite数据库操作类
    """
    def __init__(self, filename):
        self.conn = sqlite3.connect(filename)
        self.db = self.conn.cursor()
        # 没有文件和数据表则创建
        try:
            self.db.execute('''CREATE TABLE articles
                   (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                   name CHAR(50),
                   url CHAR(225) NOT NULL,
                   title CHAR(225) NOT NULL,
                   update_time CHAR(50) NOT NULL,
                   add_time INT NOT NULL);''')
        except:
            pass

    def query(self, sql):
        """
        查询
        :param sql:
        :return:
        """
        res = self.db.execute(sql)
        self.conn.commit()
        return res

    def get(self, sql):
        """
        查询获取数据（多行）
        :param sql:
        :return:
        """
        cursor = self.db.execute(sql)
        res = []
        for row in cursor:
            res.append(row)
        return res

    def get_one(self, sql):
        """
        查询返回单数据
        :param sql:
        :return:
        """
        cursor = self.db.execute(sql)
        res = []
        for row in cursor:
            res.append(row)
        return res[0][0]

    def close(self):
        """
        关闭连接
        """
        self.conn.close()


def insert_db(filename, data, rule):
    """
    数据插入数据库，根据rule规则查重，存在则不插入数据库
    :param filename:DB文件
    :param data:插入数据
    :param rule:采集规则
    :return:已插入数据
    """
    sqlite_db = Splite(filename)
    insert_data = []
    for row in data:
        # sql = "SELECT count(*) from articles where url='"+row['url']+"'"
        # 查重
        sql = "SELECT count(*) from articles where 1"
        where = ""
        for index, parse in enumerate(rule['parse']):
            if 'unique' in parse.keys() and parse['key'] != 'add_time':
                if parse['unique'] == 1:
                    where += " AND " + parse['key'] + "='" + row[parse['key']] + "'"
        sql += where
        # print('sql:'+ sql)
        tatol = sqlite_db.get_one(sql)
        if tatol == 0:
            sql = "INSERT INTO articles (name,url,title,update_time,add_time) VALUES ('"+row['name']+"', '"+row['url']+"', '"+row['title']+"', '"+row['update_time']+"', "+str(int(time.time()))+")"
            # print('insert:'+sql)
            sqlite_db.query(sql)
            insert_data.append(row)
    sqlite_db.close()
    return insert_data


exitFlag = 0
class WorkThread(threading.Thread):
    """
    工作线程，用于监视网站更新
    """
    def __init__(self, name):
        threading.Thread.__init__(self)
        # 线程内部变量
        self.name = name
        self.status = 0

    def run(self):
        global exitFlag
        is_loop = True
        while is_loop:
            # # 规则测试
            # import rule_debug
            # rule = rule_debug.ruletest
            # result = spider(rule)
            # insert_data = insert_db('update_data.db', result, rule)
            # csv_save('test.csv', insert_data)
            # for item in insert_data:
            #     row = (item['name'], item['title'], item['url'], item['update_time'], item['add_time'])
            #     print(row)
            #     treeview1.insert('', 'end', values=row)
            # tatol = int(entry1.get()) + len(insert_data)
            # entry1_text(str(tatol))
            # time.sleep(1800)
            # is_loop = False

            jsonfile = open('rules.json', 'r', encoding='utf-8')
            rules = json.load(jsonfile)
            # print(rules[0])
            # exit()

            for rule in rules:
                if exitFlag:
                    # 结束线程
                    is_loop = False
                    exitFlag = 0
                    print('stop work_thread')
                    break
                try:
                    result = spider(rule)
                    insert_data = insert_db('update_data.db', result, rule)
                    csv_save('update_data.csv', insert_data)
                    for item in insert_data:
                        row = (item['name'], item['title'], item['url'], item['update_time'], item['add_time'])
                        # print(row)
                        treeview1.insert('', 'end', values=row)
                    tatol = int(entry1.get()) + len(insert_data)
                    entry1_text(str(tatol))
                    # if len(insert_data) > 0:
                        # # windows播放音频
                        # winsound.PlaySound('complete.wav', flags=1)
                except:
                    continue
            if is_loop:
                print('Waiting '+entry2.get()+'s')
                time.sleep(int(entry2.get()))
            # is_loop = False
            # inser_data() #测试列表显示数据


# def print(str):
#     """
#     打印方法重载
#     :param str:
#     """
#     scrolledtext1.insert('end', str+"\n")
#     scrolledtext1.see('end')


def entry1_text(str):
    """
    tkinter entry1控件修改值
    :param str:修改值
    """
    entry1['state'] = 'normal'
    entry1.delete(0, "end")
    entry1.insert(0, str)
    entry1['state'] = 'readonly'


def run_spider():
    """
    启动/停止蜘蛛
    """
    thread_status = 1 if button1.cget('text')=='Stop' else 0
    if thread_status:
        # 结束线程
        global exitFlag
        exitFlag = 1
        button1.config(text='Start')
    else:
        work_thread = WorkThread('work_thread')
        work_thread.start()
        button1.config(text='Stop')


def treeview1_clear():
    """
    清空treeview1
    """
    x = treeview1.get_children()
    for item in x:
        treeview1.delete(item)
    entry1.config(text='0')
    scrolledtext1.delete(1.0, tk.END)


def treeview1_dclick(self):
    """
    双击浏览器打开网址，并删除该项
    :param self:
    """
    for item in treeview1.selection():
        item_text = treeview1.item(item, "values")
        url = item_text[2]
        webbrowser.open_new(url)
        treeview1.delete(item)
        tatol = int(entry1.get()) - 1
        entry1_text(str(tatol))


def about():
    messagebox.askokcancel("About", "网络爬虫定时检查网站更新，作者ZhenLi，QQ861003593！")


def on_closing():
    """
    关闭窗口事件
    """
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        # 结束线程
        global exitFlag
        exitFlag = 1
        button1.config(text='Start')
        # 结束窗口mainloop
        window.destroy()


if __name__=='__main__':
    # 构建窗体
    window = tk.Tk()
    window.title("UpdateSpider")
    window.geometry('900x600')
    # top window
    window.wm_attributes('-topmost', 1)
    # window.iconbitmap(default=r'icon/favicon.ico')
    window.rowconfigure(1, weight=1)
    window.columnconfigure(0, weight=1)
    # setting
    setFrame = tk.LabelFrame(window,text="Setting")
    setFrame.columnconfigure(2, weight=1)
    lable1 = tk.Label(setFrame,text="Tatol: ")
    lable1.grid(row=1,column=0)
    entry1 = tk.Entry(setFrame)
    entry1.grid(row=1,column=1,sticky=tk.EW,columnspan=2)
    entry1.insert(0, "0")
    entry1['state'] = 'readonly'
    lable2 = tk.Label(setFrame,text="Waiting(s): ")
    lable2.grid(row=1,column=3)
    entry2 = tk.Entry(setFrame)
    entry2.grid(row=1,column=4,sticky=tk.EW)
    entry2.insert(0, "1800")
    button1 = ttk.Button(setFrame,text="Start",command=run_spider)
    button1.grid(row=1,column=5)
    button2 = ttk.Button(setFrame,text="Clear",command=treeview1_clear)
    button2.grid(row=1,column=6)
    button3 = ttk.Button(setFrame,text="About",command=about)
    button3.grid(row=1,column=7)
    setFrame.grid(row=0,sticky=tk.EW)
    # TreeView
    # 实例化控件，设置表头样式和标题文本
    treeFrame = tk.LabelFrame(window,text="Data")
    treeFrame.rowconfigure(1, weight=1)
    treeFrame.columnconfigure(2, weight=1)
    columns = ("name", "title", "url", "update_time", "add_time")
    headers = ("Name", "Title", "Url", "Update_time", "Add_time")
    # headers = ("网站", "标题", "网址", "更新时间", "添加时间")
    widthes = (100, 250, 250, 120, 120)
    treeview1 = ttk.Treeview(treeFrame, show="headings", columns=columns)
    for (column, header, width) in zip(columns, headers, widthes):
        treeview1.column(column, width=width, anchor="w")
        treeview1.heading(column, text=header, anchor="w")
    treeview1.grid(row=1,column=1,sticky=tk.NSEW,columnspan=2)
    treeview1.bind("<Double-Button-1>", treeview1_dclick)
    treeFrame.grid(row=1,sticky=tk.NSEW)
    # wacher
    wacherFrame = tk.LabelFrame(window,text="Log")
    wacherFrame.columnconfigure(2, weight=1)
    scrolledtext1 = ScrolledText.ScrolledText(wacherFrame, height=12)
    scrolledtext1.grid(row=1,column=1,sticky=tk.EW,columnspan=2)
    wacherFrame.grid(row=2,sticky=tk.EW)
    # 启动运行（有命令行参数start）
    if 'start' in sys.argv:
        run_spider()
    # 窗口关闭事件触发执行on_closing
    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.mainloop()