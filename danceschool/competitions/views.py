from django.views.generic import FormView,ListView
from django.urls import reverse
from django.http import HttpResponseRedirect,HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.db import IntegrityError
from danceschool.core.models import Customer
from .forms import SkatingCalculatorForm, InitSkatingCalculatorForm

import unicodecsv as csv
from functools import cmp_to_key

from .models import Competition,Judge,Registration,PrelimsResult,FinalsResult,DanceRole
from .forms import CompetitionRegForm,PrelimsResultsForm,FinalsResultsForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

import logging

# Define logger for this file
logger = logging.getLogger(__name__)


def calculate_skating(judges_list,data_dict,starting_place=1):
    sctable = []

    judges = len(judges_list)
    competitors = len(data_dict)

    # write header
    sctable.append(['',]+ judges_list + ['"1-{0}"'.format(p) for p in range(1,competitors+1)] + [_('Place'),])

    for c_name, c_points in data_dict.items():
        # get points specific for competitor
        points = c_points

        # count points entries
        entries = [points.count(1),]
        for e in range(2,competitors+1):
            entries.append(points.count(e)+entries[-1])

        # append row specific for competitor 
        sctable.append([c_name,] + points + entries)

    # define recursive skating procedure
    def skating_rules(init_col,place,sub_sctable):
        # go over entries columns
        for pcol in range(init_col,competitors): 
            # get list of (entry,sum,idx)
            column = []
            for cidx,comp in sub_sctable.items():
                # place is not set yet
                if len(comp) != len(sctable[0]):
                    # entry is >= majority
                    if comp[judges+1+pcol] >= majority:
                        column.append((-comp[judges+1+pcol],sum([c for c in comp[1:judges+1] if c <= pcol+1]),cidx))
                        
            # go over a list sorted descending by occurences then ascending by sums
            for cval,csum,cidx in sorted(column): 
                # if current (entry,sum) is unique
                if [(c[0],c[1]) for c in column].count((cval,csum)) == 1:
                    # assign the place
                    for p in range(pcol+1,competitors):
                        sctable[cidx+1][judges+1+p] = 0
                    sctable[cidx+1].append(place)
                    place += 1
                    # set sum tiebreaker if found equal entries
                    if [c[0] for c in column].count(cval) != 1:
                        sctable[cidx+1][judges+1+pcol] = str(sctable[cidx+1][judges+1+pcol]) + '(%d)' % csum
                # process only if place is not assigned for current competitor
                elif len(sctable[cidx+1]) != len(sctable[0]):
                    # collect indexes of all equal cases
                    equal_indexes =  [c[2] for c in column if c[0] == cval and c[1] == csum ]
                    # write sums to show that there was no tiebreaker on this column
                    for eidx in equal_indexes:
                        sctable[eidx+1][judges+1+pcol] = str(sctable[eidx+1][judges+1+pcol]) + '(%d)' % csum
                    # process search across the rest of the table for equal cases
                    place = skating_rules(pcol+1, place, { i:l for i,l in sub_sctable.items() if i in equal_indexes })

        # reached the end of the table
        if init_col == competitors:
            # check if we are able to resolve the tie comparing cometitors points to each other 
            if len(sub_sctable)+1 < len(sctable):
                # calculate new table with competitors in tie
                c2c_data_dict = {k:[] for k in sub_sctable.keys()}
                for j_idx in range(1,judges+1):
                    c2c_points_ordered = sorted([c_row[j_idx] for c_row in sub_sctable.values()])
                    for c_idx,c_row in sub_sctable.items():
                        c2c = c2c_points_ordered.index(c_row[j_idx])+1
                        c2c_data_dict[c_idx].append(c2c)
                # run whole procedure on reduced table
                c2c_sctable = calculate_skating(judges_list, c2c_data_dict, place)
                # copy places from reduced table to main table
                for row in c2c_sctable[1:]:
                    cidx = row[0]
                    cplace = row[-1]
                    if isinstance(cplace,str):
                        sctable[cidx+1].append(cplace)
                    else:
                        sctable[cidx+1].append(f'{cplace}({cplace-place+1})')
                        for j_idx in range(1,judges+1):
                            sctable[cidx+1][j_idx] = f'{sctable[cidx+1][j_idx]}({row[j_idx]})'
            else:
                # share several places among rest of equal cases
                shared_places = '/'.join(map(str,range(place,place+len(sub_sctable))))
                for cidx in sub_sctable.keys():
                    sctable[cidx+1].append(shared_places)
            place += len(sub_sctable)
        return place

    # calculate places
    majority = int(judges/2)+1
    skating_rules(0, starting_place, { i:l for i,l in enumerate(sctable[1:]) })

    # clean zeroes from the table
    for ridx, row in enumerate(sctable):
        for cidx, cell in enumerate(row[1:]):
            if sctable[ridx][cidx+1] == 0:
                sctable[ridx][cidx+1] = ''

    return sctable


class SkatingCalculatorView(FormView):
    form_class = SkatingCalculatorForm
    template_name = 'sc/skating_calculator.html'
    success_url = '/skatingcalculator'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['init_form'] = InitSkatingCalculatorForm
        return context

    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs(**kwargs)
        kwargs['judges'] = self.request.session.get('judges',0)
        kwargs['competitors'] = self.request.session.get('competitors',0)
        return kwargs

    def init_tab(request):
        if request.method == "POST":
            form = InitSkatingCalculatorForm(request.POST)
            if form.is_valid():
                request.session['judges'] = form.cleaned_data.get('judges')
                request.session['competitors'] = form.cleaned_data.get('competitors')
        return HttpResponseRedirect(reverse('skatingCalculator'))

    def form_valid(self, form):
        judges = self.request.session.get('judges',0)
        competitors = self.request.session.get('competitors',0)

        data_dict = {}
        judges_list = [form.cleaned_data['j{0}'.format(jidx)] for jidx in range(0,judges)]
        for cidx in range(competitors):
            data_dict[form.cleaned_data['c{0}'.format(cidx)]] = [ 
                form.cleaned_data['p{0}_{1}'.format(jidx,cidx)] for jidx in range(0,judges) 
            ]

        sctable = calculate_skating(judges_list,data_dict) 

        if form.cleaned_data['outType'] == '1':
            # display results inplace
            return self.render_to_response(
                self.get_context_data(
                    form = form,
                    skating = list(zip(*sctable))[judges+1:] # transpose the table and get only "entries+place" part
                )
            )
        else: 
            # write table to csv
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="skating.csv"'

            writer = csv.writer(response, csv.excel)
            response.write(u'\ufeff'.encode('utf8'))

            for row_data in sctable: 
                writer.writerow(row_data)

            return response


class CompetitionListViev(ListView):
    model = Competition
    template_name = 'sc/comp_list.html'
    context_object_name = 'competitions'

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('q')

        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        return queryset


def redirect_user(request, comp_id):
    comp = Competition.objects.get(id=comp_id)
    judge = None
    if request.user.is_authenticated:
        judge = Judge.objects.filter(comp=comp,profile=request.user).first()

    if judge:
        return redirect('submit_results', comp_id=comp_id)
    else:
        return redirect('register_competitor', comp_id=comp_id)


def register_competitor(request, comp_id):
    comp = Competition.objects.get(id=comp_id)

    if comp.stage != 'r':
        #error_message = _("Registration is closed.")
        return redirect('prelims_results', comp_id=comp_id)
    
    if request.method == 'POST':
        form = CompetitionRegForm(request.POST,initial={'comp': comp,'user': request.user})
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            comp_role_id = form.cleaned_data['comp_role']
            comp_role = get_object_or_404(DanceRole, id=comp_role_id)

            comp_roles = list(comp.comp_roles.all())

            competitor, created = Customer.objects.get_or_create(first_name=first_name, last_name=last_name, email=email)

            comp_num = Registration.objects.filter(comp=comp,comp_role=comp_role).count() + 1
            comp_num = len(comp_roles)*comp_num-comp_roles.index(comp_role)
            try:
                prelims_reg_obj = Registration.objects.create(
                    competitor=competitor, comp_num=comp_num, comp=comp, comp_role=comp_role)

                competitor.save()
            
                prelims_reg_obj.save()
                return render(request, 'sc/comp_success.html', {'comp_num':comp_num})
            except IntegrityError:
                # Handle the unique constraint violation
                error_message = _("This competitor is already registered to competition.")
                return render(request, 'sc/comp_reg.html', {'form': form, 'comp': comp,'error_message':error_message})
    else:
        form = CompetitionRegForm(initial={'comp': comp,'user': request.user})
    
    return render(request, 'sc/comp_reg.html', {'form': form, 'comp': comp})

@login_required
def submit_results(request, comp_id):

    comp = Competition.objects.get(id=comp_id)
    judge = Judge.objects.filter(comp=comp,profile=request.user).first()

    if not judge or (comp.stage in ['r','p'] and not judge.prelims) or (comp.stage in ['d','f'] and not judge.finals):
        error_message = _("Current user is not a judge for this competition stage.")
        return render(request, 'sc/comp_judge.html', {'comp': comp, 'error_message':error_message})

    if comp.stage == 'r':
        error_message = _("Please wait while registration stage will be finished.")
        return render(request, 'sc/comp_judge.html', {'comp': comp, 'error_message':error_message})
    
    if comp.stage == 'd':
        return redirect('prelims_results', comp_id=comp_id)
    
    if comp.stage == 'p':
        registrations = Registration.objects.filter(comp=comp,comp_role=judge.prelims_role,comp_checked_in=True).order_by('comp_num') 
        redirect_view = 'prelims_results' 
        if PrelimsResult.objects.filter(judge__profile=request.user,judge__comp=comp).exists():
            return redirect(redirect_view, comp_id=comp_id)
    else:
        registrations = Registration.objects.filter(comp=comp,final_partner__isnull=False).order_by('final_heat_order')
        redirect_view = 'finals_results'
        if FinalsResult.objects.filter(judge__profile=request.user,judge__comp=comp).exists():
            return redirect(redirect_view, comp_id=comp_id)

    if request.method == 'POST':
        if comp.stage == 'p':
            form = PrelimsResultsForm(request.POST,initial={'comp': comp,'registrations':registrations})
        else:
            form = FinalsResultsForm(request.POST,initial={'comp': comp,'registrations':registrations})
        if form.is_valid():
            try:
                for reg in registrations:
                    comp_res = form.cleaned_data[f'competitor_{reg.comp_num}']
                    comp_comment = form.cleaned_data[f'comment_{reg.comp_num}']
                    if comp.stage == 'p':
                        
                        res_obj = PrelimsResult.objects.create(judge = judge, comp_reg=reg, 
                                                               result = comp_res, comment = comp_comment)
                    else:
                        
                        res_obj = FinalsResult.objects.create(judge = judge, comp_reg=reg, 
                                                              result = comp_res, comment = comp_comment)
                    res_obj.save()
                return redirect(redirect_view, comp_id=comp_id)
            except IntegrityError:
                # Handle the unique constraint violation
                error_message = _("This judge already submitted results.")
                return render(request, 'sc/comp_judge.html', {'form': form, 'comp': comp, 'error_message':error_message})
    else:
        if comp.stage == 'p':
            form = PrelimsResultsForm(initial={'comp': comp,'registrations':registrations})  
        else:
            form = FinalsResultsForm(initial={'comp': comp,'registrations':registrations})

    return render(request, 'sc/comp_judge.html', {'form': form, 'comp': comp})


def prelims_results(request, comp_id):
    comp = get_object_or_404(Competition, pk=comp_id)
    results = PrelimsResult.objects.filter(judge__comp=comp).order_by('comp_reg','judge__profile').all()
    judges = {}
    main_judge_idx = {}
    all_results_ready = True
    for comp_role in comp.comp_roles.all():
        judge_objs = Judge.objects.filter(comp=comp,prelims=True,prelims_role=comp_role).order_by('profile').all()
        role_judges = [j.profile for j in judge_objs]
        judges[comp_role] = role_judges
        main_judge_idx[comp_role] = [i for i,j in enumerate(judge_objs) if j.prelims_main_judge][0]
        role_results = [r for r in results if r.comp_reg.comp_role == comp_role]
        all_results_ready &= set(role_judges).issubset({result.judge.profile for result in role_results})

    context = {}

    user_is_judge = any(request.user in judges[comp_role] for comp_role in comp.comp_roles.all())

    if user_is_judge:
        if not all_results_ready:
            if request.user not in {result.judge.profile for result in results}:
                return redirect('submit_results', comp_id=comp_id)
            error_message = _("Waiting other judges to finish.")
            context['error_message'] = error_message
    elif not comp.results_visible:
        error_message = _("Prelims results are not available yet.")
        if comp.stage in ['d','f']:
            role_results_dict = {}
            for comp_role in comp.comp_roles.all():
                role_finalists = Registration.objects.filter(comp=comp,finalist=True,comp_role=comp_role).order_by('comp_num').all()
                if role_finalists:
                    role_results_dict[comp_role.pluralName] = {
                        'judges':[],'results':{(reg.comp_num,reg.competitor.fullName,reg):[] for reg in role_finalists}
                    }
                else:
                    context['error_message'] = error_message
            context['results_dict'] = role_results_dict
        else:
            context['error_message'] = error_message

    if context == {}:
        context['prelims_active'] = 1
        results_dict = {}
        for res in results:
            if res.comp_reg not in results_dict:
                results_dict[res.comp_reg] = []
            results_dict[res.comp_reg].append(res.get_result_display())

        role_results_dict = {}
        for comp_role in comp.comp_roles.all():

            def prelims_priority_rules(item1,item2):
                # compare by points
                c1_points = item1[1][-1]
                c2_points = item2[1][-1]
                #print('points:',c1_points,c2_points)
                if c1_points > c2_points:
                    return 1
                elif c1_points < c2_points:
                    return -1
                else:
                    # compare by Y's
                    c1_points = item1[1].count('Y')
                    c2_points = item2[1].count('Y')
                    #print('Ys:',c1_points,c2_points)
                    if c1_points > c2_points:
                        return 1
                    elif c1_points < c2_points:
                        return -1
                    else:
                        # compare with each other
                        new_dict = {item1[0]:[],item2[0]:[]}
                        for judge_points in zip(item1[1],item2[1]):
                            if judge_points == ('Y','Mb'):
                                judge_points = ('Y','')
                            if judge_points == ('Mb','Y'):
                                judge_points = ('','Y')
                            new_dict[item1[0]].append(judge_points[0])
                            new_dict[item2[0]].append(judge_points[1])
                        
                        c1_points = new_dict[item1[0]].count('Y')+ 0.5*new_dict[item1[0]].count('Mb')
                        c2_points = new_dict[item2[0]].count('Y')+ 0.5*new_dict[item2[0]].count('Mb')
                        #print('c2c:',c1_points,c2_points)
                        if c1_points > c2_points:
                            return 1
                        elif c1_points < c2_points:
                            return -1
                        else:
                            # compare by main judge
                            weight = {'Y':1,'Mb':0.5,'':0}
                            c1_points = weight[item1[1][main_judge_idx[comp_role]]]
                            c2_points = weight[item2[1][main_judge_idx[comp_role]]]
                            #print('main judge:',c1_points,c2_points)
                            if c1_points > c2_points:
                                return 1
                            elif c1_points < c2_points:
                                return -1
                            else:
                                # compare by finalist mark (conflict already resolved)
                                c1_points = 1 if item1[0][2].finalist else 0
                                c2_points = 1 if item2[0][2].finalist else 0
                                if c1_points > c2_points:
                                    return 1
                                elif c1_points < c2_points:
                                    return -1
                                else:
                                    conflicts.append((item1[0][0],item2[0][0]))
                                    # equal
                                    return 0

            tmp_dict = {
                (reg.comp_num,reg.competitor.fullName,reg):
                    res_list+[res_list.count('Y') + 0.5*res_list.count('Mb'),] 
                for reg,res_list in results_dict.items() if reg.comp_role == comp_role
            }
            conflicts = []
            tmp_dict = dict(sorted(tmp_dict.items(), key=cmp_to_key(prelims_priority_rules), reverse=True))

            role_results_dict[comp_role.pluralName] = {
                'judges':[j.first_name for j in judges[comp_role]],
                'results':tmp_dict,
            }            

            if comp.stage == 'p' and user_is_judge:
                # check if unresolved conflicts have impact on final list
                unique_conflicts = set(conflicts)
                conflicts = {}
                for c0,c1 in unique_conflicts:
                    places = { t[0]:i for i,t in enumerate(tmp_dict.keys())}    
                    if (places[c0] < comp.finalists_number) != (places[c1] < comp.finalists_number):
                        conflicts[c0]=places[c0]
                        conflicts[c1]=places[c1]
                        
                if conflicts != {}:
                    context['additional_info'] = _(f"Conflicts for competitors {list(conflicts.keys())} need to be resolved manually")
                else:
                    for i,t in enumerate(tmp_dict.keys()):
                        reg = t[2]
                        if i < comp.finalists_number:
                            reg.finalist=True
                        else:
                            reg.finalist=False
                        reg.save()

        if comp.stage == 'p' and user_is_judge:
            comp.stage = 'd'
            comp.save()

        if (comp.stage == 'f' and user_is_judge) or comp.results_visible:
            context['comp_id'] = comp_id


        context['results_dict'] = role_results_dict

    return render(request, 'sc/comp_results.html', context)

def finals_results(request, comp_id):
    comp = get_object_or_404(Competition, pk=comp_id)
    judges = Judge.objects.filter(comp=comp,finals=True).order_by('profile').all()
    results = FinalsResult.objects.filter(judge__comp=comp).order_by('judge__profile').all()
    results_ready = set(judges).issubset({result.judge for result in results})
    context = {'comp_id':comp_id}
    if request.user in [j.profile for j in judges]:
        if not results_ready:
            if request.user not in {result.judge.profile for result in results}:
                return redirect('submit_results', comp_id=comp_id)
            error_message = _("Waiting other judges to finish.")
            context['error_message'] = error_message
    else:
        if not comp.results_visible or not results_ready:
            error_message = _("Finals results are not available yet.")
            context['error_message'] = error_message
    
    if 'error_message' not in context:
        results_dict = {}
        for res in results:
            if res.comp_reg not in results_dict:
                results_dict[res.comp_reg] = []
            results_dict[res.comp_reg].append(res.result)

        judges_list = [j.profile.first_name for j in judges]
        tmp_dict = {
            (
                f'{reg.comp_num}/{reg.final_partner.comp_num}',
                f'{reg.competitor.first_name} - '+
                    f'{reg.final_partner.competitor.first_name}',
                reg,
            ): res_list
            for reg,res_list in results_dict.items()
        }

        sctable = calculate_skating(judges_list,tmp_dict) 
        tmp_dict = {sc_line[0]:sc_line[1:] for sc_line in sctable[1:]}
        tmp_dict = dict(sorted(tmp_dict.items(), key=lambda item: str(item[1][-1])))
        
        results_dict = {
            'judges':sctable[0][1:],
            'results':tmp_dict,
        }  
        context['results_dict'] = {'':results_dict}

    return render(request, 'sc/comp_results.html', context)
    
