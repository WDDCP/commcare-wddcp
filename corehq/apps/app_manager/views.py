from django.http import HttpResponse, Http404
from corehq.util.webutils import render_to_response

from corehq.apps.app_manager.forms import NewXFormForm, NewAppForm, NewModuleForm

from corehq.apps.domain.decorators import login_and_domain_required

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse, resolve
from corehq.apps.app_manager.models import RemoteApp, Application, VersionedDoc, get_app, DetailColumn, Form, FormAction, FormActionCondition, FormActions

from corehq.apps.app_manager.models import DETAIL_TYPES
from django.utils.http import urlencode

from django.views.decorators.http import require_POST
from django.conf import settings
from corehq.util.xforms import readable_form
from corehq.util.webutils import get_url_base
from BeautifulSoup import BeautifulStoneSoup
from lxml import etree as ET
import json
from utilities.profile import profile
import urllib
import urlparse
from collections import defaultdict

_str_to_cls = {"Application":Application, "RemoteApp":RemoteApp}

@login_and_domain_required
def back_to_main(req, domain, app_id='', module_id='', form_id='', edit=True, error='', **kwargs):
    """
    returns an HttpResponseRedirect back to the main page for the App Manager app
    with the correct GET parameters.

    This is meant to be used by views that process a POST request, which then redirect to the
    main page. The idiom for calling back_to_main used in this file is
        return back_to_main(**locals())
    which harvests the values for req, domain, app_id, module_id form_id, edit, and error from
    the local namespace.

    """
    params = {'m': module_id, 'f': form_id}
    if edit:
        params['edit'] = 'true'
    if error:
        params['error'] = error

    args = [domain]
    if app_id:
        args.append(app_id)
    view_name = 'default' if len(args) == 1 else 'view_app'
    return HttpResponseRedirect("%s%s" % (
        reverse('corehq.apps.app_manager.views.%s' % view_name, args=args),
        "?%s" % urlencode(params) if params else ""
    ))


def xform_display(req, domain, form_unique_id):
    form, app = Form.get_form(form_unique_id, and_app=True)
    if domain != app.domain: raise Http404
    langs = [req.GET.get('lang')] + app.langs
    #try:
    tree = ET.fromstring(form.contents.encode('utf-8'))
    #except:
    #    return HttpResponse("[]")
    ns = {'h': '{http://www.w3.org/1999/xhtml}', 'f': '{http://www.w3.org/2002/xforms}'}
    def lookup_translation(s,pre = 'jr:itext(', post = ')'):
        if s.startswith(pre) and post[-len(post):] == post:
            s = s[len(pre):-len(post)]
        if s[0] == s[-1] and s[0] in ('"', "'"):
            id = s[1:-1]
        for lang in langs:
            x = tree.find('.//{f}translation[@lang="%s"]'.format(**ns) % lang)
            if x:
                break
        x = x.find('{f}text[@id="%s"]'.format(**ns) % id)
        #print ET.tostring(x, pretty_print=True)
        x = x.findtext('{f}value'.format(**ns)).strip()
        return x
    def get_ref(elem):
        try:
            ref = elem.attrib['ref']
        except:
            bind_id = elem.attrib['bind']
            bind = tree.find('.//{f}bind[@id="%s"]'.format(**ns) % bind_id)
            ref = bind.attrib['nodeset']
        return ref
    questions = []
    for elem in tree.findall('{h}body/*'.format(**ns)):
        try:
            question = {
                "label": lookup_translation(elem.find('{f}label'.format(**ns)).attrib['ref']),
                "tag": elem.tag.split('}')[-1],
                "value": get_ref(elem),
            }

        except None:
            continue
        if question['tag'] == "select1":
            options = []
            for item in elem.findall('{f}item'.format(**ns)):
                options.append({
                    'label': lookup_translation(item.find('{f}label'.format(**ns)).attrib['ref']),
                    'value': item.findtext('{f}value'.format(**ns)).strip()
                })
            question.update({'options': options})
        questions.append(question)
    return HttpResponse(json.dumps(questions))

@login_and_domain_required
def form_casexml(req, domain, form_unique_id):
    form, app = Form.get_form(form_unique_id, and_app=True)
    if domain != app.domain: raise Http404
    return HttpResponse(form.create_casexml())

@login_and_domain_required
def app_source(req, domain, app_id):
    app = get_app(domain, app_id)
    return HttpResponse(json.dumps(app.export_json()))
    
@login_and_domain_required
@require_POST
def import_app(req, domain):
    source = req.POST.get('source')
    name = req.POST.get('name')
    source = json.loads(source)
    if name:
        source['name'] = name
    cls = _str_to_cls[source['doc_type']]
    app = cls.from_source(source, domain)
    app.save()
    app_id = app._id
    return back_to_main(**locals())

@login_and_domain_required
@require_POST
def import_factory_app(req, domain):
    factory_app = get_app('factory', req.POST['app_id'])
    source = factory_app.export_json()
    name = req.POST.get('name')
    if name:
        source['name'] = name
    cls = _str_to_cls[source['doc_type']]
    app = cls.from_source(source, domain)
    app.save()
    app_id = app._id
    return back_to_main(**locals())

@login_and_domain_required
@require_POST
def import_factory_module(req, domain, app_id):
    fapp_id, fmodule_id = req.POST['app_module_id'].split('/')
    fapp = get_app('factory', fapp_id)
    fmodule = fapp.get_module(fmodule_id)
    app = get_app(domain, app_id)
    source = fmodule.export_json()
    app.new_module_from_source(source)
    app.save()
    return back_to_main(**locals())

@login_and_domain_required
@require_POST
def import_factory_form(req, domain, app_id, module_id):
    fapp_id, fmodule_id, fform_id = req.POST['app_module_form_id'].split('/')
    fapp = get_app('factory', fapp_id)
    fform = fapp.get_module(fmodule_id).get_form(fform_id)
    source = fform.export_json()
    app = get_app(domain, app_id)
    app.new_form_from_source(module_id, source)
    app.save()
    return back_to_main(**locals())
    

#@profile("apps_context.prof")
def _apps_context(req, domain, app_id='', module_id='', form_id=''):
    """
    Does most of the processing for creating the template context for the App Manager.
    It's currently only used by view_app, and the distribution of labor is not really
    that clear; for that reason, this may soon be revisited and merged with view_app

    """
    edit = (req.GET.get('edit', '') == 'true')
    lang = req.GET.get('lang',
       req.COOKIES.get('lang', '')
    )
    
    factory_apps = [app['value'] for app in VersionedDoc._db.view('app_manager/factory_apps')]

    applications = []
    for app in VersionedDoc._db.view('app_manager/applications_brief', startkey=[domain], endkey=[domain, {}]).all():
        app = app['value']
        applications.append(app)
    app = module = form = None
    if app_id:
        app = get_app(domain, app_id)
    if module_id:
        module = app.get_module(module_id)
    if form_id:
        form = module.get_form(form_id)
    xform = ""
    xform_contents = ""
    try:
        xform = form
    except:
        pass
    if xform:
        xform_contents = form.contents
        #xform_contents, err, has_err = readable_form(xform_contents)

    if app:
        saved_apps = [x['value'] for x in VersionedDoc._db.view('app_manager/saved_app',
            startkey=[domain, app_id, {}],
            endkey=[domain, app_id],
            descending=True
        ).all()]
    else:
        saved_apps = []
    if app and not app.langs:
        # lots of things fail if the app doesn't have any languages.
        # the best we can do is add 'en' if there's nothing else.
        app.langs.append('en')
        app.save()
    if app and not lang:
        lang = app.langs[0]

    case_fields = set()
    if module:
        for _form in module.forms:
            case_fields.update(_form.actions.update_case.update.keys())
    case_fields = sorted(case_fields)

    return {
        'domain': domain,
        'applications': applications,

        'app': app,
        'module': module,
        'form': form,

        'xform': xform,
        #'xform_contents': xform_contents,
        #'form_err': err if form and has_err else None,
        'form_actions': json.dumps(form.actions.to_json()) if form else None,
        'case_fields': json.dumps(case_fields),


        'new_app_form': NewAppForm(),
        'new_module_form': NewModuleForm(),
        'new_xform_form': NewXFormForm(),
        'edit': edit,
        'langs': [lang] + (app.langs if app else []),
        'lang': lang,

        'saved_apps': saved_apps,
        'factory_apps': factory_apps,
        'editor_url': settings.EDITOR_URL,
        'URL_BASE': get_url_base(),

        'build_errors': req.GET.getlist('build_errors'),
    }
def default(req, domain):
    """
    Handles a url that does not include an app_id.
    Currently the logic is taken care of by view_app,
    but this view exists so that there's something to
    reverse() to. (I guess I should use url(..., name="default")
    in url.py instead?)


    """
    return view_app(req, domain, app_id='')

@login_and_domain_required
def view_app(req, domain, app_id=''):
    """
    This is the main view for the app. All other views redirect to here.

    """
    module_id = req.GET.get('m', '')
    form_id = req.GET.get('f', '')
    if form_id:
        template="app_manager/form_view.html"
    elif module_id:
        template="app_manager/module_view.html"
    else:
        template="app_manager/app_view.html"
    error = req.GET.get('error', '')
    context = _apps_context(req, domain, app_id, module_id, form_id)
    app = context['app']
    if not app and context['applications']:
        app_id = context['applications'][0]['id']
        return back_to_main(edit=False, **locals())
    if app and app.copy_of:
        raise Http404
    force_edit = False
    if (not context['applications']) or (app and app.doc_type == "Application" and not app.modules):
        edit = True
        force_edit = True
    context.update({
        'force_edit': force_edit,
        'error':error,
        'app': app,
    })
    response = render_to_response(req, template, context)
    response.set_cookie('lang', context['lang'])
    return response

@require_POST
@login_and_domain_required
def new_app(req, domain):
    "Adds an app to the database"
    form = NewAppForm(req.POST)
    if form.is_valid():
        cd = form.cleaned_data
        name = cd['name']
        if " (remote)" == name[-9:]:
            name = name[:-9]
            cls = RemoteApp
        else:
            cls = Application


        all_apps = Application.view('app_manager/applications', key=[domain]).all()
        if name in [a.name.get(lang, "") for a in all_apps]:
            error="app_exists"
        else:
            app = cls.new_app(domain, name)
            app.save()
            app_id = app.id
    return back_to_main(**locals())

@require_POST
@login_and_domain_required
def new_module(req, domain, app_id):
    "Adds a module to an app"
    app = get_app(domain, app_id)
    lang = req.COOKIES.get('lang', app.langs[0])
    form = NewModuleForm(req.POST)
    if form.is_valid():
        cd = form.cleaned_data
        name = cd['name']
        if name in [m['name'].get(lang, "") for m in app.modules]:
            error = "module_exists"
        else:
            module = app.new_module(name, lang)
            app.save()
    return back_to_main(**locals())

@require_POST
@login_and_domain_required
def new_form(req, domain, app_id, module_id, template="app_manager/new_form.html"):
    "Adds a form to an app (under a module)"
    app = get_app(domain, app_id)
    lang = req.COOKIES.get('lang', app.langs[0])
    new_xform_form = NewXFormForm(req.POST, req.FILES)

    if new_xform_form.is_valid():
        cd = new_xform_form.cleaned_data
        name = cd['name']
        form = app.new_form(module_id, name, lang)
        app.save()
        # add form_id to locals()
        form_id = form.id
    return back_to_main(**locals())

@require_POST
@login_and_domain_required
def delete_app(req, domain, app_id):
    "Deletes an app from the database"
    get_app(domain, app_id).delete()
    del app_id
    return back_to_main(**locals())

@require_POST
@login_and_domain_required
def delete_module(req, domain, app_id, module_id):
    "Deletes a module from an app"
    app = get_app(domain, app_id)
    app.delete_module(module_id)
    app.save()
    del module_id
    return back_to_main(**locals())

@require_POST
@login_and_domain_required
def delete_form(req, domain, app_id, module_id, form_id):
    "Deletes a form from an app"
    app = get_app(domain, app_id)
    app.delete_form(module_id, form_id)
    app.save()
    del form_id
    return back_to_main(**locals())

@require_POST
@login_and_domain_required
def edit_module_attr(req, domain, app_id, module_id, attr):
    """
    Called to edit any (supported) module attribute, given by attr
    """
    app = get_app(domain, app_id)
    module = app.get_module(module_id)
    lang = req.COOKIES.get('lang', app.langs[0])
    if   "case_type" == attr:
        case_type = req.POST.get("case_type", None)
        module.case_type = case_type
    elif ("name", "case_name", "ref_name").__contains__(attr):
        name = req.POST.get(attr, None)
        module[attr][lang] = name
    app.save()
    return back_to_main(**locals())

@require_POST
@login_and_domain_required
def edit_module_detail(req, domain, app_id, module_id):
    """
    Called to add a new module detail column or edit an existing one

    """
    column_id = int(req.POST.get('column_id', -1))
    detail_type = req.POST.get('detail_type', '')
    assert(detail_type in DETAIL_TYPES)

    column = dict((key, req.POST[key]) for key in ('header', 'model', 'field', 'format', 'enum'))
    app = get_app(domain, app_id)
    module = app.get_module(module_id)
    lang = req.COOKIES.get('lang', app.langs[0])


    def _enum_to_dict(enum):
        if not enum:
            return {}
        answ = {}
        for s in enum.split(','):
            key, val = (x.strip() for x in s.strip().split('='))
            answ[key] = {}
            answ[key][lang] = val
        return answ

    column['enum'] = _enum_to_dict(column['enum'])
    column['header'] = {lang: column['header']}
    column = DetailColumn.wrap(column)
    detail = app.get_module(module_id).get_detail(detail_type)

    if(column_id == -1):
        detail.append_column(column)
    else:
        detail.update_column(column_id, column)
    app.save()

    return back_to_main(**locals())

@require_POST
@login_and_domain_required
def delete_module_detail(req, domain, app_id, module_id):
    """
    Called when a module detail column is to be deleted

    """
    column_id = int(req.POST['column_id'])
    detail_type = req.POST['detail_type']
    app = get_app(domain, app_id)
    module = app.get_module(module_id)
    module.get_detail(detail_type).delete_column(column_id)
    app.save()
    return back_to_main(**locals())

@require_POST
@login_and_domain_required
def edit_form_attr(req, domain, app_id, module_id, form_id, attr):
    """
    Called to edit any (supported) form attribute, given by attr

    """
    app = get_app(domain, app_id)
    form = app.get_module(module_id).get_form(form_id)
    lang = req.COOKIES.get('lang', app.langs[0])

    if   "requires" == attr:
        requires = req.POST['requires']
        form.requires = requires
    elif "name" == attr:
        name = req.POST['name']
        form.name[lang] = name
    elif "xform" == attr:
        xform = req.FILES['xform']
        xform = xform.read()
        form.contents = unicode(xform, encoding="utf-8")
        form.refresh()
    elif "show_count" == attr:
        show_count = req.POST['show_count']
        form.show_count = True if show_count == "True" else False
    elif "put_in_root" == attr:
        put_in_root = req.POST['put_in_root']
        form.put_in_root = True if put_in_root == "True" else False
    app.save()
    return back_to_main(**locals())

@require_POST
@login_and_domain_required
def edit_form_actions(req, domain, app_id, module_id, form_id):
    app = get_app(domain, app_id)
    form = app.get_module(module_id).get_form(form_id)
    form.actions = FormActions.wrap(json.loads(req.POST['actions']))
    app.save()
    return back_to_main(**locals())

@require_POST
@login_and_domain_required
def edit_app_lang(req, domain, app_id):
    """
    Called when an existing language (such as 'zh') is changed (e.g. to 'zh-cn')
    or when a language is to be added.

    """
    lang = req.POST['lang']
    lang_id = int(req.POST.get('lang_id', -1))
    app = get_app(domain, app_id)
    if lang_id == -1:
        app.langs.append(lang)
    else:
        app.langs[lang_id] = lang
    app.save()
    return back_to_main(**locals())

@require_POST
@login_and_domain_required
def delete_app_lang(req, domain, app_id):
    """
    Called when a language (such as 'zh') is to be deleted from app.langs

    """
    lang_id = int(req.POST['lang_id'])
    app = get_app(domain, app_id)
    del app.langs[lang_id]
    app.save()
    return back_to_main(**locals())

@require_POST
@login_and_domain_required
def edit_app_attr(req, domain, app_id, attr):
    """
    Called to edit any (supported) app attribute, given by attr

    """
    app = get_app(domain, app_id)
    lang = req.COOKIES.get('lang', app.langs[0])
    if   "profile_url" == attr:
        if app.doc_type not in ("RemoteApp",):
            raise Exception("App type %s does not support suite urls" % app.doc_type)
        app['profile_url'] = req.POST['profile_url']
        app.save()
    return back_to_main(**locals())


@require_POST
@login_and_domain_required
def swap(req, domain, app_id, key):
    """
    This function handels any request to switch two items in a list.
    Key tells us the list in question and must be one of
    'forms', 'modules', 'detail', or 'langs'. The two POST params
    'to' and 'from' give us the indicies of the items to be swapped.
    (They must respect to < from because of an implementation detail of
    the app.swap_* functions)

    """
    app = get_app(domain, app_id)
    i, j = (int(x) for x in (req.POST['to'], req.POST['from']))
    assert(i < j)
    if   "forms" == key:
        module_id = int(req.POST['module_id'])
        app.swap_forms(module_id, i, j)
    elif "modules" == key:
        app.swap_modules(i, j)
    elif "detail" == key:
        module_id = int(req.POST['module_id'])
        app.swap_detail_columns(module_id, req.POST['detail_type'], i, j)
    elif "langs" == key:
        app.swap_langs(i, j)
    app.save()
    return back_to_main(**locals())


# The following three functions deal with
# Saving multiple versions of the same app

@require_POST
@login_and_domain_required
def save_copy(req, domain, app_id):
    """
    Saves a copy of the app to a new doc.
    See VersionedDoc.save_copy

    """
    next = req.POST.get('next')
    app = get_app(domain, app_id)
    errors = app.validate()
    if errors:
        def replace_params(next, **kwargs):
            """this is a more general function that should be moved"""
            url = urlparse.urlparse(next)
            q = urlparse.parse_qs(url.query)
            for param in kwargs:
                if isinstance(kwargs[param], basestring):
                    q[param] = [kwargs[param]]
                else:
                    q[param] = kwargs[param]
            url = url._replace(query=urllib.urlencode(q, doseq=True))
            next = urlparse.urlunparse(url)
            return next
        errors = map(json.dumps, errors)
        next = replace_params(next, build_errors=errors)
    else:
        app.save_copy()
    return HttpResponseRedirect(next)

@require_POST
@login_and_domain_required
def revert_to_copy(req, domain, app_id):
    """
    Copies a saved doc back to the original.
    See VersionedDoc.revert_to_copy

    """
    app = get_app(domain, app_id)
    copy = get_app(domain, req.POST['saved_app'])
    app = app.revert_to_copy(copy)
    return back_to_main(**locals())

@require_POST
@login_and_domain_required
def delete_copy(req, domain, app_id):
    """
    Deletes a saved copy permanently from the database.
    See VersionedDoc.delete_copy

    """
    next = req.POST.get('next')
    app = get_app(domain, app_id)
    copy = get_app(domain, req.POST['saved_app'])
    app.delete_copy(copy)
    return HttpResponseRedirect(next)

# download_* views are for downloading the files that the application generates
# (such as CommCare.jad, suite.xml, profile.xml, etc.


def download_zipped_jar(req, domain, app_id):
    """
    See ApplicationBase.create_zipped_jar

    This is the only view that will actually be called
    in the process of downloading a commplete CommCare.jar
    build (i.e. over the air to a phone).

    """
    response = HttpResponse(mimetype="application/java-archive")
    response['Content-Disposition'] = "filename=CommCare.jar"
    app = get_app(domain, app_id)
    response.write(app.create_zipped_jar())
    return response

def download_index(req, domain, app_id, template="app_manager/download_index.html"):
    """
    A landing page, mostly for debugging, that has links the jad and jar as well as
    all the resource files that will end up zipped into the jar.

    """
    app = get_app(domain, app_id)
    return render_to_response(req, template, {
        'app': app,
        'files': sorted(app.create_all_files().items()),
    })

def download_profile(req, domain, app_id):
    """
    See ApplicationBase.create_profile

    """
    return HttpResponse(
        get_app(domain, app_id).create_profile()
    )
def download_suite(req, domain, app_id):
    """
    See Application.create_suite

    """
    return HttpResponse(
        get_app(domain, app_id).create_suite()
    )

def download_app_strings(req, domain, app_id, lang):
    """
    See Application.create_app_strings

    """
    return HttpResponse(
        get_app(domain, app_id).create_app_strings(lang)
    )

def download_xform(req, domain, app_id, module_id, form_id):
    """
    See Application.fetch_xform

    """
    return HttpResponse(
        get_app(domain, app_id).fetch_xform(module_id, form_id)
    )

def download_jad(req, domain, app_id):
    """
    See ApplicationBase.create_jad

    """
    response = HttpResponse(
        get_app(domain, app_id).create_jad()
    )
    response["Content-Type"] = "text/vnd.sun.j2me.app-descriptor"
    return response

def download_jar(req, domain, app_id):
    """
    See ApplicationBase.fetch_jar

    """
    response = HttpResponse(
        get_app(domain, app_id).fetch_jar()
    )
    response['Content-Type'] = "application/java-archive"
    return response
