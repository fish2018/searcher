# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

# Create your tests here.
import jieba

seg_list = jieba.cut("邮箱需要配置一下账号和密码才可以使用，我帮你看看", cut_all=True)
print ' '.join(seg_list)