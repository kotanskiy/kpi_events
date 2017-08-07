
from django.contrib import auth
from django.core.files.storage import default_storage
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect, render_to_response

# Create your views here.
from django.template.context_processors import csrf
from events_calendar.models import Event, Comment, Category
from datetime import datetime
from django.core.paginator import Paginator


def calendar(request, page_number=1):
    user = auth.get_user(request)
    events = Event.objects.all()
    current_page = Paginator(events, 5)
    context = {
        'page_header': 'Главная',
        'events': current_page.page(page_number),
        'user': user,
        'type': 'Все события',
    }

    return render(request, 'events_calendar/calendar.html', context)

def filter_by_signed_organizations(request, page_number=1):
    user = auth.get_user(request)
    organizations = user.profile.signed_organizations.all()
    events = set()
    for organization in organizations:
        local_events = Event.objects.filter(creator__profile__organization=organization)
        events = events.union(local_events)

    current_page = Paginator(list(events), 5)
    if len(events) == 0:
        info = 'Подпишитесь на события организаций'
    else:
        info = ''
    context = {
        'page_header': 'Главная',
        'events': current_page.page(page_number),
        'user': user,
        'type': 'Моя лента событий',
        'info': info,
    }
    return render(request, 'events_calendar/calendar.html', context)

def filter_by_category(request):
    return None

def calendar_details(request, calendar_id):
    user = auth.get_user(request)
    event = get_object_or_404(Event, pk=calendar_id)
    context = {
        'page_header': event.name,
        'event': event,
        'user': user,
    }
    if request.user.username:
        signed_organizations = user.profile.signed_organizations.all()
        context['signed_organizations'] = signed_organizations


    return render(request, 'events_calendar/details.html', context)

def comments(request, calendar_id):
    event = get_object_or_404(Event, pk=calendar_id)
    comments = Comment.objects.all().filter(event=event)
    context = {
        'comments': comments
    }
    return render(request, 'events_calendar/comments.html', context)

def add_comment(request, calendar_id):
    event = get_object_or_404(Event, pk=calendar_id)
    text = request.POST.get('text')
    text = text.strip()
    if text != '':
        comment = Comment(creator=request.user, text=text, event=event)
        comment.save()
    return redirect('/')


def organization_events(request, page_number=1):
    try:
        if request.user.profile.organization:
            events = Event.objects.all().filter(creator=request.user)
            current_page = Paginator(events, 5)
            context = {
                'page_header': request.user.profile.organization.name,
                'events': current_page.page(page_number),
                'user':request.user
            }
            return render(request, 'events_calendar/organization_events.html', context)
        else:
            return redirect('/')
    except:
        return redirect('/')


def create_event(request):
    args = {}
    args['user'] = request.user
    args.update(csrf(request))
    args['page_header'] = 'Новое событие ' + request.user.profile.organization.name
    args['categories'] = Category.objects.all()
    if request.user.profile.organization:
        if request.POST:
            try:
                try:
                    post = request.POST
                    if post.get('start_date') != '':
                        start_date = str(datetime.strptime(post.get('start_date'), '%Y-%m-%dT%H:%M'))
                    else:
                        start_date = None
                    if post.get('end_date') != '':
                        end_date = str(datetime.strptime(post.get('end_date'), '%Y-%m-%dT%H:%M'))
                    else:
                        end_date = None

                    for file in request.FILES.getlist('image'):
                        link_image = 'images/organization/' + request.user.username + str(file)
                        with default_storage.open(link_image, 'wb+') as destination:
                            for chunk in file.chunks():
                                destination.write(chunk)
                    if post.get('name').strip() == '':
                        args['error'] = 'Название события не заполнено'
                        return render_to_response('events_calendar/create_event.html', args)
                    if post.get('description').strip() == '':
                        args['error'] = 'Описание не заполнено'
                        return render_to_response('events_calendar/create_event.html', args)
                    if post.get('place_of_event').strip() != '':
                        place_of_event = post.get('place_of_event').strip()
                    else:
                        place_of_event = None
                    if post.get('vk_link').strip() != '':
                        vk_link = post.get('vk_link').strip()
                    else:
                        vk_link = None
                    if post.get('fb_link').strip() != '':
                        fb_link = post.get('fb_link').strip()
                    else:
                        fb_link = None
                    if post.get('category') != '----------':
                        categories = Category.objects.all().filter(name=post.get('category'))
                        for el in categories:
                            category = el
                    else:
                        args['error'] = 'Категория не заполнена'
                        return render_to_response('events_calendar/create_event.html', args)
                    event = Event(
                        name=post.get('name'),
                        description=post.get('description'),
                        start_date=start_date,
                        end_date=end_date,
                        category=category,
                        image=link_image,
                        place_of_event=place_of_event,
                        vk_link=vk_link,
                        fb_link=fb_link,
                    )
                    event.save()
                    return redirect('/organization_events')
                except UnboundLocalError:
                    post = request.POST
                    if post.get('start_date') != '':
                        start_date = str(datetime.strptime(post.get('start_date'), '%Y-%m-%dT%H:%M'))
                    else:
                        start_date = None
                    if post.get('end_date') != '':
                        end_date = str(datetime.strptime(post.get('end_date'), '%Y-%m-%dT%H:%M'))
                    else:
                        end_date = None
                    if post.get('name').strip() == '':
                        args['error'] = 'Название события не заполнено'
                        return render_to_response('events_calendar/create_event.html', args)
                    if post.get('description').strip() == '':
                        args['error'] = 'Описание не заполнено'
                        return render_to_response('events_calendar/create_event.html', args)
                    if post.get('place_of_event').strip() != '':
                        place_of_event = post.get('place_of_event').strip()
                    else:
                        place_of_event = None
                    if post.get('vk_link').strip() != '':
                        vk_link = post.get('vk_link').strip()
                    else:
                        vk_link = None
                    if post.get('fb_link').strip() != '':
                        fb_link = post.get('fb_link').strip()
                    else:
                        fb_link = None
                    if post.get('category') != '----------':
                        categories = Category.objects.all().filter(name=post.get('category'))
                        for el in categories:
                            category = el
                    else:
                        args['error'] = 'Категория не заполнена'
                        return render_to_response('events_calendar/create_event.html', args)
                    event = Event(
                        name=post.get('name'),
                        description=post.get('description'),
                        start_date=start_date,
                        end_date=end_date,
                        category=category,
                        image=link_image,
                        place_of_event=place_of_event,
                        vk_link=vk_link,
                        fb_link=fb_link,
                    )
                    event.save()
                    return redirect('/organization_events')
            except IntegrityError:
                args['error'] = 'Не выбрана категория'
                return render_to_response('events_calendar/create_event.html', args)
        return render_to_response('events_calendar/create_event.html', args)
    else:
        return redirect('/')


def edit_event(request, calendar_id):
    event = get_object_or_404(Event, pk=calendar_id)
    if request.user.profile.organization == event.creator.profile.organization:
        args = {}
        args.update(csrf(request))
        args['event'] = event
        args['categories'] = Category.objects.all()
        args['page_header'] = event.name
        args['user'] = request.user
        if request.POST:
            try:
                if request.POST.get('name').strip() != '':
                    event.name = request.POST.get('name').strip()
                if request.POST.get('description').strip() != '':
                    event.description = request.POST.get('description').strip()
                for file in request.FILES.getlist('image'):
                    link_image = 'images/events_calendar/' + request.user.username + str(file)
                    with default_storage.open(link_image, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                if str(file).strip() != '':
                    event.image = link_image
                categories = Category.objects.all().filter(name=request.POST.get('category'))
                for el in categories:
                    category = el
                event.category = category
                if request.POST.get('start_date') != '':
                    event.start_date = str(datetime.strptime(request.POST.get('start_date'), '%Y-%m-%dT%H:%M'))
                if request.POST.get('end_date') != '':
                    event.end_date = str(datetime.strptime(request.POST.get('end_date'), '%Y-%m-%dT%H:%M'))
                if request.POST.get('place_of_event').strip() != '':
                    event.place_of_event = request.POST.get('place_of_event').strip()
                if request.POST.get('vk_link').strip() != '':
                    event.vk_link = request.POST.get('vk_link').strip()
                if request.POST.get('fb_link').strip() != '':
                    event.fb_link = request.POST.get('fb_link').strip()
                event.save()
                return render(request, 'events_calendar/edit_event.html', args)
            except UnboundLocalError:
                if request.POST.get('name').strip() != '':
                    event.name = request.POST.get('name').strip()
                if request.POST.get('description').strip() != '':
                    event.description = request.POST.get('description').strip()
                categories = Category.objects.all().filter(name=request.POST.get('category'))
                for el in categories:
                    category = el
                event.category = category
                if request.POST.get('start_date') != '':
                    event.start_date = str(datetime.strptime(request.POST.get('start_date'), '%Y-%m-%dT%H:%M'))
                if request.POST.get('end_date') != '':
                    event.end_date = str(datetime.strptime(request.POST.get('end_date'), '%Y-%m-%dT%H:%M'))
                if request.POST.get('place_of_event').strip() != '':
                    event.place_of_event = request.POST.get('place_of_event').strip()
                if request.POST.get('vk_link').strip() != '':
                    event.vk_link = request.POST.get('vk_link').strip()
                if request.POST.get('fb_link').strip() != '':
                    event.fb_link = request.POST.get('fb_link').strip()
                event.save()
                return render(request, 'events_calendar/edit_event.html', args)
        return render(request, 'events_calendar/edit_event.html', args)
    else:
        return redirect('/')


def edit_organization(request):
    args = {}
    args.update(csrf(request))
    organization = request.user.profile.organization
    args['organization'] = organization
    args['page_header'] = request.user.profile.organization.name
    args['user'] = request.user
    if request.POST:
        try:
            if request.POST.get('name').strip() != '':
                organization.name = request.POST.get('name').strip()
            for file in request.FILES.getlist('image'):
                link_image = 'images/events_calendar/' + request.user.username + str(file)
                with default_storage.open(link_image, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
            organization.image = link_image
            organization.save()
        except UnboundLocalError:
            if request.POST.get('name').strip() != '':
                organization.name = request.POST.get('name').strip()
            organization.save()
    return render_to_response('events_calendar/edit_organization.html', args)


def subscribe(request):
    if request.POST:
        event = get_object_or_404(Event, pk=request.POST.get('event'))
        organization = event.creator.profile.organization
        user = request.user
        sub = request.POST.get('sub')
        if sub == 'Subscribe':
            user.profile.signed_organizations.add(organization)
        elif sub == 'Unsubscribe':
            user.profile.signed_organizations.remove(organization)
        return redirect('/event/' + str(event.id))


