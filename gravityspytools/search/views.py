# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

from django.shortcuts import render, redirect
import os
from django.http import HttpResponse
from django.http import JsonResponse
from matplotlib import use
use('agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from .forms import SearchForm, LIGOSearchForm
from .forms import get_imageid_json
from .forms import get_zooid_json
from .forms import get_gpstimes_json

from .utils import similarity_search
from .utils import create_collection
from .utils import histogram as make_histogram
from login.utils import make_authorization_url

import pandas as pd
from sqlalchemy.engine import create_engine


# Create your views here.
def get_imageids(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        data = get_imageid_json(name=q)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


def get_zooids(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        data = get_zooid_json(name=q)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


def get_gpstimes(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        data = get_gpstimes_json(name=q)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


def index(request):
    if request.user.is_authenticated():
        request.session['auth_user_backend'] = request.session['_auth_user_backend']
        if request.session['auth_user_backend'] == 'django.contrib.auth.backends.RemoteUserBackend':
            form = LIGOSearchForm()
        else:
            form = SearchForm()
        return render(request, 'form.html', {'form': form})
    else:
        return redirect(make_authorization_url())


def do_similarity_search(request):
    # if this is a POST request we need to process the form data
    if request.method == 'GET':

        # create a form instance and populate it with data from the request:
        if request.session['_auth_user_backend'] == 'django.contrib.auth.backends.RemoteUserBackend':
            form = LIGOSearchForm(request.GET)
        else:
            form = SearchForm(request.GET)
        # check whether it's valid:
        if form.is_valid():
            SI_glitches = similarity_search(form)
            histogramurl = request.get_full_path().replace('do_similarity_search', 'histogram')

            return render(request, 'searchresults.html', {'results': SI_glitches.to_dict(orient='records'), 'histogramurl' : histogramurl})
        else:
            return render(request, 'form.html', {'form': form}) 


def similarity_search_restful_API(request):
    # if this is a POST request we need to process the form data
    if request.method == 'GET':

        # create a form instance and populate it with data from the request:
        form = SearchForm(request.GET)
        # check whether it's valid:
        if form.is_valid():
            SI_glitches = similarity_search(form)

            return JsonResponse(SI_glitches.to_dict(orient='list'))


def do_collection_creation(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':

        # create a form instance and populate it with data from the request:
        form = SearchForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            SI_glitches = similarity_search(form)
            howmany = int(form.cleaned_data['howmany'])
            collection_url = create_collection(request, SI_glitches)

            #engine = create_engine('postgresql://{0}:{1}@gravityspy.ciera.northwestern.edu:5432/gravityspy'.format(os.environ['GRAVITYSPY_DATABASE_USER'], os.environ['GRAVITYSPY_DATABASE_PASSWD']))
            #searchquery = pd.DataFrame({'search_created_at' : pd.to_datetime('now'), 'uniqueid_searched' : SI_glitches['searchedID'].iloc[0], 'zooid_searched' : int(SI_glitches['searchedzooID'].iloc[0]), 'user': username, 'returned_ids' : ','.join(SI_glitches.links_subjects.apply(str).tolist()), 'howmany': howmany}, index=[0])
            #searchquery.to_sql('searchlog', engine, if_exists='append', index=False)

            return render(request, 'createcollection.html', {'urls' : {collection_url}, 'results': SI_glitches.to_dict(orient='records')})
        else:
            return render(request, 'form.html', {'form': form})


def histogram(request):
    # if this is a POST request we need to process the form data
    if request.method == 'GET':

        # create a form instance and populate it with data from the request:
        form = SearchForm(request.GET)
        # check whether it's valid:
        if form.is_valid():
            if form.cleaned_data['imageid']:
                uniqueID = str(form.cleaned_data['imageid'])
            else:
                uniqueID = form.cleaned_data['imageid']
            if form.cleaned_data['zooid']:
                zooID = float(str(form.cleaned_data['zooid']))
            else:
                zooID = form.cleaned_data['zooid']
            fig = make_histogram(uniqueID, zooID)
            canvas = FigureCanvas(fig)
            response = HttpResponse(content_type='image/png')
            canvas.print_png(response)
            fig.clear()
            return response
