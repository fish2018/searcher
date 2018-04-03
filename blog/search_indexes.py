# -*- coding: utf-8 -*-
import datetime
from haystack import indexes
# 修改此处，为你自己的model
from blog.models import Note


class NoteIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Note

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()