# searcher
django基于haystack，Whoosh，Jieba的中文全文检索demo

demo地址：[https://github.com/fish2018/searcher](https://github.com/fish2018/searcher "https://github.com/fish2018/searcher")

1、安装相关包
- Whoosh：
whoosh是一个纯python实现的全文搜索组件,是原生唯一的python写的全文搜索引擎，虽然有说whoosh性能比不上sphinx,xapian等。不过whoosh本身很小，安装后才2.61M，非常容易集成到django/python里面
whoosh主要特性：
	- 敏捷的API（Pythonic API）。
	- 纯python实现，无二进制包。程序不会莫名其妙的崩溃。
	- 按字段进行索引。
	- 索引和搜索都非常的快 -- 是目前最快的纯python全文搜索引擎。
	- 良好的构架，评分模块/分词模块/存储模块等各个模块都是可插拔的。
	- 功能强大的查询语言（通过pyparsing实现功能）。
	- 纯python实现的拼写检查（目前唯一的纯python拼写检查实现）

- Jieba：
如果把用户输入的内容全部拿去检索那不就和数据库的模糊查询一个意思了嘛，所以我需要一个能分词的工具。Jieba是一款免费的中文分词包，由于Whoosh自带的是英文分词，对中文的分词支持不是太好，故用jieba替换whoosh的分词组件。

- haystack：
现在检索引擎和分词库都有了，那么接下来就是如何将这两个整合到我们的项目中了。haystack是一款同时支持whoosh,solr,Xapian,Elasticsearc四种全文检索引擎的第三方app，这意味着如果你不想使用whoosh，那你随时可以将之更换成Xapian等其他搜索引擎，而不用更改代码。正如Django一样，Django-haystack的使用也非常简单。

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
如果你想针对某个app例如blog做全文检索，则必须在blog的目录下面建立search_indexes.py文件，文件名不能修改。

为什么要创建索引？索引就像是一本书的目录，可以为读者提供更快速的导航与查找。在这里也是同样的道理，当数据量非常大的时候，若要从这些数据里找出所有的满足搜索条件的几乎是不太可能的，将会给服务器带来极大的负担。所以我们需要为指定的数据添加一个索引（目录），在这里是为Note创建一个索引。

接下来我们了解一下它的哪些字段创建索引，怎么指定。

每个索引里面必须有且只能有一个字段为 document=True，这代表haystack 和搜索引擎将使用此字段的内容作为索引进行检索(primary field)。其他的字段只是附属的属性，方便调用，并不作为检索数据。

>注意：如果使用一个字段设置了document=True，则一般约定此字段名为text，这是在SearchIndex类里面一贯的命名，以防止后台混乱，当然名字你也可以随便改，不过不建议改。

并且，haystack提供了use_template=True在text字段，这样就允许我们使用数据模板去建立搜索引擎索引的文件，说得通俗点就是索引里面需要存放一些什么东西，例如 Note 的 title 字段，这样我们可以通过 title 内容来检索 Note 数据了，举个例子，假如你搜索 `python` ，那么就可以检索出title中含有`python`的Note了。

数据模板的路径为,文件名必须为`要索引的类名_text.txt`:
```
templates/search/indexes/<yourapp>/<ModelName>_text.txt
```


5、编辑blog/views.py
```
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from haystack.forms import SearchForm
from django.shortcuts import render


def full_search(request):
    sform = SearchForm(request.GET)
    return render(request,'search/s.html',{'form':sform})
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
这里的`form`用的`haystack.forms中的SearchForm`,同普通django form用法差不多。
这里`name="q"`是搜索框架中view使用到的，详情查看源码或官方文档

7、编辑项目的urls.py
```
from django.conf.urls import url,include
from django.contrib import admin
from blog import views

urlpatterns = [
    url(r'^$', views.full_search),
    url(r'^search/', include('haystack.urls')),
]
```
其实haystack.urls的内容为：
```
from django.conf.urls import url  
from haystack.views import SearchView  
  
urlpatterns = [  
    url(r'^$', SearchView(), name='haystack_search'),  
]
```
SearchView()视图函数默认使用的html模板路径为`templates/search/search.html`


8、添加搜索结果页面 blog/templates/search/search.html
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
| query  | 搜索的字符串  |
| page  | 当前页的page对象  |
| paginator  | 分页paginator对象  |

haystack自带分页，每页显示数量在settings.py可以设置。

对于一个search页面来说，我们肯定会需要用到更多自定义的 context 内容，可以通过继承SeachView来实现重载 context 的内容。

我们在blog目录下再创建一个search_views.py 文件，位置名字可以自己定，用于写自己的搜索视图，代码实例如下：
```
from haystack.views import SearchView  
from .models import *  
  
class MySeachView(SearchView):
	template = 'search_result.html'
    def extra_context(self):       #重载extra_context来添加额外的context内容  
        context = super(MySeachView,self).extra_context()  
        side_list = Note.objects.filter(title__contains='文章').order_by('id')[:8]  
        context['side_list'] = side_list  
        return context  
```
然后再修改urls.py将search请求映射到MySearchView：
```
from blog.search_views import MySeachView
url(r'^search/', MySeachView.as_view(), name='haystack_search'),
```

haystack为我们提供了 {% highlight %}和 {% more_like_this %} 2个标签,可以让匹配的关键字显示高亮。
语法：
```
{% highlight <text_block> with <query> [css_class "class_name"] [html_tag "span"] [max_length 200] %}
```
大概意思是为 text_block 里的 query 部分添加css_class，html_tag，而max_length 为最终返回长度，相当于 cut ，我看了一下此标签实现源码，默认的html_tag 值为 span ，css_class 值为 highlighted，max_length 值为 200，然后就可以通过CSS来添加效果。
我们先在search.html中做如下设置：
```
加载highlight标签
{% load highlight  %}

设置css样式为红色
<style type="text/css">
span.highlighted {
color: red;
}
</style>

使用标签
{% highlight result.object.title with query  max_length 40 start_head True %}
```

效果如图：

![](http://www.seczh.com/doc/Public/Uploads/2018-04-03/5ac31c1b2982c.png)

9、指定索引模板文件
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
这个数据模板的作用是对Note.title，Note.user，Note.body这三个字段建立索引，当检索的时候会对这三个字段做全文检索匹配。

10、使用jieba中文分词
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
其他引擎配置参考[官方文档](http://django-haystack.readthedocs.io/en/v2.4.1/tutorial.html#configuration "官方文档")

11、同步数据库
```
python manager.py makemigrations
python migrate
```
12、数据库blog_note表插入数据（略）
13、生成索引
手动生成一次索引：
```
python manage.py rebuild_index
```

### 测试一下效果：

####输入搜索

![](http://www.seczh.com/doc/Public/Uploads/2018-04-03/5ac2fcffe45b2.png)

####返回结果

![](http://www.seczh.com/doc/Public/Uploads/2018-04-03/5ac2fd20e2f6d.png)



其他中文分词工具：
https://www.cnblogs.com/qqhfeng/p/5321949.html
