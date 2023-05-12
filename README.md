

# UpdateSpider监视网站更新爬虫程序

updateSpider是使用Python开发的定时爬取网站链接监视网站更新的爬虫程序，可以在windows/linux/macos主流操作系统上运行。



## 下载

~~~bash
# git克隆到本地，或者下载zip包解压
git clone https://github.com/supercoderlee/updatespider.git
~~~



## 环境配置和启动

终端进入当前项目目录根据不同操作系统执行命令

### windows

~~~bash
# 创建虚拟环境
python -m venv venv
# 激活虚拟环境
venv/Scripts/activate
# 安装依赖包
pip install -r requirements.txt
# 启动程序
python spider.py
~~~

### linux/macos

~~~bash
# 创建虚拟环境
sudo apt install python3.10-venv
python3 -m venv venv
# 激活虚拟环境
source venv/bin/activate
# 安装模块包
pip3 install -r requirements.txt
# 安装tkinter依赖
sudo apt-get install python3-tk
# 启动程序
source ./run.sh
~~~



## GUI界面

### Setting设置栏

**按钮**

- Start:启动爬虫
- Clear:清空列表
- About:关于程序

**文本框**

- Tatol:监测更新数量
- Waiting:监视更新时间间隔，单位秒

### Data数据列表

- Name:数据名称，来自规则的Name字段
- Title:更新标题，来自规则Title字段
- Url:更新链接，来自规则url字段
- Update_time:更新时间，来自规则update_time字段
- Add_time:添加到列表时间。来自规则add_time字段

### Log日志栏

- 查看爬虫采集状态栏



## 规则配置

爬虫规则是一个json数组，每项规则包含以下元素：

- name:规则名称
- urls:采集网址，可添加多个网址，使用通配符[起始位,生成数,步长]生成网址，如[0,3,1]表示从0开始生成3个网址，每个数字步长为1，结果为0,1,2
- type:请求方式get/post
- response:返回数据类型html/json
- encoding:数据编码默认是utf-8
- parse:解析数据

**parse**

- key:键名对应软件列表列名url/title/update_time/add_time/name
- selector:css选择器
- attr:HTML元素属性
- data_type:数据类型，用于对数据的过滤。url网址/string字符串/now当前时间（将获取当前时间）
- unique:数据是否唯一，用于检查数据库该数据是否存在
- value:最终结果用于对结果格式化处理

### 案例

~~~json
[
    {
        "name":"中国政府网",
        "urls":[
            {
                "url":"http://sousuo.gov.cn/column/30469/[0,3,1].htm"
            }
        ],
        "type":"get",
        "response":"html",
        "encoding":"utf-8",
        "parse":[
            {
                "key":"url",
                "selector":"body > div.content > div > div.news_box > div.list.list_1.list_2 > ul > li > h4 > a",
                "attr":"href",
                "data_type":"url",
                "unique":1,
                "value":"{$val}"
            },
            {
                "key":"title",
                "selector":"body > div.content > div > div.news_box > div.list.list_1.list_2 > ul > li > h4 > a",
                "data_type":"string",
                "value":"{$val}"
            },
            {
                "key":"update_time",
                "selector":"body > div.content > div > div.news_box > div.list.list_1.list_2 > ul > li > h4 > span",
                "data_type":"string",
                "value":"{$val}"
            },
            {
                "key":"add_time",
                "selector":"",
                "data_type":"now",
                "value":"{$val}"
            },
            {
                "key":"name",
                "selector":"",
                "data_type":"string",
                "value":"中国政府网"
            }
        ]
    },
    {
        "name":"北京市",
        "urls":[
            {
                "url":"http://www.beijing.gov.cn/zhengce/zhengcefagui/index.html"
            },
            {
                "url":"http://www.beijing.gov.cn/zhengce/zhengcefagui/index_[1,3,1].html"
            }
        ],
        "type":"get",
        "response":"html",
        "encoding":"utf-8",
        "parse":[
            {
                "key":"url",
                "selector":"body > div.listBox > ul > li > a",
                "attr":"href",
                "data_type":"url",
                "unique":1,
                "value":"{$val}"
            },
            {
                "key":"title",
                "selector":"body > div.listBox > ul > li > a",
                "attr":"title",
                "data_type":"string",
                "value":"{$val}"
            },
            {
                "key":"update_time",
                "selector":"body > div.listBox > ul > li > span",
                "data_type":"string",
                "value":"{$val}"
            },
            {
                "key":"add_time",
                "selector":"",
                "data_type":"now",
                "value":"{$val}"
            },
            {
                "key":"name",
                "selector":"",
                "data_type":"string",
                "value":"北京市"
            }
        ]
    }
    
]
~~~

