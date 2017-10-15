import httplib2
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from googleapiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.contrib import xsrfutil
from oauth2client.contrib.django_util.storage import DjangoORMStorage
from pure_pagination.mixins import PaginationMixin
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect, render_to_response
from django.template.context_processors import csrf
from django.views.generic import ListView, DetailView, CreateView, FormView, UpdateView

from events_calendar.forms import EventForm, OrganizationForm
from events_calendar.models import Event, Comment, Category, Organization, CredentialsModel
from datetime import timedelta
from django.utils import timezone

from kpi_events import settings


class EventsWithBaseFiltersListView(PaginationMixin, ListView):
    all_categories = Category.objects.all()
    model = Event
    context_object_name = 'events'
    template_name = 'events_calendar/calendar.html'
    paginate_by = 5

    def post(self, request, *args, **kwargs):
        current_date = request.POST['date_filter']
        if not current_date:
            current_date = '1'
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
        list_categories_id = []
        for category in self.all_categories:
            try:
                category_id = self.request.session[category.name]
                list_categories_id.append(category_id)
            except KeyError:
                pass
        current_categories = Category.objects.filter(pk__in=list_categories_id)
        return current_categories

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()
        context = super(EventsWithBaseFiltersListView, self).get_context_data(**kwargs)
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
            events = Event.objects.filter(category__in=filters_data['for_filter_categories']).filter(
                published=True).filter(
                start_date__gte=filters_data['end_date']).order_by('start_date').exclude(end_date__lte=timezone.now())
        elif filters_data['current_date'] == '2':
            events = Event.objects.filter(category__in=filters_data['for_filter_categories']).filter(
                published=True).filter(
                start_date__lte=filters_data['end_date']).order_by('-start_date').exclude(end_date__gte=timezone.now())
        return events


class EventsBySignedOrganizationsListView(EventsWithBaseFiltersListView):
    def get_signed_organizations(self):
        return self.request.user.profile.signed_organizations.all()

    def get_context_data(self, **kwargs):
        context = super(EventsBySignedOrganizationsListView, self).get_context_data(**kwargs)
        context['type'] = 'Моя лента событий'
        return context

    def get_queryset(self):
        return super(EventsBySignedOrganizationsListView, self).get_queryset()\
            .filter(creator__in=self.get_signed_organizations())

class EventDetailsView(DetailView):
    model = Event
    context_object_name = 'event'
    template_name = 'events_calendar/details.html'

    def get_context_data(self, **kwargs):
        event = self.get_object()
        context = super(EventDetailsView, self).get_context_data()
        context['page_header'] = event.name
        context['user'] = self.request.user
        if self.request.user.username:
            signed_organizations = self.request.user.profile.signed_organizations.all()
            context['signed_organizations'] = signed_organizations
        return context

def insert_into_google_calendar(request):
    if request.POST:
        event = get_object_or_404(Event, pk=request.POST.get('event_id'))
        auth_calendar_api(event)
        print('done')
        return redirect('/event/'+str(event.id))

class CommentsListView(ListView):
    model = Comment
    template_name = 'events_calendar/comments.html'
    context_object_name = 'comments'

    def get_queryset(self):
        return Comment.objects.filter(event__pk=self.kwargs['event_id'])

@login_required
def add_comment(request, event_id):
    if request.POST:
        event = get_object_or_404(Event, pk=event_id)
        text = request.POST.get('text')
        text = text.strip()
        if text != '':
            comment = Comment(creator=request.user, text=text, event=event)
            comment.save()
        return redirect('/')

class AdminOrganizationEvents(EventsWithBaseFiltersListView):
    template_name = 'events_calendar/organization_events.html'

    def get_context_data(self, **kwargs):
        context = super(AdminOrganizationEvents, self).get_context_data()
        context['type'] = ''
        context['page_header'] = self.request.user.profile.organization.name
        context['count_proposed_events'] = Event.objects.filter(published=False).count()
        return context

    def get_queryset(self):
        if self.request.user.profile.organization:
            return super(AdminOrganizationEvents, self).get_queryset().filter(creator=self.request.user.profile.organization)


class EventCreateView(CreateView):
    form_class = EventForm
    template_name = 'events_calendar/create_event.html'

    def get_context_data(self, **kwargs):
        context = super(EventCreateView, self).get_context_data()
        context['page_header'] = 'Нова подія'
        context['button_info'] = 'Опублікувати'
        context['type'] = 'create'
        context.update(csrf(self.request))
        return context

    def form_valid(self, form):
        if self.request.user.profile.organization:
            form.instance.creator = self.request.user.profile.organization
            return super(EventCreateView, self).form_valid(form)

class ProposeEventCreateView(EventCreateView):

    def get_context_data(self, **kwargs):
        context = super(ProposeEventCreateView, self).get_context_data()
        context['page_header'] = 'Запропонувати'
        context['button_info'] = 'Запропонувати'
        context['type'] = 'propose'
        return context

    def form_valid(self, form):
        form.instance.published = False
        return super(EventCreateView, self).form_valid(form)

class EventEditView(UpdateView):
    model = Event
    form_class = EventForm
    template_name_suffix = '_update_form'

    def get_context_data(self, **kwargs):
        context = super(EventEditView, self).get_context_data()
        context['page_header'] = 'Редагувати'
        context['button_info'] = 'Зберегти'
        context['start_time'] = str(timezone.now().date())
        context['type'] = 'event'
        return context

    def form_valid(self, form):
        if self.request.user.profile.organization == form.instance.creator:
            return super(EventEditView, self).form_valid(form)

class OrganizationEditView(UpdateView):
    model = Organization
    form_class = OrganizationForm
    template_name_suffix = '_update_form'

    def form_valid(self, form):
        if self.request.user.profile.organization == form.instance:
            return super(OrganizationEditView, self).form_valid(form)

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

class ProposedEventsListView(PaginationMixin, ListView):
    model = Event
    template_name = 'events_calendar/proposed_events.html'
    context_object_name = 'events'
    paginate_by = 5

    def get_context_data(self, **kwargs):
        context = super(ProposedEventsListView, self).get_context_data(**kwargs)
        context['page_header'] = 'Предложка'
        context['user'] = self.request.user
        return context

    def get_queryset(self):
        if self.request.user.profile.organization.access_to_the_offer:
            return Event.objects.filter(published=False).order_by('-start_date')

class ProposeEventEditView(EventEditView):
    def get_context_data(self, **kwargs):
        context = super(ProposeEventEditView, self).get_context_data(**kwargs)
        context['button_info'] = 'Опублікувати'
        context['type'] = 'propose_event'
        return context

    def form_valid(self, form):
        if self.request.user.profile.organization.access_to_the_offer:
            form.instance.published = True
            form.instance.creator = self.request.user.profile.organization
            return super(EventEditView, self).form_valid(form)


class EventsByOrganizationListView(EventsWithBaseFiltersListView):
    template_name = 'events_calendar/organization.html'

    def get_context_data(self, **kwargs):
        context = super(EventsByOrganizationListView, self).get_context_data()
        context['organization'] = get_object_or_404(Organization, pk=self.kwargs['organization_id'])
        context['type'] = ''
        return context

    def get_queryset(self):
        organization = get_object_or_404(Organization, pk=self.kwargs['organization_id'])
        return super(EventsByOrganizationListView, self).get_queryset().filter(creator=organization)


def remove_proposed_event(request, event_id):
    user = request.user
    if user.is_authenticated and user.profile.organization.access_to_the_offer:
        get_object_or_404(Event, pk=event_id).delete()
        return redirect('/proposed_events')


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

FLOW = flow_from_clientsecrets(
    settings.GOOGLE_OAUTH2_CLIENT_SECRETS_JSON,
    scope='https://www.googleapis.com/auth/calendar',
    redirect_uri='https://events.kpi.ua/oauth2callback')

def auth_calendar_api(request):
  storage = DjangoORMStorage(CredentialsModel, 'id', request.user, 'credential')
  credential = storage.get()
  if credential is None or credential.invalid == True:
    FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                   request.user)
    authorize_url = FLOW.step1_get_authorize_url()
    return HttpResponseRedirect(authorize_url)
  else:
    http = httplib2.Http()
    http = credential.authorize(http)
    service = build("calendar", "v3", http=http)
    return redirect('/event/'+str(request.GET.get('event_id')))

def auth_return(request):
    # if not xsrfutil.validate_token(bytes(settings.SECRET_KEY, "utf-8"), request.GET.get('state'),
    #                                request.user):
    #     return HttpResponseBadRequest()
    credential = FLOW.step2_exchange(code=request.GET.get('code'))
    storage = DjangoORMStorage(CredentialsModel, 'id', request.user, 'credential')
    storage.put(credential)
    return HttpResponseRedirect("/")
