from pure_pagination.mixins import PaginationMixin
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect, render_to_response
from django.template.context_processors import csrf
from django.views.generic import ListView

from events_calendar.models import Event, Comment, Category, Organization
from datetime import datetime, timedelta
from django.utils import timezone

class EventsWithBasicFiltersListView(PaginationMixin, ListView):
    all_categories = Category.objects.all()
    model = Event
    context_object_name = 'events'
    template_name = 'events_calendar/calendar.html'
    paginate_by = 5

    def post(self, request, *args, **kwargs):
        current_date = request.POST['date_filter']
        try:
            del request.session['current_date']
        except KeyError:
            pass
        if not current_date:
            current_date = '1'
        request.session.set_expiry(3600)
        request.session['current_date'] = current_date

        list_categories_id = []
        for category in self.all_categories:
            category_id = request.POST.get(category.name)
            list_categories_id.append(category_id)
            try:
                del request.session[category.name]
            except KeyError:
                pass
        current_categories = Category.objects.filter(pk__in=list_categories_id)
        for category in current_categories:
            request.session.set_expiry(3600)
            request.session[category.name] = category.id
        return render(request, self.template_name, self.get_context_data())

    def get_current_date_from_session(self):
        current_date = '1'
        try:
            current_date = self.request.session['current_date']
        except KeyError:
            pass
        return current_date

    def get_list_current_categories_from_session(self):
        current_categories = []
        list_categories_id = []
        for category in self.all_categories:
            try:
                category_id = self.request.session[category.name]
                list_categories_id.append(category_id)
            except KeyError:
                pass
        for categ in Category.objects.filter(pk__in=list_categories_id):
            current_categories.append(categ)
        return current_categories

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()
        context = super(EventsWithBasicFiltersListView, self).get_context_data(**kwargs)
        context['page_header'] = 'Головна'
        context['user'] = self.request.user
        context['type'] = 'Все события'
        context['categories'] = self.all_categories
        context['current_categories'] = self.get_list_current_categories_from_session()
        context['info_filter'] = ''
        context['current_date'] = self.get_current_date_from_session()
        return context

    def get_filters_data(self):
        current_date = self.get_current_date_from_session()
        end_date = timezone.now() - timedelta(hours=3)
        for_filter_categories = self.get_list_current_categories_from_session()
        if not for_filter_categories:
            for_filter_categories = self.all_categories[:]
        filters_data = {
            'current_date':current_date,
            'for_filter_categories':for_filter_categories,
            'end_date':end_date,
        }
        return filters_data

    def get_queryset(self):
        filters_data = self.get_filters_data()
        if filters_data['current_date'] == '1':
            events = Event.objects.filter(category__in=filters_data['for_filter_categories']).filter(published=True).filter(
                start_date__gte=filters_data['end_date']).order_by('start_date').exclude(end_date__lte=timezone.now())
        elif filters_data['current_date'] == '2':
            events = Event.objects.filter(category__in=filters_data['for_filter_categories']).filter(published=True).filter(
                start_date__lte=filters_data['end_date']).order_by('-start_date').exclude(end_date__gte=timezone.now())
        return events


class EventsBySignedOrganizationsListView(EventsWithBasicFiltersListView):
    def get_signed_organizations(self):
        return self.request.user.profile.signed_organizations.all()

    def get_context_data(self, **kwargs):
        context = super(EventsBySignedOrganizationsListView, self).get_context_data(**kwargs)
        context['type'] = 'Моя лента событий'
        return context

    def get_queryset(self):
        filters_data = self.get_filters_data()
        if filters_data['current_date'] == '1':
            events = Event.objects.filter(creator__in=self.get_signed_organizations()).filter(category__in=filters_data['for_filter_categories']).filter(
                published=True).filter(
                start_date__gte=filters_data['end_date']).order_by('start_date').exclude(end_date__lte=timezone.now())
        elif filters_data['current_date'] == '2':
            events = Event.objects.filter(creator__in=self.get_signed_organizations()).filter(category__in=filters_data['for_filter_categories']).filter(
                published=True).filter(
                start_date__lte=filters_data['end_date']).order_by('-start_date').exclude(end_date__gte=timezone.now())
        return events

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
    comments = Comment.objects.filter(event=event)
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

@login_required
def organization_events(request, page_number=1):
    if request.user.profile.organization:
        events = Event.objects.filter(creator=request.user.profile.organization).order_by('-start_date')
        current_page = Paginator(events, 5)
        context = {
            'page_header': request.user.profile.organization.name,
            'events': current_page.page(page_number),
            'user':request.user
        }
        return render(request, 'events_calendar/organization_events.html', context)



def create_event(request):
    args = {}
    args['user'] = request.user
    args.update(csrf(request))
    args['page_header'] = 'Нова подія ' + request.user.profile.organization.name
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
                        link_image = 'images/organization/' + request.user.profile.organization.name + str(file)
                        with default_storage.open(link_image, 'wb+') as destination:
                            for chunk in file.chunks():
                                destination.write(chunk)
                    if post.get('name').strip() == '':
                        args['error'] = 'Назва події не заповнено'
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
                    if post.get('web_site').strip() != '':
                        web_site = post.get('web_site').strip()
                    else:
                        web_site = None
                    if post.get('category') != '----------':
                        categories = Category.objects.all().filter(name=post.get('category'))
                        for el in categories:
                            category = el
                    else:
                        args['error'] = 'Категорія не заповнена'
                        return render_to_response('events_calendar/create_event.html', args)
                    event = Event(
                        name=post.get('name'),
                        description=post.get('description'),
                        start_date=start_date,
                        end_date=end_date,
                        category=category,
                        image=link_image,
                        web_site=web_site,
                        place_of_event=place_of_event,
                        vk_link=vk_link,
                        fb_link=fb_link,
                        creator=request.user.profile.organization,
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
                        args['error'] = 'Назва події не заповнено'
                        return render_to_response('events_calendar/create_event.html', args)
                    if post.get('place_of_event').strip() != '':
                        place_of_event = post.get('place_of_event').strip()
                    else:
                        place_of_event = None
                    if post.get('web_site').strip() != '':
                        web_site = post.get('web_site').strip()
                    else:
                        web_site = None
                    if post.get('vk_link').strip() != '':
                        vk_link = post.get('vk_link').strip()
                    else:
                        vk_link = None
                    if post.get('fb_link').strip() != '':
                        fb_link = post.get('fb_link').strip()
                    else:
                        fb_link = None
                    if post.get('category') != '----------':
                        categories = Category.objects.filter(name=post.get('category'))
                        for el in categories:
                            category = el
                    else:
                        args['error'] = 'Категорія не заповнена'
                        return render_to_response('events_calendar/create_event.html', args)
                    event = Event(
                        name=post.get('name'),
                        description=post.get('description'),
                        start_date=start_date,
                        end_date=end_date,
                        category=category,
                        web_site = web_site,
                        place_of_event=place_of_event,
                        vk_link=vk_link,
                        fb_link=fb_link,
                        creator=request.user.profile.organization,
                    )
                    event.save()
                    return redirect('/organization_events')
            except IntegrityError:
                args['error'] = 'Не обрана категорія'
                return render_to_response('events_calendar/create_event.html', args)
        return render_to_response('events_calendar/create_event.html', args)
    else:
        return redirect('/')


def edit_event(request, calendar_id):
    event = get_object_or_404(Event, pk=calendar_id)
    if request.user.profile.organization == event.creator:
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
                    link_image = 'images/events_calendar/' + request.user.profile.organization.name + str(file)
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
                if request.POST.get('web_site').strip() != '':
                    event.web_site = request.POST.get('web_site').strip()
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
                if request.POST.get('web_site').strip() != '':
                    event.web_site = request.POST.get('web_site').strip()
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
    if request.user.username and request.user.profile.organization:
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
                    link_image = 'images/events_calendar/' + request.user.profile.organization.name + str(file)
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
    else:
        return redirect('/')

@login_required
def subscribe(request):
    if request.POST:
        event = get_object_or_404(Event, pk=request.POST.get('event'))
        organization = event.creator
        user = request.user
        sub = request.POST.get('sub')
        if sub == 'Subscribe':
            user.profile.signed_organizations.add(organization)
        elif sub == 'Unsubscribe':
            user.profile.signed_organizations.remove(organization)
        return redirect('/event/' + str(event.id))

@login_required
def unsubscribe(request):
    if request.POST:
        organization = get_object_or_404(Organization, pk=request.POST.get('organization'))
        user = request.user
        user.profile.signed_organizations.remove(organization)
    return redirect('/auth/edit_user/')

def searching_results(request):
    user = auth.get_user(request)
    text = request.GET.get('text').strip()
    if text == '' or len(text) < 5:
        return redirect('/')
    events = Event.objects.filter(name__icontains=text).filter(published=True)
    if not events:
        events = Event.objects.filter(description__icontains=text).filter(published=True)
    events = list(events)
    events.reverse()
    context = {
        'user':user,
        'page_header':'Результати пошуку',
        'events':events,
    }
    return render(request, 'events_calendar/searching_results.html', context)


def suggest_an_event(request):
    args = {}
    args['user'] = request.user
    args.update(csrf(request))
    args['page_header'] = 'Запропонувати подію'
    args['categories'] = Category.objects.all()
    if request.user.username:
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
                        link_image = 'images/events_calendar/' + str(file)
                        with default_storage.open(link_image, 'wb+') as destination:
                            for chunk in file.chunks():
                                destination.write(chunk)
                    if post.get('name').strip() == '':
                        args['error'] = 'Назва події не заповнено'
                        return render_to_response('events_calendar/propose_event.html', args)
                    if post.get('web_site').strip() != '':
                        web_site = post.get('web_site').strip()
                    else:
                        web_site = None
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
                        args['error'] = 'Категорія не заповнена'
                        return render_to_response('events_calendar/propose_event.html', args)
                    event = Event(
                        name=post.get('name'),
                        description=post.get('description'),
                        start_date=start_date,
                        end_date=end_date,
                        category=category,
                        image=link_image,
                        web_site=web_site,
                        place_of_event=place_of_event,
                        vk_link=vk_link,
                        fb_link=fb_link,
                        published=False,
                    )
                    event.save()
                    return redirect('/')
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
                        args['error'] = 'Назва події не заповнено'
                        return render_to_response('events_calendar/propose_event.html', args)
                    if post.get('web_site').strip() != '':
                        web_site = post.get('web_site').strip()
                    else:
                        web_site = None
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
                        args['error'] = 'Категорія не заповнена'
                        return render_to_response('events_calendar/propose_event.html', args)
                    event = Event(
                        name=post.get('name'),
                        description=post.get('description'),
                        start_date=start_date,
                        end_date=end_date,
                        category=category,
                        web_site=web_site,
                        place_of_event=place_of_event,
                        vk_link=vk_link,
                        fb_link=fb_link,
                        published=False,
                    )
                    event.save()
                    return redirect('/')
            except IntegrityError:
                args['error'] = 'Не обрана категорія'
                return render_to_response('events_calendar/propose_event.html', args)
        return render_to_response('events_calendar/propose_event.html', args)
    else:
        return redirect('/')

@login_required
def proposed_events(request, page_id=1):
    if request.user.profile.organization.access_to_the_offer:
        events = Event.objects.filter(published=False).order_by('-start_date')
        current_page = Paginator(events, 5)
        context = {
            'page_header':'Предложка',
            'user':request.user,
            'events':current_page.page(page_id),
        }
        return render(request, 'events_calendar/proposed_events.html', context)


def edit_proposed_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.user.is_authenticated and request.user.profile.organization.access_to_the_offer:
        organization = request.user.profile.organization
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
                    link_image = 'images/events_calendar/' + request.user.profile.organization.name + str(file)
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
                if request.POST.get('web_site').strip() != '':
                    event.web_site = request.POST.get('web_site').strip()
                if request.POST.get('place_of_event').strip() != '':
                    event.place_of_event = request.POST.get('place_of_event').strip()
                if request.POST.get('vk_link').strip() != '':
                    event.vk_link = request.POST.get('vk_link').strip()
                if request.POST.get('fb_link').strip() != '':
                    event.fb_link = request.POST.get('fb_link').strip()
                event.published = True
                event.creator = organization
                event.save()
                return redirect('/proposed_events')
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
                if request.POST.get('web_site').strip() != '':
                    event.web_site = request.POST.get('web_site').strip()
                if request.POST.get('place_of_event').strip() != '':
                    event.place_of_event = request.POST.get('place_of_event').strip()
                if request.POST.get('vk_link').strip() != '':
                    event.vk_link = request.POST.get('vk_link').strip()
                if request.POST.get('fb_link').strip() != '':
                    event.fb_link = request.POST.get('fb_link').strip()
                print(event.image)
                event.published = True
                event.creator = organization
                event.save()
                return redirect('/proposed_events')
        return render(request, 'events_calendar/edit_propose_event.html', args)
    else:
        return redirect('/')


def filter_by_organization(request, organization_id, page_number=1):
    select_organization = get_object_or_404(Organization, pk=organization_id)
    events = Event.objects.none()
    all_categories = Category.objects.all()
    current_date = ''
    current_categories = []
    try:
        current_date = request.session['current_date']
    except KeyError:
        pass
    list_categories_id = []
    for category in all_categories:
        try:
            category_id = request.session[category.name]
            list_categories_id.append(category_id)
        except KeyError:
            pass
    for categ in Category.objects.filter(pk__in=list_categories_id):
        current_categories.append(categ)
    list_categories_id = []
    if request.POST:
        for category in all_categories:
            category_id = request.POST.get(category.name)
            list_categories_id.append(category_id)
            try:
                del request.session[category.name]
            except KeyError:
                pass
        current_categories = []
        for categ in Category.objects.filter(pk__in=list_categories_id):
            current_categories.append(categ)
            # update current date from post request
        if request.POST['date_filter']:
            current_date = request.POST['date_filter']
            # update current_date into session
            try:
                del request.session['current_date']
            except KeyError:
                pass
            request.session.set_expiry(3600)
            request.session['current_date'] = current_date

    for category in current_categories:
        request.session.set_expiry(3600)
        request.session[category.name] = category.id

    if not current_date:
        current_date = '1'
    for_filter_categories = current_categories
    if not for_filter_categories:
        for_filter_categories = all_categories[:]
    end_date = timezone.now() - timedelta(hours=3)
    if current_date == '1':
        events = Event.objects.filter(creator=select_organization).filter(
            category__in=for_filter_categories).filter(published=True).filter(
            start_date__gte=end_date).order_by('start_date').exclude(end_date__lte=timezone.now())
    elif current_date == '2':
        events = Event.objects.filter(creator=select_organization).filter(
            category__in=for_filter_categories).filter(published=True).filter(
            start_date__lte=end_date).order_by('-start_date').exclude(end_date__lte=timezone.now())

    info_filter = ''
    current_page = Paginator(events, 5)
    context = {
        'page_header': 'Головна',
        'events': current_page.page(page_number),
        'user': request.user,
        'type': 'Моя лента событий',
        'categories': all_categories,
        'current_categories': current_categories,
        'info_filter': info_filter,
        'current_date': current_date,
        'organization': select_organization,
    }
    context.update(csrf(request))
    return render(request, 'events_calendar/organization.html', context)


def remove_proposed_event(request, event_id):
    user = request.user
    if user.is_authenticated and user.profile.organization.access_to_the_offer:
        get_object_or_404(Event, pk=event_id).delete()
        return redirect('/proposed_events')
    return redirect('/')


def subscribe_on_organization(request):
    if request.POST and request.user.is_authenticated:
        user = request.user
        organization = get_object_or_404(Organization, pk=request.POST.get('organization'))
        sub = request.POST.get('sub')
        if sub == 'Subscribe':
            user.profile.signed_organizations.add(organization)
        elif sub == 'Unsubscribe':
            user.profile.signed_organizations.remove(organization)
        return redirect('/filter_by_organization/' + str(organization.id))