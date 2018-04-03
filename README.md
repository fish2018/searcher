# searcher
django基于haystack，Whoosh，Jieba的中文全文检索demo

1、安装相关包
- haystack：
是django的开源全文检索框架，该框架支持Solr,Elasticsearch,Whoosh, *Xapian*搜索引擎，不用更改代码，直接切换引擎，减少代码量。
- Whoosh：
这是一个由纯Python实现的全文搜索引擎，没有二进制文件等，比较小巧，配置比较简单，当然性能自然略低。
- Jieba：
一款免费的中文分词包，由于Whoosh自带的是英文分词，对中文的分词支持不是太好，故用jieba替换whoosh的分词组件。

```python
pip install django-haystack whoosh jieba
```

2、创建blog应用，编辑settings.py配置文件,添加`blog`和`haystack`
```
vi settings.py
###############
INSTALLED_APPS = (
    ...
    'blog',
    'haystack',
)
###############
```
3、编辑blog/models.py
```
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User


class Note(models.Model):
    user = models.ForeignKey(User)
    pub_date = models.DateTimeField()
    title = models.CharField(max_length=200)
    body = models.TextField()

    def __str__(self):
        return self.title
```
同步数据库
```
python manager.py makemigrations
python migrate
```
4、在blog应用目录下，添加一个索引
编辑blog/search_indexes.py
```
# -*- coding: utf-8 -*-
from haystack import indexes
from blog.models import Note

# 修改此处，类名为模型类的名称+Index，比如模型类为Note,则这里类名为NoteIndex
class NoteIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
		# 修改此处，为你自己的model
        return Note

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
```
5、编辑blog/views.py
```
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from haystack.forms import SearchForm
from django.shortcuts import render


def full_search(request):
    sform = SearchForm(request.GET)
    posts = sform.search()
    return render(request,'search/s.html',{'posts':posts,'form':sform})
```
6、添加搜索页面 blog/templates/search/s.html
```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Title</title>
</head>
<body>


<form method='get' action="/search/" target="_blank">
    {{ form }}
    <input type="submit" value="查询">
</form>

</body>
</html>
```
这里`name="q"`是搜索框架中view使用到的，详情查看源码

7、添加搜索结果页面 blog/templates/search/search.html
这个模板路径是搜索框架默认的
```
<!DOCTYPE html>
<html>
<head>
    <title></title>
</head>
<body>
这是搜索结果：



{% if query %}

    <h3>搜索结果如下：</h3>

    {% for result in page.object_list %}

        <a href="{{ result.object.get_absolute_url }}">{{ result.object.title }}</a><br/>
    {% empty %}
        <p>啥也没找到</p>
    {% endfor %}

    {% if page.has_previous or page.has_next %}
        <div>
            {% if page.has_previous %}<a href="?q={{ query }}&amp;page={{ page.previous_page_number }}">{% endif %}&laquo; 上一页{% if page.has_previous %}</a>{% endif %}
        |
            {% if page.has_next %}<a href="?q={{ query }}&amp;page={{ page.next_page_number }}">{% endif %}下一页 &raquo;{% if page.has_next %}</a>{% endif %}
        </div>
    {% endif %}
{% endif %}
<a href="/">重新搜索<a>
</body>
</html>
```
|  变量 | 含义  |
| ------------ | ------------ |
| query  | 搜索关键字  |
| page  | 当前页的page对象  |
| paginator  | 分页paginator对象  |


8、指定索引模板文件
在`templates/search/indexes/应用名称/`下创建`模型名称_text.txt`文件。
此文件指定将模型中的哪些字段建立索引，写入如下内容：（只修改中文，不要改掉object）
```
{{ object.字段1 }}
{{ object.字段2 }}
{{ object.字段3 }}
```
这里我们创建`blog/templates/search/indexes/blog/note_text.txt`
```
{{ object.title }}
{{ object.user}}
{{ object.body }}
```
9、使用jieba中文分词
拷贝`whoosh_backend.py`到blog应用目录下，并重命名`whoosh_cn_backend.py`
```
cp /usr/lib/python2.7/site-packages/haystack/backends/whoosh_backend.py /blog/whoosh_cn_backend.py
```
然后修改whoosh_cn_backend.py
```
#在顶部添加
from jieba.analyse import ChineseAnalyzer
# 搜索`schema_fields[field_class.index_fieldname] = TEXT`,改成如下：
schema_fields[field_class.index_fieldname] = TEXT(stored=True, analyzer=ChineseAnalyzer(),field_boost=field_class.boost, sortable=True)
```
设置settings.py
```
# 全文检索框架配置
HAYSTACK_CONNECTIONS = {
    'default': {
		# 修改后的whoosh引擎，支持中文分词
        'ENGINE': 'blog.whoosh_cn_backend.WhooshEngine',
		# 索引文件路径
        'PATH': os.path.join(BASE_DIR, 'whoosh_index'),
    }
}
# 当添加、修改、删除数据时，自动生成索引
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
# 指定搜索结果每页显示多少条信息
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 6
```
11、编辑项目的urls.py
```
from django.conf.urls import url,include
from django.contrib import admin
from blog import views

urlpatterns = [
    url(r'^$', views.full_search),
    url(r'^search/', include('haystack.urls')),
]

```
12、数据库blog_note表插入数据（略）
13、生成索引
手动生成一次索引：
```
python manage.py rebuild_index
```

### 测试一下效果：

输入搜索

![](http://www.seczh.com/doc/Public/Uploads/2018-04-03/5ac2fcffe45b2.png)

返回结果

![](http://www.seczh.com/doc/Public/Uploads/2018-04-03/5ac2fd20e2f6d.png)
