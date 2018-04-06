# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from haystack.forms import SearchForm
from django.shortcuts import render


def full_search(request):
    sform = SearchForm(request.GET)
    return render(request,'search/s.html',{'posts':posts,'form':sform})
